"""The radar's shadow records, kept for a review and shown nowhere: Google Ads' money figures for the
keywords it sizes (cpc_shadow.py, migration 032), CapCut's Most Used templates (capcut.py, migration
033) and what holds a meme's results pages (meme_checks.slots, in the lead's evidence). No network:
test_radar.py's guard and stubs are reused."""
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops/radar"))

import capcut  # noqa: E402
import meme_checks  # noqa: E402
import memes  # noqa: E402
import radar  # noqa: E402
import usecases  # noqa: E402

# no_network is autouse: imported here, it holds every test of this file to the same offline rule
from .test_radar import _quiet_memes_and_charts, no_network  # noqa: E402, F401


# --- CPC in shadow (cpc_shadow.py, migration 032) ---------------------------------------

def test_volumes_keeps_what_google_ads_says_about_the_money(monkeypatch):
    answer = {"vol": {"tasks": [{"result": [{
        "keyword": "ai music video", "search_volume": 2900, "cpc": 1.84, "competition": "LOW",
        "competition_index": 12, "low_top_of_page_bid": 0.41, "high_top_of_page_bid": 2.7,
        "monthly_searches": [{"year": 2026, "month": 9, "search_volume": 2900}]}]}]}}
    monkeypatch.setattr(usecases.aisa, "call", lambda calls: (answer, 90_000))
    vol, cost = usecases.volumes(["ai music video"], 2840)
    assert cost == 90_000 and vol["ai music video"]["volume"] == 2900 and vol["ai music video"]["month"] == "2026-09"
    assert vol["ai music video"]["gads"] == {"cpc": 1.84, "bid_low": 0.41, "bid_high": 2.7,
                                             "competition": "LOW", "competition_index": 12}


def test_the_shadow_rows_are_the_answered_rows_of_the_keyword_table():
    import cpc_shadow
    money = {"cpc": None, "bid_low": None, "bid_high": None, "competition": None, "competition_index": None}
    block = {"location_code": 2840, "rows": [
        {"phrase": "iphone kupi", "kind": "name", "names": [], "volume": 2900, "gads": dict(money, cpc=0.5)},
        {"phrase": "ai poster maker", "kind": "generic", "names": ["iphone kupi"], "volume": 880, "gads": money},
        {"phrase": "unsized", "kind": "generic", "names": [], "volume": 10}]}
    rows = cpc_shadow.rows_of(block, date(2026, 10, 28))
    assert [r["phrase"] for r in rows] == ["iphone kupi", "ai poster maker"]
    assert rows[0] == {"day": date(2026, 10, 28), "phrase": "iphone kupi", "location": 2840, "kind": "name",
                       "names": [], "volume": 2900, **dict(money, cpc=0.5)}
    assert cpc_shadow.rows_of({"rows": block["rows"]}, date(2026, 10, 28)) == []
    assert cpc_shadow.record({"rows": []}) == 0


def test_skip_db_records_no_cpc(monkeypatch, tmp_path):
    import cpc_shadow
    monkeypatch.setattr(usecases, "names_to_read", lambda keep, rows: ["iphone kupi"])
    monkeypatch.setattr(usecases, "run", lambda snaps, names, repos: {"rows": [], "location_code": 2840})
    monkeypatch.setattr(cpc_shadow, "record", lambda block: (_ for _ in ()).throw(AssertionError("wrote with --skip-db")))
    blocks = {"recent_sources": {"rows": []}}
    radar.keywords(blocks, [], [], tmp_path, {"--skip-db"})
    assert blocks["usecases"] == {"rows": [], "location_code": 2840}


# --- CapCut's Most Used templates in shadow (capcut.py, migration 033) --------------------------

CC_NOW = datetime(2026, 10, 29, 16, 30, tzinfo=timezone.utc)   # 00:30 on 10-30 in Asia/Shanghai


def _card(tid, position, uses=1_200_000):
    return {"templateId": tid, "position": position, "title": f"t{tid}", "slug": f"s{tid}",
            "useCountText": "1.2M", "useCountEstimate": uses, "templateUrl": f"https://www.capcut.com/t/{tid}"}


class _FakeGoAny:
    """GoAnyAPI's CapCut listing: the hours it holds per day, and per (day, hour) a status and its pages."""
    def __init__(self, times, snaps):
        self.times, self.snaps, self.calls = times, snaps, []

    def __call__(self, path, *, timeout, **params):
        self.calls.append((path, params))
        if path.endswith("/times"):
            return {"times": self.times.get(params["day"], [])}, 0
        status, pages = self.snaps[(params["day"], params["time"])]
        items = pages[params["page"]] if params["page"] < len(pages) else []
        return {"status": status, "items": items}, 2000 if items else 0


def test_the_newest_hours_reach_back_past_midnight(monkeypatch):
    monkeypatch.setattr(capcut.goanyapi, "call", _FakeGoAny({"20261030": [0], "20261029": [21, 22, 23]}, {}))
    assert capcut.hours(CC_NOW) == [("20261030", 0), ("20261029", 23), ("20261029", 22)]


def test_a_template_is_kept_once_at_its_best_place():
    cards = [_card("7", 1), _card("8", 2, uses=None), _card("7", 30), {"templateId": "", "position": 4}]
    rows = capcut.rows_of("20261029", 23, cards)
    assert [(r["template_id"], r["position"]) for r in rows] == [("7", 1), ("8", 2)]
    assert (rows[0]["day"], rows[0]["hour"], rows[0]["use_count"]) == (date(2026, 10, 29), 23, 1_200_000)
    assert rows[1]["use_count"] is None and rows[1]["use_count_text"] == "1.2M"


def test_a_snapshot_still_collecting_is_passed_over_for_the_last_finished_one(monkeypatch):
    fake = _FakeGoAny({"20261030": [0], "20261029": [23, 22]}, {
        ("20261030", 0): ("RUNNING", [[_card("1", 1)]]),
        ("20261029", 23): ("SUCCESS", [[_card("1", 1), _card("2", 2)], [_card("2", 3), _card("3", 4)]])})
    monkeypatch.setattr(capcut.goanyapi, "call", fake)
    written = []
    monkeypatch.setattr(capcut, "_seen", lambda engine, day, hour: False)
    monkeypatch.setattr(capcut, "_write", lambda engine, rows: written.extend(rows))
    block = capcut._record(None, capcut.hours(CC_NOW))
    assert block == {"day": "20261029", "hour": 23, "templates": 3, "cards": 4, "cost_micros": 6000}
    assert [r["template_id"] for r in written] == ["1", "2", "3"]
    assert sum(path.endswith("/history") for path, _ in fake.calls) == 1 + capcut.PAGES   # pages past the end are free
    assert capcut.status(block) == "- CapCut 模板榜(影子记录,不进邮件):10-29 23 点(北京时间)那张,3 个模板(4 张卡),$0.006"


def test_a_snapshot_already_kept_is_not_bought_again(monkeypatch):
    fake = _FakeGoAny({"20261030": [0], "20261029": [23, 22]}, {})
    monkeypatch.setattr(capcut.goanyapi, "call", fake)
    monkeypatch.setattr(capcut, "_seen", lambda engine, day, hour: True)
    block = capcut._record(None, capcut.hours(CC_NOW))
    assert block == {"day": "20261030", "hour": 0, "already": True, "cost_micros": 0}
    assert all(path.endswith("/times") for path, _ in fake.calls)
    assert capcut.status(block).endswith("10-30 0 点(北京时间)那张已经记过")


def test_without_a_key_nothing_is_read(monkeypatch):
    monkeypatch.delenv("GOANYAPI_API_KEY", raising=False)
    block = capcut.record(CC_NOW)
    assert block == {"skipped": True, "why": "没有 GOANYAPI_API_KEY"}
    assert capcut.status(block) == "- CapCut 模板榜(影子记录,不进邮件):这轮不记(没有 GOANYAPI_API_KEY)"
    assert capcut.status({"error": "GoAnyError: HTTP 502"}).endswith("没记录(GoAnyError: HTTP 502)")
    assert capcut.status({"none": True, "cost_micros": 0}).endswith("这两天没有抓完的快照")


def test_the_source_run_logs_capcut_and_keeps_it_out_of_the_report_and_the_mail(monkeypatch, tmp_path, capsys):
    _quiet_memes_and_charts(monkeypatch)
    monkeypatch.setattr(radar.source_signals, "x_new", lambda snaps: {"posts": 400, "terms": []})
    monkeypatch.setattr(radar.source_signals, "hf_new", lambda snaps: {"models": 100, "terms": []})
    monkeypatch.setattr(radar.capcut, "record", lambda: (_ for _ in ()).throw(AssertionError("read with --skip-db")))
    radar.sources_main(tmp_path / "sources.md", tmp_path, {"--sources", "--skip-db"})
    assert "CapCut 模板榜(影子记录,不进邮件):这轮不记(跳过数据库)" in capsys.readouterr().out
    monkeypatch.setattr(radar.capcut, "record", lambda: {"day": "20261029", "hour": 23, "templates": 3, "cards": 4,
                                                         "cost_micros": 6000})
    monkeypatch.setattr(radar.review, "record", lambda rows: len(rows))
    radar.sources_main(tmp_path / "sources.md", tmp_path, {"--sources"})
    assert "10-29 23 点(北京时间)那张,3 个模板(4 张卡)" in capsys.readouterr().out
    assert not (tmp_path / "sources.md").exists() and not (tmp_path / "sources.picks.md").exists()


# --- a meme's results pages in shadow (meme_checks.slots, radar_leads.evidence) ------------

def _serp_answer(results, item_types):
    items = [{"type": "organic", "domain": d, "title": t} for d, t in results]
    return {"s": {"tasks": [{"result": [{"items": items, "item_types": item_types}]}]}}


def _page(platforms, others, blocks):
    return {"top": [{"domain": "youtube.com", "title": "clip"}] * platforms
            + [{"domain": "maker.example", "title": "Free maker"}] * others, "blocks": blocks}


def test_serp_names_the_other_blocks_on_the_page(monkeypatch):
    answer = _serp_answer([("www.youtube.com", "Lobby Song (Official Video)"), ("tiktok.com", "#lobbysong")],
                          ["ai_overview", "organic", "short_videos", "video"])
    monkeypatch.setattr(meme_checks.aisa, "call", lambda calls: (answer, 2000))
    page, cost = meme_checks.serp("lobby song")
    assert cost == 2000 and page["blocks"] == ["ai_overview", "short_videos", "video"]
    assert page["top"][0] == {"domain": "youtube.com", "title": "Lobby Song (Official Video)"}
    monkeypatch.setattr(meme_checks.aisa, "call", lambda calls: ({"s": {"tasks": []}}, 2000))
    assert meme_checks.serp("lobby song") == ({"top": [], "blocks": []}, 2000)


def test_competition_reads_the_names_own_page_and_keeps_its_slots(monkeypatch):
    pages = {"lobby song ai": _serp_answer([("lobbysong-ai.com", "Lobby Song AI Video Generator"), ("youtube.com", "x")],
                                           ["organic"]),
             "lobby song": _serp_answer([("youtube.com", "a"), ("tiktok.com", "b"), ("music.apple.com", "c"),
                                         ("lyrics.example", "d")], ["ai_overview", "organic", "short_videos"])}
    asked = []

    def call(calls):
        asked.append(calls[0]["arguments"]["body"][0]["keyword"])
        return pages[asked[-1]], 2000
    monkeypatch.setattr(meme_checks.aisa, "call", call)
    monkeypatch.setattr(meme_checks, "rdap", lambda d: {"domain": d, "free": True, "registered": ""})
    co, cost = meme_checks.competition({"name": "lobby song", "query": "lobby song ai"})
    assert asked == ["lobby song ai", "lobby song"] and cost == 4000
    assert (co["results"], co["tools"]) == (2, ["lobbysong-ai.com"])          # the mail's count, as before
    head, tool = co["slots"]["head"], co["slots"]["tool"]
    assert (head["results"], head["platforms"], head["blocks"]) == (4, 3, ["ai_overview", "short_videos"])
    assert (tool["tools"], tool["ads"], co["slots"]["taken"]) == (1, False, True)


def test_a_failed_name_page_keeps_the_tool_count(monkeypatch):
    def call(calls):
        if calls[0]["arguments"]["body"][0]["keyword"] == "lobby song":
            raise meme_checks.aisa.AisaError("HTTP 500")
        return _serp_answer([("maker.example", "Lobby Song AI generator")], ["organic", "paid"]), 2000
    monkeypatch.setattr(meme_checks.aisa, "call", call)
    monkeypatch.setattr(meme_checks, "rdap", lambda d: {"domain": d, "free": None, "registered": ""})
    co, cost = meme_checks.competition({"name": "lobby song", "query": "lobby song ai"})
    assert (co["tools"], co["slots"], cost) == (["maker.example"], None, 2000)


def test_ads_or_a_name_page_of_sites_is_not_taken():
    assert meme_checks.slots("x", _page(8, 2, []), _page(0, 10, []))["taken"]
    assert not meme_checks.slots("x", _page(8, 2, []), _page(0, 10, ["paid"]))["taken"]   # someone pays for the tool click
    assert not meme_checks.slots("x", _page(5, 5, ["video"]), _page(0, 10, []))["taken"]  # half is not more than half
    assert not meme_checks.slots("x", _page(0, 0, []), _page(0, 0, []))["taken"]          # no results, nothing to read


def test_slots_stay_out_of_the_mail_and_go_to_the_evidence():
    slots = meme_checks.slots("x", _page(8, 2, ["ai_overview"]), _page(0, 10, []))
    co = {"domains": [{"domain": "xai.com", "free": True, "registered": ""}], "free": ["xai.com"], "results": 10,
          "tools": [], "slots": slots}
    m = {"name": "x", "what": "w", "competition": co, "earliest": "2026-10-30", "edge": False, "age": 1}
    assert meme_checks.summary(m) == "xai.com 还空着｜Google 前 10 有 0 个工具站"
    assert memes.evidence(m)["slots"] == slots
    assert "slots" not in memes.evidence({**m, "competition": None})
