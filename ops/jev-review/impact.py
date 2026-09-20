"""What the second pass would do to the live catalog at the zero-loss threshold."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
import app.services.security_scanner as ss  # noqa: E402

THRESHOLD = 0.0  # the operating point that cleared 64% of citations and lost zero real flags


def grade_of(flags: list[str], tier: int) -> str:
    high = [f for f in flags if f in ss.HIGH_RISK_FLAG_NAMES]
    med = [f for f in flags if f in ss.MEDIUM_RISK_FLAG_NAMES]
    if any(f in ss.REJECT_FLAG_NAMES for f in flags):
        return "unsafe" if tier <= 2 else "reject"
    if high:
        if tier <= 3:
            return "caution"
        if tier == 4:
            return "caution" if len(high) == 1 else "unsafe"
        return "unsafe"
    if med:
        return "unsafe" if (tier == 5 and len(med) >= 3) else "caution"
    return "safe"


def main() -> None:
    items = json.load(open(OUT / "adjudicated-dataset.json"))
    per_repo: dict[str, dict] = {}
    for it in items:
        r = per_repo.setdefault(it["repo"], {"grade": it["grade"], "keep": [], "drop": []})
        (r["keep"] if it["jev_score"] > THRESHOLD else r["drop"]).append(it["flag"])

    sup = sum(len(r["drop"]) for r in per_repo.values())
    print(f"flag instances adjudicated: {len(items)} · suppressed at score<={THRESHOLD}: {sup} ({sup/len(items):.1%})")
    by_flag = Counter(f for r in per_repo.values() for f in r["drop"])
    tot = Counter(it["flag"] for it in items)
    print("\nsuppression rate per flag (the flags that grade the catalog):")
    for flag, n in sorted(tot.items(), key=lambda kv: -by_flag[kv[0]] / kv[1]):
        if n >= 5:
            print(f"  {flag:26s} {by_flag[flag]:4d}/{n:<4d} {by_flag[flag]/n:6.0%}")

    moves = Counter()
    for repo, r in per_repo.items():
        # Tier is unknown here, so hold it fixed: only the flag set changes.
        for tier in (5,):
            before, after = grade_of(r["keep"] + r["drop"], tier), grade_of(r["keep"], tier)
            if before != after:
                moves[f"{before} → {after}"] += 1
    print(f"\nrepos whose grade would move (at tier 5, the strictest): {sum(moves.values())} of {len(per_repo)}")
    for k, v in moves.most_common():
        print(f"  {k:22s} {v}")


if __name__ == "__main__":
    main()
