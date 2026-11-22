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
    if oa:
        for a in oa.get("authorships", []):
            if not is_ours(a.get("raw")):
                continue
            wrong_name = not is_ours(a.get("display_name"))
            wrong_orcid = bool(a.get("orcid")) and ORCID not in a["orcid"]
            if wrong_name or wrong_orcid:
                issues.append({"kind": "openalex_misattributed", "doi": doi,
                               "detail": (f"OpenAlex 把署名「{a.get('raw')}」归到了别人 {a.get('author_id')}"
                                          f"（{a.get('display_name')}"
                                          + ("，挂的是别人的 ORCID" if wrong_orcid else "") + f"），作品 {oa.get('id')}"),
                               "fix": ("DataCite 改对后等 OpenAlex 刷新（约两天）；还不对就在 openalex.org 关联 ORCID、"
                                       f"认领自己的作者页后添加这条作品，或提工单让 {a.get('author_id')} 移走 {oa.get('id')}")})
            else:
                our_authors.append(a.get("author_id") or "")
                if not a.get("orcid"):
                    notes.append(f"OpenAlex 作者 {a.get('author_id')} 没挂 ORCID（认领后会补上）")

    return {
        "doi": doi, "title": work.get("title", ""), "published": work.get("published", ""),
        "resolves": work.get("handle"), "openalex": (oa or {}).get("id", "") if oa else "",
        "semantic_scholar": work.get("semantic_scholar"), "wikidata": work.get("wikidata", ""),
        "our_openalex_authors": sorted(set(filter(None, our_authors))), "issues": issues, "notes": notes,
    }


def summarize(rows: list[dict[str, Any]], orcid_author: str, fetch_errors: dict[str, str]) -> dict[str, Any]:
    n = len(rows)
    issues = [i for r in rows for i in r["issues"]]
    authors = sorted({a for r in rows for a in r["our_openalex_authors"]})
    if len(authors) > 1:
        issues.append({"kind": "openalex_split", "doi": "",
                       "detail": f"OpenAlex 把你拆成了 {len(authors)} 个作者：{'、'.join(authors)}",
                       "fix": "openalex.org 登录 → Settings → Link ORCID，认领后把另几个作者页的作品添加进来（添加即合并）"})
    status = "ISSUES_FOUND" if issues else ("PARTIAL_FETCH" if fetch_errors or not n else "VERIFIED")
    return {
        "node": "8_Academic_Index",
        "status": status,
        "works": rows,
        "issues": issues,
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
    else:
        work["datacite_creators"] = None

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
    rows = []
    for w in works:
        rows.append(check_work(fetch_work(http_get, w, wikidata), today))
        time.sleep(pause)                          # Semantic Scholar allows about one request a second without a key
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
