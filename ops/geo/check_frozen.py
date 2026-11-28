"""GIGALinks 冻结页守卫：一次推送里有人改了冻结页的源文件，就报错（2026-11-27 起）。

GIGALinks 实验（ops/geo/experiments.json 的 gigalinks-agentskillshub）要在 12-01、12-15、2027-01-01 复测，
到那之前所有 /best/ 页、/、/zh/、/how-we-grade/、/analyzer/、/agent-skills-directories/、/daily/、/stats/、
/blog/securing-117k-ai-skills/ 都不改。下面 FROZEN 是只生成这些页面的源文件；所有 SPA 页共用的首页壳
frontend/index.html 也在里面。几种页面共用的生成器（generate-static-pages.mjs、shell-meta.mjs 等）不在名单里，
改它们时自己确认冻结页的 HTML 没变。

不算违规的：
- 机器人提交（作者名以 [bot] 结尾，比如每天的 content(best): daily video review、renamed-repos 的改名），那是数据更新；
- 只改测试文件（*.test.mjs / *.test.ts）；
- 提交说明里写了 [frozen-ok]（必须改的时候用，比如法律或安全问题，说明里写清原因）。
2027-01-02（UTC）起不再检查，冻结页的修复分支 entity/gigalinks-frozen-fixes 那天合并。

用法：
  python3 ops/geo/check_frozen.py <起点提交> <终点提交>   # 查这一段里的提交，有违规退出码 1
  python3 ops/geo/check_frozen.py --selftest
"""
from __future__ import annotations

import fnmatch
import subprocess
import sys
from datetime import date, datetime, timezone

FROZEN_UNTIL = date(2027, 1, 1)     # 这一天还查，第二天起不查
OVERRIDE = "[frozen-ok]"
SHOW = 8                            # 每个提交最多列几个文件
FROZEN = (
    "frontend/index.html",                                   # 首页，也是所有 SPA 页的 head
    "frontend/src/pages/Home.tsx",
    "frontend/scripts/generate-home-zh.mjs",                 # /zh/
    "frontend/scripts/generate-scenario-pages.mjs",          # 全部 /best/
    "frontend/scripts/scenario-*",
    "frontend/public/best-runs/*",
    "frontend/public/best-pages.css",
    "frontend/scripts/generate-daily-pages.mjs",             # /daily/
    "frontend/scripts/daily-meta.mjs",
    "frontend/scripts/generate-how-we-grade-page.mjs",       # /how-we-grade/
    "frontend/src/pages/HowWeGradePage.tsx",
    "frontend/src/pages/AnalyzerPage.tsx",                   # /analyzer/
    "frontend/scripts/generate-directories-page.mjs",        # /agent-skills-directories/
    "frontend/src/pages/DirectoriesPage.tsx",
    "frontend/scripts/generate-stats-page.mjs",              # /stats/
    "frontend/scripts/stats-charts.mjs",
    "frontend/scripts/stats-live.mjs",
    "frontend/public/stats/*",
    "frontend/public/stats-page.css",
    "frontend/public/blog/securing-117k-ai-skills/index.html",   # 只有英文版冻结
)
TESTS = ("*.test.mjs", "*.test.ts", "*.test.tsx")


def frozen_files(paths: list[str]) -> list[str]:
    return [p for p in paths if any(fnmatch.fnmatch(p, f) for f in FROZEN) and not any(fnmatch.fnmatch(p, t) for t in TESTS)]


def violations(commits: list[dict], today: date) -> list[dict]:
    """commits：[{sha, author, message, files}]。返回违规的提交，每个带上碰到的冻结文件。"""
    if today > FROZEN_UNTIL:
        return []
    out = []
    for c in commits:
        if c["author"].endswith("[bot]") or OVERRIDE in c["message"]:
            continue
        hit = frozen_files(c["files"])
        if hit:
            out.append({**c, "frozen": hit})
    return out


def git_commits(start: str, end: str) -> list[dict]:
    sep = "\x1e"
    log = subprocess.run(["git", "log", "--no-merges", f"--format={sep}%H%x1f%an%x1f%B%x1f", "--name-only", f"{start}..{end}"],
                         capture_output=True, text=True, check=True).stdout
    out = []
    for chunk in filter(None, log.split(sep)):
        sha, author, message, files = chunk.split("\x1f", 3)
        out.append({"sha": sha, "author": author, "message": message.strip(),
                    "files": [f for f in files.split("\n") if f.strip()]})
    return out


def selftest() -> int:
    c = lambda files, author="JasonZhu", msg="feat: x": {"sha": "abc", "author": author, "message": msg, "files": files}
    d = date(2026, 11, 27)
    assert violations([c(["frontend/scripts/scenario-runs.json", "ops/x.py"])], d)[0]["frozen"] == ["frontend/scripts/scenario-runs.json"]
    assert violations([c(["frontend/public/best-runs/summary/a.html"])], d)
    assert violations([c(["frontend/index.html"])], d) and violations([c(["frontend/public/blog/securing-117k-ai-skills/index.html"])], d)
    assert not violations([c(["frontend/public/blog/securing-117k-ai-skills/zh/index.html"])], d)     # 中文版不冻结
    assert not violations([c(["frontend/scripts/scenario-links.test.mjs"])], d)                     # 测试文件
    assert not violations([c(["frontend/scripts/generate-static-pages.mjs", "ops/geo/entity_edges.py"])], d)   # 共用生成器不在名单
    assert not violations([c(["frontend/scripts/scenario-kinds.json"], author="github-actions[bot]")], d)
    assert not violations([c(["frontend/index.html"], msg="fix: 法律要求下线一段 [frozen-ok]")], d)
    assert violations([c(["frontend/index.html"])], FROZEN_UNTIL) and not violations([c(["frontend/index.html"])], date(2027, 1, 2))
    print("自测通过")
    return 0


def main(argv: list[str]) -> int:
    if argv[1:2] == ["--selftest"]:
        return selftest()
    if len(argv) != 3:
        print(__doc__)
        return 2
    start, end = argv[1], argv[2]
    if set(start) == {"0"}:          # 新建分支的第一次推送：只看最后一个提交
        start = f"{end}^"
    today = datetime.now(timezone.utc).date()
    bad = violations(git_commits(start, end), today)
    if not bad:
        print(f"冻结页守卫：{start[:8]}..{end[:8]} 没有改冻结页的源文件" + ("（2027-01-01 以后不再检查）" if today > FROZEN_UNTIL else "") + "。")
        return 0
    print(f"冻结页守卫：下面 {len(bad)} 个提交改了 GIGALinks 冻结页的源文件（冻结到 {FROZEN_UNTIL}，见 ops/geo/experiments.json）。")
    print("请撤回这些改动，或者改到分支 entity/gigalinks-frozen-fixes 上 2027-01-02 再合；必须现在改的，在提交说明里写 [frozen-ok] 和原因。\n")
    for c in bad:
        print(f"- {c['sha'][:8]} {c['author']}：{c['message'].splitlines()[0][:90]}")
        for f in c["frozen"][:SHOW]:
            print(f"    {f}")
        if len(c["frozen"]) > SHOW:
            print(f"    ……另外 {len(c['frozen']) - SHOW} 个文件")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
