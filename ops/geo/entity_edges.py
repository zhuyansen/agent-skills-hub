#!/usr/bin/env python3
"""Entity-audit node 1, relation rules: the founder, Agent Skills Hub and the operating company stay separate.

Node 1 checks that the pages carry the @id graph. Until 2026-11-24 it did not notice that the JSON-LD
described the three as one thing (fixed in 77e2eb2):
  - the Agent Skills Hub organization carried the company's legal name, "BRICKAI (GoSailGlobal LLC)";
  - its sameAs listed the founder's own X and YouTube accounts;
  - the founder's Person listed site pages (agentskillshub.top/about/, jasonzhu.ai) as profiles and had worksFor;
  - blog posts named an anonymous Person, linked to the founder's X, as their author.
Shared names and accounts invite search engines to merge a person, a product and a company into one entity.
The rules, checked on the live pages:
  1. only a Person lists the founder's profiles in sameAs
  2. the founder's Person (@id https://jasonzhu.ai/#person), where it lists sameAs, lists the same profiles
     as the Person on jasonzhu.ai
  3. a Person's sameAs holds profiles, never pages of our own sites
  4. the Agent Skills Hub organization has no legalName and no company name in alternateName
  5. no Person has worksFor: the founder is described on jasonzhu.ai, pages here reference the @id
  6. the home page carries the operating company, https://gosailglobal.com/#organization, with its address
  7. the Agent Skills Hub organization names that company as parentOrganization
  8. a Person named Jason Zhu, or named as a blog post's author, is https://jasonzhu.ai/#person
  9. every JSON-LD block parses

The founder's profiles come from the Person on jasonzhu.ai, so a profile added there is expected here too.
If jasonzhu.ai cannot be read, rule 1 uses FALLBACK_PROFILES, rule 2 is skipped and the status is PARTIAL_FETCH.
Blog posts are the ones under frontend/public/blog that carry JSON-LD, so a new post is checked once it exists.

Public pages, no keys. Pure checks in `check_pages`; `audit_entity_edges` does the fetching.

  python3 ops/geo/entity_edges.py           # readable report
  python3 ops/geo/entity_edges.py --json    # what the daily digest reads
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

GEO_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = GEO_DIR.parent.parent / "frontend" / "public"
SITE = "https://agentskillshub.top"
MAIN_PAGES = ["/", "/about/", "/ai-info/", "/contact/"]
PERSON = "https://jasonzhu.ai/#person"
PERSON_SOURCE = "https://jasonzhu.ai/en/about"
ASH_ORG = f"{SITE}/#organization"
OPERATOR = "https://gosailglobal.com/#organization"
OWN_SITES = {"agentskillshub.top", "jasonzhu.ai", "gosailglobal.com"}
COMPANY_NAMES = re.compile(r"gosail\s*global|brickai", re.I)
FOUNDER_NAMES = re.compile(r"jason\s*zhu|yansen\s*zhu|zhu\s*yansen|祝彦森", re.I)
LD = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)
LOG = "jasonzhu.ai: ops/geo/ENTITY-GRAPH-ITERATION-LOG.md（v2.5）"

# The Person's sameAs on jasonzhu.ai on 2026-11-25; used only when that page cannot be read.
FALLBACK_PROFILES = frozenset({
    "https://orcid.org/0009-0000-2894-6285",
    "https://scholar.google.com/citations?user=AlP5JacAAAAJ",
    "https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=14044888",
    "https://www.linkedin.com/in/jason-zhu-a52aa73bb/",
    "https://www.producthunt.com/@yansen_zhu",
    "https://x.com/GoSailGlobal",
    "https://github.com/zhuyansen",
    "https://huggingface.co/jasonzhuyansen",
    "https://www.kaggle.com/yansenzhu",
    "https://www.youtube.com/@JasonZhuGoSail",
    "https://www.douyin.com/user/MS4wLjABAAAABDQoQfOA67afaoRQ4u79rww04pMm4OoHwwyzJvPWS9E",
    "https://www.xiaohongshu.com/user/profile/5bffc7d70000000008003b90",
})

PAGES_SRC = "frontend/index.html（首页）、frontend/scripts/generate-static-pages.mjs（/about/、/ai-info/）、frontend/public/contact/index.html"
FIX = {
    1: f"把本人的档案从这个节点的 sameAs 拿掉，个人档案只放在 Person（@id {PERSON}）里。改 {PAGES_SRC}",
    2: f"照 jasonzhu.ai 的 src/lib/profiles.ts 改这里 Person 的 sameAs，两边要一样。改 {PAGES_SRC}",
    3: "Person 的 sameAs 只放个人档案，自家网站的页面拿掉",
    4: f"ASH 机构不写法定名和公司别名，公司写在 parentOrganization（{OPERATOR}）里",
    5: f"拿掉 worksFor，这里只引用 @id {PERSON}；人在哪工作写在 jasonzhu.ai 上",
    6: f"frontend/index.html 补回运营公司节点（@id {OPERATOR}，带注册地址）",
    7: f"ASH 机构的 parentOrganization 指向 {OPERATOR}",
    8: f'写成 {{"@type": "Person", "@id": "{PERSON}", "name": "Jason Zhu", "url": "https://jasonzhu.ai/en"}}',
    9: "这段 JSON-LD 解析不了，查引号、逗号和模板变量",
}

HttpGet = Callable[..., tuple[int, dict[str, str], str]]


def as_list(v: Any) -> list[Any]:
    return v if isinstance(v, list) else ([] if v is None else [v])


def types_of(node: dict[str, Any]) -> set[str]:
    return {str(t) for t in as_list(node.get("@type"))}


def ref_id(v: Any) -> str:
    if isinstance(v, dict):
        return str(v.get("@id") or "")
    return v if isinstance(v, str) else ""


def nodes_of(doc: Any) -> list[dict[str, Any]]:
    """Every object in a JSON-LD document, nested ones included."""
    out: list[dict[str, Any]] = []

    def walk(o: Any) -> None:
        if isinstance(o, dict):
            out.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)

    walk(doc)
    return out


def host(url: str) -> str:
    return (urlparse(url).hostname or "").removeprefix("www.")


def check_pages(pages: dict[str, str], profiles: set[str] | None, blog_paths: set[str]) -> dict[str, Any]:
    """Apply rules 1-9 to {path: html}. `profiles` is the Person's sameAs on jasonzhu.ai, None if unreadable."""
    known = set(profiles) if profiles is not None else set(FALLBACK_PROFILES)
    issues: list[dict[str, Any]] = []
    nodes_by_page: dict[str, list[dict[str, Any]]] = {}
    blocks = 0

    def add(rule: int, page: str, node: str, detail: str) -> None:
        issues.append({"rule": rule, "page": page, "node": node, "detail": detail, "fix": FIX[rule]})

    for page, html in pages.items():
        nodes: list[dict[str, Any]] = []
        for raw in LD.findall(html):
            try:
                doc = json.loads(raw.strip())
            except ValueError as exc:
                add(9, page, "", f"JSON-LD 解析不了：{exc}")
                continue
            blocks += 1
            nodes += nodes_of(doc)
        nodes_by_page[page] = nodes
        authors = {id(a) for n in nodes for key in ("author", "creator") for a in as_list(n.get(key))
                   if page in blog_paths and isinstance(a, dict)}
        for n in nodes:
            t, nid = types_of(n), str(n.get("@id") or "")
            label = nid or "/".join(sorted(t)) or "?"
            same = [str(u) for u in as_list(n.get("sameAs"))]
            if "Person" not in t and set(same) & known:
                add(1, page, label, "sameAs 里有本人的档案：" + "、".join(sorted(set(same) & known)))
            if "Person" in t:
                if nid == PERSON and same and profiles is not None and set(same) != set(profiles):
                    extra, missing = sorted(set(same) - set(profiles)), sorted(set(profiles) - set(same))
                    add(2, page, label, f"和 jasonzhu.ai 不一致：多了 {'、'.join(extra) or '无'}；少了 {'、'.join(missing) or '无'}")
                own = [u for u in same if host(u) in OWN_SITES]
                if own:
                    add(3, page, label, "sameAs 里有自家网站的页面：" + "、".join(own))
                if "worksFor" in n:
                    add(5, page, label, "Person 带着 worksFor")
                name = " ".join(str(x) for x in as_list(n.get("name")))
                if nid != PERSON and (FOUNDER_NAMES.search(name) or id(n) in authors):
                    add(8, page, label, f"Person「{name or '没写名字'}」没有接到 {PERSON}")
            if nid == ASH_ORG:
                alts = [str(a) for a in as_list(n.get("alternateName"))]
                bad = (["legalName「" + str(n["legalName"]) + "」"] if "legalName" in n else []) + \
                      [f"alternateName「{a}」" for a in alts if COMPANY_NAMES.search(a)]
                if bad:
                    add(4, page, label, "ASH 机构带着公司的名字：" + "、".join(bad))
                parent = n.get("parentOrganization")
                if parent is not None and ref_id(parent) != OPERATOR:
                    add(7, page, label, f"parentOrganization 指向 {ref_id(parent) or '没有 @id 的节点'}")

    home = nodes_by_page.get("/")
    if home is not None:
        if not any(n.get("@id") == OPERATOR and "Organization" in types_of(n) and n.get("address") for n in home):
            add(6, "/", OPERATOR, "首页没有带注册地址的运营公司节点")
        if not any(n.get("@id") == ASH_ORG and ref_id(n.get("parentOrganization")) == OPERATOR for n in home):
            add(7, "/", ASH_ORG, "首页的 ASH 机构没有用 parentOrganization 指向运营公司")
    return {
        "rules": 9,
        "pages_checked": len(pages),
        "blocks": blocks,
        "nodes": sum(len(v) for v in nodes_by_page.values()),
        "issues": issues,
    }


# ---------------------------------------------------------------- fetching

def blog_pages() -> list[str]:
    """Blog posts in the repo that carry JSON-LD, as site paths."""
    blog = PUBLIC_DIR / "blog"
    if not blog.is_dir():
        return []
    return ["/" + f.parent.relative_to(PUBLIC_DIR).as_posix() + "/" for f in sorted(blog.rglob("index.html"))
            if "application/ld+json" in f.read_text(encoding="utf-8", errors="ignore")]


def founder_profiles(http_get: HttpGet) -> set[str] | None:
    code, _, html = http_get(PERSON_SOURCE)
    if code != 200:
        return None
    for raw in LD.findall(html):
        try:
            doc = json.loads(raw.strip())
        except ValueError:
            continue
        for n in nodes_of(doc):
            if n.get("@id") == PERSON and n.get("sameAs"):
                return {str(u) for u in as_list(n["sameAs"])}
    return None


def audit_entity_edges(http_get: HttpGet, html_by_path: dict[str, str] | None = None) -> dict[str, Any]:
    """Fetch the main pages (unless given) and the blog posts, read the founder's profiles, apply the rules."""
    errors: dict[str, str] = {}
    pages = dict(html_by_path or {})
    blogs = blog_pages()
    for path in MAIN_PAGES + blogs:
        if path in pages:
            continue
        code, _, html = http_get(SITE + path)
        if code == 200:
            pages[path] = html
        else:
            errors[path] = f"HTTP {code}"
    profiles = founder_profiles(http_get)
    if profiles is None:
        errors["jasonzhu.ai"] = f"{PERSON_SOURCE} 读不到 Person 的 sameAs：第 2 条没查，第 1 条用备用名单"
    result = check_pages(pages, profiles, set(blogs))
    status = "ISSUES_FOUND" if result["issues"] else ("PARTIAL_FETCH" if errors else "VERIFIED")
    return {"status": status, **result, "blog_pages": blogs,
            "profiles": len(profiles) if profiles is not None else None, "fetch_errors": errors, "log": LOG}


# ---------------------------------------------------------------- report

def print_report(r: dict[str, Any]) -> None:
    print(f"Node 1 relation rules: {r['status']}")
    print(f"  {r['pages_checked']} pages ({len(r['blog_pages'])} blog posts) · {r['blocks']} JSON-LD blocks · "
          f"{r['nodes']} nodes · founder profiles from jasonzhu.ai: {r['profiles'] if r['profiles'] is not None else 'unreadable'}")
    for name, err in r["fetch_errors"].items():
        print(f"  ! {name}: {err}")
    for i in r["issues"]:
        print(f"\n  [rule {i['rule']}] {i['page']} {i['node']}\n    {i['detail']}\n    fix: {i['fix']}")


def main() -> int:
    sys.path.insert(0, str(GEO_DIR))
    from entity_audit import http_get  # same UA and timeouts as the rest of the audit

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = audit_entity_edges(http_get)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print_report(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
