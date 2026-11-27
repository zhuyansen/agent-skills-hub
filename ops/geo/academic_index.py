#!/usr/bin/env python3
"""Entity-audit node 8: are our papers and datasets where scholarly indexes can find them, under our name?

Node 3 asks whether two DOIs answer at DataCite and OpenAlex. This asks the questions that went wrong on
2026-11-22 without node 3 noticing:
  - a published DOI that doi.org cannot resolve (10.5281/zenodo.24420920 was never registered);
  - a DataCite record naming the same person twice, or without the ORCID (21292799 had both
    "zhu, yansen" and "Jason Zhu"; 24386243 had no ORCID);
  - OpenAlex filing our work under someone else (it matched "zhu, yansen" to 竹彦 森, A5009989201).

The works come from the public ORCID record, so a new paper is checked from the day it is added there.
For each DOI: doi.org (handle API), DataCite creators, OpenAlex authorships, Semantic Scholar, Wikidata.
Missing from OpenAlex / Semantic Scholar / Wikidata is coverage, not an issue: indexing takes weeks.

An OpenAlex author page is ours when it carries our ORCID, or when most of its works are ours (the ORCID
works plus the concept DOI of each, from DataCite's IsVersionOf, because OpenAlex files the concept DOIs).
A page that only shares the name is not: until 2026-11-27 any "Jason Zhu" counted, so a Stanford
researcher's page holding one of our datasets was called ours and the fix said to merge it. Maintenance
rule 1 fixes misfiled works only: no claiming, no merging. A same-name page whose works could not be read
is unverified (PARTIAL_FETCH), never ours.

Free APIs, no keys. Pure checks in `check_work` and `summarize`; `audit_academic_index` does the fetching.

  python3 ops/geo/academic_index.py           # readable report
  python3 ops/geo/academic_index.py --json    # what the daily digest reads
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

GEO_DIR = Path(__file__).resolve().parent
ORCID = "0009-0000-2894-6285"
PENDING_DAYS = 2            # a DOI younger than this may still be on its way to DataCite
FIX_CREATORS = "jasonzhu.ai: ops/geo/zenodo/fix_creators.py（把记录号加进 RECORDS，先预览再 --apply）"
LOG = "jasonzhu.ai: ops/geo/ENTITY-GRAPH-ITERATION-LOG.md"
MISATTRIBUTED_FIX = ("DataCite 改对后等 OpenAlex 刷新（约两天）；还不对就提工单，请 OpenAlex 把 {work} 从 {author} 移走。"
                     "只修挂错人，不认领、不合并作者页（维护规则 1）")

HttpGet = Callable[..., tuple[int, dict[str, str], str]]


# ---------------------------------------------------------------- names

def is_ours(name: str | None) -> bool:
    """'Zhu, Jason', 'J ZHU', 'zhu, yansen', 'Yansen Zhu', '祝彦森' are us; '竹彦 森' is not."""
    if not name:
        return False
    if "祝彦森" in name.replace(" ", ""):
        return True
    tokens = re.findall(r"[a-z]+", name.lower())
    rest = [t for t in tokens if t != "zhu"]
    return "zhu" in tokens and bool(rest) and all(t in {"jason", "yansen", "j", "y"} for t in rest)


def has_our_orcid(ids: list[str]) -> bool:
    return any(ORCID in (i or "") for i in ids)


# ---------------------------------------------------------------- pure checks

def zenodo_record(doi: str) -> str:
    m = re.match(r"10\.5281/zenodo\.(\d+)$", doi, re.I)
    return m.group(1) if m else ""


def author_verdict(a: dict[str, Any], work: dict[str, Any]) -> tuple[str, str]:
    """'ours', 'theirs' or 'unverified' for an authorship that carries our name, and the reason in words.

    work["our_dois"]: our DOIs, versions and concepts; work["author_works"]: {author_id: [doi] or None}.
    """
    if a.get("orcid") and ORCID in a["orcid"]:
        return "ours", "ORCID 一致"
    dois = (work.get("author_works") or {}).get(a.get("author_id"))
    if dois is None:
        return "unverified", ""
    ours = {d.lower() for d in work.get("our_dois") or ()}
    total = len(dois)                                # one entry per work; "" for a work without a DOI
    mine = sum(1 for d in dois if d and d.lower() in ours)
    if total and mine * 2 > total:
        return "ours", f"这个作者页 {total} 个作品里 {mine} 个是你的"
    return "theirs", f"这个作者页 {total} 个作品里只有 {mine} 个是你的"


def check_work(work: dict[str, Any], today: date) -> dict[str, Any]:
    """One work's fetched facts -> its row: where it is indexed and what is wrong with it.

    work: {doi, title, published (YYYY-MM-DD or ''), handle (True/False/None), datacite_creators
           ([{name, ids}] or None), openalex ({id, authorships: [{author_id, display_name, raw, orcid}]} or None),
           semantic_scholar (True/False/None), wikidata (QID or '')}
    """
    doi, issues, notes = work["doi"], [], []
    record = zenodo_record(doi)
    age = None
    if work.get("published"):
        try:
            age = (today - date.fromisoformat(work["published"][:10])).days
        except ValueError:
            age = None

    # 1. the DOI resolves
    if work.get("handle") is False:
        if age is not None and age < PENDING_DAYS:
            notes.append(f"doi.org 还解析不了，发布才 {age} 天，等登记")
        else:
            fix = (f"先在 Zenodo 打开 https://zenodo.org/records/{record} 点 Edit → Publish（不改内容）触发重新登记；"
                   f"一天后还不行就到 https://zenodo.org/support 提工单，模板见 {LOG}") if record else "联系发布方"
            issues.append({"kind": "doi_unresolved", "doi": doi,
                           "detail": f"doi.org 解析不了（发布 {age if age is not None else '?'} 天）", "fix": fix})

    # 2. DataCite names us once, with the ORCID
    creators = work.get("datacite_creators")
    if creators is not None:
        ours = [c for c in creators if has_our_orcid(c.get("ids", [])) or is_ours(c.get("name"))]
        if len(ours) > 1:
            issues.append({"kind": "creator_duplicate", "doi": doi,
                           "detail": "同一个人登记成了 " + "、".join(f"「{c.get('name')}」" for c in ours),
                           "fix": FIX_CREATORS})
        for c in ours:
            if not has_our_orcid(c.get("ids", [])):
                issues.append({"kind": "creator_no_orcid", "doi": doi,
                               "detail": f"作者「{c.get('name')}」没挂 ORCID", "fix": FIX_CREATORS})

    # 3. OpenAlex files it under us
    oa = work.get("openalex")
    our_authors: list[str] = []
    unverified: list[str] = []
    if oa:
        for a in oa.get("authorships", []):
            if not is_ours(a.get("raw")):
                continue
            aid = a.get("author_id") or ""
            wrong_name = not is_ours(a.get("display_name"))
            wrong_orcid = bool(a.get("orcid")) and ORCID not in a["orcid"]
            verdict, why = ("theirs", "") if (wrong_name or wrong_orcid) else author_verdict(a, work)
            if verdict == "ours":
                our_authors.append(aid)
                if not a.get("orcid"):
                    notes.append(f"OpenAlex 作者 {aid} 没挂 ORCID；{why}，算是你")
            elif verdict == "unverified":
                unverified.append(aid)
                notes.append(f"OpenAlex 作者 {aid}「{a.get('display_name')}」同名、没挂 ORCID，作品列表没读到，没法确认是不是你")
            else:
                issues.append({"kind": "openalex_misattributed", "doi": doi,
                               "detail": (f"OpenAlex 把署名「{a.get('raw')}」归到了别人 {aid}"
                                          f"（{a.get('display_name')}"
                                          + ("，挂的是别人的 ORCID" if wrong_orcid else "")
                                          + (f"，{why}" if why else "") + f"），作品 {oa.get('id')}"),
                               "fix": MISATTRIBUTED_FIX.format(work=oa.get("id"), author=aid)})

    return {
        "doi": doi, "title": work.get("title", ""), "published": work.get("published", ""),
        "resolves": work.get("handle"), "openalex": (oa or {}).get("id", "") if oa else "",
        "semantic_scholar": work.get("semantic_scholar"), "wikidata": work.get("wikidata", ""),
        "our_openalex_authors": sorted(set(filter(None, our_authors))),
        "unverified_openalex_authors": sorted(set(filter(None, unverified))), "issues": issues, "notes": notes,
    }


def summarize(rows: list[dict[str, Any]], orcid_author: str, fetch_errors: dict[str, str]) -> dict[str, Any]:
    n = len(rows)
    issues = [i for r in rows for i in r["issues"]]
    authors = sorted({a for r in rows for a in r["our_openalex_authors"]})
    unverified = sorted({a for r in rows for a in r.get("unverified_openalex_authors", [])} - set(authors))
    notes = []
    if len(authors) > 1:
        # A split is not one of the three errors rule 1 fixes; merging pages is what it rules out.
        notes.append(f"OpenAlex 里你有 {len(authors)} 个作者页：{'、'.join(authors)}。按维护规则 1 不认领、不合并，作品挂对人就行")
    status = "ISSUES_FOUND" if issues else ("PARTIAL_FETCH" if fetch_errors or not n or unverified else "VERIFIED")
    return {
        "node": "8_Academic_Index",
        "status": status,
        "works": rows,
        "issues": issues,
        "notes": notes,
        "openalex_unverified_authors": unverified,
        "coverage": {
            "works": n,
            "doi_resolves": sum(1 for r in rows if r["resolves"]),
            "openalex": sum(1 for r in rows if r["openalex"]),
            "semantic_scholar": sum(1 for r in rows if r["semantic_scholar"]),
            "wikidata": sum(1 for r in rows if r["wikidata"]),
        },
        "openalex_orcid_author": orcid_author,
        "openalex_our_authors": authors,
        "fetch_errors": fetch_errors,
    }


# ---------------------------------------------------------------- fetching

def _json(code: int, body: str) -> Any:
    if code != 200:
        return None
    try:
        return json.loads(body)
    except ValueError:
        return None


def orcid_works(http_get: HttpGet) -> list[dict[str, str]] | None:
    data = _json(*http_get(f"https://pub.orcid.org/v3.0/{ORCID}/works", {"Accept": "application/json"})[::2])
    if data is None:
        return None
    out = []
    for g in data.get("group", []):
        s = g["work-summary"][0]
        doi = next((e["external-id-value"] for e in s.get("external-ids", {}).get("external-id", [])
                    if e.get("external-id-type") == "doi"), "")
        if not doi:
            continue
        pd = s.get("publication-date") or {}
        parts = [(pd.get(k) or {}).get("value") for k in ("year", "month", "day")]
        published = "-".join(p for p in parts if p) if all(parts) else ""
        out.append({"doi": doi.lower(), "title": s["title"]["title"]["value"], "published": published})
    return out


def fetch_work(http_get: HttpGet, w: dict[str, str], wikidata: dict[str, str]) -> dict[str, Any]:
    doi = w["doi"]
    work: dict[str, Any] = dict(w)
    code, _, body = http_get(f"https://doi.org/api/handles/{doi}")
    handle = _json(200, body) if code in (200, 404) else None    # 404 still carries {"responseCode": 100}
    work["handle"] = None if handle is None else handle.get("responseCode") == 1

    dc = _json(*http_get(f"https://api.datacite.org/dois/{doi}")[::2])
    if dc:
        creators = dc["data"]["attributes"].get("creators", [])
        work["datacite_creators"] = [{"name": c.get("name"),
                                      "ids": [n.get("nameIdentifier", "") for n in c.get("nameIdentifiers", [])]}
                                     for c in creators]
        work["concept_dois"] = [str(r.get("relatedIdentifier", "")).lower()
                                for r in dc["data"]["attributes"].get("relatedIdentifiers") or []
                                if r.get("relationType") == "IsVersionOf" and r.get("relatedIdentifierType") == "DOI"]
    else:
        work["datacite_creators"] = None
        work["concept_dois"] = []

    oa = _json(*http_get(f"https://api.openalex.org/works/doi:{doi}?select=id,authorships")[::2])
    work["openalex"] = None if not oa else {
        "id": oa["id"].rsplit("/", 1)[-1],
        "authorships": [{"author_id": (a.get("author") or {}).get("id", "").rsplit("/", 1)[-1],
                         "display_name": (a.get("author") or {}).get("display_name"),
                         "raw": a.get("raw_author_name"),
                         "orcid": (a.get("author") or {}).get("orcid") or ""} for a in oa.get("authorships", [])],
    }

    code, _, body = http_get(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title")
    work["semantic_scholar"] = True if code == 200 else (False if code == 404 else None)   # 429: unknown
    work["wikidata"] = wikidata.get(doi.upper(), "")
    return work


def openalex_author_dois(http_get: HttpGet, author_id: str) -> list[str] | None:
    """The DOIs of an OpenAlex author page's works, or None if they could not be read."""
    data = _json(*http_get(f"https://api.openalex.org/works?filter=author.id:{author_id}&per-page=200&select=doi")[::2])
    if data is None:
        return None
    return [str(r.get("doi") or "").lower().removeprefix("https://doi.org/") for r in data.get("results", [])]


def wikidata_items(http_get: HttpGet, dois: list[str]) -> dict[str, str] | None:
    values = " ".join(f'"{d.upper()}"' for d in dois)
    query = f"SELECT ?item ?doi WHERE {{ VALUES ?doi {{ {values} }} ?item wdt:P356 ?doi }}"
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": query})
    data = _json(*http_get(url, {"Accept": "application/sparql-results+json"})[::2])
    if data is None:
        return None
    return {b["doi"]["value"]: b["item"]["value"].rsplit("/", 1)[-1] for b in data["results"]["bindings"]}


def audit_academic_index(http_get: HttpGet, today: date | None = None, pause: float = 1.0) -> dict[str, Any]:
    today = today or datetime.now(timezone.utc).date()
    errors: dict[str, str] = {}
    works = orcid_works(http_get)
    if works is None:
        return summarize([], "", {"orcid": "ORCID works unreadable"})
    wikidata = wikidata_items(http_get, [w["doi"] for w in works])
    if wikidata is None:
        errors["wikidata"] = "SPARQL unreadable"
        wikidata = {}
    fetched = []
    for w in works:
        fetched.append(fetch_work(http_get, w, wikidata))
        time.sleep(pause)                          # Semantic Scholar allows about one request a second without a key
    our_dois = {w["doi"].lower() for w in fetched} | {c for w in fetched for c in w.get("concept_dois", [])}
    same_name = sorted({a["author_id"] for w in fetched for a in (w.get("openalex") or {}).get("authorships", [])
                        if a.get("author_id") and not a.get("orcid") and is_ours(a.get("raw")) and is_ours(a.get("display_name"))})
    author_works = {aid: openalex_author_dois(http_get, aid) for aid in same_name}
    rows = [check_work(w | {"our_dois": our_dois, "author_works": author_works}, today) for w in fetched]
    author = _json(*http_get(f"https://api.openalex.org/authors/orcid:{ORCID}?select=id")[::2])
    return summarize(rows, (author or {}).get("id", "").rsplit("/", 1)[-1], errors)


# ---------------------------------------------------------------- report

def print_report(node: dict[str, Any]) -> None:
    c = node["coverage"]
    print(f"Node 8 academic index: {node['status']}")
    print(f"  {c['works']} works on ORCID · doi.org resolves {c['doi_resolves']} · OpenAlex {c['openalex']} · "
          f"Semantic Scholar {c['semantic_scholar']} · Wikidata {c['wikidata']}")
    print(f"  OpenAlex author with our ORCID: {node['openalex_orcid_author'] or 'none'} · "
          f"our authorships sit on: {', '.join(node['openalex_our_authors']) or 'none'}")
    for name, err in node["fetch_errors"].items():
        print(f"  ! {name}: {err}")
    for i in node["issues"]:
        print(f"\n  [{i['kind']}] {i['doi']}\n    {i['detail']}\n    fix: {i['fix']}")
    for n in node.get("notes", []):
        print(f"  · {n}")
    for r in node["works"]:
        for n in r["notes"]:
            print(f"  · {r['doi']}: {n}")


def main() -> int:
    sys.path.insert(0, str(GEO_DIR))
    from entity_audit import http_get  # same UA and timeouts as the rest of the audit

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    node = audit_academic_index(http_get)
    if a.json:
        print(json.dumps(node, ensure_ascii=False, indent=2))
    else:
        print_report(node)
    return 0


if __name__ == "__main__":
    sys.exit(main())
