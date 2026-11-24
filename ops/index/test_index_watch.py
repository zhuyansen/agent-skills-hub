"""Unit tests for ops/index/index_watch.py: the time budget, the quota stop and the parallel inspections.

  cd ops/index && python -m pytest test_index_watch.py
"""
import sys
import threading
import time
import types
from collections import Counter
from datetime import date
from pathlib import Path

sys.modules.setdefault("fetch_gsc", types.ModuleType("fetch_gsc"))  # needs Google libraries and a token
sys.path.insert(0, str(Path(__file__).parent))
import index_watch as iw  # noqa: E402

TODAY = date(2026, 11, 24)
INDEXED = {"coverageState": "Submitted and indexed", "verdict": "PASS"}


def pages(n):
    return [iw.Page(f"https://example.com/p{i}/", "sc-domain:example.com", "p") for i in range(n)]


def fake_inspect(monkeypatch, fn):
    monkeypatch.setattr(iw, "inspect", fn)
    monkeypatch.setattr(iw, "PAUSE", 0)


def test_every_page_inspected_before_the_deadline(monkeypatch):
    fake_inspect(monkeypatch, lambda sess, site, url: INDEXED)
    chunk, tally = pages(10), Counter()
    checks, stopped = iw.inspect_chunk(None, "s", chunk, TODAY, tally, deadline=time.monotonic() + 60)
    assert len(checks) == 10 and not stopped
    assert all(p.last_checked == TODAY and p.first_indexed == TODAY for p in chunk)
    assert tally["Submitted and indexed"] == 10 and tally["deferred"] == 0


def test_a_passed_deadline_starts_nothing_and_leaves_pages_due(monkeypatch):
    fake_inspect(monkeypatch, lambda *a: (_ for _ in ()).throw(AssertionError("inspected after the deadline")))
    chunk, tally = pages(5), Counter()
    checks, stopped = iw.inspect_chunk(None, "s", chunk, TODAY, tally, deadline=time.monotonic() - 1)
    assert checks == [] and stopped and tally["deferred"] == 5
    assert all(p.last_checked is None for p in chunk)


def test_quota_stops_the_chunk_and_is_counted(monkeypatch):
    calls = Counter()

    def inspect(sess, site, url):
        calls["n"] += 1
        if calls["n"] > 3:
            raise iw.Quota(site)
        return INDEXED

    fake_inspect(monkeypatch, inspect)
    tally = Counter()
    checks, stopped = iw.inspect_chunk(None, "s", pages(20), TODAY, tally, workers=1)
    assert len(checks) == 3 and stopped
    assert tally["quota spent"] == 1 and tally["deferred"] == 17


def test_failed_inspection_is_counted_not_applied(monkeypatch):
    fake_inspect(monkeypatch, lambda sess, site, url: None if url.endswith("p1/") else INDEXED)
    chunk, tally = pages(3), Counter()
    checks, _ = iw.inspect_chunk(None, "s", chunk, TODAY, tally)
    assert len(checks) == 2 and tally["failed"] == 1 and chunk[1].last_checked is None


def test_inspections_run_in_parallel(monkeypatch):
    live, peak, lock = Counter(), Counter(), threading.Lock()

    def inspect(sess, site, url):
        with lock:
            live["n"] += 1
            peak["n"] = max(peak["n"], live["n"])
        time.sleep(0.05)
        with lock:
            live["n"] -= 1
        return INDEXED

    fake_inspect(monkeypatch, inspect)
    iw.inspect_chunk(None, "s", pages(8), TODAY, Counter(), workers=4)
    assert peak["n"] == 4


def test_watch_defers_the_chunks_after_the_deadline(monkeypatch):
    fake_inspect(monkeypatch, lambda sess, site, url: INDEXED)
    monkeypatch.setattr(iw, "SAVE_EVERY", 4)
    monkeypatch.setattr(iw, "sitemap", lambda root: {p.url: None for p in pages(10)})
    monkeypatch.setattr(iw, "searched", lambda sess, site, today: set())
    saved = []
    monkeypatch.setattr(iw, "save", lambda conn, ps, checks: saved.append(len(checks)))
    calls, lock = Counter(), threading.Lock()

    def clock():  # the deadline (5.0) passes after the first lookup; workers call it concurrently
        with lock:
            calls["n"] += 1
            return 0.0 if calls["n"] == 1 else 10.0

    monkeypatch.setattr(iw.time, "monotonic", clock)
    tally = iw.watch(None, None, "s", "root", TODAY, 1800, deadline=5.0)
    assert tally["due"] == 10 and tally["deferred"] == 9  # one inspected, 3 skipped in its chunk, 6 never started
    assert "deferred 9" in iw.line("s", tally)


def test_site_deadline_keeps_time_for_later_sites():
    minute = 60
    # 140 minutes, two sites after this one: this one may use 110, keeping 15 for each of the others
    assert iw.site_deadline(0, 140 * minute, 2) == 110 * minute
    # the last site gets everything left
    assert iw.site_deadline(100 * minute, 140 * minute, 0) == 140 * minute
    # little time left: an even share, not less
    assert iw.site_deadline(0, 20 * minute, 2) == 20 * minute / 3
    # past the end: no time
    assert iw.site_deadline(200, 100, 1) == 200
