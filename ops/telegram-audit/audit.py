"""Code-level audit of open-source Telegram bots: who can use the bot, and what it can do.

  python ops/telegram-audit/audit.py [owner/repo ...]     # default: candidates.json without a result

A bot needs a BotFather token to run, so this is a reading of the source, not a run:
each repo is cloned shallow (nothing is executed), the lines about access control, tokens
and confirmation are pulled out with the README, and a judge (gpt-6-astra, three passes,
majority) answers four questions with a quote. A regex also looks for a real-looking bot
token committed to the repo. Writes out/<owner__repo>.json; table.py makes the summary.
"""
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
CLONES = HERE / "clones"
PASSES, RETRIES, RETRY_SECONDS = 3, 6, 20
CODE = {".py", ".ts", ".js", ".mjs", ".go", ".rs", ".tsx", ".sh", ".toml", ".yaml", ".yml", ".example", ".env.example", ".json"}
SKIP = {"node_modules", ".git", "dist", "build", "vendor", "__pycache__", "docs", "tests", "test"}
ACCESS = re.compile(r"allow(ed|list)?_?(user|chat|id)|whitelist|authoriz|ALLOWED|admin_?(id|user)|owner_?id|is_allowed|permitted|auth(entication)? provider|not configured", re.I)
CONFIRM = re.compile(r"confirm|approv|permission|dangerous|skip-permissions|bypass|sandbox|working_?dir|allowed_?dir|workdir|cwd", re.I)
TOKEN_USE = re.compile(r"(BOT_?TOKEN|TELEGRAM_?TOKEN|TG_?TOKEN|telegram.*token)", re.I)
REAL_TOKEN = re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b")
MAX_LINES, README_MAX = 70, 6000
TOP_FILES, CONTEXT = 4, 8   # files with most matches, lines of code kept around each match

QUESTIONS = """You audit one open-source Telegram bot from excerpts of its source and README. Answer only from what is shown.
Return JSON only:
{"access": "allowlist" | "optional" | "none" | "unclear",
   // allowlist: the bot only serves configured Telegram user or chat IDs; optional: it can, but works without one; none: no such restriction
 "default": "refuses" | "open" | "unclear",
   // with the default configuration and no allowlist set, does it refuse everyone (or refuse to start), or serve anyone who messages it
 "token": "env" | "hardcoded" | "unclear",       // where the bot token comes from
 "confirms": "yes" | "no" | "n/a" | "unclear",
   // for a bot that lets a coding agent run commands or edit files on the host: does it ask for approval before risky actions, or
   // confine the agent to a working directory, by default? "no" if it runs the agent with permissions skipped by default. n/a for a chat-only bot
 "quote_access": "<the line or sentence that shows the access rule, with its file>",
 "quote_confirms": "<the line or sentence about approval, permissions or working directory, with its file, or empty>"}

Repository: {repo} ({kind})

=== README (start) ===
{readme}

=== Lines about access control ===
{access}

=== Lines about confirmation, permissions, working directory ===
{confirm}

=== Lines about the token ===
{token}"""


def env() -> dict:
    vals = {}
    for line in (Path.home() / ".claude/.env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1); vals[k.strip()] = v.strip().strip('"')
    return vals


def ask(e: dict, text: str) -> dict:
    body = {"model": e.get("FLATROUTER_MODEL", "gpt-6-astra"), "temperature": 0, "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": text}]}
    req = urllib.request.Request(e["FLATROUTER_BASE_URL"] + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": "Bearer " + e["FLATROUTER_API_KEY"], "Content-Type": "application/json"})
    for attempt in range(RETRIES):
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=300) as r:
                return json.loads(json.load(r)["choices"][0]["message"]["content"])
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as err:
            if attempt == RETRIES - 1 or (isinstance(err, urllib.error.HTTPError) and err.code < 500 and err.code != 429):
                raise
            time.sleep(RETRY_SECONDS * (attempt + 1))
    return {}


def clone(repo: str) -> Path:
    dest = CLONES / repo.replace("/", "__")
    if not dest.exists():
        subprocess.run(["git", "clone", "-q", "--depth", "1", f"https://github.com/{repo}.git", str(dest)], check=True, timeout=300)
    return dest


def files(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and not (set(p.relative_to(root).parts) & SKIP) and (p.suffix in CODE or p.name.startswith(".env")) and p.stat().st_size < 400_000:
            yield p


def grep(root: Path, pattern: re.Pattern) -> str:
    """Matching lines with the code around them, from the files that match most. A lone line
    hid the logic: "if config.allowed_users:" was shown without the branch below it that
    refuses to start when no auth is configured (claude-code-telegram, misread as open)."""
    per_file = []
    for p in files(root):
        lines = p.read_text(errors="ignore").splitlines()
        hits = [n for n, line in enumerate(lines) if pattern.search(line) and len(line) < 300]
        if hits:
            per_file.append((len(hits), p, lines, hits))
    out, budget = [], MAX_LINES * 4
    for _, p, lines, hits in sorted(per_file, key=lambda t: -t[0])[:TOP_FILES]:
        keep = sorted({i for n in hits for i in range(max(0, n - CONTEXT), min(len(lines), n + CONTEXT + 1))})
        out.append(f"--- {p.relative_to(root)} ---")
        for i in keep:
            out.append(f"{i + 1}: {lines[i][:240]}")
            budget -= 1
            if budget <= 0:
                return "\n".join(out)
    return "\n".join(out) or "(none found)"


def readme(root: Path) -> str:
    for name in ("README.md", "readme.md", "README.rst", "README"):
        if (root / name).exists():
            return (root / name).read_text(errors="ignore")[:README_MAX]
    return "(no README)"


def leaked_tokens(root: Path) -> list[str]:
    found = []
    for p in files(root):
        if REAL_TOKEN.search(p.read_text(errors="ignore")) and "example" not in p.name.lower():
            found.append(str(p.relative_to(root)))
    return found[:5]


def majority(votes: list[dict], key: str) -> str:
    vals = [str(v.get(key)) for v in votes]
    return max(set(vals), key=vals.count)


def audit(c: dict, e: dict) -> dict:
    root = clone(c["repo"])
    prompt = (QUESTIONS.replace("{repo}", c["repo"]).replace("{kind}", c["kind"]).replace("{readme}", readme(root))
              .replace("{access}", grep(root, ACCESS)).replace("{confirm}", grep(root, CONFIRM)).replace("{token}", grep(root, TOKEN_USE)[:3000]))
    votes = [ask(e, prompt) for _ in range(PASSES)]
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()[:12]
    result = {**c, **{k: majority(votes, k) for k in ("access", "default", "token", "confirms")},
              "votes": {k: [v.get(k) for v in votes] for k in ("access", "default", "confirms")},
              "quote_access": next((v.get("quote_access") for v in votes if v.get("quote_access")), ""),
              "quote_confirms": next((v.get("quote_confirms") for v in votes if v.get("quote_confirms")), ""),
              "leaked_token_files": leaked_tokens(root), "commit": head}
    (OUT / (c["repo"].replace("/", "__") + ".json")).write_text(json.dumps(result, indent=1, ensure_ascii=False))
    return result


def main() -> None:
    OUT.mkdir(exist_ok=True); CLONES.mkdir(exist_ok=True)
    e = env()
    cands = json.loads((HERE / "candidates.json").read_text())
    want = set(sys.argv[1:])
    for c in cands:
        if (want and c["repo"] not in want) or (not want and (OUT / (c["repo"].replace("/", "__") + ".json")).exists()):
            continue
        try:
            r = audit(c, e)
            print(f"{c['repo']:44} access={r['access']:9} default={r['default']:8} token={r['token']:9} confirms={r['confirms']:7} leaked={len(r['leaked_token_files'])}", flush=True)
        except Exception as err:  # noqa: BLE001 (one repo failing must not stop the rest)
            print(f"{c['repo']}: failed: {str(err)[:200]}", flush=True)


if __name__ == "__main__":
    main()
