"""The daily digest's PostHog funnel list keeps revenue rows (ops/analytics_digest.py)."""

import importlib.util
from pathlib import Path

DIGEST_PATH = Path(__file__).resolve().parents[2] / "ops" / "analytics_digest.py"
SPEC = importlib.util.spec_from_file_location("analytics_digest", DIGEST_PATH)
assert SPEC and SPEC.loader
digest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(digest)


def rows(*events):
    return [{"event": e, "users_28d": 100 - i} for i, e in enumerate(events)]


def test_purchase_row_survives_the_top_15_cut():
    # fetch_posthog sorts by people; a purchase (1 person) ranks last, so a plain [:15] drops it.
    many = rows(*[f"event_{i}" for i in range(20)], "purchase_completed")
    shown = [r["event"] for r in digest.funnel_rows(many)]
    assert shown[:15] == [f"event_{i}" for i in range(15)]
    assert shown[-1] == "purchase_completed" and len(shown) == 16


def test_short_list_is_unchanged():
    few = rows("$pageview", "audit_run", "purchase_completed")
    assert digest.funnel_rows(few) == few
