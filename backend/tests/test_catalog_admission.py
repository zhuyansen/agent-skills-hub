"""The admission rule, its parsers, and the pending-only write."""
from app.services.catalog_admission import (
    AUTO_APPROVE_MIN_STARS,
    UPSERT_SQL,
    admission,
    parse_commands,
    parse_repo_url,
)


def repo(full_name, stars, description="", archived=False, fork=False):
    return {"full_name": full_name, "stargazers_count": stars, "description": description,
            "archived": archived, "fork": fork}


def test_high_star_on_topic_is_approved():
    assert admission(repo("dream-num/univer", 14411, "The Office Harness for AI Agents")) == "approved"


def test_the_seleniumbase_boundary_is_admitted_on_purpose():
    # 13K stars, "AI agents" in the description: browser automation is inside the catalog's remit.
    assert admission(repo("seleniumbase/SeleniumBase", 13025, "Browser automation … for AI agents")) == "approved"


def test_just_under_the_star_line_is_pending():
    assert admission(repo("x/agent-skills", AUTO_APPROVE_MIN_STARS - 1, "agent skills")) == "pending"


def test_high_stars_without_a_topic_word_is_pending():
    assert admission(repo("x/fast-json", 20000, "A JSON parser")) == "pending"


def test_topic_word_in_the_name_counts():
    assert admission(repo("humanlayer/skills", 4339, None)) == "approved"


def test_forks_archived_and_lists_are_excluded():
    assert admission(repo("x/skills", 5000, "agent skills", fork=True)) == "excluded"
    assert admission(repo("x/skills", 5000, "agent skills", archived=True)) == "excluded"
    assert admission(repo("x/awesome-agents", 5000, "curated list of agents")) == "excluded"


def test_parse_repo_url_accepts_the_usual_spellings():
    for text in ("https://github.com/agentbody/skills", "see github.com/agentbody/skills/ please",
                 "https://github.com/agentbody/skills.git", "https://github.com/agentbody/skills/tree/main/x"):
        assert parse_repo_url(text) == "agentbody/skills"
    assert parse_repo_url("no link here") is None
    assert parse_repo_url("https://github.com/agentbody") is None


def test_parse_commands_reads_one_per_line_and_rejects_bad_names():
    body = "/approve Hisn00w/ASu-skills\nsome prose\n/reject bad name here\n/approve ../../etc\n/reject x/y"
    cmds, bad = parse_commands(body)
    assert cmds == [("approve", "Hisn00w/ASu-skills"), ("reject", "x/y")]
    assert bad == ["/reject bad name here", "/approve ../../etc"]


def test_upsert_only_overwrites_pending_rows():
    assert "ON CONFLICT (full_name) DO UPDATE" in UPSERT_SQL
    assert "WHERE extra_repos.status = 'pending'" in UPSERT_SQL
