"""The radar's noise filters (10-20): partial sitemap reads, registry namespaces, words that
only doubled on GitHub, and app names not worth a keyword read. No network or database."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops/radar"))

import radar  # noqa: E402
import signals  # noqa: E402
import sitemap_diff  # noqa: E402
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


# --- sitemap_diff.diff(): partial reads and redesigns are not news --------------------------

def _day(monkeypatch, tmp_path, urls):
    monkeypatch.setattr(sitemap_diff, "SOURCES", {"site": ("https://x.test/sitemap.xml", None, 0, None)})
    monkeypatch.setattr(sitemap_diff, "site_urls", lambda *a: set(urls))
    return sitemap_diff.diff(tmp_path)


FULL = [f"https://x.test/servers/tool-{i}" for i in range(1000)]


def test_urls_missing_from_a_partial_read_are_not_new_when_they_return(monkeypatch, tmp_path):
    _day(monkeypatch, tmp_path, FULL)
    half = _day(monkeypatch, tmp_path, FULL[:500])["sites"]["site"]
    assert half["new"] == 0 and half["partial"] and half["known"] == 1000
    fresh = [f"https://x.test/servers/brandnew-{j}" for j in range(3)]
    back = _day(monkeypatch, tmp_path, FULL + fresh)
    assert back["sites"]["site"]["new"] == 3
    assert [t["term"] for t in back["terms"]] == ["brandnew"]


def test_a_redesign_day_gives_no_terms_and_is_not_new_again(monkeypatch, tmp_path):
    _day(monkeypatch, tmp_path, FULL)
    moved = [f"https://x.test/connectors/io.github.pub{k % 40}/srv-{k}" for k in range(1000)]
    day = _day(monkeypatch, tmp_path, FULL + moved)
    assert day["sites"]["site"]["flood"] and day["terms"] == []
    assert _day(monkeypatch, tmp_path, FULL + moved)["sites"]["site"]["new"] == 0


def test_a_normal_day_is_neither(monkeypatch, tmp_path):
    _day(monkeypatch, tmp_path, FULL)
    s = _day(monkeypatch, tmp_path, FULL + ["https://x.test/servers/one-more"])["sites"]["site"]
    assert not s["flood"] and not s["partial"] and s["new"] == 1


def test_status_line_says_why_new_urls_were_not_counted():
    flood = radar._site_state({"urls": 138567, "new": 71536, "flood": True, "partial": False, "known": 67058})
    assert "占 52%" in flood and "今天不从它取词" in flood
    part = radar._site_state({"urls": 67058, "new": 747, "flood": False, "partial": True, "known": 136318})
    assert "只读到已知 136318 个的 49%" in part


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
