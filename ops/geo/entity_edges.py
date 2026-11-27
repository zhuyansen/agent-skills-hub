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
  2. the founder's Person (@id https://jasonzhu.ai/#person), where it lists sameAs or alternateName, lists the
     same profiles and aliases as the Person on jasonzhu.ai
  3. a Person's sameAs holds profiles, never pages of our own sites
  4. the Agent Skills Hub organization has no legalName and no company name in alternateName
  5. no Person has worksFor: the founder is described on jasonzhu.ai, pages here reference the @id
  6. the home page carries the operating company, https://gosailglobal.com/#organization, with its address
  7. the Agent Skills Hub organization names that company as parentOrganization
  8. a Person named Jason Zhu, or named as a blog post's author, is https://jasonzhu.ai/#person
  9. every JSON-LD block parses
 10. the Agent Skills Hub organization and the operating company name the founder's Person as founder, and the
     home page's Agent Skills Hub organization has one (on 2026-11-27 deleting it, or pointing it at the
     company, passed rules 1-9)
 11. every blog post carries an author or creator edge: a post with no JSON-LD, or with no author, is a finding
 12. twitter:site names the product's account, never one of the founder's profiles (twitter:creator may)

Which pages: every page template in the sitemaps. Until 2026-11-27 only the four main pages and the blog posts
were read, so the 11-26 「9 条都过」 covered 12 pages while 36 scenario and Blue Book pages still carried an
anonymous "Jason Zhu". Small templates are read in full; the large ones (top, audit, daily) by a fixed sample of
SAMPLE pages spread evenly over the sorted sitemap, so a run can be repeated. Without the sitemap the main pages
and blog posts are still checked and the status is PARTIAL_FETCH; the result says which templates were read.

The GIGALinks controlled experiment keeps some pages as they were until its last readout (see FROZEN_UNTIL).
Findings there are listed under "frozen", not as issues, until that date, and are issues again the day after.

The founder's profiles and aliases come from the Person on jasonzhu.ai, so one added there is expected here too.
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
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

GEO_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = GEO_DIR.parent.parent / "frontend" / "public"
SITE = "https://agentskillshub.top"
SITEMAP = f"{SITE}/sitemap.xml"
MAIN_PAGES = ["/", "/about/", "/ai-info/", "/contact/"]
FULL_TEMPLATES = ("static", "categories", "scenarios", "comparisons", "book", "blog")
SAMPLE = 20        # pages read from each of the other templates (top, audit, daily: thousands of pages each)
WORKERS = 8
PERSON = "https://jasonzhu.ai/#person"
PERSON_SOURCE = "https://jasonzhu.ai/en/about"
ASH_ORG = f"{SITE}/#organization"
OPERATOR = "https://gosailglobal.com/#organization"
OWN_SITES = {"agentskillshub.top", "jasonzhu.ai", "gosailglobal.com"}
COMPANY_NAMES = re.compile(r"gosail\s*global|brickai", re.I)
FOUNDER_NAMES = re.compile(r"jason\s*zhu|yansen\s*zhu|zhu\s*yansen|祝彦森", re.I)
LD = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.I | re.S)
LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)
META = re.compile(r"<meta\b[^>]*>", re.I)
ATTR = re.compile(r'([\w:-]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')')
LOG = "jasonzhu.ai: ops/geo/ENTITY-GRAPH-ITERATION-LOG.md（v2.6）"
RULES = 12

# The GIGALinks controlled experiment (ops/geo/experiments.json, gigalinks-agentskillshub) keeps these pages as they
# were until its last readout on 2027-01-01: every /best/ page, the brand questions' target pages and /stats/.
# /daily/ shares its template with the daily pages, and every page served from the SPA shell (frontend/index.html,
# frozen with /; such a page carries <div id="root">) keeps the shell's twitter:site and the founder's aliases:
# the categories, the Blue Book, /submit/ and the other shell pages that do not write their own. Their fixes wait on branch FROZEN_BRANCH,
# to merge on 2027-01-02. Until then a finding there is listed as frozen; from then on it is an issue, merged or not.
FROZEN_UNTIL = date(2027, 1, 1)
FROZEN_BRANCH = "entity/gigalinks-frozen-fixes"
FROZEN_PAGES = frozenset({"/", "/zh/", "/how-we-grade/", "/analyzer/", "/agent-skills-directories/", "/stats/",
                          "/blog/securing-117k-ai-skills/"})
FROZEN_PREFIXES = ("/best/", "/daily/")
SHELL_MARK = re.compile(r'<div[^>]+id=["\']root["\']', re.I)

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
    2: f"照 jasonzhu.ai 的 src/lib/profiles.ts 改这里 Person 的 sameAs 和 alternateName，两边要一样；"
       f"只引用本人的节点只写 @id、name、url。改 {PAGES_SRC}",
    3: "Person 的 sameAs 只放个人档案，自家网站的页面拿掉",
    4: f"ASH 机构不写法定名和公司别名，公司写在 parentOrganization（{OPERATOR}）里",
    5: f"拿掉 worksFor，这里只引用 @id {PERSON}；人在哪工作写在 jasonzhu.ai 上",
    6: f"frontend/index.html 补回运营公司节点（@id {OPERATOR}，带注册地址）",
    7: f"ASH 机构的 parentOrganization 指向 {OPERATOR}",
    8: f'写成 {{"@type": "Person", "@id": "{PERSON}", "name": "Jason Zhu", "url": "https://jasonzhu.ai/en"}}'
       "（场景页在 frontend/scripts/scenario-method.mjs，蓝皮书页在 frontend/scripts/generate-book-pages.mjs）",
    9: "这段 JSON-LD 解析不了，查引号、逗号和模板变量",
    10: f'ASH 机构和运营公司写 "founder": {{"@id": "{PERSON}"}}；首页 frontend/index.html 的 ASH 机构必须带它',
    11: f'博客的 BlogPosting 写 "author": {{"@type": "Person", "@id": "{PERSON}", "name": "Jason Zhu", '
        '"url": "https://jasonzhu.ai/en"}}（frontend/public/blog/<slug>/index.html）',
    12: "twitter:site 写产品的 @agentskillshub，本人的账号只能放在 twitter:creator。"
        "改 frontend/index.html、frontend/scripts/generate-*.mjs、frontend/scripts/sub-skills.mjs 和 frontend/public/blog/",
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


def meta_content(html: str, name: str) -> list[str]:
    """The content of every <meta name|property=name> tag, attributes in any order."""
    out = []
    for tag in META.findall(html):
        attrs = {m.group(1).lower(): m.group(2) if m.group(2) is not None else m.group(3) for m in ATTR.finditer(tag)}
        if (attrs.get("name") or attrs.get("property") or "").lower() == name and attrs.get("content"):
            out.append(attrs["content"])
    return out


def x_handles(profiles: set[str]) -> set[str]:
    return {urlparse(u).path.strip("/").lower() for u in profiles if host(u) in ("x.com", "twitter.com")}


def check_pages(pages: dict[str, str], profiles: set[str] | None, blog_paths: set[str],
                aliases: set[str] | None = None) -> dict[str, Any]:
    """Apply the rules to {path: html}. `profiles` / `aliases` are the Person's sameAs / alternateName on
    jasonzhu.ai, None if unreadable."""
    known = set(profiles) if profiles is not None else set(FALLBACK_PROFILES)
    handles = x_handles(known)
    issues: list[dict[str, Any]] = []
    nodes_by_page: dict[str, list[dict[str, Any]]] = {}
    blocks = 0

    def add(rule: int, page: str, node: str, detail: str) -> None:
        issues.append({"rule": rule, "page": page, "node": node, "detail": detail, "fix": FIX[rule]})

    for page, html in pages.items():
        nodes: list[dict[str, Any]] = []
        page_blocks = 0
        for raw in LD.findall(html):
            try:
                doc = json.loads(raw.strip())
            except ValueError as exc:
                add(9, page, "", f"JSON-LD 解析不了：{exc}")
                continue
            page_blocks += 1
            nodes += nodes_of(doc)
        blocks += page_blocks
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
                alts = {str(a) for a in as_list(n.get("alternateName"))}
                if nid == PERSON and alts and aliases is not None and alts != aliases:
                    extra, missing = sorted(alts - aliases), sorted(aliases - alts)
                    add(2, page, label, f"别名和 jasonzhu.ai 不一致：多了 {'、'.join(extra) or '无'}；少了 {'、'.join(missing) or '无'}")
                own = [u for u in same if host(u) in OWN_SITES]
                if own:
                    add(3, page, label, "sameAs 里有自家网站的页面：" + "、".join(own))
                if "worksFor" in n:
                    add(5, page, label, "Person 带着 worksFor")
                name = " ".join(str(x) for x in as_list(n.get("name")))
                if nid != PERSON and (FOUNDER_NAMES.search(name) or id(n) in authors):
                    add(8, page, label, f"Person「{name or '没写名字'}」没有接到 {PERSON}")
            if nid in (ASH_ORG, OPERATOR) and "founder" in n and ref_id(n["founder"]) != PERSON:
                add(10, page, label, f"founder 指向 {ref_id(n['founder']) or '没有 @id 的节点'}，不是本人")
            if nid == ASH_ORG:
                alts = [str(a) for a in as_list(n.get("alternateName"))]
                bad = (["legalName「" + str(n["legalName"]) + "」"] if "legalName" in n else []) + \
                      [f"alternateName「{a}」" for a in alts if COMPANY_NAMES.search(a)]
                if bad:
                    add(4, page, label, "ASH 机构带着公司的名字：" + "、".join(bad))
                parent = n.get("parentOrganization")
                if parent is not None and ref_id(parent) != OPERATOR:
                    add(7, page, label, f"parentOrganization 指向 {ref_id(parent) or '没有 @id 的节点'}")
        if page in blog_paths:
            edges = [a for n in nodes for key in ("author", "creator") for a in as_list(n.get(key))]
            if not edges and not any(i["page"] == page and i["rule"] == 9 for i in issues):
                add(11, page, "", "博客页的 JSON-LD 没有 author 或 creator" if page_blocks else "博客页没有 JSON-LD")
        for v in meta_content(html, "twitter:site"):
            if v.strip().lstrip("@").lower() in handles:
                add(12, page, "twitter:site", f"站点账号写的是本人的 {v.strip()}")

    home = nodes_by_page.get("/")
    if home is not None:
        if not any(n.get("@id") == OPERATOR and "Organization" in types_of(n) and n.get("address") for n in home):
            add(6, "/", OPERATOR, "首页没有带注册地址的运营公司节点")
        if not any(n.get("@id") == ASH_ORG and ref_id(n.get("parentOrganization")) == OPERATOR for n in home):
            add(7, "/", ASH_ORG, "首页的 ASH 机构没有用 parentOrganization 指向运营公司")
        if not any(n.get("@id") == ASH_ORG and ref_id(n.get("founder")) == PERSON for n in home):
            add(10, "/", ASH_ORG, "首页的 ASH 机构没有用 founder 指向本人")
    return {
        "rules": RULES,
        "pages_checked": len(pages),
        "blocks": blocks,
        "nodes": sum(len(v) for v in nodes_by_page.values()),
        "issues": issues,
    }


# ---------------------------------------------------------------- the GIGALinks freeze

def is_frozen(path: str) -> bool:
    return path in FROZEN_PAGES or path.startswith(FROZEN_PREFIXES)


def shell_person_block(home: str) -> str:
    """The home page's Person JSON-LD block as written: every page copied from the SPA shell carries it verbatim."""
    for raw in LD.findall(home):
        try:
            doc = json.loads(raw.strip())
        except ValueError:
            continue
        if isinstance(doc, dict) and doc.get("@id") == PERSON and "Person" in types_of(doc):
            return raw.strip()
    return ""


def hold_frozen(result: dict[str, Any], pages: dict[str, str], today: date) -> dict[str, Any]:
    """Move the findings the freeze holds back from issues to frozen: those on frozen pages, and the shell's part
    (twitter:site, the founder's aliases) on pages served from the shell. After FROZEN_UNTIL nothing is held."""
    if today > FROZEN_UNTIL:
        return {**result, "frozen": []}
    shell = shell_person_block(pages.get("/", ""))

    def held(i: dict[str, Any]) -> bool:
        if is_frozen(i["page"]):
            return True
        shell_part = i["rule"] == 12 or (i["rule"] == 2 and i["detail"].startswith("别名"))
        html = pages.get(i["page"], "")
        return shell_part and (bool(SHELL_MARK.search(html)) or (bool(shell) and shell in html))

    return {**result, "issues": [i for i in result["issues"] if not held(i)],
            "frozen": [i for i in result["issues"] if held(i)]}


# ---------------------------------------------------------------- which pages

def pick(paths: list[str], n: int) -> list[str]:
    """n paths spread evenly over the sorted list: the same ones on every run while the list stays the same."""
    paths = sorted(set(paths))
    if len(paths) <= n:
        return paths
    step = len(paths) / n
    return [paths[int(i * step)] for i in range(n)]


def sitemap_paths(http_get: HttpGet) -> tuple[dict[str, list[str]], dict[str, str]]:
    """{template: [path, ...]} from the sitemap index (sitemap-<template>.xml), and what could not be read."""
    errors: dict[str, str] = {}
    code, _, body = http_get(SITEMAP)
    if code != 200:
        return {}, {"sitemap": f"{SITEMAP} HTTP {code}：只查了主页面和博客"}
    groups: dict[str, list[str]] = {}
    for loc in LOC.findall(body):
        if not loc.endswith(".xml"):
            groups.setdefault("root", []).append(urlparse(loc).path or "/")
            continue
        name = re.sub(r"^sitemap-|\.xml$", "", loc.rsplit("/", 1)[-1])
        c, _, b = http_get(loc)
        if c != 200:
            errors[f"sitemap:{name}"] = f"{loc} HTTP {c}"
            continue
        groups[name] = sorted({urlparse(u).path or "/" for u in LOC.findall(b) if host(u) == host(SITE)})
    return groups, errors


def blog_pages() -> list[str]:
    """Blog posts in the repo that carry JSON-LD, as site paths."""
    blog = PUBLIC_DIR / "blog"
    if not blog.is_dir():
        return []
    return ["/" + f.parent.relative_to(PUBLIC_DIR).as_posix() + "/" for f in sorted(blog.rglob("index.html"))
            if "application/ld+json" in f.read_text(encoding="utf-8", errors="ignore")]


def founder_facts(http_get: HttpGet) -> tuple[set[str], set[str]] | None:
    """(sameAs, alternateName) of the Person on jasonzhu.ai, or None if it cannot be read."""
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
                return {str(u) for u in as_list(n["sameAs"])}, {str(a) for a in as_list(n.get("alternateName"))}
    return None


def founder_profiles(http_get: HttpGet) -> set[str] | None:
    facts = founder_facts(http_get)
    return facts[0] if facts else None


def audit_entity_edges(http_get: HttpGet, html_by_path: dict[str, str] | None = None,
                       sample: int = SAMPLE, today: date | None = None) -> dict[str, Any]:
    """Fetch every template's pages (unless given) and the blog posts, read the founder's Person, apply the rules."""
    pages = dict(html_by_path or {})
    blogs = blog_pages()
    groups, errors = sitemap_paths(http_get)
    wanted = {"main": MAIN_PAGES, "blog posts": blogs}
    for name, paths in groups.items():
        wanted[name] = paths if name in FULL_TEMPLATES else pick(paths, sample)
    todo = [p for p in dict.fromkeys(p for ps in wanted.values() for p in ps) if p not in pages]
    failed: dict[str, int] = {}
    for attempt in range(2):           # one retry, so a single slow page does not cost the run its status
        with ThreadPoolExecutor(WORKERS) as ex:
            results = list(ex.map(lambda p: http_get(SITE + p), todo))
        failed = {}
        for path, (code, _, html) in zip(todo, results):
            if code == 200:
                pages[path] = html
            else:
                failed[path] = code
        todo = list(failed)
        if not todo:
            break
    errors.update({path: f"HTTP {code}" for path, code in failed.items()})
    coverage = {name: {"in_sitemap": len(groups[name]), "checked": sum(1 for p in wanted[name] if p in pages)}
                for name in groups}
    facts = founder_facts(http_get)
    if facts is None:
        errors["jasonzhu.ai"] = f"{PERSON_SOURCE} 读不到 Person 的 sameAs：第 2 条没查，第 1 条用备用名单"
    result = check_pages(pages, facts[0] if facts else None, set(blogs), facts[1] if facts else None)
    result = hold_frozen(result, pages, today or datetime.now(timezone.utc).date())
    status = "ISSUES_FOUND" if result["issues"] else ("PARTIAL_FETCH" if errors else "VERIFIED")
    return {"status": status, **result, "coverage": coverage, "sample_per_template": sample, "blog_pages": blogs,
            "profiles": len(facts[0]) if facts else None, "fetch_errors": errors,
            "frozen_until": FROZEN_UNTIL.isoformat(), "frozen_branch": FROZEN_BRANCH, "log": LOG}


# ---------------------------------------------------------------- report

def coverage_line(coverage: dict[str, dict[str, int]]) -> str:
    """'static 11/11 · top 20/4719 · …': pages read out of each template's sitemap."""
    return " · ".join(f"{name} {c['checked']}/{c['in_sitemap']}" for name, c in coverage.items()) or "no sitemap"


def print_report(r: dict[str, Any]) -> None:
    print(f"Node 1 relation rules ({r['rules']}): {r['status']}")
    print(f"  {r['pages_checked']} pages ({len(r['blog_pages'])} blog posts) · {r['blocks']} JSON-LD blocks · "
          f"{r['nodes']} nodes · founder profiles from jasonzhu.ai: {r['profiles'] if r['profiles'] is not None else 'unreadable'}")
    print(f"  templates read: {coverage_line(r.get('coverage', {}))}")
    for name, err in r["fetch_errors"].items():
        print(f"  ! {name}: {err}")
    for i in r["issues"]:
        print(f"\n  [rule {i['rule']}] {i['page']} {i['node']}\n    {i['detail']}\n    fix: {i['fix']}")
    if r.get("frozen"):
        rules = sorted({i["rule"] for i in r["frozen"]})
        print(f"\n  frozen until {r['frozen_until']} (GIGALinks): {len(r['frozen'])} findings on rules {rules}; "
              f"fixes on branch {r['frozen_branch']}")


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
