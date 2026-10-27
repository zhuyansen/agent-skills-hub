"""ops/release/propagate.py: re-pinning, skill bodies, the ClawHub command, the WorkBuddy zip. No network."""
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops/release"))

import propagate as pr  # noqa: E402


def test_repin_moves_every_mention_and_leaves_other_versions():
    text = '{"args": ["--with", "mcp==2.3.0", "new-term-radar==0.6.0"], "note": "0.6.0 adds", "x": "10.6.0 0.6.01"}'
    out = pr.repin(text, "0.6.0", "0.6.1")
    assert '"new-term-radar==0.6.1"' in out and '"note": "0.6.1 adds"' in out
    assert "mcp==2.3.0" in out and "10.6.0 0.6.01" in out


def test_a_skill_body_drops_the_frontmatter_and_trims():
    text = "---\nname: x\ndescription: y\n---\n\n# Title\n\nBody.\n"
    assert pr.skill_body(text) == "# Title\n\nBody."
    assert pr.skill_body("# No frontmatter\n") == "# No frontmatter"


def test_the_clawhub_command_carries_the_source_and_the_dry_run():
    cmd = pr.clawhub_command("backlink-guard", "0.12.0", "abc123", Path("/tmp/t/skills/backlink-guard"), "v0.12.0", True)
    assert cmd[:4] == pr.CLAWHUB and cmd[4] == "publish" and cmd[-1] == "--dry-run"
    pairs = dict(zip(cmd[6::2], cmd[7::2]))
    assert pairs["--slug"] == "backlink-guard" and pairs["--version"] == "0.12.0"
    assert pairs["--source-repo"] == "zhuyansen/backlink-guard" and pairs["--source-ref"] == "v0.12.0"
    assert pairs["--source-path"] == "skills/backlink-guard" and pairs["--source-commit"] == "abc123"


def test_clawhub_runs_without_the_proxy(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:7897")
    monkeypatch.setenv("PATH_KEEP", "1")
    env = pr.no_proxy_env()
    assert "HTTPS_PROXY" not in env and env["PATH_KEEP"] == "1"


def _package(root):
    folder = root / "ops/workbuddy/new-term-radar"
    (folder / "skills/new-term-radar").mkdir(parents=True)
    (folder / "mcp.json").write_text('{"args": ["--with", "mcp==2.3.0", "new-term-radar==0.6.0"]}')
    (folder / "connector-meta.json").write_text('{"version": "0.6.0"}')
    (folder / "skills/new-term-radar/SKILL.md").write_text("uvx new-term-radar==0.6.0 daily\n")
    (folder / "icon.svg").write_text("<svg/>")
    return folder


def test_workbuddy_dry_run_writes_nothing(tmp_path, monkeypatch):
    folder = _package(tmp_path)
    monkeypatch.setattr(pr, "ROOT", tmp_path)
    lines = pr.workbuddy("new-term-radar", "0.6.1", dry=True)
    assert lines == ["WorkBuddy: would move 0.6.0 -> 0.6.1 in connector-meta.json, mcp.json, SKILL.md"]
    assert "0.6.0" in (folder / "mcp.json").read_text() and not folder.with_suffix(".zip").exists()


def test_workbuddy_repins_and_zips_with_the_folder_on_top(tmp_path, monkeypatch):
    folder = _package(tmp_path)
    monkeypatch.setattr(pr, "ROOT", tmp_path)
    assert pr.workbuddy("new-term-radar", "0.6.1", dry=False)[0].startswith("WorkBuddy: new-term-radar.zip re-pinned 0.6.0 -> 0.6.1")
    names = zipfile.ZipFile(folder.with_suffix(".zip")).namelist()
    assert "new-term-radar/" in names and "new-term-radar/skills/new-term-radar/SKILL.md" in names
    assert "mcp==2.3.0" in (folder / "mcp.json").read_text() and "new-term-radar==0.6.1" in (folder / "mcp.json").read_text()
    assert pr.workbuddy("new-term-radar", "0.6.1", dry=False) == ["WorkBuddy: already 0.6.1"]


def test_the_hand_steps_name_the_connector_and_the_hashes():
    steps = pr.by_hand("new-term-radar", "0.6.1", ["new-term-radar: 15c8b18d"])
    text = "\n".join(steps)
    assert "oc_02d71d5619d9802a" in text and "15c8b18d" in text and "new-term-radar==0.6.1" in text
