"""ops/index/index_watch.py: sitemaps, what to inspect when, and what an inspection records. No network."""
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops/index"))

import index_watch as iw  # noqa: E402

TODAY = date(2026, 11, 2)
SITE = "sc-domain:agentskillshub.top"
HUB = "https://agentskillshub.top"
INDEX = f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>{HUB}/sitemap-top.xml</loc></sitemap>
  <sitemap><loc>{HUB}/sitemap-blog.xml</loc></sitemap>
</sitemapindex>""".encode()


def urlset(*locs):
    rows = "".join(f"<url><loc>{loc}</loc><lastmod>2026-10-20T08:00:00Z</lastmod></url>" for loc in locs)
    return f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{rows}</urlset>'.encode()


def page(path="/skill/a/b/", **kw):
    return iw.Page(f"{HUB}{path}", SITE, iw.kind(f"{HUB}{path}"), **kw)


def days_ago(n):
    return TODAY - timedelta(days=n)


# --- sitemaps ---------------------------------------------------------------------------

def test_a_sitemap_index_is_followed_one_level_down():
    files = {f"{HUB}/sitemap.xml": INDEX, f"{HUB}/sitemap-top.xml": urlset(f"{HUB}/skill/a/b/"),
             f"{HUB}/sitemap-blog.xml": urlset(f"{HUB}/blog/x/")}
    listed = iw.sitemap(f"{HUB}/sitemap.xml", get=files.__getitem__)
    assert listed == {f"{HUB}/skill/a/b/": date(2026, 10, 20), f"{HUB}/blog/x/": date(2026, 10, 20)}


def test_a_plain_urlset_is_read_as_is_and_a_bad_lastmod_is_none():
    xml = b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc> https://jasonzhu.ai/zh/blog/a </loc><lastmod>soon</lastmod></url></urlset>'
    assert iw.sitemap("https://jasonzhu.ai/sitemap.xml", get=lambda _: xml) == {"https://jasonzhu.ai/zh/blog/a": None}


def test_kind_is_the_first_segment_after_a_locale():
    assert iw.kind(f"{HUB}/skill/owner/repo/") == "skill"
    assert iw.kind("https://jasonzhu.ai/zh/prompts/x") == "prompts"
    assert iw.kind("https://jasonzhu.ai/en/") == "home"
    assert iw.kind(f"{HUB}/") == "home"


def test_the_first_run_dates_nothing_and_later_runs_date_new_urls():
    first = iw.merge({}, {f"{HUB}/skill/a/b/": None}, SITE, TODAY)
    assert first[f"{HUB}/skill/a/b/"].first_seen is None
    later = iw.merge(first, {f"{HUB}/skill/a/b/": None, f"{HUB}/best/new/": None}, SITE, TODAY)
    assert later[f"{HUB}/best/new/"].first_seen == TODAY and later[f"{HUB}/best/new/"].kind == "best"


def test_a_site_with_a_known_launch_day_dates_its_first_pages_by_it():
    first = iw.merge({}, {"https://new.example/": None}, "https://new.example/", TODAY, since=days_ago(1))
    assert first["https://new.example/"].first_seen == days_ago(1)


def test_sites_from_the_secret_come_after_ours_and_print_without_their_address():
    env = {iw.EXTRA_SITES: '{"https://new.example/": {"sitemap": "https://new.example/sitemap.xml", "since": "2026-10-28"}}'}
    listed = iw.sites(env)
    assert [s for s, *_ in listed[:-1]] == list(iw.SITES)
    assert listed[-1] == ("https://new.example/", "https://new.example/sitemap.xml", date(2026, 10, 28), "extra site 1")
    assert iw.sites({}) == [(s, r, None, s) for s, r in iw.SITES.items()]


def test_a_failing_secret_site_names_neither_itself_nor_stops_the_run(monkeypatch, capsys):
    env = {iw.EXTRA_SITES: '{"https://new.example/": {"sitemap": "https://new.example/sitemap.xml"}}'}
    monkeypatch.setattr(iw.os, "environ", env)
    monkeypatch.setattr(iw.gsc, "get_service", lambda: None)
    def fake(sess, conn, site, root, today, limit, since=None):
        if site.startswith("https://new.example"):
            raise ConnectionError(f"could not reach {root}")
        return Counter(listed=1)
    monkeypatch.setattr(iw, "watch", fake)
    try:
        iw.main(["--dry-run"])
    except SystemExit as stop:
        assert "extra site 1" in str(stop)
    out = capsys.readouterr().out
    assert "extra site 1: failed (ConnectionError)" in out and "new.example" not in out
    assert all(f"{s}: listed 1" in out for s in iw.SITES)


def test_a_url_gone_from_the_sitemaps_is_kept_but_marked():
    pages = iw.merge({}, {f"{HUB}/skill/a/b/": None}, SITE, days_ago(1))
    pages = iw.merge(pages, {}, SITE, TODAY)
    assert pages[f"{HUB}/skill/a/b/"].in_sitemap is False


# --- what to inspect --------------------------------------------------------------------

def test_impressions_mark_a_page_indexed_so_it_needs_no_inspection():
    pages = {p.url: p for p in [page(first_seen=days_ago(2))]}
    iw.note_search(pages, {page().url, f"{HUB}/not/ours/"}, TODAY)
    only = pages[page().url]
    assert only.search_seen == TODAY and only.first_indexed == TODAY
    assert iw.due(only, TODAY) is None


def test_a_new_page_not_yet_indexed_is_checked_daily_until_thirty_days():
    assert iw.due(page(first_seen=days_ago(3), last_checked=days_ago(1), last_state="Discovered - currently not indexed"), TODAY) == 0
    old = page(first_seen=days_ago(31), last_checked=days_ago(1), last_state="Discovered - currently not indexed")
    assert iw.due(old, TODAY) is None


def test_old_pages_wait_a_week_when_not_indexed_and_a_month_when_indexed():
    assert iw.due(page(last_checked=days_ago(7), last_state="Crawled - currently not indexed"), TODAY) == 2
    assert iw.due(page(last_checked=days_ago(6), last_state="Crawled - currently not indexed"), TODAY) is None
    assert iw.due(page(last_checked=days_ago(30), last_state="Submitted and indexed"), TODAY) == 3
    assert iw.due(page(last_checked=days_ago(29), last_state="Submitted and indexed"), TODAY) is None


def test_nothing_is_checked_twice_a_day_or_off_the_sitemaps():
    assert iw.due(page(first_seen=TODAY, last_checked=TODAY), TODAY) is None
    assert iw.due(page(in_sitemap=False), TODAY) is None


def test_pick_puts_new_pages_first_then_the_unchecked_and_keeps_to_the_limit():
    pages = [page("/skill/old/", last_checked=days_ago(40), last_state="Submitted and indexed"),
             page("/skill/never/"),
             page("/best/fresh/", first_seen=days_ago(1)),
             page("/skill/stale/", last_checked=days_ago(9), last_state="Discovered - currently not indexed")]
    assert [p.url.removeprefix(HUB) for p in iw.pick(pages, TODAY, 3)] == ["/best/fresh/", "/skill/never/", "/skill/stale/"]


# --- inspections ------------------------------------------------------------------------

STATUS = {"verdict": "PASS", "coverageState": "Submitted and indexed", "indexingState": "INDEXING_ALLOWED",
          "lastCrawlTime": "2026-11-01T07:38:34Z", "googleCanonical": f"{HUB}/skill/a/b/",
          "userCanonical": f"{HUB}/skill/a/b/", "sitemap": [f"{HUB}/sitemap-top.xml"], "pageFetchState": "SUCCESSFUL"}


def test_an_inspection_updates_its_page_and_returns_its_row():
    p = page(first_seen=days_ago(4))
    row = iw.apply(p, STATUS, TODAY)
    assert (p.last_checked, p.last_state, p.first_indexed) == (TODAY, "Submitted and indexed", TODAY)
    assert row["coverage_state"] == "Submitted and indexed" and row["sitemaps"] == [f"{HUB}/sitemap-top.xml"]
    assert row["robots_state"] is None and set(row) == {"url", *iw.FIELDS}


def test_a_page_not_indexed_keeps_no_first_indexed_day():
    p = page(first_seen=days_ago(4))
    iw.apply(p, {"coverageState": "URL is unknown to Google"}, TODAY)
    assert p.first_indexed is None and p.last_state == "URL is unknown to Google"


class _Reply:
    def __init__(self, code, body=None):
        self.status_code, self.ok, self._body = code, code == 200, body or {}

    def json(self):
        return self._body


class _Session:
    def __init__(self, *codes):
        self.codes = list(codes)

    def post(self, url, json, timeout):
        code = self.codes.pop(0)
        return _Reply(code, {"inspectionResult": {"indexStatusResult": STATUS}})


def test_failed_calls_get_tallied_and_the_daily_quota_stops_the_site(monkeypatch):
    monkeypatch.setattr(iw, "PAUSE", 0)
    tally = Counter()
    checks = iw.inspect_chunk(_Session(200, 500), SITE, [page("/a/"), page("/b/")], TODAY, tally)
    assert len(checks) == 1 and tally["failed"] == 1 and tally["Submitted and indexed"] == 1
    try:
        iw.inspect_chunk(_Session(429), SITE, [page("/c/")], TODAY, Counter())
    except iw.Quota:
        return
    raise AssertionError("a 429 should raise Quota")


def test_the_log_line_holds_counts_and_states_but_no_url():
    text = iw.line(SITE, Counter(listed=4, new=1, searched=2, due=2, **{"Submitted and indexed": 2}))
    assert text.startswith(f"{SITE}: listed 4, new 1, searched 2, due 2, failed 0")
    assert "Submitted and indexed 2" in text and "http" not in text
