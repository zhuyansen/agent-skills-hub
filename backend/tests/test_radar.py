"""The radar's pure logic (ops/radar): name extraction, signal scoring, the review's verdict.
Network and database calls are not exercised here."""
import gzip
import json
import socket
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops/radar"))

import breakout  # noqa: E402
import radar  # noqa: E402
import review  # noqa: E402
import source_signals  # noqa: E402
from source_signals import base_name, novel_names  # noqa: E402
from terms import names  # noqa: E402

NOW = datetime(2026, 10, 3, 12, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Every test here runs offline: a source left unstubbed fails at its first connection instead
    of hanging on the proxy (sources_main, 2026-10-20). pytest.fail is a BaseException, so the
    sources' `except Exception` and their retries do not swallow it."""
    def refuse(target):
        pytest.fail(f"test_radar.py reached the network ({target}): stub the source that called it")
    monkeypatch.setattr(socket, "getaddrinfo", lambda host, *a, **k: refuse(host))
    monkeypatch.setattr(socket.socket, "connect", lambda self, address: refuse(address))
    monkeypatch.setattr(socket.socket, "connect_ex", lambda self, address: refuse(address))


# --- names(): what a post can name -------------------------------------------------

def test_names_keeps_versioned_model_names_whole():
    found = names("Introducing Claude Opus 5.5, our best model.")
    assert "claude opus 5.5" in found and "opus 5.5" in found


def test_names_drops_phrases_made_only_of_stop_words():
    assert "claude code" not in names("Try it in Claude Code today")


def test_names_takes_a_name_that_starts_the_sentence():
    assert "strata" in names("Strata now runs Qwen3.8-Flash-Next on a 12GB RTX 5070. Big day.")


def test_names_stops_at_the_end_of_a_sentence():
    assert not any("big" in n and "5070" in n for n in names("on a RTX 5070. Big day."))


def test_names_ignores_urls_and_handles():
    assert names("see https://Example.com/Foo by @SomeOne") == set()


# --- ① X: only names the accounts have not used before ------------------------------

def _post(account, text, likes=0, hours_ago=2):
    return {"account": account, "text": text, "likes": likes, "url": "", "created": NOW - timedelta(hours=hours_ago)}


def test_x_reports_a_new_name_two_accounts_used():
    rows = novel_names([_post("a", "Strata is fast"), _post("b", "Tried Strata today")], {}, NOW)
    assert [r["term"] for r in rows] == ["strata"] and rows[0]["sources"] == ["a", "b"]


def test_x_skips_names_already_in_the_vocabulary():
    rows = novel_names([_post("a", "Strata is fast"), _post("b", "Tried Strata today")], {"strata": "2026-09-01"}, NOW)
    assert rows == []


def test_x_one_account_needs_likes_and_an_unmistakable_name():
    assert novel_names([_post("a", "Qwen3.9 is fast", likes=20)], {}, NOW) == []
    assert [r["term"] for r in novel_names([_post("a", "Qwen3.9 is fast", likes=500)], {}, NOW)] == ["qwen3.9"]
    # a plain capitalised word may only be the start of a sentence: one account is not enough
    assert novel_names([_post("a", "Strata is fast", likes=500)], {}, NOW) == []


def test_x_one_post_yields_at_most_three_names():
    post = _post("a", "New: Alpha1 Beta2 Gamma3 Delta4 Eps5 Zeta6 models", likes=900)
    assert len(novel_names([post], {}, NOW)) <= 3


def test_names_breaks_on_chinese_text_between_words():
    found = names("用 Opus 5.5 配音（Gemini 3.8 Flash TTS，我提供了 API Key）")
    assert "gemini 3.8 flash" in found and not any("tts" in n and "api" in n for n in found)


def test_x_ignores_old_posts_and_retweets():
    old = [_post("a", "Strata is fast", hours_ago=48), _post("b", "Strata rocks", hours_ago=48)]
    rts = [_post("a", "RT @x: Strata is fast"), _post("b", "RT @x: Strata rocks")]
    assert novel_names(old, {}, NOW) == [] and novel_names(rts, {}, NOW) == []


def test_x_is_read_about_once_a_day(monkeypatch, tmp_path):
    tweet = {"text": "Strata is fast", "likeCount": 5, "url": "https://x.com/a/status/1", "createdAt": "Wed Oct 21 08:00:00 +0000 2026"}
    monkeypatch.setattr(source_signals.aisa, "call_all", lambda calls: ({c["call_id"]: {"data": {"tweets": [tweet]}} for c in calls},
                                                                       3000 * len(calls)))
    assert source_signals.x_wait(tmp_path) is None                                  # no read on record: due
    out = source_signals.x_new(tmp_path)
    assert out["posts"] == len(source_signals.accounts()) and out["cost_micros"] == 3000 * len(source_signals.accounts())
    read = datetime.fromisoformat(json.loads((tmp_path / source_signals.X_READ).read_text())["at"])
    waiting = source_signals.x_wait(tmp_path, read + timedelta(hours=16))
    assert waiting["skipped"] and waiting["waiting"] and waiting["hours"] == 16.0
    assert source_signals.x_wait(tmp_path, read + timedelta(hours=source_signals.X_EVERY_HOURS)) is None
    # a read that got nothing (no credit, the gateway down) leaves the last read on record: the next run tries again
    monkeypatch.setattr(source_signals.aisa, "call_all", lambda calls: ({}, 0))
    source_signals.x_new(tmp_path / "failed")
    assert not (tmp_path / "failed" / source_signals.X_READ).exists()
    assert source_signals.LOOKBACK_HOURS >= 30                                       # a day's posts, and a late run, are covered


def test_the_source_runs_between_two_x_reads_leave_x_out(monkeypatch, tmp_path):
    _quiet_memes_and_charts(monkeypatch)
    monkeypatch.setattr(radar.source_signals, "hf_new", lambda snaps: {"models": 100, "terms": []})
    reads = []
    monkeypatch.setattr(radar.source_signals, "x_new", lambda snaps: reads.append(snaps) or {"posts": 400, "terms": []})
    stamp = tmp_path / radar.source_signals.X_READ
    for hours_ago in (8, 16, 21):
        stamp.write_text(json.dumps({"at": (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()}))
        radar.sources_main(tmp_path / "sources.md", tmp_path, {"--sources", "--skip-db"})
    assert reads == [tmp_path]                                                       # only the run 21 hours on read X
    assert radar.x_waiting({"hours": 8.2, "last_read": "2026-10-21T00:41+00:00"}) == \
        "- ① X:8.2 小时前读过(10-21 00:41 UTC),每 20 小时读一次,这轮不读"


# --- ① HF: copies of one model group under its base name -----------------------------

def test_hf_base_name_strips_quantisation_and_size():
    assert base_name("abenzerps/Qwen-Image-2.1-Uncensored-GGUF") == "qwen image 2.1"
    assert base_name("Qwen/Qwen3.8-Flash-Next-A6B-Instruct") == "qwen3.8 flash next"
    assert base_name("Lightricks/LTX-2.5") == "ltx 2.5"


# --- ② breakout: one repo taking off --------------------------------------------------

def _repo(name, stars, days_old):
    created = (NOW - timedelta(days=days_old)).isoformat().replace("+00:00", "Z")
    return {"full_name": name, "stargazers_count": stars, "created_at": created, "description": ""}


def test_breakout_flags_a_fast_repo_and_skips_a_slow_one():
    rows = breakout.score([_repo("Niko1221/Strata", 7734, 9), _repo("a/slow", 900, 12)], None, NOW)
    assert [r["repo"] for r in rows] == ["Niko1221/Strata"]


def test_breakout_flags_a_jump_since_yesterday_even_when_the_average_is_low():
    rows = breakout.score([_repo("a/late", 1500, 13)], {"a/late": 900}, NOW)
    assert rows and rows[0]["delta"] == 600


def test_breakout_variants_include_handle_and_display_name():
    row = {"owner": "Niko1221", "name": "Strata"}
    assert breakout.variants(row, "Niko") == ["strata", "niko1221 strata", "niko strata"]
    assert breakout.variants(row, "") == ["strata", "niko1221 strata"]


def test_breakout_flags_a_repo_that_takes_off_in_its_third_week():
    # Filee-like: under the average bar for three weeks, then +900 since yesterday
    rows = breakout.score([_repo("KnifeLemon/Filee", 3900, 20)], {"KnifeLemon/Filee": 3000}, NOW)
    assert rows and rows[0]["delta"] == 900 and rows[0]["age_days"] == 20


def test_breakout_searches_late_repos_apart_so_young_ones_keep_their_pages(monkeypatch):
    queries = []

    def search(query, tok):
        queries.append(query)
        young = [_repo("a/young", 900, 2)]
        return young if query.startswith("created:>=") else [_repo("KnifeLemon/Filee", 7647, 21)] + young
    monkeypatch.setattr(breakout, "_search", search)
    repos, late, error = breakout.searched("", date(2026, 10, 20))
    assert queries == ["created:>=2026-10-06 stars:>=300", "created:2026-09-20..2026-10-05 stars:>=1000"]
    assert [r["full_name"] for r in repos] == ["a/young", "KnifeLemon/Filee"] and late == 1 and error is None


def test_breakout_a_failed_late_search_keeps_the_young_repos(monkeypatch):
    def search(query, tok):
        if query.startswith("created:>="):
            return [_repo("a/young", 900, 2)]
        raise OSError("HTTP Error 403: rate limit exceeded")
    monkeypatch.setattr(breakout, "_search", search)
    repos, late, error = breakout.searched("", date(2026, 10, 20))
    assert [r["full_name"] for r in repos] == ["a/young"] and late == 0 and "403" in error


def _fast(repo, velocity):
    return {"repo": repo, "velocity": velocity, "delta": None}


def _flagged(path):
    return json.loads(gzip.decompress(path.read_bytes())) if path.exists() else {}


def test_breakout_scores_every_repo_above_the_bar_not_only_the_fastest():
    assert len(breakout.score([_repo(f"a/r{i}", 3000, 2) for i in range(20)], None, NOW)) == 20


def test_breakout_a_first_time_breakout_below_the_fifteenth_is_still_new(tmp_path):
    path = tmp_path / "gh_flagged.json.gz"
    path.write_bytes(gzip.compress(json.dumps({f"old/r{i}": "2026-10-15" for i in range(16)}).encode()))
    rows = [_fast(f"old/r{i}", 1000 - i) for i in range(16)] + [_fast("new/late", 300)]
    shown = breakout.mark_new(rows, path, date(2026, 10, 20))
    assert len(shown) == breakout.TOP and [r["repo"] for r in shown if r["new"]] == ["new/late"]
    assert _flagged(path)["new/late"] == "2026-10-20"


def test_breakout_a_first_time_breakout_left_out_today_stays_new_tomorrow(tmp_path):
    path = tmp_path / "gh_flagged.json.gz"
    shown = breakout.mark_new([_fast(f"new/r{i}", 1000 - i) for i in range(18)], path, date(2026, 10, 20))
    assert len(shown) == breakout.TOP and all(r["new"] for r in shown)
    assert "new/r0" in _flagged(path) and "new/r17" not in _flagged(path)


def test_breakout_remembers_a_flag_longer_than_a_repo_stays_in_the_searches():
    assert breakout.FLAGGED_DAYS > breakout.LATE_DAYS


# --- merging the signals ----------------------------------------------------------------

def test_leads_merge_a_term_seen_by_two_signals(monkeypatch):
    monkeypatch.setattr(radar, "judge", lambda rows: None)
    blocks = {"x": {"terms": [{"term": "strata", "recent": 2, "note": "X 2 个账号"}]},
              "breakout": {"terms": [{"term": "strata", "recent": 1, "note": "GitHub 爆发",
                                      "variants": ["strata", "niko1221 strata"]}]},
              "github": {"terms": [{"term": "other", "recent": 3, "lift": 4.0}]}}
    rows = radar.leads(blocks)
    assert rows[0]["term"] == "strata" and rows[0]["kinds"] == ["x", "breakout"]
    assert rows[0]["variants"] == ["strata", "niko1221 strata"]
    assert rows[1]["signals"] == ["②GitHub 3 处 (×4.0)"]


def test_the_daily_snapshot_drops_what_retired_signals_kept(tmp_path):
    for name in [*radar.RETIRED_SNAPSHOTS, "gh_stars.json.gz"]:
        (tmp_path / name).write_bytes(b"x")
    radar.drop_retired(tmp_path)
    assert [p.name for p in tmp_path.iterdir()] == ["gh_stars.json.gz"]   # breakout's own snapshot stays
    radar.drop_retired(tmp_path)                                         # nothing left to drop: no error


# --- ⑤ review: did it rise, judged against its own baseline ----------------------------

SEEN = date(2026, 9, 25)


def _series(values_by_day):
    start = date(2026, 9, 19)
    return [(start + timedelta(days=i), v) for i, v in enumerate(values_by_day)]


def test_review_a_word_with_an_older_meaning_does_not_count_as_rising():
    # 'strata' alone, 2026-09-19..10-02, as DataForSEO returned it: high baseline throughout
    assert not review.rose(_series([40, 67, 70, 67, 76, 80, 68, 62, 70, 100, 89, 98, 36, 33]), SEEN)["rose"]


def test_review_a_new_name_rising_from_zero_counts_and_dates_the_rise():
    out = review.rose(_series([0, 0, 0, 0, 0, 0, 0, 0, 0, 30, 30, 100, 0, 0]), SEEN)
    assert out["rose"] and out["first_rise"] == "2026-09-28"


def test_review_all_zero_is_no_data():
    assert review.rose(_series([0] * 14), SEEN)["no_data"]


def test_review_verdict_takes_the_earliest_variant_that_rose():
    per = {"strata": {"rose": False, "no_data": False},
           "niko1221 strata": {"rose": True, "first_rise": "2026-09-27"},
           "niko strata": {"rose": True, "first_rise": "2026-09-30"}}
    assert review.verdict(per, SEEN) == ("hit", 2)


def test_review_verdict_miss_and_no_data():
    assert review.verdict({"a": {"rose": False, "no_data": False}}, SEEN) == ("miss", None)
    assert review.verdict({"a": {"rose": False, "no_data": True}}, SEEN) == ("no_data", None)


def test_a_hit_counts_as_early_only_when_trends_rose_after_the_radar_saw_it():
    # 10-21: 16 of 17 hits had lead_days <= 0, so "75%" was mostly terms the radar saw late
    rows = [(["x"], "hit", 2), (["x"], "hit", 0), (["x", "breakout"], "hit", -4), (["x"], "miss", None),
            (["breakout"], "no_data", None), (["breakout"], "hit", 1), (["breakout"], "hit", 5), (["sitemap"], "miss", None)]
    by = review.tally(rows)
    assert by["x"] == {"checked": 4, "early": 1, "late": 2, "miss": 1, "no_data": 0, "median_lead": 2}
    assert by["breakout"] == {"checked": 4, "early": 2, "late": 1, "miss": 0, "no_data": 1, "median_lead": 3}
    assert (by["sitemap"]["early"], by["sitemap"]["median_lead"]) == (0, None)
    assert review.outcome("hit", None) == "late"   # a hit without a date is not counted as early


def test_the_review_section_names_only_the_early_hits():
    rev = {"checked": [{"term": "strata", "first_seen": "2026-10-04", "verdict": "hit", "lead_days": 2},
                       {"term": "v4.1 flash", "first_seen": "2026-10-04", "verdict": "hit", "lead_days": -24},
                       {"term": "genpark", "first_seen": "2026-10-04", "verdict": "miss", "lead_days": None},
                       {"term": "connectors in.zelta", "first_seen": "2026-10-04", "verdict": "no_data", "lead_days": None}]}
    summ = {"by_signal": review.tally([(["x"], "hit", 2), (["x"], "hit", -24), (["sitemap"], "miss", None)]),
            "pending": 412, "window_days": 60}
    lines = radar.review_lines(rev, summ)
    text = "\n".join(lines)
    assert "今天复盘 4 个:提前命中 1,晚到 1,没起来 1,没数据 1。" in text
    assert "- 提前命中 **strata**:2026-10-04 报出,提前 2 天" in lines
    assert not any(t in text for t in ("v4.1 flash", "genpark", "in.zelta"))     # the rest are counts, not rows
    assert "| ①X | 2 | 1 | 1 | 0 | 0 | 50% | 2 |" in lines and "| ③竞品(已停) | 1 | 0 | 0 | 1 | 0 | 0% | — |" in lines


# --- the 8-hourly source run --------------------------------------------------------------

def _quiet_memes_and_charts(monkeypatch):
    """The run's other sources, without the network (the real ones make about 400 calls to
    AIsa, Apple and Apolu, plus Bluesky, t.co and RDAP): all read fine and found nothing new."""
    monkeypatch.setattr(radar.memes, "memes", lambda snaps: {
        "posts": 120, "by_platform": {"tiktok": 40, "instagram": 30, "youtube": 30, "x": 20}, "tags": 6,
        "memes": [], "terms": [], "errors": [], "jev": True, "cost_micros": 0})
    monkeypatch.setattr(radar.appstore, "apps", lambda snaps: {
        "charts": 290, "failed": [], "apps": [], "terms": [], "read": [], "errors": [], "cost_micros": 0})
    _social_world(monkeypatch, [], {})   # the new sites people link: no links on Bluesky, none in the X posts


def test_sources_run_writes_no_report_when_nothing_is_new(monkeypatch, tmp_path):
    _quiet_memes_and_charts(monkeypatch)
    monkeypatch.setattr(radar.source_signals, "x_new", lambda snaps: {"posts": 400, "terms": []})
    monkeypatch.setattr(radar.source_signals, "hf_new", lambda snaps: {"models": 100, "terms": []})
    report = tmp_path / "sources.md"
    assert radar.sources_main(report, tmp_path, {"--sources", "--skip-db"}) == 0
    assert not report.exists()


def test_sources_run_reports_a_new_name(monkeypatch, tmp_path):
    _quiet_memes_and_charts(monkeypatch)
    monkeypatch.setattr(radar, "judge", lambda rows: None)
    monkeypatch.setattr(radar.source_signals, "x_new", lambda snaps: {"posts": 400, "cost_micros": 72000, "terms": [
        {"term": "qwen3.9", "recent": 2, "note": "X 2 个账号 ♥900", "examples": ["@Alibaba_Qwen: Qwen3.9 is out"]}]})
    monkeypatch.setattr(radar.source_signals, "hf_new", lambda snaps: {"models": 100, "terms": []})
    report = tmp_path / "sources.md"
    radar.sources_main(report, tmp_path, {"--sources", "--skip-db"})
    text = report.read_text()
    assert "**qwen3.9**" in text and "$0.072" in text


# --- mail ------------------------------------------------------------------------

def test_mail_html_renders_tables():
    import notify
    out = notify.html("| a | b |\n|---|---|\n| 1 | 2 |")
    assert "<table style=" in out and ">1</td>" in out
    # Gmail drops a <style> block outside <head>: every tag carries its own style.
    assert "<style>" not in out and '<td style="border:1px solid' in out


def test_mail_without_recipient_is_skipped(monkeypatch):
    import notify
    monkeypatch.delenv("RADAR_EMAIL_TO", raising=False)
    assert notify.send("s", "x").startswith("skipped")


def test_review_sends_one_trends_task_per_call():
    # DataForSEO's live endpoint runs only the first task of a body (2026-10-03)
    due = [("strata", date(2026, 9, 25), ["strata", "niko1221 strata", "niko strata", "a fourth"]), ("veo 3 free", date(2026, 10, 3), [])]
    calls, plan = review.plan_calls(due, date(2026, 10, 17))
    assert len(calls) == 4 and all(len(c["arguments"]["body"]) == 1 for c in calls)
    assert [c["arguments"]["body"][0]["keywords"] for c in calls[:3]] == [["strata"], ["niko1221 strata"], ["niko strata"]]
    assert calls[3]["arguments"]["body"][0]["keywords"] == ["veo 3 free"]
    assert calls[0]["arguments"]["body"][0]["date_to"] == "2026-10-09" and calls[3]["arguments"]["body"][0]["date_to"] == "2026-10-17"


def test_review_takes_whole_leads_up_to_the_call_budget_and_leaves_the_rest_due():
    seen = date(2026, 10, 1)
    due = [(f"name {i}", seen, ["a", "b", "c", "d"]) for i in range(review.REVIEW_CALLS_MAX)] + [("last", seen, [])]
    kept = review.within_budget(due)
    assert len(kept) == review.REVIEW_CALLS_MAX // review.MAX_VARIANTS   # 3 tasks a lead: variants past the third are not read
    assert kept == due[:len(kept)]                                        # oldest first; the rest stay due for tomorrow
    assert review.within_budget([("solo", seen, [])]) == [("solo", seen, [])]


def test_mail_recipients_tolerate_how_people_type_them():
    import notify
    assert notify.recipients('"a@b.com"') == ["a@b.com"]
    assert notify.recipients("a@b.com，c@d.cn") == ["a@b.com", "c@d.cn"]
    assert notify.recipients("<a@b.com>; c@d.cn\n") == ["a@b.com", "c@d.cn"]


# --- the keyword table (usecases.py) and Trends' unsettled days ------------------------------

import usecases  # noqa: E402

TODAY = date(2026, 10, 12)


def _daily(values, end=TODAY - timedelta(days=1)):
    """A daily series ending yesterday, as Trends returns it; its last two days are unsettled."""
    start = end - timedelta(days=len(values) - 1)
    return [(start + timedelta(days=i), v) for i, v in enumerate(values)]


def test_trends_last_two_days_are_not_a_rise():
    # "ai image detector" on 2026-10-12: flat for 88 days, then 0 and 100 on the two unsettled days
    assert not usecases.shape(_daily([5] * 88 + [0, 100]), TODAY)["rose"]
    assert review.settled(_daily([5] * 88 + [0, 100]), TODAY)[-1][1] == 5


def test_a_real_rise_counts_and_a_single_day_spike_does_not():
    s = usecases.shape(_daily([1] * 85 + [9, 53, 40, 59, 100]), TODAY)     # "synthid detector"
    assert s["rose"] and s["now"] == "rising" and s["peak_day"] == "2026-10-08"
    assert not usecases.shape(_daily([0] * 80 + [100] + [0] * 9), TODAY)["rose"]   # "debloat macos"


def test_usecase_decisions_and_sizes():
    assert usecases.decide({"now": "rising"}, 5000, 300) == "prioritize" and usecases.decide({"now": "flat"}, 5000, 300) == "watch"
    assert usecases.decide({"now": "flat"}, 40, 300) == "skip" and usecases.decide({"no_data": True}, None, 300) == "watch"
    assert usecases.own_per_day(_daily([10] * 81 + [20] * 9), 30000, "2026-08", TODAY) == 2000


def test_keyword_table_in_the_report(monkeypatch, tmp_path):
    rise, flat = _daily([1] * 85 + [9, 53, 40, 59, 100]), _daily([20] * 90)
    monkeypatch.setattr(usecases, "evidence", lambda names, repos, today: (
        {n: {"posts": [{"text": "check if any image is AI generated", "likes": 900, "by": "a", "url": ""}], "readme": "", "repo": ""} for n in names}, 3000))
    monkeypatch.setattr(usecases, "propose", lambda model, name, ev: [
        {"phrase": "ai image detector", "evidence": "check if any image is AI generated", "brand": False},
        {"phrase": "photoshop alternative", "evidence": "free clone", "brand": True}])
    monkeypatch.setattr(usecases, "screen", lambda model, name, ev, cands: cands)
    monkeypatch.setattr(usecases, "volumes", lambda phrases, loc: (
        {"ai image detector": {"volume": 60000, "month": "2026-08"}, "photoshop alternative": {"volume": 6000, "month": "2026-08"}}, 90000))
    monkeypatch.setattr(usecases, "fetch_series", lambda keywords, bench, today: (
        {k: {"solo": rise if k == "synthid detector" else flat, "pair": [(d, v, 40) for d, v in (rise if k == "synthid detector" else flat)]}
         for k in keywords}, 7200))
    monkeypatch.delenv("GOANYAPI_API_KEY", raising=False)
    uc = usecases.run(tmp_path, ["synthid detector"], {}, TODAY)
    text = "\n".join(usecases.table(uc))
    assert "| **synthid detector** | 名字 |" in text and "**优先**" in text
    assert "| **photoshop alternative** ⚠ | 通用词 | synthid detector |" in text and "别人的品牌" in text
    assert [x["term"] for x in usecases.leads(uc)] == ["ai image detector", "photoshop alternative"]
    assert usecases.run(tmp_path, ["synthid detector"], {}, TODAY + timedelta(days=1))["names"] == []
    assert usecases.run(tmp_path, ["synthid detector"], {}, TODAY + timedelta(days=3))["names"] == ["synthid detector"]


def test_screen_drops_loosely_related_keywords_and_keeps_all_when_the_call_fails(monkeypatch):
    cands = [{"phrase": p, "brand": False} for p in ("ai image detector", "chatgpt alternative", "ai audio detector")]
    ev = {"posts": [{"text": "check if any image is AI generated", "likes": 900, "by": "a"}], "readme": ""}
    monkeypatch.setattr(usecases.aisa, "chat", lambda *a, **k: '[{"i": 0, "score": 0.95}, {"i": 1, "score": 0.2}, {"i": 2, "score": 0.7}]')
    kept = usecases.relevant(usecases.screen("m", "synthid detector", ev, cands))
    assert [(c["phrase"], c["relevance"]) for c in kept] == [("ai image detector", 0.95), ("ai audio detector", 0.7)]

    def down(*a, **k):
        raise usecases.aisa.AisaError("HTTP 500")
    monkeypatch.setattr(usecases.aisa, "chat", down)
    assert usecases.screen("m", "synthid detector", ev, cands) == cands


def test_momentum_is_the_last_settled_week_against_the_week_before():
    assert usecases.shape(_daily([10] * 76 + [20] * 7 + [40] * 7 + [0, 100]), TODAY)["momentum"] == 2.0
    assert usecases.shape(_daily([0] * 83 + [40] * 7 + [0, 100]), TODAY)["momentum"] is None   # nothing the week before


def test_related_queries_feed_the_table_and_other_rising_names_become_leads(monkeypatch, tmp_path):
    rise, flat = _daily([1] * 85 + [9, 53, 40, 59, 100]), _daily([20] * 90)
    monkeypatch.setenv("GOANYAPI_API_KEY", "k")
    monkeypatch.setattr(usecases, "evidence", lambda names, repos, today: ({n: {"posts": [], "readme": "x", "repo": ""} for n in names}, 3000))
    monkeypatch.setitem(usecases.SETTINGS, "country_trends", False)
    monkeypatch.setattr(usecases, "propose", lambda model, name, ev: [])
    monkeypatch.setattr(usecases.goanyapi, "related_queries", lambda name, geo: (
        {"rising": ["ai photo detector", "gpt image 2.5", "google nano banana", "nano banana 2.1 vs pro"], "top": ["google gemini"]}, 6000))
    monkeypatch.setattr(usecases, "screen", lambda model, name, ev, cands: [
        dict(c, relevance=0.9, is_name=c["phrase"] != "ai photo detector") for c in cands])
    monkeypatch.setattr(usecases, "volumes", lambda phrases, loc: ({p: {"volume": 9000, "month": "2026-08"} for p in phrases}, 90000))
    monkeypatch.setattr(usecases, "fetch_series", lambda keywords, bench, today: (
        {k: {"solo": flat, "pair": [(d, v, 40) for d, v in flat]} for k in keywords}, 2400))
    uc = usecases.run(tmp_path, ["nano banana 2.1"], {}, TODAY)
    assert uc["cosearch"] == [{"term": "gpt image 2.5", "with": "nano banana 2.1"}]     # same family and non-rising are left out
    assert uc["tails"] == {"nano banana 2.1": ["nano banana 2.1 vs pro"]}
    text = "\n".join(usecases.table(uc))
    assert "| **ai photo detector** 🔎 |" in text and "gpt image 2.5(和 nano banana 2.1 一起)" in text
    assert usecases.leads(uc)[-1]["kinds"] == ["cosearch"]


def test_the_country_series_reads_a_rise_the_worldwide_one_flattens(monkeypatch, tmp_path):
    # "photoshop alternative" in the US around PhotoCraft: about 50, then 77, 86, 83, 100, 94, and the partial day
    month = [(TODAY - timedelta(days=29 - i), v) for i, v in enumerate([50] * 24 + [77, 86, 83, 100, 94, 79])]
    s = usecases.shape(month, TODAY, usecases.COUNTRY)
    assert s["rose"] and not s["new"] and s["now"] == "rising" and s["started"] == "2026-10-07"
    flat = _daily([20] * 90)
    monkeypatch.setenv("GOANYAPI_API_KEY", "k")
    monkeypatch.setitem(usecases.SETTINGS, "related", False)
    monkeypatch.setattr(usecases, "evidence", lambda names, repos, today: ({n: {"posts": [], "readme": "x", "repo": ""} for n in names}, 0))
    monkeypatch.setattr(usecases, "propose", lambda model, name, ev: [{"phrase": "photoshop alternative", "evidence": "free clone", "brand": True}])
    monkeypatch.setattr(usecases, "screen", lambda model, name, ev, cands: cands)
    monkeypatch.setattr(usecases, "volumes", lambda phrases, loc: ({p: {"volume": 6600, "month": "2026-08"} for p in phrases}, 0))
    monkeypatch.setattr(usecases, "fetch_series", lambda keywords, bench, today: (
        {k: {"solo": flat, "pair": [(d, v, 40) for d, v in flat]} for k in keywords}, 0))

    def daily_series(term, geo):
        if term == "photocraft":
            raise usecases.goanyapi.GoAnyError("HTTP 502")
        return month, 6000
    monkeypatch.setattr(usecases.goanyapi, "daily_series", daily_series)
    uc = usecases.run(tmp_path, ["photocraft"], {}, TODAY)
    text = "\n".join(usecases.table(uc))
    assert "还在涨 (US)" in text and "已退回全球数据:photocraft: HTTP 502" in text
    assert "今天这张表不完整" in text


def test_only_things_are_read_for_generic_terms_not_words_that_surged():
    today = [{"term": "mcd", "kinds": ["github"], "named": 0.75}, {"term": "kr.co.klisten.api", "kinds": ["sitemap"], "named": 0.78},
             {"term": "photocraft", "kinds": ["breakout"], "named": 0.95}, {"term": "dots", "kinds": ["breakout"], "named": 0.65},
             {"term": "hailuo", "kinds": ["newsite", "sitemap"]}]
    recent = [{"term": "qwen image 2.1", "kinds": ["hf"], "named": 0.96}, {"term": "use rea", "kinds": ["x"], "named": 0.72},
              {"term": "photocraft", "kinds": ["x"], "named": 0.9}]
    assert usecases.names_to_read(today, recent) == ["photocraft", "hailuo", "qwen image 2.1"]


def test_a_failed_post_search_costs_one_name_its_posts_not_the_step(monkeypatch):
    def call(calls):
        if "photocraft" in calls[0]["arguments"]["query"]:
            raise usecases.aisa.AisaError("HTTP 504: <html><h1>504 Gateway Time-out</h1></html>")
        return {"s": {"tweets": [{"text": "check any image", "likeCount": 900, "author": {"userName": "a"}}]}}, 3000
    monkeypatch.setattr(usecases.aisa, "call", call)
    monkeypatch.setattr(usecases, "_readme", lambda repo: "PhotoCraft opens real PSD files")
    ev, cost = usecases.evidence(["photocraft", "synthid detector"], {"photocraft": "storytold/photocraft"}, TODAY)
    assert cost == 3000 and ev["photocraft"]["readme"] and ev["photocraft"]["posts"] == []
    assert ev["photocraft"]["error"] == "HTTP 504: 504 Gateway Time-out" and len(ev["synthid detector"]["posts"]) == 1


def test_other_names_leave_out_old_products_siblings_and_spelling_variants():
    # what the first real run of the skill kept beside filmcraft and pdfcraft (2026-10-13)
    viewed = [{"phrase": p, "is_name": True, "rising": True, "established": old} for p, old in (
        ("premiere pro", True), ("davinci resolve", True), ("photocraft github", False), ("gpt image 2.5", False),
        ("adobe artcraft", False), ("artcraft adobe", False))]
    assert [x["term"] for x in usecases.other_names("filmcraft", viewed, ["photocraft", "filmcraft"])] == ["gpt image 2.5", "adobe artcraft"]
    tails, cands = usecases.split_related("pdfcraft", {"rising": ["pdf craft", "merge pdf files"], "top": []})
    assert tails == ["pdf craft"] and [c["phrase"] for c in cands] == ["merge pdf files"]


def test_every_name_gets_the_country_series_and_the_cap_is_on_generic_terms(monkeypatch):
    rows = [{"phrase": f"name{i}", "kind": "name"} for i in range(5)] + \
           [{"phrase": f"g{v}", "kind": "generic", "volume": v} for v in (27100, 22200, 8100, 6600, 900)]
    monkeypatch.setitem(usecases.SETTINGS, "country_max", 3)
    asked = []
    monkeypatch.setattr(usecases.goanyapi, "daily_series", lambda term, geo: (asked.append(term) or [(TODAY, 1)], 6000))
    out, cost, errors = usecases.country_series(rows, usecases.SETTINGS)
    assert sorted(asked) == sorted([f"name{i}" for i in range(5)] + ["g27100", "g22200", "g8100"]) and cost == 48000 and not errors


# --- ① new sites people link (social_sites.py, bluesky.py), shadow mode -------------------------

import contextlib  # noqa: E402
import struct  # noqa: E402
import types  # noqa: E402
import urllib.error  # noqa: E402

import bluesky  # noqa: E402
import social_sites  # noqa: E402

SOC_NOW = datetime(2026, 10, 21, 12, tzinfo=timezone.utc)
REAL_SOCIAL = social_sites.social_sites
TRAFFIC = {"costCredits": 2, "TrafficSources": {"Social": 0.41, "SocialPaid": 0.04, "Search": 0.1, "SearchPaid": 0.02,
                                                "Direct": 0.4},
           "EstimatedMonthlyVisits": {"2026-08-01": 0, "2026-09-01": 12000}, "DateData": {"registration": "2026-08-21T10:00:00Z"}}


def _sky(author, link, likes=5, hours_ago=3):
    at = (SOC_NOW - timedelta(hours=hours_ago)).isoformat()
    return {"platform": "bluesky", "author": author, "url": f"https://bsky.app/profile/{author}/post/{link[-3:]}{hours_ago}",
            "text": f"look {link}", "likes": likes, "at": at, "links": [link]}


def _social_world(monkeypatch, sky_posts, registered):
    """Bluesky, RDAP and t.co answered without the network; no GoAnyAPI key."""
    monkeypatch.setattr(social_sites.bluesky, "posts", lambda since: {
        "source": "search", "requests": 6, "refused": "", "read": 40, "posts": list(sky_posts), "errors": []})
    monkeypatch.setattr(social_sites.meme_checks, "rdap", lambda d: {"domain": d, "free": d not in registered,
                                                                      "registered": registered.get(d, "")})
    monkeypatch.setattr(social_sites, "location", lambda u: pytest.fail(f"unexpected t.co lookup {u}"))
    monkeypatch.setattr(social_sites, "RDAP_PAUSE", 0)
    monkeypatch.delenv("GOANYAPI_API_KEY", raising=False)


def test_links_reduce_to_the_site_and_platforms_shorteners_and_our_sites_are_dropped():
    assert social_sites.domain_of("https://www.Altstream.online/watch?v=1") == "altstream.online"
    assert social_sites.domain_of("https://news.bbc.co.uk/x") == "bbc.co.uk"
    assert social_sites.domain_of("https://geckodaily.vercel.app/") == "vercel.app"     # a host's subdomain is the host
    assert social_sites.domain_of("http://127.0.0.1:8000/") == "" and social_sites.domain_of("not a link") == ""
    dropped = ["youtu.be", "x.com", "t.co", "bit.ly", "github.com", "huggingface.co", "chatgpt.com", "claude.ai",
               "vercel.app", "deepmind.google", "fraud.gov", "agentskillshub.top", "jasonzhu.ai", "ab.io"]
    assert [d for d in dropped if not social_sites.excluded(d)] == [] and not social_sites.excluded("altstream.online")


def test_tweet_links_use_xs_expansion_and_expand_the_other_tco_once(monkeypatch):
    tweet = {"text": "Try https://t.co/AAAA and https://t.co/BBBB",
             "entities": {"urls": [{"url": "https://t.co/AAAA", "expanded_url": "https://altstream.online/"}]}}
    links = social_sites.tweet_links(tweet)
    assert links == ["https://altstream.online/", "https://t.co/BBBB"]
    asked, cache = [], {}
    monkeypatch.setattr(social_sites, "location", lambda u: asked.append(u) or "https://newtool.app/x")
    assert social_sites.expand(links, cache, SOC_NOW.date()) == (1, 0) and cache["https://t.co/BBBB"]["to"] == "https://newtool.app/x"
    assert social_sites.expand(links, cache, SOC_NOW.date()) == (0, 0) and asked == ["https://t.co/BBBB"]   # cached


def test_bluesky_links_come_from_facets_and_external_embeds():
    rec = {"text": "made this", "embed": {"$type": "app.bsky.embed.recordWithMedia", "media": {"external": {"uri": "https://b.site/x"}}},
           "facets": [{"features": [{"$type": "app.bsky.richtext.facet#link", "uri": "https://altstream.online"}]}]}
    p = bluesky.from_view({"uri": "at://did:plc:a/app.bsky.feed.post/3mabc", "author": {"handle": "ann.bsky.social"},
                           "record": rec, "likeCount": 12, "indexedAt": "2026-10-21T08:00:00.000Z"})
    assert p["links"] == ["https://altstream.online", "https://b.site/x"] and p["likes"] == 12
    assert p["url"] == "https://bsky.app/profile/ann.bsky.social/post/3mabc"


def test_bluesky_samples_the_firehose_when_search_wants_a_login(monkeypatch):
    def refused(q, since):
        raise urllib.error.HTTPError("u", 403, "Forbidden", {}, None)
    post = bluesky.make_post("did:plc:b", "at://did:plc:b/app.bsky.feed.post/3m", {"embed": {"external": {"uri": "https://a.site"}}},
                             0, "2026-10-21T09:00:00+00:00")
    monkeypatch.setattr(bluesky, "_search_page", refused)
    monkeypatch.setattr(bluesky, "sample", lambda seconds, most: [post])
    got = bluesky.posts(SOC_NOW - timedelta(hours=72))
    assert (got["source"], got["refused"], got["requests"], got["posts"]) == ("jetstream", "HTTP 403", 1, [post])


def test_firehose_frames_answer_pings_and_join_a_fragmented_message():
    msg = json.dumps({"kind": "commit", "did": "did:plc:c", "time_us": 1792000000000000, "commit": {
        "operation": "create", "collection": "app.bsky.feed.post", "rkey": "3k", "record": {
            "text": "hi", "facets": [{"features": [{"$type": "app.bsky.richtext.facet#link", "uri": "https://a.site"}]}]}}}).encode()
    data = bytes([0x89, 1]) + b"p" + bytes([0x01, 5]) + msg[:5] + bytes([0x80, 126]) + struct.pack(">H", len(msg) - 5) + msg[5:]
    sock = types.SimpleNamespace(data=data + bytes([0x88, 0]), sent=b"")
    sock.recv = lambda n: [sock.data[:n], setattr(sock, "data", sock.data[n:])][0]
    sock.sendall = lambda b: setattr(sock, "sent", sock.sent + b)
    frames = bluesky.Frames(sock)
    assert frames.next_text() == msg and sock.sent[:2] == bytes([0x8A, 0x81])   # a masked pong of one byte
    with pytest.raises(OSError):
        frames.next_text()                                                      # the close frame
    assert bluesky.event_post(msg)["url"] == "https://bsky.app/profile/did:plc:c/post/3k"


def test_a_new_site_needs_two_people_and_a_registration_in_the_last_90_days(monkeypatch, tmp_path):
    posts = [_sky("ann", "https://altstream.online/a"), _sky("bob", "https://www.altstream.online/b"),
             _sky("ann", "https://solo.app/1"), _sky("ann", "https://solo.app/2", likes=7),    # one person, twice
             _sky("ann", "https://oldsite.com"), _sky("cat", "https://oldsite.com"),           # registered long ago
             _sky("ann", "https://noage.de"), _sky("dan", "https://noage.de")]                # RDAP gives no date
    _social_world(monkeypatch, posts, {"altstream.online": "2026-08-21", "solo.app": "2026-10-01", "oldsite.com": "2019-01-01"})
    out = REAL_SOCIAL(tmp_path, {"linked": []}, SOC_NOW)
    assert [(s["domain"], s["age"], s["authors"]) for s in out["sites"]] == [("altstream.online", 61, 2)]
    assert (out["many"], out["rdap_looked"], out["rdap_unknown"]) == (3, 3, 1)
    lead = out["shadow_leads"][0]
    assert out["terms"] == [] and (lead["term"], lead["kinds"], lead["variants"]) == ("altstream", ["social"], ["altstream", "altstream.online"])
    assert {p["link"] for p in lead["posts"]} == {"https://altstream.online/a", "https://www.altstream.online/b"}
    assert "没查流量(没有 GOANYAPI_API_KEY)" in lead["signals"][0]
    again = REAL_SOCIAL(tmp_path, {"linked": []}, SOC_NOW + timedelta(hours=8))
    assert again["sites"] == [] and again["rdap_looked"] == 0      # reported once; RDAP answers kept


def test_the_window_forgets_links_older_than_72_hours(monkeypatch, tmp_path):
    _social_world(monkeypatch, [_sky("ann", "https://altstream.online/a")], {"altstream.online": "2026-08-21"})
    REAL_SOCIAL(tmp_path, {"linked": []}, SOC_NOW)
    _social_world(monkeypatch, [_sky("bob", "https://altstream.online/b", hours_ago=-80)], {"altstream.online": "2026-08-21"})
    assert REAL_SOCIAL(tmp_path, {"linked": []}, SOC_NOW + timedelta(hours=83))["sites"] == []   # ann's link is 86 hours old


def test_an_x_link_and_a_bluesky_link_are_two_people(monkeypatch, tmp_path):
    _social_world(monkeypatch, [_sky("ann", "https://altstream.online/a")], {"altstream.online": "2026-08-21"})
    monkeypatch.setattr(social_sites, "location", lambda u: "https://altstream.online/from-x")
    linked = [{"account": "simonw", "text": "neat https://t.co/CCCC", "likes": 300, "url": "https://x.com/simonw/status/1",
               "created": SOC_NOW - timedelta(hours=5), "links": ["https://t.co/CCCC"]},
              {"account": "dotey", "text": "RT @a: https://t.co/DDDD", "likes": 9, "url": "", "created": SOC_NOW, "links": ["https://t.co/DDDD"]},
              {"account": "swyx", "text": "old https://t.co/EEEE", "likes": 9, "url": "", "created": SOC_NOW - timedelta(hours=80),
               "links": ["https://t.co/EEEE"]}]
    out = REAL_SOCIAL(tmp_path, {"linked": linked}, SOC_NOW)
    # a retweet is not a person, and a post older than the window is not even expanded
    assert out["sites"][0]["by"] == {"x": 1, "bluesky": 1} and out["tco"] == {"asked": 1, "failed": 0} and out["x_posts"] == 1
    assert out["shadow_leads"][0]["posts"][0]["url"] == "https://x.com/simonw/status/1"                    # most-liked first


def test_traffic_tags_say_social_or_search_and_stop_at_the_cap(monkeypatch):
    t = social_sites.traffic_tag(TRAFFIC)
    assert (t["driven"], t["visits"], t["month"], t["registered"]) == ("social", 12000, "2026-09", "2026-08-21")
    assert social_sites.traffic_tag({"TrafficSources": {"Search": 0.6, "Social": 0.1}})["driven"] == "search"
    assert social_sites.traffic_tag({})["driven"] == "unknown"
    monkeypatch.setenv("GOANYAPI_API_KEY", "k")
    monkeypatch.setattr(social_sites.goanyapi, "call", lambda path, timeout, **p: (TRAFFIC, 2000))
    cands = [{"domain": f"site{i}.com"} for i in range(social_sites.TRAFFIC_MAX + 2)]
    assert social_sites.tag_traffic(cands, {}, SOC_NOW.date()) == (2000 * social_sites.TRAFFIC_MAX, social_sites.TRAFFIC_MAX, [])
    assert social_sites.traffic_text(cands[0]) == "社交带量(社交 45%、搜索 12%),约 12k 访问/月(2026-09)"
    assert "额度" in cands[-1]["traffic_note"]


def test_evidence_merge_keeps_posts_by_url_and_the_newest_of_the_rest():
    old = review.evidence({"posts": [{"url": f"u{i}", "account": "a", "text": "t", "likes": i} for i in range(8)],
                           "examples": ["old"], "variants": ["a"], "meme": {"what": "old"}}, date(2026, 10, 19))
    new = review.evidence({"posts": [{"url": "u1", "account": "a", "text": "t", "likes": 50},
                                     *({"url": f"n{i}", "account": "b", "text": "x" * 400, "likes": 10 + i} for i in range(4))],
                           "examples": ["new"]}, date(2026, 10, 21))
    merged = review.merge_evidence(old, new)
    assert [p["url"] for p in merged["posts"]] == ["u1", "n3", "n2", "n1", "n0", "u7", "u6", "u5", "u4", "u3"]
    assert set(merged["posts"][0]) == {"url", "account", "text", "likes", "date", "platform"} and len(merged["posts"][1]["text"]) == 280
    assert (merged["examples"], merged["variants"], merged["meme"], merged["updated"]) == (["new"], ["a"], {"what": "old"}, "2026-10-21")
    assert review.merge_evidence(None, new) == new


class _FakeDB:
    """Enough of an engine for review.record(): the column check, and one lead already held."""

    def __init__(self, column):
        self.column, self.calls = column, []

    def begin(self):
        return contextlib.nullcontext(self)

    def dispose(self):
        pass

    def execute(self, sql, params=None):
        self.calls.append((str(sql), params))
        held = [("altstream", {"posts": [{"url": "u0", "likes": 99, "text": "old"}]})] if "FOR UPDATE" in str(sql) else []
        return types.SimpleNamespace(first=lambda: (1,) if self.column else None, fetchall=lambda: held)


def test_record_writes_evidence_only_once_the_column_exists(monkeypatch):
    row = {"term": "altstream", "kinds": ["social"], "signals": ["①社交新站 altstream.online"], "variants": ["altstream"],
           "posts": [{"url": "u1", "account": "ann", "text": "new", "likes": 5, "platform": "bluesky"}]}
    for column in (False, True):
        db = _FakeDB(column)
        monkeypatch.setattr(review, "_engine", lambda: db)
        monkeypatch.setattr(review, "_EVIDENCE_COLUMN", None)
        assert review.record([row], date(2026, 10, 21)) == 1
        upsert = next(p for s, p in db.calls if s.lstrip().startswith("INSERT"))
        assert ("evidence" in upsert) is column and all("SET statement_timeout" not in s for s, _ in db.calls)
    assert [p["url"] for p in json.loads(upsert["evidence"])["posts"]] == ["u0", "u1"]   # merged into what the lead held


def test_a_shadow_lead_leaves_a_lead_another_signal_holds_as_it_is(monkeypatch):
    rows = [{"term": t, "kinds": ["social"], "signals": [f"①社交新站 {t}.online"], "variants": [t],
             "posts": [{"url": f"https://bsky.app/{t}", "likes": 3, "text": t, "platform": "bluesky"}]} for t in ("altstream", "fresh")]
    for column in (True, False):
        db = _FakeDB(column)
        monkeypatch.setattr(review, "_engine", lambda: db)
        monkeypatch.setattr(review, "_EVIDENCE_COLUMN", None)
        assert review.record_new(rows, date(2026, 10, 21)) == {"recorded": 1, "merged": int(column)}
        inserted = [p["term"] for s, p in db.calls if s.lstrip().startswith("INSERT")]
        updated = [p["term"] for s, p in db.calls if s.startswith("UPDATE")]
        assert inserted == ["fresh"] and updated == (["altstream"] if column else [])   # its notes and last_seen untouched


def test_the_keyword_tables_reading_of_a_name_goes_into_its_evidence():
    uc = {"names": ["photocraft"], "tails": {"photocraft": ["photocraft download"]},
          "cosearch": [{"term": "gpt image 2.5", "with": "photocraft"}], "rows": [
              {"phrase": "photocraft", "kind": "name", "names": [], "per_day": 900, "decision": "watch", "now": "rising"},
              {"phrase": "photoshop alternative", "kind": "generic", "names": ["photocraft"], "per_day": 4000, "decision": "prioritize"},
              {"phrase": "other", "kind": "generic", "names": ["x"], "decision": "skip", "no_data": True}]}
    kw = usecases.name_evidence(uc)[0]["keywords"]
    assert [(r["phrase"], r["now"]) for r in kw["rows"]] == [("photocraft", "rising"), ("photoshop alternative", None)]
    assert (kw["tails"], kw["cosearch"]) == (["photocraft download"], ["gpt image 2.5"])


def _sources_with_social(monkeypatch, x_terms):
    _quiet_memes_and_charts(monkeypatch)
    monkeypatch.setattr(radar, "judge", lambda rows: None)
    monkeypatch.setattr(radar.source_signals, "x_new", lambda snaps: {"posts": 400, "cost_micros": 0, "linked": [], "terms": x_terms})
    monkeypatch.setattr(radar.source_signals, "hf_new", lambda snaps: {"models": 100, "terms": []})
    _social_world(monkeypatch, [_sky("ann", "https://altstream.online/a"), _sky("bob", "https://altstream.online/b")],
                  {"altstream.online": "2026-08-21"})
    monkeypatch.setattr(radar.social_sites, "social_sites", lambda snaps, x: REAL_SOCIAL(snaps, x, SOC_NOW))
    recorded, shadow = [], []
    monkeypatch.setattr(radar.review, "record", lambda rows: recorded.extend(rows) or len(rows))
    monkeypatch.setattr(radar.review, "record_new", lambda rows: shadow.extend(rows) or {"recorded": len(rows), "merged": 0})
    return recorded, shadow


def test_shadow_new_sites_are_recorded_for_the_review_and_never_shown(monkeypatch, tmp_path):
    recorded, shadow = _sources_with_social(monkeypatch, [{"term": "qwen3.9", "recent": 2, "note": "X 2 个账号 ♥900",
                                                           "examples": ["@Alibaba_Qwen: Qwen3.9 is out"]}])
    report = tmp_path / "sources.md"
    radar.sources_main(report, tmp_path, {"--sources"})
    text = report.read_text()
    assert "qwen3.9" in text and "altstream" not in text and "①社交新站" not in text
    assert "- ① 社交新站(影子模式,只记录不展示):1 个候选,已记录 1 个(" in text
    assert [r["term"] for r in recorded] == ["qwen3.9"]
    assert [(r["term"], r["kinds"]) for r in shadow] == [("altstream", ["social"])] and shadow[0]["posts"]


def test_shadow_new_sites_alone_send_no_mail(monkeypatch, tmp_path):
    recorded, shadow = _sources_with_social(monkeypatch, [])
    radar.sources_main(tmp_path / "sources.md", tmp_path, {"--sources"})
    assert not (tmp_path / "sources.md").exists() and not recorded and [r["term"] for r in shadow] == ["altstream"]
    assert not radar.report_errors({"social": {"error": "boom"}}) and radar.report_errors({"x": {"error": "boom"}})
    monkeypatch.setattr(social_sites, "SOCIAL_SHOW", True)    # the one switch: the leads go to the report instead
    shown = REAL_SOCIAL(tmp_path / "again", {"linked": []}, SOC_NOW)
    assert [r["term"] for r in shown["terms"]] == ["altstream"] and shown["shadow_leads"] == []


# --- the daily run (radar.daily_main) --------------------------------------------------------

DAILY_FLAGS = {"--skip-x", "--skip-hf", "--skip-memes", "--skip-appstore"}   # as radar-daily.yml runs it


def _daily_world(monkeypatch, recent=(), github_terms=(), breakout_terms=()):
    """Every source of the daily run, answered without the network or the database. Returns what
    record(), record_new() and the keyword table were handed."""
    monkeypatch.setattr(radar, "judge", lambda rows: None)
    repos = [{"repo": t["repo"], "stars": 14671, "velocity": 2989, "delta": None, "age_days": 4.9, "description": "", "new": True}
             for t in breakout_terms]
    monkeypatch.setattr(radar.breakout, "breakouts", lambda snaps: {
        "searched": 305, "searched_late": 105, "first_run": False, "repos": repos, "terms": [dict(t) for t in breakout_terms]})
    monkeypatch.setattr(radar.signals, "github_surge", lambda: {
        "repos_recent": 1843, "repos_baseline": 24130, "terms": [dict(t) for t in github_terms]})
    got = {"recorded": [], "shadow": [], "read": []}
    monkeypatch.setattr(radar.review, "record", lambda rows: got["recorded"].extend(rows) or len(rows))
    monkeypatch.setattr(radar.review, "record_new", lambda rows: got["shadow"].extend(rows) or {"recorded": len(rows), "merged": 0})
    monkeypatch.setattr(radar.review, "review", lambda: {"checked": [], "cost_micros": 0})
    monkeypatch.setattr(radar.review, "summary", lambda: {"by_signal": {}, "pending": 0, "window_days": 60})
    monkeypatch.setattr(radar.review, "recent_sources", lambda kinds: [dict(r) for r in recent])
    monkeypatch.setattr(radar.review, "add_evidence", lambda rows: 0)
    monkeypatch.setattr(radar.usecases, "run", lambda snaps, names, repos: got["read"].extend(names) or {"names": [], "rows": []})
    return got


def test_github_words_are_recorded_for_the_review_and_never_shown(monkeypatch, tmp_path):
    got = _daily_world(monkeypatch, github_terms=[{"term": "falkordb", "recent": 9, "lift": 4.5,
                                                   "examples": ["falkor/falkordb-mcp: graph database"]}])
    report = tmp_path / "radar.md"
    radar.daily_main(report, tmp_path / "snap", DAILY_FLAGS)
    text = report.read_text()
    assert [(r["term"], r["kinds"], r["signals"]) for r in got["shadow"]] == [("falkordb", ["github"], ["②GitHub 9 处 (×4.5)"])]
    assert got["shadow"][0]["examples"] == ["falkor/falkordb-mcp: graph database"] and "named" not in got["shadow"][0]
    assert "falkordb" not in text and not got["recorded"] and not got["read"]       # no candidate, keyword table or pick
    assert "- ② GitHub 共用词(影子模式,只记录不展示):近 3 天新建 1843 个仓库,基线 24130 个,1 个上升词,已记录 1 个" in text


def test_shadow_blocks_keep_their_terms_out_of_the_leads_and_one_switch_turns_them_on(monkeypatch):
    monkeypatch.setattr(radar, "judge", lambda rows: None)
    block = radar.shadow({"repos_recent": 5, "repos_baseline": 9, "terms": [{"term": "falkordb", "recent": 9, "lift": 4.5}]}, "github")
    assert radar.leads({"github": block}) == [] and [r["term"] for r in block["shadow_leads"]] == ["falkordb"]
    assert radar.github_status({"skipped": True, "shadow": True}) == "- ② GitHub 共用词(影子模式,只记录不展示):跳过"
    assert radar.github_status(dict(block, recorded={"error": "timeout"})).endswith(",1 个上升词,没记录(timeout)")
    monkeypatch.setattr(radar.signals, "GITHUB_SHOW", True)
    shown = radar.daily_blocks(Path("unused"), DAILY_FLAGS | {"--skip-breakout", "--skip-db"})
    assert "shadow" not in shown["github"]                                          # skipped here, but not shadowed


def _section(path, head):
    """One section of a written report, from its heading to the next one."""
    text = path.read_text()
    start = text.index(head)
    end = text.find("\n### ", start + 1)
    return text[start:end if end > 0 else None]


def test_the_daily_lists_a_source_lead_once(monkeypatch, tmp_path):
    deepinfer = {"term": "deepinfer", "recent": 1, "repo": "deepseek-ai/DeepInfer", "variants": ["deepinfer"],
                 "note": "GitHub 爆发 deepseek-ai/DeepInfer ★14671(均 2989/天)"}
    recent = [{"term": "orchestra bio", "kinds": ["x"], "note": "X 2 个账号 ♥3130", "named": 0.95},
              {"term": "deepinfer", "kinds": ["x", "breakout"], "note": deepinfer["note"], "named": 0.96}]
    _daily_world(monkeypatch, recent=recent, breakout_terms=[deepinfer])
    snaps = tmp_path / "snap"
    radar.daily_main(tmp_path / "d1.md", snaps, DAILY_FLAGS)
    first = _section(tmp_path / "d1.md", "### ① ")
    assert "**orchestra bio**" in first and "deepinfer" not in first                 # deepinfer is ② 单仓爆发's 🆕 today
    recent.append({"term": "sm100", "kinds": ["x"], "note": "X 2 个账号 ♥74", "named": 0.65})
    _daily_world(monkeypatch, recent=recent)                                          # the next day, one more lead
    radar.daily_main(tmp_path / "d2.md", snaps, DAILY_FLAGS)
    second = _section(tmp_path / "d2.md", "### ① ")
    assert "**sm100**" in second and "orchestra bio" not in second and "deepinfer" not in second
    radar.daily_main(tmp_path / "d3.md", snaps, DAILY_FLAGS)
    assert "无(3 个都已列过)" in _section(tmp_path / "d3.md", "### ① ")
    assert set(radar.memory(snaps / radar.LISTED)) == {"orchestra bio", "deepinfer", "sm100"}


def test_the_daily_leaves_out_the_picks_the_8_hourly_mails_sent(monkeypatch, tmp_path):
    app = {"term": "2am cam", "kinds": ["appstore"], "named": 0.66, "note": "②榜单 德摄影录像付费 #8(上架 20 天,1 个区上榜),先手"}
    _daily_world(monkeypatch, recent=[app])
    sent = tmp_path / "src" / radar.SENT
    sent.parent.mkdir()
    sent.write_text(json.dumps({"2am cam": datetime.now(timezone.utc).isoformat(timespec="minutes")}))
    radar.daily_main(tmp_path / "d.md", tmp_path / "snap", DAILY_FLAGS | {f"--sent-picks={sent}"})
    text = (tmp_path / "d.md").read_text()
    assert "今天够格的词都已在每 8 小时的邮件里发过:2am cam。" in text                  # named once, in one line,
    assert text.count("2am cam") == 1 and "无(1 个都已列过)" in _section(tmp_path / "d.md", "### ① ")   # not again in ①
    # with no memory (a local run) it is the day's pick, and ① does not list it again
    radar.daily_main(tmp_path / "e.md", tmp_path / "snap2", DAILY_FLAGS)
    text = (tmp_path / "e.md").read_text()
    assert "1. **2am cam**" in text and text.count("2am cam") == 1
    # a pick mailed three days ago is not "since yesterday"
    sent.write_text(json.dumps({"2am cam": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(timespec="minutes")}))
    assert radar.sent_lately({f"--sent-picks={sent}"}, date.today()) == set() and radar.sent_lately(set(), date.today()) == set()


def test_the_mail_memories_keep_14_days():
    held = {"old": "2026-10-01T08:00+00:00", "kept": "2026-10-10T08:00+00:00"}
    assert radar.remember(held, ["kept", "new"], "2026-10-21T08:00+00:00", date(2026, 10, 21)) == \
        {"kept": "2026-10-10T08:00+00:00", "new": "2026-10-21T08:00+00:00"}
    assert radar.memory(Path("/nonexistent/sent_picks.json")) == {}


# --- the 8-hourly mail: new picks only -------------------------------------------------------

def _meme_term(term, days_ago=1):
    """A trend's lead row as memes.memes() hands it on: over Jev's bar, first seen `days_ago`, with its top post."""
    first = date.today() - timedelta(days=days_ago)
    return {"term": term, "recent": 2, "named": 0.6, "what": "用AI把自己放进视频", "variants": [term],
            "note": f"①梗 TikTok 2 帖,最早 {first:%m-%d},Jev 机会 0.60｜做什么:用AI把自己放进视频", "examples": ["t"],
            "posts": [{"account": "TikTok", "likes": 900, "url": "https://www.tiktok.com/@a/video/7", "text": "t", "platform": "tiktok"}]}


def _app_term(term):
    return {"term": term, "recent": 3, "named": 0.66, "window": "first", "described": True, "tied": "", "variants": [term],
            "what": "新应用,德摄影录像付费 #8,上架 20 天,卖点词 night camera,同类新应用 0 个(先手)",
            "note": "②榜单 德摄影录像付费 #8(上架 20 天,1 个区上榜),先手", "examples": [term], "link": "https://apps.apple.com/de/app/id1"}


def _sources_with(monkeypatch, memes_=(), apps=(), hf_error=""):
    _quiet_memes_and_charts(monkeypatch)
    monkeypatch.setattr(radar, "judge", lambda rows: None)
    monkeypatch.setattr(radar.memes, "memes", lambda snaps: {
        "posts": 120, "by_platform": {"tiktok": 120}, "tags": 6, "memes": [], "terms": [dict(t) for t in memes_],
        "errors": [], "jev": True, "cost_micros": 0})
    monkeypatch.setattr(radar.appstore, "apps", lambda snaps: {
        "charts": 290, "failed": [], "apps": [], "terms": [dict(t) for t in apps], "read": [], "errors": [], "cost_micros": 0})
    monkeypatch.setattr(radar.source_signals, "x_new", lambda snaps: {"posts": 400, "terms": []})

    def hf(snaps):
        if hf_error:
            raise OSError(hf_error)
        return {"models": 100, "terms": []}
    monkeypatch.setattr(radar.source_signals, "hf_new", hf)


def test_the_8_hourly_run_mails_only_the_picks_no_earlier_mail_sent(monkeypatch, tmp_path):
    report, snaps, mail = tmp_path / "sources.md", tmp_path / "snap", tmp_path / "sources.picks.md"
    flags = {"--sources", "--skip-db"}
    _sources_with(monkeypatch, memes_=[_meme_term("korean baseball ai")])
    radar.sources_main(report, snaps, flags)
    first = mail.read_text()
    assert first.startswith("1. **korean baseball ai**:AI 视频梗,用AI把自己放进视频。") and "\n2. " not in first
    assert "**今天上线**" in first and first.rstrip().endswith("[最热一条](https://www.tiktok.com/@a/video/7)")
    assert "明细" not in first and "|" not in first and "### " not in first           # the picks, nothing else
    assert "korean baseball ai" in report.read_text()                                    # the step summary keeps the full report
    assert not (snaps / radar.SENT).exists() and set(radar.memory(snaps / radar.SENT_NEXT)) == {"korean baseball ai"}
    radar.sources_main(report, snaps, flags)                                             # that mail failed: not moved in place
    assert mail.read_text() == first                                                     # so the next run sends it again
    (snaps / radar.SENT_NEXT).rename(snaps / radar.SENT)                                 # what radar-source.yml does once it is sent
    _sources_with(monkeypatch, memes_=[_meme_term("korean baseball ai")], apps=[_app_term("2am cam")])
    radar.sources_main(report, snaps, flags)
    second = mail.read_text()
    assert second.startswith("1. **2am cam**:新应用") and "korean" not in second and "[应用页](https://apps.apple.com/de/app/id1)" in second
    (snaps / radar.SENT_NEXT).rename(snaps / radar.SENT)
    radar.sources_main(report, snaps, flags)
    assert not mail.exists() and not (snaps / radar.SENT_NEXT).exists()                  # nothing new: no mail
    assert set(radar.memory(snaps / radar.SENT)) == {"korean baseball ai", "2am cam"}


def test_a_source_error_goes_to_the_step_summary_not_the_mail(monkeypatch, tmp_path):
    _sources_with(monkeypatch, hf_error="HTTP Error 503: Service Unavailable")
    radar.sources_main(tmp_path / "sources.md", tmp_path / "snap", {"--sources", "--skip-db"})
    assert "HTTP Error 503" in (tmp_path / "sources.md").read_text() and not (tmp_path / "sources.picks.md").exists()
