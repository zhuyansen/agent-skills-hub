"""The radar's mails (2026-10-21): the 8-hourly mail holds only picks no earlier mail sent, the
daily mail shows each lead once, ⑤ names only early hits, the words new repos share are in
shadow mode, X is read once a day, and retired signals leave no snapshot behind. No network:
test_radar.py's guard and stubs are reused."""
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops/radar"))

import radar  # noqa: E402
import review  # noqa: E402
import source_signals  # noqa: E402

# no_network is autouse: imported here, it holds every test of this file to the same offline rule
from .test_radar import _quiet_memes_and_charts, no_network  # noqa: E402, F401


# --- ① X, once a day ---------------------------------------------------------------------------

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


# --- retired signals --------------------------------------------------------------------

def test_the_daily_snapshot_drops_what_retired_signals_kept(tmp_path):
    for name in [*radar.RETIRED_SNAPSHOTS, "gh_stars.json.gz"]:
        (tmp_path / name).write_bytes(b"x")
    radar.drop_retired(tmp_path)
    assert [p.name for p in tmp_path.iterdir()] == ["gh_stars.json.gz"]   # breakout's own snapshot stays
    radar.drop_retired(tmp_path)                                         # nothing left to drop: no error


# --- ⑤ review: early hits only ----------------------------------------------------------

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
    assert "### 候选新词" not in (tmp_path / "d1.md").read_text()                     # nor a candidate row repeating it
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


def test_the_candidate_table_lists_only_leads_without_a_section_of_their_own():
    lead = [{"term": "deepinfer", "kinds": ["breakout"], "signals": ["GitHub 爆发 deepseek-ai/DeepInfer"], "examples": [],
             "variants": ["deepinfer"], "named": 0.96},
            {"term": "qwen3.9", "kinds": ["x", "breakout"], "signals": ["X 2 个账号"], "examples": [], "variants": ["qwen3.9"], "named": 0.9}]
    text = "\n".join(radar.candidate_lines(lead))
    assert "**qwen3.9**" in text and "deepinfer" not in text                          # X said it too: not only ②'s
    assert radar.candidate_lines(lead[:1]) == []


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
