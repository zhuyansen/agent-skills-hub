"""Pure helpers of sub_skills_collect.py: which files count, URL slugs, frontmatter, excerpts."""
from sub_skills_collect import (
    MAX_SKILLS_PER_REPO,
    assign_slugs,
    close_list_items,
    cut,
    parse_skill_md,
    skill_md_paths,
    split_frontmatter,
)


def blob(path, sha="s"):
    return {"path": path, "type": "blob", "sha": sha}


def test_skill_md_paths_keeps_skill_files_and_skips_vendored_and_template_folders():
    tree = [
        blob("unslop/SKILL.md", "a"), blob("implement/Skill.md", "b"), blob("SKILL.md", "c"),
        blob("node_modules/x/SKILL.md"), blob("templates/SKILL.md"), blob("docs/README.md"),
        blob("skills/in-progress/draft-skill/SKILL.md"), blob("deprecated/old/SKILL.md"),
        blob("packages/sdk/test-data/skills/pirate/SKILL.md"), blob("docs/examples/demo/SKILL.md"),
        {"path": "interview", "type": "tree", "sha": "t"},
    ]
    assert skill_md_paths(tree) == [("", "c"), ("implement", "b"), ("unslop", "a")]


def test_skill_md_paths_keeps_one_copy_per_skill_and_drops_translations():
    tree = [
        blob(".agents/skills/tdd/SKILL.md", "m1"), blob(".kiro/skills/tdd/SKILL.md", "m2"),
        blob("pi/core/skills/tdd/SKILL.md", "m3"), blob("skills/tdd/SKILL.md", "canon"),
        blob(".claude/skills/only-here/SKILL.md", "dot"),
        blob("docs/ja-JP/skills/tdd/SKILL.md"), blob("docs/zh-cn/skills/extra/SKILL.md"),
        blob("docs/tr/skills/extra2/SKILL.md"), blob("skills/ai-sdk/SKILL.md", "ai"),
    ]
    assert skill_md_paths(tree) == [(".claude/skills/only-here", "dot"), ("skills/ai-sdk", "ai"), ("skills/tdd", "canon")]


def test_skill_md_paths_caps_a_huge_collection():
    tree = [blob(f"skills/s{i:04d}/SKILL.md") for i in range(MAX_SKILLS_PER_REPO + 50)]
    assert len(skill_md_paths(tree)) == MAX_SKILLS_PER_REPO


def test_assign_slugs_uses_the_folder_then_the_name_and_stays_unique():
    slugs = assign_slugs([("skills/Unslop FR", "x"), ("other/unslop-fr", "y"), ("", "Root Router"), ("a/index", "z")])
    assert slugs == {"skills/Unslop FR": "unslop-fr", "other/unslop-fr": "unslop-fr-2", "": "root-router",
                     "a/index": "index-skill"}


def test_assign_slugs_never_moves_a_published_slug():
    # A new folder that sorts first must not take the slug an existing page already uses.
    slugs = assign_slugs([("Foo Bar", "x"), ("foo-bar", "y")], stable={"foo-bar": "foo-bar"})
    assert slugs == {"foo-bar": "foo-bar", "Foo Bar": "foo-bar-2"}


def test_split_frontmatter_reads_yaml_and_survives_an_unquoted_colon():
    fields, body = split_frontmatter("---\nname: unslop\ndescription: Use when: the text sounds generated\n---\n# Unslop\nBody")
    assert fields == {"name": "unslop", "description": "Use when: the text sounds generated"}
    assert body.strip() == "# Unslop\nBody"


def test_split_frontmatter_without_a_closing_fence_is_all_body():
    assert split_frontmatter("---\nname: x\nno end") == ({}, "---\nname: x\nno end")


def test_parse_skill_md_falls_back_to_the_folder_and_the_body():
    text = ("# Title\n\nCleans up [prose](https://x.y) so it reads human.\n\n```bash\nrm -rf /\n```\n"
            "## Usage\nTopic: $ARGUMENTS\n\n| a | b |\n|---|---|\n| 1 | 2 |\nMore text.")
    name, description, excerpt = parse_skill_md(text, "skills/unslop")
    assert name == "unslop"
    assert description == excerpt == "Cleans up prose so it reads human. Topic: a b 1 2 More text."


def test_cut_ends_on_a_sentence_past_halfway():
    text = "First sentence is here. Second one runs on and on past the limit"
    assert cut(text, 40) == "First sentence is here."
    assert cut("short", 40) == "short"


def test_list_tree_calls_an_old_name_that_redirects_moved(monkeypatch):
    import sub_skills_collect as c
    moved_to = "https://api.github.com/repositories/1/git/trees/HEAD?recursive=1"
    monkeypatch.setattr(c, "http_get", lambda url, *_: (200, b'{"tree": []}', 4000, moved_to))
    assert c.list_tree("affaan-m/everything-claude-code", "t", None) == ("moved", None, 4000)
    monkeypatch.setattr(c, "http_get", lambda url, *_: (200, b'{"tree": []}', 4000, url))
    assert c.list_tree("affaan-m/ECC", "t", None) == ("ok", {"tree": []}, 4000)


def test_list_items_end_with_a_full_stop_and_keep_their_continuation_lines():
    text = "Use for:\n- Test failures\n- Bugs in production\n  that recur\n1. Done already.\n\nMore text"
    assert close_list_items(text) == "Use for:\nTest failures.\nBugs in production\n  that recur.\nDone already.\n\nMore text"
