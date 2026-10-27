"""After a GitHub Release of new-term-radar or backlink-guard: put the new version on the platforms that
have a command line, re-pin and zip the WorkBuddy packages, and print what is left to do by hand.

  python ops/release/propagate.py <new-term-radar|backlink-guard> <version> [--dry-run]

- PyPI and the official MCP Registry: the Release's publish workflow does both; this only checks.
- ClawHub: every skill under skills/ at the tag, with its source. Needs `npx clawhub@0.23.3 login`
  once. clawhub.ai refuses the 7897 proxy, so these run without one.
- LobeHub: the manifest kept in ops/release/lobehub/<tool>.json with the new version, sent with
  `plugin update` (needs `npx @lobehub/market-cli login` once; no GitHub connection). When the MCP
  server's tools changed, run `plugin init --stdio` again first and save its tools into that file.
- WorkBuddy: ops/workbuddy/<tool>/ re-pinned and zipped. Uploading is by hand.

--dry-run: ClawHub's own --dry-run; LobeHub and the zips are only described, nothing is written.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOME = Path.home()
TOOLS = {
    "new-term-radar": {"repo": HOME / "content/new-term-radar", "workbuddy": "oc_02d71d5619d9802a",
                       "cursor": "https://cursor.directory/plugins/new-term-radar"},
    "backlink-guard": {"repo": HOME / "content/backlink-guard", "workbuddy": "oc_b6d687a4c8cb5e92",
                       "cursor": "https://cursor.directory/plugins/backlink-guard"},
}
OWNER = "zhuyansen"
CLAWHUB = ["npx", "-y", "clawhub@0.23.3", "--no-input"]
LOBEHUB = ["npx", "-y", "@lobehub/market-cli"]
PROXY_VARS = ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy", "ALL_PROXY", "all_proxy")
WORKBUDDY_FILES = ("connector-meta.json", "mcp.json")
TIMEOUT = 30          # seconds for each status check
VERSION = re.compile(r"^\d+\.\d+\.\d+$")


def no_proxy_env() -> dict:
    return {k: v for k, v in os.environ.items() if k not in PROXY_VARS}


def sh(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, **kw)


# --- PyPI and the MCP Registry: only checked ----------------------------------------------

def get_json(url: str) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            return json.load(r)
    except (OSError, ValueError):
        return None


def registry_versions(tool: str) -> list[str]:
    """Versions of io.github.<owner>/<tool> the official registry lists, the latest marked with *."""
    name = f"io.github.{OWNER}/{tool}"
    data = get_json(f"https://registry.modelcontextprotocol.io/v0/servers?search={name}") or {}
    out = []
    for entry in data.get("servers", []):
        server = entry.get("server", entry)
        latest = entry.get("_meta", {}).get("io.modelcontextprotocol.registry/official", {}).get("isLatest")
        if server.get("name") == name:
            out.append(server.get("version", "?") + ("*" if latest else ""))
    return out


def check_published(tool: str, version: str) -> list[str]:
    on_pypi = get_json(f"https://pypi.org/pypi/{tool}/{version}/json") is not None
    listed = registry_versions(tool)
    return [f"PyPI {version}: {'yes' if on_pypi else 'NOT YET'}",
            f"MCP Registry: {', '.join(listed) or 'not found'} (* = latest)"]


# --- ClawHub ------------------------------------------------------------------------------

def checkout(tool: str, version: str) -> tuple[Path, str]:
    """A detached worktree of the tag in a temporary folder, and the tag's commit."""
    repo = TOOLS[tool]["repo"]
    sh(["git", "-C", str(repo), "fetch", "-q", "--tags", "origin"])
    sha = sh(["git", "-C", str(repo), "rev-list", "-n1", f"v{version}"]).stdout.strip()
    if not sha:
        sys.exit(f"no tag v{version} in {repo}")
    path = Path(tempfile.mkdtemp(prefix=f"{tool}-{version}-"))
    sh(["git", "-C", str(repo), "worktree", "add", "--detach", "-f", str(path), sha], check=True)
    return path, sha


def clawhub_command(tool: str, version: str, sha: str, skill_dir: Path, changelog: str, dry: bool) -> list[str]:
    slug = skill_dir.name
    cmd = [*CLAWHUB, "publish", str(skill_dir), "--slug", slug, "--version", version, "--changelog", changelog,
           "--source-repo", f"{OWNER}/{tool}", "--source-commit", sha, "--source-ref", f"v{version}",
           "--source-path", f"skills/{slug}"]
    return cmd + (["--dry-run"] if dry else [])


def clawhub(tool: str, version: str, tree: Path, sha: str, dry: bool) -> list[str]:
    lines = []
    for skill_dir in sorted(p.parent for p in (tree / "skills").glob("*/SKILL.md")):
        cmd = clawhub_command(tool, version, sha, skill_dir, f"v{version}", dry)
        done = sh(cmd, env=no_proxy_env())
        tail = (done.stdout + done.stderr).strip().splitlines()[-1:] or [""]
        lines.append(f"ClawHub {skill_dir.name}: {'ok' if done.returncode == 0 else 'FAILED'} {tail[0][:120]}")
    return lines


FRONTMATTER = re.compile(r"^---\n.*?\n---\n", re.S)


def skill_body(text: str) -> str:
    """What a cursor.directory skill body holds: the SKILL.md without its frontmatter, trimmed."""
    return FRONTMATTER.sub("", text, count=1).strip()


def skill_hashes(tree: Path) -> list[str]:
    """sha256 of each skill body at the tag: what cursor.directory's bodies should hash to after saving."""
    return [f"{p.parent.name}: {hashlib.sha256(skill_body(p.read_text()).encode()).hexdigest()[:16]}"
            for p in sorted((tree / "skills").glob("*/SKILL.md"))]


# --- LobeHub ------------------------------------------------------------------------------

def lobehub(tool: str, version: str, dry: bool) -> list[str]:
    template = ROOT / f"ops/release/lobehub/{tool}.json"
    manifest = json.loads(template.read_text())
    old, manifest["version"] = manifest.get("version"), version
    if dry:
        return [f"LobeHub: would send {manifest['identifier']} {old} -> {version} ({len(manifest['tools'])} tools)"]
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "lhm.plugin.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        done = sh([*LOBEHUB, "plugin", "update", "--dir", tmp])
    if done.returncode != 0:
        return [f"LobeHub: FAILED {(done.stdout + done.stderr).strip()[-160:]}"]
    template.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return [f"LobeHub: {manifest['identifier']} {old} -> {version} sent"]


# --- WorkBuddy ----------------------------------------------------------------------------

def repin(text: str, old: str, new: str) -> str:
    """Every mention of the old version moved to the new one, as the README's sed did; a longer version
    that merely contains it (10.6.0 for 0.6.0) and other packages' pins (mcp==2.3.0) stay as they are."""
    return re.sub(rf"(?<![\d.]){re.escape(old)}(?![\d.])", new, text)


def workbuddy_files(folder: Path) -> list[Path]:
    return [folder / f for f in WORKBUDDY_FILES] + sorted(folder.glob("skills/*/SKILL.md"))


def workbuddy(tool: str, version: str, dry: bool) -> list[str]:
    folder = ROOT / "ops/workbuddy" / tool
    pinned = re.search(rf"{tool}==(\d+\.\d+\.\d+)", (folder / "mcp.json").read_text())
    old = pinned.group(1) if pinned else None
    if old is None or old == version:
        return [f"WorkBuddy: already {version}" if old else "WorkBuddy: no pin found in mcp.json"]
    changed = [p for p in workbuddy_files(folder) if repin(p.read_text(), old, version) != p.read_text()]
    if dry:
        return [f"WorkBuddy: would move {old} -> {version} in {', '.join(p.name for p in changed)}"]
    for p in changed:
        p.write_text(repin(p.read_text(), old, version))
    archive = zip_folder(folder)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    return [f"WorkBuddy: {archive.name} re-pinned {old} -> {version}, {archive.stat().st_size} bytes, sha256 {digest[:16]}"]


def zip_folder(folder: Path) -> Path:
    """<tool>.zip beside the folder, laid out as `zip -r -X <tool>.zip <tool>` made it: folders included."""
    archive = folder.with_suffix(".zip")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for p in [folder, *sorted(folder.rglob("*"))]:
            if p.name != ".DS_Store":
                z.write(p, p.relative_to(folder.parent))
    return archive


# --- by hand ------------------------------------------------------------------------------

def by_hand(tool: str, version: str, hashes: list[str]) -> list[str]:
    wb, cursor = TOOLS[tool]["workbuddy"], TOOLS[tool]["cursor"]
    return [
        f"[ ] cursor.directory {cursor}: each skill body = skills/<name>/SKILL.md at v{version} without its "
        f"frontmatter, the MCP config pins "
        f"{tool}=={version}. sha256 after saving: {'; '.join(hashes)}",
        f"[ ] Skillstore https://skillstore.io/submit: resubmit https://github.com/{OWNER}/{tool}; a bot opens the "
        "update PR in aiskillstore/marketplace, the page changes once it is merged",
        f"[ ] WorkBuddy {wb}: withdraw if under review -> edit -> open "
        f"https://open.workbuddy.cn/connector/publish/{wb}?action=create&step=1&entry=2 -> upload "
        f"ops/workbuddy/{tool}.zip -> continue twice -> submit; after approval check the listed version",
        f"[ ] the scoreboard ops/{tool}-submissions.md",
        "Nothing to do: PyPI and the MCP Registry (the Release), skills.sh, Tessl, SkillsMP, ModelScope (they sync "
        "on their own), the Anthropic directory (rescans about every 6 hours)",
    ]


def main(argv: list[str]) -> None:
    if len(argv) < 2 or argv[0] not in TOOLS or not VERSION.match(argv[1]):
        sys.exit(__doc__)
    tool, version, dry = argv[0], argv[1], "--dry-run" in argv
    tree, sha = checkout(tool, version)
    try:
        hashes = skill_hashes(tree)
        report = [*check_published(tool, version), *clawhub(tool, version, tree, sha, dry),
                  *lobehub(tool, version, dry), *workbuddy(tool, version, dry)]
    finally:
        sh(["git", "-C", str(TOOLS[tool]["repo"]), "worktree", "remove", "--force", str(tree)])
    print("\n".join(report + ["", "By hand:"] + by_hand(tool, version, hashes)))


if __name__ == "__main__":
    main(sys.argv[1:])
