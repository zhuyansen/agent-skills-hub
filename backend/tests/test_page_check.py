"""ops/seo/page_check.py: target keyword choice, the word-frequency check, changed pages."""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops/seo"))

import page_check as pc  # noqa: E402

PAGE = "https://agentskillshub.top/best/{}/"


def _gsc(slug, *queries):
    return pc.pick_queries([{"page": PAGE.format(slug), "query": q, "impressions": n} for q, n in queries])


# --- target keyword ---------------------------------------------------------------------

def test_gsc_query_needs_to_share_the_subject():
    gsc = _gsc("typesafe-jev", ("jev ultrafast", 90), ("typesafe jev skills", 40))
    assert pc.target_keyword({"slug": "typesafe-jev"}, "TypeSafe Jev: 140 Graded", gsc) == ("typesafe jev skills", "GSC")


def test_operator_and_overlong_queries_are_ignored():
    gsc = _gsc("codex-skills", ("%site.developers.openai.com codex skills", 300), ("china codex skills market report", 200))
    assert pc.target_keyword({"slug": "codex-skills"}, "Codex Skills: 2,960 Graded", gsc) == ("codex skills", "标题")


def test_configured_keyword_and_serp_subject_win():
    assert pc.target_keyword({"slug": "x", "seo_keyword": "PPT Skills"}, "T", {}) == ("ppt skills", "配置")
    page = {"slug": "mcp-database", "serp_subject": "Database MCP Servers: Supabase & Postgres"}
    assert pc.target_keyword(page, "Whatever", {}) == ("database mcp servers", "标题")


def test_ampersand_subject_keeps_its_head_noun():
    assert pc.subject({}, "Claude & Codex Design Skills: 178 Graded") == "claude design skills"
    assert pc.subject({}, "Humanizer Skills & AI Slop Detectors") == "humanizer skills"


def test_plural_s_does_not_matter():
    gsc = _gsc("claude-video-skills", ("claude video skill", 50))
    kw, _ = pc.target_keyword({"slug": "claude-video-skills"}, "Claude Video Skills: 120 Graded", gsc)
    assert kw == "claude video skill" and pc._has("Best Claude Video Skills in 2026", kw)


# --- the word-frequency check -------------------------------------------------------------

def test_core_keeps_the_phrase_middle_and_drops_generic_ends():
    assert pc.core("best code review skill") == "code review"
    assert pc.core("mcp tools for github") == "mcp tools for github"
    assert pc.core("claude code hooks") == "claude code hooks"


def test_ngram_rank_ignores_function_word_grams():
    words = ("the the the by by " + "ppt skill " * 3 + "python mit " * 2).split()
    rank, top = pc.ngram_rank(words, "ppt skills")
    assert rank == 1 and top[0] == ("ppt skill", 3)


def test_checks_flag_a_page_whose_card_text_outranks_its_keyword():
    body = "<p>" + "python mcp server " * 60 + "database mcp servers " * 5 + "</p>"
    html = (f'<html><head><title>Database MCP Servers: 50 Graded</title>'
            f'<meta name="description" content="{"x" * 100}"><link rel="canonical" href="{PAGE.format("db")}">'
            f'</head><body><h1>Database MCP Servers</h1>{body}</body></html>')
    results = dict((n, s) for n, s, _ in pc.checks(pc.parse(html), "database mcp servers", PAGE.format("db")))
    assert results["词频榜(核心词)"] != "ok" and results["标题长度"] == "ok" and results["canonical"] == "ok"


# --- Suski citation structure & freshness checks ------------------------------------------

def test_structure_checks_pass_with_bluf_table_bold_h2_and_valid_dates():
    cells = "".join("<td>cell</td>" for _ in range(36))
    bolds = "".join("<strong>verdict</strong> " for _ in range(6))
    h2s = "".join(f"<h2>Section {i}</h2>" for i in range(8))
    html = (
        f'<html><head><title>Code Review Skills: 180 Graded (2026)</title>'
        f'<meta name="description" content="{"x" * 100}">'
        f'<link rel="canonical" href="{PAGE.format("code-review")}">'
        f'<script type="application/ld+json">{{"dateModified": "2026-10-08"}}</script>'
        f'</head><body><h1>Best Code Review Skills in 2026</h1>'
        f'<div class="bp-quick-pick">The best code review skills in 2026 is code-review-skill — best for PR review.</div>'
        f'{bolds}{h2s}<table><tr>{cells}</tr></table></body></html>'
    )
    results = dict((n, s) for n, s, _ in pc.checks(
        pc.parse(html), "code review skills", PAGE.format("code-review"), today=date(2026, 11, 16)
    ))
    assert results["对比表单元格数"] == "ok"
    assert results["加粗 verdict/span 数"] == "ok"
    assert results["H2 数量"] == "ok"
    assert results["首 100 词直答(BLUF)"] == "ok"
    assert results["URL 不含年份"] == "ok"
    assert results["标题年份与更新日期一致"] == "ok"


def test_structure_checks_flag_missing_bluf_url_year_and_stale_or_future_dates():
    html_stale = (
        '<html><head><title>Best Tools in 2025</title></head>'
        '<body><h1>Best Tools in 2025</h1><p>Welcome to our directory of tools.</p></body></html>'
    )
    res_stale = dict((n, s) for n, s, _ in pc.checks(
        pc.parse(html_stale), "best tools", PAGE.format("tools-2026"), today=date(2026, 11, 16)
    ))
    assert res_stale["对比表单元格数"] == "fail"
    assert res_stale["加粗 verdict/span 数"] == "warn"
    assert res_stale["H2 数量"] == "warn"
    assert res_stale["首 100 词直答(BLUF)"] == "warn"
    assert res_stale["URL 不含年份"] == "fail"
    assert res_stale["标题年份与更新日期一致"] == "warn"

    html_future = (
        '<html><head><title>Best Tools (2026)</title>'
        '<script type="application/ld+json">{"lastReviewed": "2026-12-31"}</script></head>'
        '<body><h1>Best Tools (2026)</h1></body></html>'
    )
    res_future = dict((n, s) for n, s, _ in pc.checks(
        pc.parse(html_future), "best tools", PAGE.format("tools"), today=date(2026, 11, 16)
    ))
    assert res_future["标题年份与更新日期一致"] == "fail"


# --- which pages a deploy changed ----------------------------------------------------------

def _repo(tmp_path, pages, desc):
    scripts = tmp_path / pc.SCRIPTS
    scripts.mkdir(parents=True, exist_ok=True)
    (tmp_path / pc.KEYWORDS_FILE).write_text(json.dumps(pages))
    (tmp_path / pc.PER_SLUG_FILES[0]).write_text(json.dumps(desc))
    git = lambda *a: subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True, text=True).stdout  # noqa: E731
    git("add", "-A")
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "c")
    return git("rev-parse", "HEAD").strip()


def test_changed_slugs_reads_entries_and_per_slug_files(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    monkeypatch.setattr(pc, "ROOT", tmp_path)
    pages = [{"slug": "a", "title": "A"}, {"slug": "b", "title": "B"}, {"slug": "c", "title": "C", "retired": True}]
    base = _repo(tmp_path, pages, {"b": "old"})
    pages[0]["title"] = "A2"
    pages[2]["title"] = "C2"
    head = _repo(tmp_path, pages, {"b": "new"})
    assert pc.changed_slugs(base, head) == ["a", "b"]    # c is retired


def test_a_changed_generator_means_every_live_page(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    monkeypatch.setattr(pc, "ROOT", tmp_path)
    pages = [{"slug": "a", "title": "A"}, {"slug": "b", "title": "B"}]
    base = _repo(tmp_path, pages, {})
    (tmp_path / pc.SHARED_FILES[0]).write_text("// new layout")
    head = _repo(tmp_path, pages, {})
    assert pc.changed_slugs(base, head) == ["a", "b"]

