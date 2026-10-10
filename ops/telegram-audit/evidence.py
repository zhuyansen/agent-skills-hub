"""Evidence pages and page data for the Telegram bot source audit.

  python ops/telegram-audit/evidence.py      # reads results.json

A bot needs a BotFather token to run, so this is a reading of each repo's source at one
commit, not a run. results.json holds, per bot, the answers and the lines that show them
(file and line); the claims shown as "open" were re-read by hand. Writes
frontend/public/best-runs/telegram/<owner__repo>.html (noindex) and the "telegram-bot"
entry of frontend/scripts/scenario-runs.json (type "table": the page and the GitHub list
render it as given). Bots that drive a coding agent on your machine and chat-only bots
are ranked apart: an open chat bot costs you API credit, an open agent bot is a shell.
"""
import html
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
PUBLIC = ROOT / "frontend/public/best-runs/telegram"
RUNS_JSON = ROOT / "frontend/scripts/scenario-runs.json"
DATE = "2026-10-10"
REPO_URL = "https://github.com/zhuyansen/agent-skills-hub/blob/main/ops/telegram-audit/"
DEFAULT = {  # with no allowlist configured: (rank, table en, table zh, card en, card zh, colour)
    "refuses": (0, "Serves nobody", "谁都不服务", "Serves nobody until you list your Telegram ID", "不填你的 Telegram ID 就谁都不服务", "touch-ups"),
    "partly open": (1, "Side commands open to anyone", "部分命令对所有人开放", "Until you set your chat ID, some commands answer anyone", "没填 chat ID 之前，部分命令任何人可用", ""),
    "open": (2, "Serves anyone", "任何人可用", "Serves anyone who finds the bot unless you set an allowlist", "不设白名单的话，找到 bot 的人都能用", "substantial"),
}
NO_ACCESS = (3, "Serves anyone, no setting to change it", "任何人可用，且没有开关", "Has no allowlist at all: anyone who finds the bot can use it", "完全没有白名单：找到 bot 的人都能用", "substantial")
CONFIRMS = {  # what stands between an allowed message and a command on your machine
    "asks": (0, "Permission prompts sent to Telegram", "权限确认发到 Telegram", "Claude's permission prompts come to you in Telegram", "Claude 的权限确认会发到 Telegram 给你点", "touch-ups"),
    "relays": (0, "Agent's own prompts sent to Telegram", "agent 的确认发到 Telegram", "the agent's own permission prompts come to you in Telegram", "agent 自己的权限确认会发到 Telegram", "touch-ups"),
    "confined": (1, "No prompts; kept to one directory", "不确认；限制在一个目录内", "no approval step, but the agent is kept to one directory", "没有确认步骤，但 agent 被限制在一个目录内", ""),
    "unclear": (2, "Depends on your Claude Code settings", "取决于你本机 Claude Code 的设置", "what the agent may do depends on your own Claude Code settings", "agent 能做什么取决于你本机 Claude Code 的设置", ""),
    "skips": (3, "Runs with permission prompts off", "跳过权限确认直接执行", "runs the agent with permission prompts switched off", "agent 跳过权限确认直接执行", "substantial"),
}
SETTING = {  # the one thing to set, short enough for a table cell
    "overwirehq/claude-code-telegram": "ALLOWED_USERS, and ENVIRONMENT=production", "grinev/opencode-telegram-bot": "TELEGRAM_ALLOWED_USER_ID (required)",
    "banteg/takopi": "chat_id (required); allowed_user_ids for groups", "hanxiao/claudecode-telegram": "none exists",
    "duckbugio/flock": "ALLOWED_USERS", "PleasePrompto/ductor": "allowed_user_ids (required)", "linuz90/claude-telegram-bot": "TELEGRAM_ALLOWED_USERS (required)",
    "smixs/agent-second-brain": "ALLOWED_USER_IDS", "godagoo/claude-telegram-relay": "TELEGRAM_USER_ID", "alexei-led/ccgram": "ALLOWED_USERS (required)",
    "six-ddc/ccbot": "ALLOWED_USERS (required)", "earlyaidopters/claudeclaw": "ALLOWED_CHAT_ID", "emreturkmencom/antigravity-telegram-suite": "ALLOWED_CHAT_ID (required)",
    "NachoSEO/claudegram": "ALLOWED_USER_IDS (required)", "father-bot/chatgpt_telegram_bot": "allowed_telegram_usernames", "tbxark/ChatGPT-Telegram-Workers": "allowedUserIds (deny by default)",
    "altryne/chatGPT-telegram-bot": "TELEGRAM_USER_ID (required)", "yym68686/ChatGPT-Telegram-Bot": "whitelist, ADMIN_LIST", "V-know/ChatGPT-Telegram-Bot": "none exists (rate limits only)",
    "polakowo/gpt2bot": "none exists",
}
EXTRA = {  # one more thing the source shows, beside the two codes
    "hanxiao/claudecode-telegram": ("its webhook listens on every network interface with no secret", "webhook 监听所有网卡，且没有密钥校验"),
    "emreturkmencom/antigravity-telegram-suite": ("/cmd runs your text as a shell command, and auto-accept ships switched on", "/cmd 会把文字当 shell 命令执行，自动同意默认开启"),
    "overwirehq/claude-code-telegram": ("the open default applies unless ENVIRONMENT=production", "除非设 ENVIRONMENT=production，否则默认就是开放的"),
    "banteg/takopi": ("in a group chat every member can drive the agent unless you also list user IDs", "放在群里时，不另填用户 ID 的话每个群成员都能指挥 agent"),
    "alexei-led/ccgram": ("an allowed user can switch a session to YOLO, which skips the prompts", "白名单用户可以把会话切到 YOLO，那样就不再确认"),
    "tbxark/ChatGPT-Telegram-Workers": ("runs on Cloudflare Workers, nothing executes on a machine of yours", "跑在 Cloudflare Workers 上，不在你自己的机器上执行任何东西"),
}
VERDICT = {
    "title": ["Which one to run", "到底跑哪个"],
    "lead": ["We read the source of {n} of these bots: who each one serves, and what it can do on your machine. This is what we would pick; the [full audit](#{anchor}) is below.",
             "我们读了其中 {n} 个 bot 的源码:它为谁服务,能在你机器上做什么。结论如下,[完整审计](#{anchor})在下面。"],
    "basis": ["after reading their source", "读完源码后"], "more": ["See the audit →", "看源码审计 →"],
    "rule": ["Ranked by what the bot does when no allowlist is set, then (for bots that drive a coding agent) by what stands between a message and a command, then GitHub stars. Read from the source at the commit on each evidence page; nothing was run.",
             "排名规则：先看没设白名单时 bot 怎么做，再看（对能指挥编码 agent 的 bot）一条消息到一条命令之间隔着什么，最后看 GitHub 星数。结论来自各证据页所标 commit 的源码，没有实际运行。"],
    "picks": [
        {"repo": "alexei-led/ccgram", "role": ["To drive Claude Code from your phone", "想用手机遥控 Claude Code"],
         "why": ["One of two bots of 14 that both refuse to start without your Telegram ID and send Claude's permission prompts to you in Telegram, so a risky command still waits for your tap. The other is six-ddc/ccbot, which it grew out of; ccgram had commits this week, ccbot's last was in July.",
                 "14 个里只有两个同时做到：不填你的 Telegram ID 就拒绝启动，并且把 Claude 的权限确认发到 Telegram 让你点，所以危险命令仍然要等你同意。另一个是它的前身 six-ddc/ccbot；ccgram 本周还有提交，ccbot 最后一次提交在 7 月。"]},
        {"repo": "grinev/opencode-telegram-bot", "role": ["If your agent is OpenCode", "你用的是 OpenCode"],
         "why": ["Locked to exactly one Telegram user ID and will not start without it. When OpenCode asks for permission it shows Allow and Reject buttons in the chat; how often it asks is your OpenCode config.",
                 "只认一个 Telegram 用户 ID，不填就不启动。OpenCode 请求权限时，它在聊天里给你「允许 / 拒绝」按钮；多久问一次取决于你的 OpenCode 配置。"]},
        {"repo": "tbxark/ChatGPT-Telegram-Workers", "role": ["If you only want an AI chat bot", "只想要一个 AI 聊天 bot"],
         "why": ["The only popular chat bot here that denies by default: it answers the admin and the IDs you add, nobody else. It runs on Cloudflare Workers, so there is no server of yours to break into. Set TELEGRAM_SECRET_TOKEN as well.",
                 "这里唯一默认拒绝的热门聊天 bot：只回应管理员和你加进去的 ID。它跑在 Cloudflare Workers 上，没有你自己的服务器可被攻破。记得同时设 TELEGRAM_SECRET_TOKEN。"]},
    ],
    "avoid_label": ["Do not run as shipped:", "别按默认配置直接跑："],
    "avoid": [
        {"repo": "hanxiao/claudecode-telegram", "why": ["no access check at all, Claude runs with permissions skipped, and the webhook listens on every interface", "完全没有访问控制，Claude 跳过权限确认，webhook 还监听所有网卡"]},
        {"repo": "godagoo/claude-telegram-relay", "why": ["forget one variable and it starts anyway, serving anyone", "漏填一个变量它也照常启动，并对所有人开放"]},
        {"repo": "overwirehq/claude-code-telegram", "why": ["the most-starred one; with an empty allowlist it lets everyone in unless ENVIRONMENT=production", "星数最高的一个；白名单为空且没设 ENVIRONMENT=production 时放所有人进来"]},
    ],
    "caveat": ["Whichever you pick: 9 of the 14 agent bots run with permission prompts off, so the allowlist is the only lock. Whoever controls your Telegram account then has a shell on that machine. Turn on Telegram two-step verification, and run the bot as its own user or in a container.",
               "不管选哪个：14 个 agent 类 bot 里有 9 个跳过权限确认，白名单就是唯一一道锁。谁控制了你的 Telegram 账号，谁就拿到那台机器的 shell。给 Telegram 开两步验证，并让 bot 跑在单独的系统用户或容器里。"],
}
GROUPS = [{"id": "remote", "title": ["Bots that drive a coding agent on your machine (14)", "能在你机器上指挥编码 agent 的 bot（14 个）"]},
          {"id": "chat", "title": ["Chat-only bots (6)", "纯聊天 bot（6 个）"]}]
STYLE = """:root{--bg:#fff;--fg:#1f2328;--mute:#59636e;--line:#d0d7de;--card:#f6f8fa}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--mute:#9198a1;--line:#30363d;--card:#161b22}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,'PingFang SC',sans-serif}
main{max-width:920px;margin:0 auto;padding:24px 16px 48px}a{color:#0969da}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 8px}.mute{color:var(--mute);font-size:13px}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid var(--line);padding:6px 10px;text-align:left;vertical-align:top}
th{background:var(--card);white-space:nowrap}code{font:13px/1.5 ui-monospace,Menlo,monospace;word-break:break-word}"""


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def commit(repo: str) -> str:
    clone = HERE / "clones" / repo.replace("/", "__")
    return subprocess.run(["git", "-C", str(clone), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()[:12]


def default_code(r: dict) -> tuple:
    return NO_ACCESS if r["access"] == "none" else DEFAULT[r["default"]]


def rank(r: dict) -> tuple:
    return (default_code(r)[0], CONFIRMS[r["confirms"]][0] if r["kind"] == "remote" else 0, -r["stars"])


def page(r: dict) -> str:
    ev, sha = r["evidence"], commit(r["repo"])
    rows = [("Who can use it", default_code(r)[3], ev.get("access")), ("With no allowlist set", r["default_setting"], ev.get("default")),
            ("Before the agent acts" if r["kind"] == "remote" else "What it can do", CONFIRMS[r["confirms"]][3] if r["kind"] == "remote" else "Chat only", ev.get("confirms")),
            ("Bot token", "Read from the environment or a config file; no real token is committed", "")]
    body = "".join(f"<tr><th>{esc(a)}</th><td>{esc(b)}</td><td><code>{esc(c)}</code></td></tr>" for a, b, c in rows)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>{esc(r['repo'])}: Telegram bot source audit</title><style>{STYLE}</style></head><body><main>
<p class="mute"><a href="/best/telegram-bot/">← Open-source Telegram bots</a></p>
<h1>{esc(r['repo'])}: source audit, {DATE}</h1>
<p class="mute">Read from the source at commit <a href="https://github.com/{esc(r['repo'])}/tree/{sha}">{sha}</a>; the bot was not run (it needs a BotFather token).
Each answer cites the file and line that shows it. <a href="{REPO_URL}RESULTS.md">All 20 bots</a></p>
<h2>In short</h2><p>{esc(r['notes'])}</p>
<h2>What the source shows</h2><table><tr><th></th><th>Answer</th><th>Where</th></tr>{body}</table>
</main></body></html>"""


def card(r: dict) -> dict:
    remote = r["kind"] == "remote"
    d, c = default_code(r), CONFIRMS.get(r["confirms"])
    cells = [[d[1], d[2], d[5]], *([[c[1], c[2], c[5]]] if remote else []), [SETTING[r["repo"]], None]]
    bits = [[d[3], d[4]], *([[c[3], c[4]]] if remote else [["chat only, runs nothing on your machine", "纯聊天，不在你机器上执行任何东西"]])]
    if r["repo"] in EXTRA:
        bits.append(list(EXTRA[r["repo"]]))
    return {"ran": True, "stars": r["stars"], "sheet": r["repo"].replace("/", "__") + ".html", "group": r["kind"], "cells": cells, "bits": bits}


def markdown(rows: list[dict]) -> str:
    out = [f"# Telegram bot source audit, {DATE}", "", "Read from each repo's source; nothing was run. Evidence (file and line) is in results.json.", ""]
    for g in GROUPS:
        out += [f"## {g['title'][0]}", "", "| # | Bot | ★ | With no allowlist | Before the agent acts | Setting |", "|---|---|---:|---|---|---|"]
        for n, r in enumerate((r for r in rows if r["kind"] == g["id"]), 1):
            out.append(f"| {n} | {r['repo']} | {r['stars']} | {default_code(r)[1]} | {CONFIRMS[r['confirms']][1] if g['id'] == 'remote' else 'chat only'} | {SETTING[r['repo']]} |")
        out.append("")
    return "\n".join(out)


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    rows = sorted(json.loads((HERE / "results.json").read_text()), key=rank)
    for r in rows:
        (PUBLIC / (r["repo"].replace("/", "__") + ".html")).write_text(page(r))
    (HERE / "RESULTS.md").write_text(markdown(rows))
    remote = [r for r in rows if r["kind"] == "remote"]
    count = lambda rs, f: sum(1 for r in rs if f(r))   # noqa: E731
    skips, closed = count(remote, lambda r: r["confirms"] == "skips"), count(remote, lambda r: r["default"] == "refuses")
    chat_open = count(rows, lambda r: r["kind"] == "chat" and r["default"] == "open")
    runs = json.loads(RUNS_JSON.read_text())
    runs["telegram-bot"] = {
        "type": "table", "date": DATE, "dir": "/best-runs/telegram/", "results": REPO_URL + "RESULTS.md",
        "title": ["Source audit: who can use each bot, and what it can do", "源码审计：谁能用这个 bot，它能做什么"],
        "list_title": ["Source audit", "源码审计"],
        "intro": [f"On {DATE} we read the source of {len(rows)} of these bots. A bot needs a BotFather token to run, so this is a reading, not a run: for each one, who it serves when you set no allowlist, and for bots that drive a coding agent, what stands between a Telegram message and a command on your machine. Every answer cites its file and line; every \"serves anyone\" was re-read by hand.",
                  f"{DATE} 我们读了其中 {len(rows)} 个 bot 的源码。bot 要有 BotFather token 才能跑，所以这是读代码，不是实跑：每个 bot 在你没设白名单时为谁服务；对能指挥编码 agent 的 bot，还看一条 Telegram 消息到你机器上的一条命令之间隔着什么。每个结论都标了文件和行号；所有「任何人可用」都人工复读过。"],
        "finding": [f"{closed} of {len(remote)} agent bots serve nobody until you list your ID, but {skips} of {len(remote)} run the agent with permission prompts off, so that list is the only lock. {chat_open} of 6 chat bots answer anyone by default. No repository had a real bot token committed.",
                    f"{len(remote)} 个 agent 类 bot 里 {closed} 个在你填 ID 之前谁都不服务，但有 {skips} 个让 agent 跳过权限确认，于是白名单成了唯一一道锁。6 个聊天 bot 里 {chat_open} 个默认对所有人开放。没有仓库提交了真实的 bot token。"],
        "name_col": ["Bot", "Bot"], "columns": [["With no allowlist set", "没设白名单时"], ["Before the agent acts", "agent 动手之前"], ["Setting to check", "要检查的设置"]],
        "group_columns": {"chat": [["With no allowlist set", "没设白名单时"], ["Setting to check", "要检查的设置"]]},
        "see": ["See the lines →", "看源码依据 →"], "evidence": ["The lines", "源码依据"], "line_label": [f"Source audit {DATE}:", f"{DATE} 源码审计："],
        "groups": GROUPS, "verdict": VERDICT, "runs": {r["repo"]: card(r) for r in rows}}
    RUNS_JSON.write_text(json.dumps(runs, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(rows)} evidence pages; agent bots: {closed}/{len(remote)} closed by default, {skips} skip prompts; chat open {chat_open}/6")


if __name__ == "__main__":
    main()
