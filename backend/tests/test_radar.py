"""The radar's pure logic (ops/radar): name extraction, signal scoring, the review's verdict.
Network and database calls are not exercised here."""
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops/radar"))

import breakout  # noqa: E402
import radar  # noqa: E402
import review  # noqa: E402
import sitemap_diff  # noqa: E402
from source_signals import base_name, novel_names  # noqa: E402
from terms import names  # noqa: E402

NOW = datetime(2026, 10, 3, 12, tzinfo=timezone.utc)


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


# --- ③ LobeHub: 17 languages are one entry ---------------------------------------------

def test_lobehub_locale_prefix_is_stripped():
    urls = ["https://lobehub.com/skills/x", "https://lobehub.com/zh/skills/x", "https://lobehub.com/zh-TW/skills/x"]
    assert {re.sub(sitemap_diff._LOCALE, r"\1", u) for u in urls} == {"https://lobehub.com/skills/x"}


def test_lobehub_paths_are_not_mistaken_for_locales():
    assert re.sub(sitemap_diff._LOCALE, r"\1", "https://lobehub.com/mcp/foo") == "https://lobehub.com/mcp/foo"


# --- merging the signals ----------------------------------------------------------------

def test_leads_merge_a_term_seen_by_two_signals(monkeypatch):
    monkeypatch.setattr(radar, "judge", lambda rows: None)
    blocks = {"x": {"terms": [{"term": "strata", "recent": 2, "note": "X 2 个账号"}]},
              "breakout": {"terms": [{"term": "strata", "recent": 1, "note": "GitHub 爆发",
                                      "variants": ["strata", "niko1221 strata"]}]},
              "sitemap": {"terms": [{"term": "other", "recent": 3, "lift": 4.0}]}}
    rows = radar.leads(blocks)
    assert rows[0]["term"] == "strata" and rows[0]["kinds"] == ["x", "breakout"]
    assert rows[0]["variants"] == ["strata", "niko1221 strata"]
    assert rows[1]["signals"] == ["③竞品 3 处 (×4.0)"]


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


# --- the 8-hourly source run --------------------------------------------------------------

def test_sources_run_writes_no_report_when_nothing_is_new(monkeypatch, tmp_path):
    monkeypatch.setattr(radar.source_signals, "x_new", lambda snaps: {"posts": 400, "terms": []})
    monkeypatch.setattr(radar.source_signals, "hf_new", lambda snaps: {"models": 100, "terms": []})
    report = tmp_path / "sources.md"
    assert radar.sources_main(report, tmp_path, {"--sources", "--skip-db"}) == 0
    assert not report.exists()


def test_sources_run_reports_a_new_name(monkeypatch, tmp_path):
    monkeypatch.setattr(radar, "judge", lambda rows: None)
    monkeypatch.setattr(radar.source_signals, "x_new", lambda snaps: {"posts": 400, "cost_micros": 72000, "terms": [
        {"term": "qwen3.9", "recent": 2, "note": "X 2 个账号 ♥900", "examples": ["@Alibaba_Qwen: Qwen3.9 is out"]}]})
    monkeypatch.setattr(radar.source_signals, "hf_new", lambda snaps: {"models": 100, "terms": []})
    report = tmp_path / "sources.md"
    radar.sources_main(report, tmp_path, {"--sources", "--skip-db"})
    text = report.read_text()
    assert "**qwen3.9**" in text and "$0.072" in text


# --- topics and mail ------------------------------------------------------------------------

def test_topic_section_lists_matching_leads_repos_and_queries(monkeypatch):
    monkeypatch.setattr(radar, "TOPICS", {"AI 视频": re.compile(r"\bvideo", re.I)})
    lead = [{"term": "reelmimic", "examples": ["edenfunf/reelmimic: Show it a video you love"], "signals": ["②爆发"]},
            {"term": "strata", "examples": ["Niko1221/Strata: Qwen3.8 on a gaming PC"], "signals": ["②爆发"]}]
    blocks = {"breakout": {"repos": [{"repo": "a/motion-video-kit", "description": "video kit", "stars": 900, "velocity": 300},
                                     {"repo": "Niko1221/Strata", "description": "Qwen3.8", "stars": 7700, "velocity": 870}]}}
    gsc = {"queries": [{"query": "claude video skills", "impressions": 6, "page": "https://agentskillshub.top/best/x/"},
                       {"query": "best ai scraping tools", "impressions": 3, "page": "/best/web-scraping/"}]}
    text = "\n".join(radar.topic_lines(lead, blocks, gsc))
    assert "reelmimic" in text and "motion-video-kit" in text and "claude video skills" in text
    assert "strata" not in text.lower() and "scraping" not in text


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


# --- ③ new sites (whois overview, weekly) --------------------------------------------------

import json as _json  # noqa: E402

import new_sites  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures/whois_new_ai_sites.json"   # real answer, 2026-10-06


def test_new_site_name_terms():
    assert new_sites.name_terms("ai-hailuo.com") == ["hailuo"]
    assert new_sites.name_terms("livephoto.video") == ["livephoto"]
    assert new_sites.name_terms("ai-video-tool.com") == []   # only stop words left


def test_new_sites_drop_domains_ranking_for_a_handful_of_terms(monkeypatch, tmp_path):
    items = _json.loads(FIXTURE.read_text())
    answer = {"tasks": [{"result": [{"items": items}]}]}
    monkeypatch.setattr(new_sites.aisa, "call_all", lambda calls: ({c["call_id"]: answer for c in calls}, 127000))
    out = new_sites.new_sites(tmp_path, date(2026, 10, 6))
    domains = [r["domain"] for r in out["sites"]]
    assert "ai-hailuo.com" in domains and "neonwin386.ai" not in domains and "oyo88.ai" not in domains
    assert all(r["new"] for r in out["sites"]) and "hailuo" in [t["term"] for t in out["terms"]]
    again = new_sites.new_sites(tmp_path, date(2026, 10, 13))
    assert not any(r["new"] for r in again["sites"]) and again["terms"] == []


def test_new_sites_query_needs_both_dates():
    body = new_sites._calls(date(2026, 10, 6))[0]["arguments"]["body"][0]
    fields = [f[0] for f in body["filters"] if isinstance(f, list)]
    assert fields[:2] == ["created_datetime", "first_seen"] and body["filters"][0][2].startswith("2026-07-08")


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
