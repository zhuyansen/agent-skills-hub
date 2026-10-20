"""AI video trends in the radar mail: when a trend first showed, and the picks that follow
from it (ops/radar/memes.py, radar.picks). No network or database calls."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops/radar"))

import memes  # noqa: E402
import radar  # noqa: E402

TODAY = date(2026, 10, 20)


def _post(day, platform="tiktok"):
    return {"platform": platform, "day": day, "likes": 10, "views": 100, "text": "t", "url": ""}


def _trend(posts, tags=(), new=True, score=0.56, checks="", what="用AI把自己放进韩国棒球比赛场景中的视频"):
    m = {"name": "x", "query": "x ai", "what": what, "posts": list(posts), "tags": list(tags), "new": new,
         "score": score, "checks": checks, "platforms": sorted({p["platform"] for p in posts} | ({"tags"} if tags else set()))}
    first, m["edge"] = memes.earliest(m, TODAY)
    m["earliest"] = first.isoformat() if first else ""
    m["age"] = (TODAY - first).days if first else None
    return m


# --- earliest(): the first day a trend shows -------------------------------------------

def test_earliest_is_the_oldest_dated_post():
    m = _trend([_post("2026-10-18"), _post("2026-10-19"), _post("", "youtube")])
    assert (m["earliest"], m["age"], m["edge"]) == ("2026-10-18", 2, False)


def test_a_post_at_the_edge_of_the_read_window_may_be_older_still():
    m = _trend([_post("2026-10-13")])   # ceiling fan outfit, 10-20: seven days back
    assert m["edge"] and m["age"] == 7


def test_youtube_only_has_no_date():
    m = _trend([_post("", "youtube")] * 3)
    assert m["earliest"] == "" and m["age"] is None


def test_a_hashtag_dates_a_trend_from_the_day_it_started_rising():
    # last point read as yesterday (10-19): 30 is three points before it, on 10-16
    m = _trend([], tags=[{"tag": "x", "curve": [0, 2, 5, 30, 60, 100, 90]}])
    assert m["earliest"] == "2026-10-16" and m["age"] == 4


def test_only_new_trends_younger_than_their_peak_are_in_the_window():
    assert memes.in_window(_trend([_post("2026-10-18")]))
    assert not memes.in_window(_trend([_post("2026-10-15")]))   # Bulin 47: one post of 10-15
    assert not memes.in_window(_trend([_post("2026-10-18")], new=False))
    assert not memes.in_window(_trend([_post("", "youtube")]))


# --- the lead's note: all the daily mail gets back from radar_leads -----------------------

def test_note_round_trip():
    checks = "评论 18% 想自己做(10/57)｜koreanbaseballai.com 还空着｜Google 前 10 有 0 个工具站"
    m = _trend([_post("2026-10-18"), _post("", "youtube")], checks=checks)
    note = memes.lead_note(m)
    assert note.startswith("①梗 TikTok/YouTube 2 帖,最早 10-18,Jev 机会 0.56｜")
    got = memes.read_note(note, TODAY)
    assert got == {"where": "TikTok/YouTube", "posts": 2, "earliest": date(2026, 10, 18), "edge": False,
                   "what": m["what"], "checks": checks}


def test_note_keeps_the_edge_mark():
    note = memes.lead_note(_trend([_post("2026-10-13")]))
    assert ",最早 ≤10-13," in note
    assert memes.read_note(note, TODAY)["edge"]


def test_notes_from_before_dates_still_read():
    got = memes.read_note("①梗 YouTube 12 帖,Jev 机会 0.56", TODAY)
    assert (got["where"], got["posts"], got["earliest"], got["what"], got["checks"]) == ("YouTube", 12, None, "", "")
    got = memes.read_note("①梗 TikTok 1 帖,Jev 机会 0.55｜评论 18% 想自己做(10/57)｜a.com 还空着", TODAY)
    assert got["checks"] == "评论 18% 想自己做(10/57)｜a.com 还空着" and got["earliest"] is None


def test_note_date_never_lands_in_the_future():
    note = "①梗 TikTok 1 帖,最早 12-30,Jev 机会 0.60"
    assert memes.read_note(note, date(2027, 1, 2))["earliest"] == date(2026, 12, 30)


# --- radar.picks(): 10-20's mail, rebuilt ---------------------------------------------

def _lead(term, posts, **kw):
    m = _trend(posts, **kw)
    return {"term": term, "kinds": ["meme"], "note": memes.lead_note(m), "named": m["score"]}


def _mail_of_10_20():
    rows = [_lead("bulin 47 ai dance", [_post("2026-10-15")], score=0.58),
            {"term": "hotel lobby migos ai", "kinds": ["meme"], "note": "①梗 YouTube 12 帖,Jev 机会 0.56", "named": 0.56},
            _lead("korean baseball ai", [_post("2026-10-18"), _post("", "youtube"), _post("", "youtube")]),
            _lead("ceiling fan outfit ai", [_post("2026-10-13")], score=0.55),
            _lead("charme dance ai", [_post("2026-10-18")], score=0.58,
                  checks="评论 1% 想自己做(1/97)｜Google 前 10 有 5 个工具站(已经挤了)"),
            _lead("too weak ai", [_post("2026-10-19")], score=0.40)]
    return radar.picks({"recent_sources": {"rows": rows}}, TODAY)


def test_only_the_trend_still_before_its_peak_is_picked():
    lines = _mail_of_10_20()
    assert lines[0].startswith("1. **korean baseball ai**:AI 视频梗,用AI把自己放进韩国棒球比赛场景中的视频。")
    assert "最早出现 10-18,已 2 天;TikTok/YouTube 3 帖,Jev 机会 0.56" in lines[0]
    assert "还剩约 2 天,**今天上线**" in lines[0] and lines[0].count("Jev 机会") == 1
    assert not any(line.startswith("2.") for line in lines)


def test_the_trends_left_out_say_why():
    held = _mail_of_10_20()[-3]
    assert held.startswith("没放进来的 AI 视频梗:")
    assert "bulin 47 ai dance(最早出现 10-15,已 5 天,过了见顶期)" in held
    assert "hotel lobby migos ai(只在 YouTube 出现,看不出日期)" in held
    assert "ceiling fan outfit ai(最早出现 10-13 或更早,已 7 天以上,过了见顶期)" in held
    assert "charme dance ai(Google 前 10 已经挤了)" in held
    assert "too weak ai" not in held


def test_the_window_closes_as_the_days_pass():
    rows = [_lead("korean baseball ai", [_post("2026-10-18")])]
    assert radar.picks({"recent_sources": {"rows": rows}}, date(2026, 10, 21))[0].startswith("1. **korean")
    later = radar.picks({"recent_sources": {"rows": rows}}, date(2026, 10, 22))
    assert later[0].startswith("**今天没有值得动手的词。**") and "已 4 天,过了见顶期" in later[-3] and later[-1] == memes.AGE_NOTE


# --- the rest of the mail -------------------------------------------------------------------

def test_daily_status_says_where_trends_and_charts_run():
    b = {"meme": {"skipped": True}, "appstore": {"skipped": True}, "recent_sources": {"rows": []}}
    assert all("在每 8 小时的源头任务里跑" in line for line in radar._meme_app_status(b))
    assert radar._meme_app_status({"meme": {"skipped": True}, "appstore": {"skipped": True}}) == \
        ["- ① 梗:跳过", "- ② 榜单:跳过"]


def test_trend_table_shows_when_each_trend_first_showed():
    found = [dict(_trend([_post("2026-10-18")]), name="korean baseball", first="2026-10-19"),
             dict(_trend([_post("2026-10-13")]), name="ceiling fan outfit", first="2026-10-20"),
             dict(_trend([_post("", "youtube")]), name="hotel lobby migos", first="2026-10-19", new=False)]
    rows = memes.section({"today": TODAY.isoformat(), "memes": found, "posts": 5, "tags": 0})
    table = "\n".join(rows)
    assert "| **10-18(2 天)** |" in table and "| 10-13 或更早(7 天+) |" in table
    assert "| 看不出(只有 YouTube) |" in table
