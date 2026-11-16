"""The 做站体检 in the radar (ops/radar/meme_window.py) and what it does to the picks: only
trends whose how-to wave has not started (还早) or started at most three days ago (窗口正开)
are mailed. No network: AIsa is replaced where a check would call it."""
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops/radar"))

import meme_window as mw  # noqa: E402
import memes  # noqa: E402
import radar  # noqa: E402

TODAY = date(2026, 11, 3)


def _post(day, text, views=50_000, ai=False, tools=(), lang="en", sound=None, pid=None):
    return {"id": pid or f"tt:{day}:{text}:{views}", "platform": "tiktok", "day": day, "text": text, "lang": lang,
            "views": views, "ai": ai, "tools": list(tools), "sound": sound}


# --- names and the posts that name the trend ------------------------------------------------

def test_the_search_name_drops_ai_and_a_generic_tail():
    assert mw.base_name("outstanding tiny desk ai") == "outstanding tiny desk"
    assert mw.base_name("zombie apocalypse ai video") == "zombie apocalypse"
    assert mw.base_name("ai dunking video") == "dunking video"   # two words left: the tail stays
    assert mw.base_name("fan lift ai") == "fan lift"


def test_a_short_name_needs_all_its_words_and_a_long_one_two_thirds():
    fan = mw.names_it("fan lift ai")
    assert not fan(_post("2026-09-27", "ceiling fan outfit transition ai tutorial"))   # September's other meme
    assert fan(_post("2026-11-01", "the fan lift trend is wild"))
    desk = mw.names_it("outstanding tiny desk ai")
    assert desk(_post("2026-10-18", "College Football's Week 8 All-Loss Tiny Desk Concert"))
    assert mw.names_it("bulin 47 ai")(_post("2026-10-08", "Dame hombro #bulin47 #parati"))   # written as one word


# --- the verdict ----------------------------------------------------------------------------

def _days(*isos):
    return [date.fromisoformat(d) for d in isos]


def test_one_stray_how_to_post_is_not_the_wave():
    how = _days("2026-09-07", "2026-10-01", "2026-10-02", "2026-10-02", "2026-10-04")
    assert how[mw.onset(how)] == date(2026, 10, 1)


def test_verdict_follows_the_days_since_the_wave_began():
    assert mw.verdict([], date(2026, 11, 1), TODAY)[0] == "还早"
    assert mw.verdict([], None, TODAY)[0] == "看不出来"
    assert mw.verdict(_days("2026-11-01", "2026-11-01", "2026-11-02"), None, TODAY)[:2] == ("窗口正开", 2)
    assert mw.verdict(_days("2026-10-24", "2026-10-25", "2026-10-25"), None, TODAY)[:2] == ("窗口在关", 10)
    assert mw.verdict(_days("2026-10-19", "2026-10-19", "2026-10-20"), None, TODAY)[:2] == ("多半晚了", 15)


def _summary(posts, term="fan lift ai"):
    return mw.summarize(term, posts, {}, None, TODAY, datetime(2026, 11, 3, 4, tzinfo=timezone.utc))


def test_summary_reads_only_posts_that_name_the_trend():
    named = [_post("2026-11-01", f"fan lift ai video number {i}", ai=True, lang="es") for i in range(16)]
    how = [_post(d, f"how to make the fan lift ai video, capcut template {i}") for i, d in enumerate(("2026-11-01", "2026-11-02", "2026-11-02"))]
    other = [_post("2026-09-24", f"ceiling fan outfit transition tutorial {i}") for i in range(30)]
    r = _summary(named + how + other)
    assert (r["label"], r["how_days"], r["how_start"]) == ("窗口正开", 2, "2026-11-01")
    assert r["named"] == 19 and r["found"] == 49 and r["first_ai"] == "2026-11-01"
    assert r["langs"].startswith("西语") and "CapCut" in r["tools"]


def test_the_line_says_what_was_found():
    r = _summary([_post("2026-11-02", f"fan lift ai clip {i}", ai=True) for i in range(20)])
    assert mw.line(r) == "做站体检:还早,AI 版 11-02 已出现,教程还没成批出来"
    late = dict(r, label="多半晚了", how_start="2026-10-19", how_days=15, named=7)
    assert mw.line(late) == "做站体检:多半晚了,教程/模版 10-19 起成批出现已 15 天,提到梗名的只有 7 帖,仅供参考"
    opened = dict(r, label="窗口正开", how_start="2026-11-01", how_days=2)
    assert mw.line(opened) == "做站体检:窗口正开,教程/模版 11-01 起成批出现 2 天"


# --- the check: one AIsa round, cached for CACHE_HOURS ----------------------------------------

def test_a_term_checked_lately_is_not_paid_for_again(tmp_path, monkeypatch):
    spent = []

    def fake(calls):
        spent.append(len(calls))
        aweme = {"aweme_id": "1", "desc": "fan lift ai how to make it, capcut template", "create_time": 1793500000,
                 "statistics": {"play_count": 90_000}, "aigc_info": {"created_by_ai": True}, "desc_language": "en"}
        return {c["call_id"]: {"data": [{"aweme_info": aweme}]} for c in calls if c["call_id"].startswith("tiktok")}, 1000 * len(calls)

    monkeypatch.setattr(mw.aisa, "call_all", fake)
    now = datetime(2026, 11, 3, 4, tzinfo=timezone.utc)
    first, cost = mw.check("fan lift ai", tmp_path, TODAY, now)
    assert cost > 0 and first["line"].startswith(mw.LABEL) and (tmp_path / mw.STATE).exists()
    again, cost = mw.check("fan lift ai", tmp_path, TODAY, now + timedelta(hours=2))
    assert cost == 0 and again == first and len(spent) == 1
    _, cost = mw.check("fan lift ai", tmp_path, TODAY, now + timedelta(hours=mw.CACHE_HOURS + 1))
    assert cost > 0


# --- the picks: only 还早 and 窗口正开 are mailed ----------------------------------------------

def _lead(term, checks, window=None):
    m = {"name": term, "query": term, "what": "用一张照片生成被风扇吹飞的AI视频", "new": True, "score": 0.7,
         "checks": checks, "platforms": ["tiktok"], "posts": [{"platform": "tiktok", "day": "2026-11-02", "likes": 9,
                                                                  "views": 90, "text": "t", "url": ""}], "tags": [], "format": "video"}
    first, m["edge"] = memes.earliest(m, TODAY)
    m["earliest"], m["age"] = first.isoformat(), (TODAY - first).days
    row = {"term": term, "kinds": ["meme"], "note": memes.lead_note(m), "named": 0.7}
    return dict(row, window=window) if window else row


def test_open_and_early_trends_are_mailed_the_rest_held_with_why():
    rows = [_lead("open ai", "Google 前 10 有 0 个工具站｜做站体检:窗口正开,教程/模版 11-01 起成批出现 2 天",
                  {"langs": "西语 58% · 英语 36%", "tools": "CapCut 58", "phrases": ["dime baby dance", "crea tu propio"]}),
            _lead("early ai", "做站体检:还早,AI 版 11-02 已出现,教程还没成批出来"),
            _lead("late ai", "做站体检:多半晚了,教程/模版 10-19 起成批出现已 15 天"),
            _lead("closing ai", "做站体检:窗口在关,教程/模版 10-24 起成批出现已 10 天"),
            _lead("unclear ai", "做站体检:看不出来,搜到的作品里没有 AI 版"),
            _lead("unchecked ai", "Google 前 10 有 1 个工具站")]
    lines = radar.picks({"meme": {"terms": rows}}, TODAY)
    picked = [line for line in lines if line[:2] in ("1.", "2.", "3.")]
    assert [line.split("**")[1] for line in picked] == ["open ai", "early ai", "unchecked ai"]
    assert "窗口:做站体检:窗口正开,教程/模版 11-01 起成批出现 2 天,**今天上线**" in picked[0]
    assert "主要语种 西语 58% · 英语 36%;工具 CapCut 58;高频说法 “dime baby dance”、“crea tu propio”" in picked[0]
    assert "Google 前 10 有 0 个工具站。" in picked[0] and picked[0].count("做站体检") == 1
    assert "**先备好模版,教程一成批出来就上线**" in picked[1] and 'check.py \\"early ai\\"' not in picked[1]
    assert 'python3 ~/content/memetree/check.py "early ai"' in picked[1]
    assert "还剩约" in picked[2]   # an unchecked lead keeps the old window line
    held = next(line for line in lines if line.startswith("没放进来的梗:"))
    assert "late ai(体检:多半晚了,教程/模版 10-19 起成批出现已 15 天)" in held
    assert "closing ai(体检:窗口在关" in held and "unclear ai(体检:看不出来" in held
