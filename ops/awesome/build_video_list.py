"""Build the public list "awesome-claude-video-skills" from the video page's data.

The list is the GitHub face of https://agentskillshub.top/best/opus-5-5-video/: the same
repos, the same types, the same security grades. Nothing is curated here by hand; an
entry is on the list because it is on the page (frontend/scripts/scenario-kinds.json,
written by ops/jev-review/scenario_gate.py).

Stars, description and license are read from GitHub at build time (one request per
repo): the catalog refreshes a row only when a sync visits it, and a public list with
last week's star counts reads as unmaintained. The security grade comes from the
catalog, with the read-only anon key, in one request per 60 names. A listed repo the
catalog has not ingested yet is shown as "pending" until a sync grades it.

Usage: python ops/awesome/build_video_list.py <output-dir>
Env:   VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY (read from frontend/.env); gh CLI
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SLUG = "opus-5-5-video"
SITE = "https://agentskillshub.top"
PAGE = f"{SITE}/best/{SLUG}/"
UTM = "?utm_source=github&utm_medium=awesome-list"
CHUNK = 60
DESC_MAX = 150
HTTP_TIMEOUT = 30
FIELDS = "repo_full_name,security_grade"
GRADES = {"safe": "SAFE", "caution": "CAUTION", "unsafe": "UNSAFE", "reject": "REJECT"}
MADE_WITH = ("JohnHeibel/ClaudeAnimationBase", "JohnHeibel/PDoomVideo",
             "lemomo-ai/lemo-opuscar", "ledbetterljoshua/functional-emotions-video")

TEXT = {
    "en": {
        "file": "README.md", "other": "[中文](README.zh-CN.md)", "title": "Awesome Claude Video Skills",
        "pitch": ("Open-source skills and toolkits that let **Claude Code, Codex and other coding agents make "
                  "video**: HyperFrames, Remotion, motion graphics, editing, explainers, avatars. "
                  "{n} repos, each one read and security-graded by [Agent Skills Hub]({site}{utm})."),
        "live": "Live page with filters: **[{page}]({page}{utm})** · refreshed every 8 hours",
        "rules_h": "How a repo gets on the list",
        "rules": ["It makes or edits video or motion graphics. A 3D web page or a prompt collection does not count.",
                  "An agent operates it: a skill, a plugin, an MCP server, or a toolkit written for the agent.",
                  "It has a README. Without one it cannot be graded.",
                  "At 50 stars or more it is listed on topic alone. Under 50 it must also clear a README "
                  "quality bar (shows the result, one-command start, a concrete outcome, complete docs), "
                  "and have 5 stars unless it names Claude Opus 5.5."],
        "rules_note": ("The questions are answered by a decision model reading each README, not by hand. "
                       "A repo near a cut-off can land on either side; open an issue if one is misfiled."),
        "made_h": "Made with Claude Opus 5.5", "made": "Projects whose README says they were built with the model.",
        "contents": "Contents", "cols": "| Repo | Stars | What it does | Security |",
        "filter": "Open this type on the live page, sorted by stars →",
        "pending": "pending", "grade_note": ("**Security** is the grade of the repo's README and install steps "
                                            "on Agent Skills Hub. *pending* means the catalog has not graded it yet."),
        "related_h": "Related collections",
        "related": ["[opusvideo/awesome-claude-video](https://github.com/opusvideo/awesome-claude-video) — "
                    "videos people made with Opus 5.5, with the original posts. Works, where this list is tools.",
                    "[TripoGrowthLab/awesome-opus-5-5-prompts](https://github.com/TripoGrowthLab/awesome-opus-5-5-prompts)"
                    " — Opus 5.5 prompts for 3D scenes, games and simulations."],
        "contrib_h": "Add a repo",
        "contrib": ("Open an issue with the GitHub URL. It goes through the same review as every entry; "
                    "the rules above decide, stars do not."),
        "data": "Machine-readable copy: [`data/skills.json`](data/skills.json). Generated {today}.",
    },
    "zh": {
        "file": "README.zh-CN.md", "other": "[English](README.md)", "title": "Awesome Claude Video Skills",
        "pitch": ("让 **Claude Code、Codex 等编程 agent 做视频**的开源 skill 和工具包:HyperFrames、Remotion、"
                  "动效、剪辑、讲解、数字人。共 {n} 个仓库,每个都由 [Agent Skills Hub]({site}{utm}) 读过 README 并做了安全评级。"),
        "live": "带类型筛选的在线页面:**[{page}]({page}{utm})** · 每 8 小时刷新",
        "rules_h": "什么样的仓库能上榜",
        "rules": ["它做视频、剪视频或做动效。3D 网页、提示词合集不算。",
                  "它是给 agent 用的:skill、插件、MCP 服务器,或为 agent 写的工具包。",
                  "它有 README。没有 README 就没法评级。",
                  "50 星及以上只看是否切题;50 星以下还要过 README 质量线(展示成品、一条命令上手、"
                  "说清产出、文档完整),并且至少 5 星——点名 Claude Opus 5.5 的除外。"],
        "rules_note": "这些问题由决策模型逐个读 README 回答,不是人工挑选。卡在线上的仓库可能判到任一边,归错了请提 issue。",
        "made_h": "用 Claude Opus 5.5 做出来的", "made": "README 写明用这个模型做的项目。",
        "contents": "目录", "cols": "| 仓库 | 星数 | 做什么 | 安全评级 |",
        "filter": "在在线页面打开这一类,按星数排序 →",
        "pending": "待评级", "grade_note": "**安全评级**是 Agent Skills Hub 对仓库 README 和安装步骤的评级。*待评级*表示目录还没评到它。",
        "related_h": "相关合集",
        "related": ["[opusvideo/awesome-claude-video](https://github.com/opusvideo/awesome-claude-video) —— "
                    "大家用 Opus 5.5 做出来的视频,附原帖。它收作品,本列表收工具。",
                    "[TripoGrowthLab/awesome-opus-5-5-prompts](https://github.com/TripoGrowthLab/awesome-opus-5-5-prompts)"
                    " —— Opus 5.5 做 3D 场景、游戏和模拟的提示词。"],
        "contrib_h": "推荐仓库",
        "contrib": "提一个 issue 附上 GitHub 链接。它会走和每个条目一样的评审;决定上不上榜的是上面的规则,不是星数。",
        "data": "机器可读版本:[`data/skills.json`](data/skills.json)。生成于 {today}。",
    },
}


def env() -> dict:
    pairs = re.findall(r"^(VITE_SUPABASE_\w+)\s*=\s*[\"']?([^\"'\n]+)", (ROOT / "frontend/.env").read_text(), re.M)
    return dict(pairs)


def catalog_rows(names: list[str]) -> dict:
    cfg, rows = env(), {}
    for i in range(0, len(names), CHUNK):
        quoted = ",".join(f'"{n}"' for n in names[i:i + CHUNK])
        query = urllib.parse.urlencode({"select": FIELDS, "repo_full_name": f"in.({quoted})"})
        req = urllib.request.Request(f"{cfg['VITE_SUPABASE_URL']}/rest/v1/skills?{query}", headers={
            "apikey": cfg["VITE_SUPABASE_ANON_KEY"], "Authorization": f"Bearer {cfg['VITE_SUPABASE_ANON_KEY']}"})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as res:
            rows.update({r["repo_full_name"]: r for r in json.load(res)})
    return rows


def github_row(name: str) -> dict | None:
    out = subprocess.run(["gh", "api", f"repos/{name}"], capture_output=True, text=True).stdout
    meta = json.loads(out or "{}")
    if not meta.get("full_name"):
        return None
    return {"repo_full_name": name, "stars": meta["stargazers_count"], "description": meta.get("description"),
            "security_grade": None, "created_at": meta.get("created_at"), "language": meta.get("language"),
            "license": (meta.get("license") or {}).get("spdx_id")}


def entries() -> tuple[list[dict], list[dict]]:
    kinds = json.loads((ROOT / "frontend/scripts/scenario-kinds.json").read_text())[SLUG]
    names = sorted(kinds["repos"])
    found = catalog_rows(names)
    rows = []
    for name in names:
        row = github_row(name)  # None when the repo is gone or private now
        if row:
            grade = (found.get(name) or {}).get("security_grade")
            rows.append({**row, "security_grade": grade, "kind": kinds["repos"][name], "in_catalog": name in found})
    return kinds["kinds"], sorted(rows, key=lambda r: -r["stars"])


def stars(n: int) -> str:
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def describe(row: dict) -> str:
    text = re.sub(r"\s+", " ", row.get("description") or "").replace("|", "\\|").strip()
    return text if len(text) <= DESC_MAX else text[:DESC_MAX - 1].rstrip() + "…"


def security(row: dict, t: dict) -> str:
    grade = GRADES.get(row.get("security_grade") or "")
    if not row["in_catalog"]:
        return f"*{t['pending']}*"
    label = grade or f"*{t['pending']}*"
    return f"[{label}]({SITE}/skill/{row['repo_full_name']}/{UTM})"


def table(rows: list[dict], t: dict) -> list[str]:
    lines = [t["cols"], "|---|---:|---|---|"]
    for r in rows:
        name = r["repo_full_name"]
        lines.append(f"| [{name}](https://github.com/{name}) | {stars(r['stars'])} | {describe(r)} | {security(r, t)} |")
    return lines


def anchor(kind: dict) -> str:
    return f"type-{kind['id']}"


def readme(lang: str, kinds: list[dict], rows: list[dict]) -> str:
    t = TEXT[lang]
    label = "zh" if lang == "zh" else "en"
    used = [k for k in kinds if any(r["kind"] == k["id"] for r in rows)]
    count = lambda k: sum(r["kind"] == k["id"] for r in rows)  # noqa: E731
    out = [f"# {t['title']}", "", t["other"], "",
           t["pitch"].format(n=len(rows), site=SITE, utm=UTM), "", t["live"].format(page=PAGE, utm=UTM), "",
           f"## {t['contents']}", "", f"- [{t['made_h']}](#made-with-opus-55)"]
    out += [f"- [{k['icon']} {k[label]}](#{anchor(k)}) ({count(k)})" for k in used]
    out += ["", f"## {t['rules_h']}", ""] + [f"{i}. {rule}" for i, rule in enumerate(t["rules"], 1)]
    out += ["", t["rules_note"], "", '<a id="made-with-opus-55"></a>', f"## {t['made_h']}", "", t["made"], ""]
    out += table([r for r in rows if r["repo_full_name"] in MADE_WITH], t)
    for k in used:
        out += ["", f'<a id="{anchor(k)}"></a>', f"## {k['icon']} {k[label]}", "",
                f"[{t['filter']}]({PAGE}{UTM}#type-{k['id']})", ""]
        out += table([r for r in rows if r["kind"] == k["id"]], t)
    out += ["", t["grade_note"], "", f"## {t['related_h']}", ""] + [f"- {x}" for x in t["related"]]
    out += ["", f"## {t['contrib_h']}", "", t["contrib"], "", "---", "", t["data"].format(today=date.today().isoformat()), ""]
    return "\n".join(out)


def main() -> None:
    out = Path(sys.argv[1]).expanduser()
    (out / "data").mkdir(parents=True, exist_ok=True)
    kinds, rows = entries()
    for lang in TEXT:
        (out / TEXT[lang]["file"]).write_text(readme(lang, kinds, rows))
    public = [{k: r[k] for k in ("repo_full_name", "stars", "description", "kind", "security_grade", "language", "license")}
              for r in rows]
    (out / "data/skills.json").write_text(json.dumps(
        {"generated": date.today().isoformat(), "source": PAGE, "kinds": kinds, "skills": public},
        ensure_ascii=False, indent=1) + "\n")
    graded = sum(bool(GRADES.get(r.get("security_grade") or "")) for r in rows)
    print(f"{len(rows)} repos · {sum(r['in_catalog'] for r in rows)} in the catalog · {graded} graded -> {out}")


if __name__ == "__main__":
    main()
