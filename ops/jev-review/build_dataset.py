"""Build the flag-adjudication dataset: every flag instance the scanner raises, with the
line that raised it.

The question each item asks is decidable from the text alone — does this line *issue* the
flagged behaviour, or does it merely mention/document/coincide with it? That is what the
scanner gets wrong, and unlike "is this repo malicious" it has a ground truth a reader can
check. Read-only against the catalog.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, text

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "out"
sys.path.insert(0, str(REPO / "backend"))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
import app.services.security_scanner as ss  # noqa: E402

# Complete corpus for the rare flags that drive grades; a capped sample for the two
# high-volume ones, which would otherwise be the whole dataset.
CAPS = {"sudo_usage": 120, "tunnel_service": 90, "eval_usage": 60, "sensitive_env_vars": 40,
        "env_access": 40, "subprocess_spawn": 40, "docker_privileged": 30}
CONTEXT_LINES = 3
MAX_LINE = 400


def pattern_index() -> dict[str, object]:
    lists = [ss.REJECT_PATTERNS, ss.HIGH_RISK_PATTERNS, ss.MEDIUM_RISK_PATTERNS,
             ss.AGENT_MEDIUM_PATTERNS, ss.SECRET_PATTERNS, ss.PIPE_TO_SHELL_PATTERNS]
    return {name: pat for lst in lists for pat, name, *_ in lst}


def context_of(low: str, start: int) -> tuple[str, str]:
    """The matched line, plus a few lines either side."""
    ls = low.rfind("\n", 0, start) + 1
    le = low.find("\n", start)
    le = len(low) if le < 0 else le
    head = low[:ls].rsplit("\n", CONTEXT_LINES + 1)[1:]
    tail = low[le + 1:].split("\n")[:CONTEXT_LINES]
    return low[ls:le][:MAX_LINE], "\n".join([*head, low[ls:le][:MAX_LINE], *tail])[:1200]


def fetch_rows(conn) -> list[dict]:
    rows, last = [], 0
    while True:
        batch = conn.execute(text("""
            SELECT id, repo_full_name, stars, description, security_grade, security_flags,
                   substring(readme_content, 1, 15000) AS readme
            FROM skills
            WHERE id > :last AND security_flags IS NOT NULL AND security_flags::text <> '[]'
              AND readme_content IS NOT NULL AND readme_content <> ''
            ORDER BY id LIMIT 300"""), {"last": last}).fetchall()
        if not batch:
            return rows
        rows += [dict(r._mapping) for r in batch]
        last = batch[-1].id


def items_for(row: dict, pats: dict) -> list[dict]:
    """One item per (row, flag) — the first match the scanner would have acted on."""
    low = (row["readme"] or "").lower()
    flags = row["security_flags"]
    flags = json.loads(flags) if isinstance(flags, str) else (flags or [])
    out = []
    for flag in flags:
        pat = pats.get(flag)
        if pat is None:
            continue
        match = next(iter(pat.finditer(low)), None)
        if match is None:
            continue
        line, ctx = context_of(low, match.start())
        out.append({
            "key": f"{row['repo_full_name']}::{flag}",
            "repo": row["repo_full_name"], "stars": row["stars"], "flag": flag,
            "grade": row["security_grade"], "description": (row["description"] or "")[:200],
            "line": line.strip(), "context": ctx,
            "in_fence": ss._is_in_code_block(low, match.start()),
            "heuristic_cited": ss._is_cited_or_negated(low, match.start(), flag),
        })
    return out


def main() -> None:
    eng = create_engine(dotenv_values(REPO / "backend/.env")["SUPABASE_DB_URL"], pool_pre_ping=True)
    with eng.connect() as conn:
        conn.execute(text("SET statement_timeout = '120s'"))
        rows = fetch_rows(conn)
    print(f"flagged rows with a README: {len(rows)}", file=sys.stderr)

    pats = pattern_index()
    items = [it for row in rows for it in items_for(row, pats)]
    items.sort(key=lambda it: (it["flag"], -it["stars"]))

    kept, seen = [], {}
    for it in items:
        n = seen.get(it["flag"], 0)
        if n >= CAPS.get(it["flag"], 10_000):
            continue
        seen[it["flag"]] = n + 1
        kept.append(it)

    OUT.mkdir(exist_ok=True)
    (OUT / "dataset.json").write_text(json.dumps(kept, ensure_ascii=False, indent=1))
    print(f"items: {len(kept)}")
    for flag, n in sorted(seen.items(), key=lambda kv: -kv[1]):
        print(f"  {flag:26s} {n:4d}")


if __name__ == "__main__":
    main()
