#!/usr/bin/env python3
"""AgentSkillsHub (agentskillshub.top) Entity Molecule & 3-Layer Verification Audit.

Ported from jasonzhu.ai/ops/geo/geo_engine.py (L2 Dennis Yu Entity Molecule +
Andrea Volpini cross-page @id graph + Duane Forrester Parametric vs Live RAG split).

Usage:
  python3 ops/geo/entity_audit.py --mode molecule          # Layer A live audit (free, no keys)
  python3 ops/geo/entity_audit.py --mode full              # Layer A + B (GoAnyAPI) + C (AIsa)
  python3 ops/geo/entity_audit.py --mode molecule --no-save

Node 1 also applies the relation rules in entity_edges.py: the founder, Agent Skills Hub and the
operating company stay separate entities (split 2026-11-24); run them alone with
`python3 ops/geo/entity_edges.py`.
Node 7 (fact consistency) checks that the nodes agree on the facts in
brand-facts.json; run it alone with `python3 ops/geo/fact_consistency.py`.
Node 8 (academic index) checks that every DOI on the ORCID record resolves and is filed under us at
DataCite and OpenAlex; run it alone with `python3 ops/geo/academic_index.py`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GEO_DIR = Path(__file__).resolve().parent
PANEL_DIR = GEO_DIR / "panel"
SITE = "https://agentskillshub.top"
UA = "AgentSkillsHub-EntityAudit/1.0 (+https://agentskillshub.top/ai-info/)"


def http_get(url: str, headers: dict[str, str] | None = None, timeout: float = 12.0) -> tuple[int, dict[str, str], str]:
    req_headers = {"User-Agent": UA}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, hdrs, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as exc:
        hdrs = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
        return exc.code, hdrs, exc.read().decode("utf-8", "ignore")[:1000]
    except Exception as exc:
        return -1, {}, str(exc)


def http_post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: float = 35.0) -> tuple[int, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "ignore")[:1000]
    except Exception as exc:
        return -1, str(exc)


def extract_jsonld_graph(html: str) -> dict[str, Any]:
    blocks = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S)
    ids: list[str] = []
    same_as: list[str] = []
    types: list[str] = []
    parse_errors = 0

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            if isinstance(obj.get("@id"), str):
                ids.append(obj["@id"])
            t = obj.get("@type")
            if isinstance(t, str):
                types.append(t)
            elif isinstance(t, list):
                types.extend(str(x) for x in t)
            sa = obj.get("sameAs")
            if isinstance(sa, list):
                same_as.extend(str(x) for x in sa)
            elif isinstance(sa, str):
                same_as.append(sa)
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    for raw in blocks:
        try:
            walk(json.loads(raw.strip()))
        except Exception:
            parse_errors += 1

    return {
        "blocks": len(blocks),
        "parse_errors": parse_errors,
        "types": sorted(set(types)),
        "at_ids": sorted(set(ids)),
        "same_as_count": len(set(same_as)),
    }


def audit_entity_home() -> dict[str, Any]:
    urls = [f"{SITE}/", f"{SITE}/about/", f"{SITE}/ai-info/", f"{SITE}/contact/"]
    pages = []
    id_map: dict[str, list[str]] = {}
    home_signals: dict[str, bool] = {}
    html_by_path: dict[str, str] = {}

    for url in urls:
        code, _, html = http_get(url)
        if code != 200:
            pages.append({"url": url, "http_status": code, "error": html[:160]})
            continue
        html_by_path[url[len(SITE):]] = html
        g = extract_jsonld_graph(html)
        for eid in g["at_ids"]:
            id_map.setdefault(eid, []).append(url)
        page_info = {
            "url": url,
            "http_status": code,
            **g,
            "has_disambiguation_dev": "agentskillshub.dev" in html,
            "has_doi_21292799": "10.5281/zenodo.21292799" in html,
            "has_doi_24387074": "10.5281/zenodo.24387074" in html,
            "has_wikidata_q141986406": "Q141986406" in html,
        }
        pages.append(page_info)
        if url == f"{SITE}/":
            home_signals = {
                "org_id_present": f"{SITE}/#organization" in g["at_ids"],
                "cross_site_person_id_present": "https://jasonzhu.ai/#person" in g["at_ids"],
                "dataset_id_present": f"{SITE}/#dataset" in g["at_ids"],
                "disambiguation_visible": "agentskillshub.dev" in html,
                "doi_21292799_present": "10.5281/zenodo.21292799" in html,
                "doi_24387074_present": "10.5281/zenodo.24387074" in html,
                "no_2024_founding_ambiguity": "since 2024" not in html.lower(),
            }

    shared_ids = {k: v for k, v in id_map.items() if len(v) > 1}
    status = "VERIFIED" if (
        home_signals.get("org_id_present")
        and home_signals.get("cross_site_person_id_present")
        and home_signals.get("doi_24387074_present")
        and len(shared_ids) >= 2
    ) else "PARTIAL"

    # The graph can be connected and still describe the founder, the product and the company as one
    # thing; it did until 2026-11-24 and this node said VERIFIED. entity_edges.py holds those rules.
    from entity_edges import audit_entity_edges  # sibling module; script dir is on sys.path
    relations = audit_entity_edges(http_get, html_by_path)
    if relations["issues"]:
        status = "ISSUES_FOUND"
    elif relations["status"] != "VERIFIED":
        status = "PARTIAL"

    return {
        "node": "1_Entity_Home_Connected_Graph",
        "status": status,
        "shared_at_ids_across_pages": shared_ids,
        "home_signals": home_signals,
        "pages": pages,
        "relations": relations,
    }


def audit_wikidata() -> dict[str, Any]:
    qids = {"organization": "Q141986406", "dataset": "Q141735092"}
    items = {}
    all_alive = True
    for role, qid in qids.items():
        code, _, body = http_get(f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={qid}&format=json")
        if code != 200:
            items[role] = {"qid": qid, "status": "UNKNOWN", "http_status": code}
            all_alive = False
            continue
        ent = json.loads(body).get("entities", {}).get(qid, {})
        missing = "missing" in ent
        claims = sorted(ent.get("claims", {}).keys())
        sitelinks = list(ent.get("sitelinks", {}).keys())
        if missing:
            all_alive = False
        gaps = []
        if role == "organization":
            for prop, label in [("P112", "founder"), ("P2037", "GitHub_username")]:
                if prop not in claims:
                    gaps.append(f"{prop}:{label}")
            p856_refs = sum(len(c.get("references", [])) for c in ent.get("claims", {}).get("P856", []))
            if p856_refs < 2:
                gaps.append(f"P856:refs<2(now={p856_refs})")
        items[role] = {
            "qid": qid,
            "alive": not missing,
            "label_en": ent.get("labels", {}).get("en", {}).get("value"),
            "claims_count": len(claims),
            "claims": claims,
            "sitelinks_count": len(sitelinks),
            "recommended_additions": gaps,
        }
    has_gaps = any(items[r].get("recommended_additions") for r in items)
    return {
        "node": "2_Wikidata_Knowledge_Graph",
        "status": ("PARTIAL_NEEDS_REINFORCEMENT" if has_gaps else "VERIFIED") if all_alive else "DEGRADED",
        "items": items,
    }


def audit_academic_graph() -> dict[str, Any]:
    dois = ["10.5281/zenodo.21292799", "10.5281/zenodo.24387074"]
    records = []
    all_bidirectional = True
    for doi in dois:
        dc_code, _, dc_body = http_get(f"https://api.datacite.org/dois/{doi}")
        oa_code, _, oa_body = http_get(f"https://api.openalex.org/works/https://doi.org/{doi}")
        rel_ids = []
        if dc_code == 200:
            rel_ids = json.loads(dc_body).get("data", {}).get("attributes", {}).get("relatedIdentifiers", [])
        backlinks_to_ash = [
            r for r in rel_ids
            if "agentskillshub.top" in str(r.get("relatedIdentifier", "")).lower()
            and r.get("relationType") in ("IsDocumentedBy", "IsSupplementTo", "HasMetadata")
        ]
        if not backlinks_to_ash:
            all_bidirectional = False
        oa_title = json.loads(oa_body).get("title") if oa_code == 200 else None
        records.append({
            "doi": doi,
            "datacite_http": dc_code,
            "openalex_http": oa_code,
            "openalex_title": oa_title,
            "related_identifiers": rel_ids,
            "has_ash_backlink_edge": len(backlinks_to_ash) > 0,
        })
    return {
        "node": "3_CERN_Zenodo_DataCite_OpenAlex",
        "status": "VERIFIED" if all_bidirectional else "PARTIAL_MISSING_BACKLINK_EDGE",
        "records": records,
    }


def audit_github_node() -> dict[str, Any]:
    rc, _, rb = http_get("https://api.github.com/repos/zhuyansen/agent-skills-hub")
    pc, _, pb = http_get("https://raw.githubusercontent.com/zhuyansen/zhuyansen/main/README.md")
    repo_info = {}
    if rc == 200:
        d = json.loads(rb)
        repo_info = {
            "full_name": d.get("full_name"),
            "homepage": d.get("homepage"),
            "stars": d.get("stargazers_count"),
            "description": d.get("description"),
        }
    profile_mentions_ash = (pc == 200) and ("agentskillshub.top" in pb.lower())
    profile_mentions_2129 = (pc == 200) and ("21292799" in pb)
    ok = ("agentskillshub.top" in str(repo_info.get("homepage", "")).lower()) and profile_mentions_ash
    return {
        "node": "4_GitHub_Developer_Node",
        "status": "VERIFIED" if ok else "PARTIAL",
        "repo": repo_info,
        "profile_readme_mentions_ash": profile_mentions_ash,
        "profile_readme_cites_21292799": profile_mentions_2129,
    }


def audit_ecosystem_and_edge() -> tuple[dict[str, Any], dict[str, Any]]:
    pkgs = {}
    for pkg in ["@agentskillshub/cli", "@agentskillshub/mcp"]:
        code, _, body = http_get(f"https://registry.npmjs.org/{urllib.parse.quote(pkg, safe='')}")
        latest = None
        if code == 200:
            latest = json.loads(body).get("dist-tags", {}).get("latest")
        pkgs[pkg] = {"http_status": code, "latest": latest}

    sc_code, _, sc_body = http_get(f"{SITE}/.well-known/mcp/server-card.json")
    llms_code, _, llms_body = http_get(f"{SITE}/llms.txt")
    eco_ok = all(v["http_status"] == 200 for v in pkgs.values()) and sc_code == 200 and llms_code == 200
    eco = {
        "node": "5_Package_MCP_Ecosystem",
        "status": "VERIFIED" if eco_ok else "PARTIAL",
        "npm_packages": pkgs,
        "mcp_server_card_http": sc_code,
        "llms_txt_http": llms_code,
        "llms_txt_cites_24387074": "24387074" in llms_body if llms_code == 200 else False,
    }

    rb_code, _, rb_body = http_get(f"{SITE}/robots.txt")
    md_code, md_hdrs, _ = http_get(f"{SITE}/", headers={"Accept": "text/markdown, text/html;q=0.9"})
    edge = {
        "node": "6_Edge_Agent_Readiness",
        "status": "VERIFIED" if ("content-signal" in rb_body.lower() and "text/markdown" in md_hdrs.get("content-type", "").lower()) else "PARTIAL_EDGE_WORKER_PENDING",
        "robots_has_content_signal": "content-signal" in rb_body.lower() if rb_code == 200 else False,
        "markdown_negotiation_content_type": md_hdrs.get("content-type"),
        "rfc8288_link_header_present": "link" in md_hdrs,
        "server_header": md_hdrs.get("server"),
    }
    return eco, edge


def run_serp_probes() -> dict[str, Any]:
    api_key = os.getenv("GOANYAPI_API_KEY", "").strip()
    if not api_key:
        return {"status": "SKIPPED_NO_GOANYAPI_API_KEY"}
    probes = [
        ("doi_21292799", '"10.5281/zenodo.21292799"'),
        ("doi_24387074", '"10.5281/zenodo.24387074"'),
        ("wikidata_q141986406", '"Q141986406" "agentskillshub"'),
        ("third_party_mentions", '"agentskillshub.top" -site:agentskillshub.top'),
        ("github_badge_adoption", 'site:github.com "agentskillshub.top/badge/"'),
    ]
    details = []
    indexed = 0
    for pid, q in probes:
        url = f"https://www.goanyapi.com/api/v1/serp?{urllib.parse.urlencode({'q': q, 'gl': 'US', 'hl': 'en'})}"
        code, _, body = http_get(url, headers={"Authorization": f"Bearer {api_key}"}, timeout=20.0)
        if code != 200:
            details.append({"probe_id": pid, "query": q, "error": f"HTTP {code}: {body[:160]}"})
            continue
        organic = (json.loads(body).get("result") or {}).get("organic") or []
        if organic:
            indexed += 1
        details.append({
            "probe_id": pid,
            "query": q,
            "indexed": bool(organic),
            "hit_count": len(organic),
            "top_3": [{"title": o.get("title"), "url": o.get("link")} for o in organic[:3]],
        })
    return {"status": "COMPLETED", "probes_indexed": f"{indexed}/{len(probes)}", "details": details}


def run_forrester_split_probe() -> dict[str, Any]:
    api_key = os.getenv("AISA_API_KEY", "").strip()
    if not api_key:
        return {"status": "SKIPPED_NO_AISA_API_KEY"}
    base = os.getenv("AISA_API_BASE_URL", "https://api.aisa.one/v1").rstrip("/")
    prompt = (
        "What is Agent Skills Hub (agentskillshub.top)? Who founded it, when did it launch, "
        "which company operates it, what open security dataset (Zenodo DOI) did it publish, "
        "and is it affiliated with agentskillshub.dev?"
    )
    results = []
    for model, layer in [
        ("perplexity/sonar", "Live_Web_RAG_Retrieval (Forrester Layer 2)"),
        ("gpt-4o-mini", "Parametric_Pretrain_Memory (Forrester Layer 1)"),
    ]:
        code, resp = http_post_json(
            f"{base}/chat/completions",
            {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.1},
            {"Authorization": f"Bearer {api_key}"},
        )
        if code != 200 or not isinstance(resp, dict):
            results.append({"model": model, "layer": layer, "error": f"HTTP {code}: {str(resp)[:200]}"})
            continue
        ans = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        low = ans.lower()
        results.append({
            "model": model,
            "layer": layer,
            "checks": {
                "mentions_top_domain": "agentskillshub.top" in low,
                "mentions_jason_zhu": "jason zhu" in low or "yansen" in low,
                "mentions_2026_03_08": "2026-03-08" in low or "march 8, 2026" in low,
                "mentions_gosailglobal": "gosailglobal" in low or "brickai" in low,
                "mentions_zenodo_doi": "21292799" in low or "24387074" in low,
                "correctly_disambiguates_dev": ("not affiliated" in low or "unaffiliated" in low) and "agentskillshub.dev" in low,
            },
            "answer_preview": ans[:420],
        })
    return {"status": "COMPLETED", "probes": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="AgentSkillsHub Entity Molecule & 3-Layer GEO Audit")
    parser.add_argument("--mode", choices=["molecule", "full"], default="molecule")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tag = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M")

    from academic_index import audit_academic_index    # sibling modules; script dir is on sys.path
    from fact_consistency import audit_fact_consistency

    eco, edge = audit_ecosystem_and_edge()
    nodes = [
        audit_entity_home(),
        audit_wikidata(),
        audit_academic_graph(),
        audit_github_node(),
        eco,
        edge,
        audit_fact_consistency(http_get),
        audit_academic_index(http_get),
    ]
    report: dict[str, Any] = {
        "timestamp_utc": ts,
        "domain": "agentskillshub.top",
        "mode": args.mode,
        "layer_A_entity_molecule": nodes,
        "verified_receipt": (
            f"Verified: Audited {len(nodes)} live molecule nodes for agentskillshub.top | "
            f"Statuses: {', '.join(n['node'] + '=' + n['status'] for n in nodes)} | Timestamp: {ts}"
        ),
    }
    if args.mode == "full":
        report["layer_B_google_us_serp"] = run_serp_probes()
        report["layer_C_forrester_split"] = run_forrester_split_probe()

    if not args.no_save:
        PANEL_DIR.mkdir(parents=True, exist_ok=True)
        out = PANEL_DIR / f"entity-audit-{tag}.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report["saved_snapshot"] = str(out)

    print("=== AgentSkillsHub Entity Molecule Scoreboard ===")
    for n in nodes:
        print(f"  [{n['status']:28s}] {n['node']}")
    by_name = {n["node"]: n for n in nodes}
    for i in by_name["1_Entity_Home_Connected_Graph"].get("relations", {}).get("issues", []):
        print(f"      - rule {i['rule']} {i['page']} {i['node']}: {i['detail']}")
    for c in by_name["7_Fact_Consistency"].get("conflicts", []):
        print(f"      - {c['fact']} @ {c['source']}: found '{c['found']}' ({c['why']})")
    for i in by_name["8_Academic_Index"].get("issues", []):
        print(f"      - {i['kind']} {i['doi']}: {i['detail']}")
    if "saved_snapshot" in report:
        print(f"\nSnapshot saved: {report['saved_snapshot']}")
    print(report["verified_receipt"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
