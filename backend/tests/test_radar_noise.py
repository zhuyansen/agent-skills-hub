"""The radar's noise filters (10-20): registry namespaces, words that only doubled on GitHub,
and app names not worth a keyword read. No network or database."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops/radar"))

import signals  # noqa: E402
import usecases  # noqa: E402
from terms import terms  # noqa: E402


# --- terms(): what is never a term ------------------------------------------------------

def test_registry_namespaces_are_not_terms():
    got = terms("connectors io.github.sadri weather-tool com.a2awire ai.getvda kr.co.klisten.api")
    assert not [t for t in got if t.split(".")[0] in {"io", "com", "ai", "kr"} and "." in t]
    assert "connectors io.github.sadri" not in got and "weather" in got


def test_a_domain_split_by_a_slug_does_not_pair():
    assert "xiaobenyang com" not in terms("xiaobenyang-com connectors")


def test_dotted_names_still_count():
    assert {"next.js", "socket.io", "qwen3.9"} <= terms("built on next.js and socket.io with qwen3.9")


# --- signals.github_surge(): a word that only doubled is not a wave ---------------------------

def _rows(word, recent, baseline):
    """One owner per repo, each description its own (signals.distinct keeps one per text)."""
    return ([(f"new{word}{i}", f"repo {word} z{word}n{i}", True) for i in range(recent)]
            + [(f"old{word}{i}", f"repo {word} z{word}o{i}", False) for i in range(baseline)])


def test_github_keeps_steep_or_wide_surges_only(monkeypatch):
    rows = _rows("pytorch", 5, 9) + _rows("falkordb", 9, 10) + _rows("hyperframes", 25, 100)
    monkeypatch.setattr(signals, "github_rows", lambda: rows)
    got = {r["term"]: r["lift"] for r in signals.github_surge()["terms"]}
    assert "pytorch" not in got                      # 5 owners, x2.6: noise
    assert got["falkordb"] == 4.5                    # steep
    assert got["hyperframes"] < 3                    # wide: 25 owners at x2.3


# --- usecases.names_to_read(): app names with nothing to read ----------------------------------

def test_apps_jev_did_not_read_today_are_not_read_for_keywords():
    rows = [{"term": "clockstack", "kinds": ["appstore"], "named": None},
            {"term": "derrimut gym", "kinds": ["appstore"], "named": 0.79},
            {"term": "big app", "kinds": ["appstore"], "named": 0.85},
            {"term": "cobol", "kinds": ["x"], "named": None},
            {"term": "seen twice", "kinds": ["appstore", "x"], "named": None}]
    assert usecases.names_to_read([], rows) == ["big app", "cobol", "seen twice"]
