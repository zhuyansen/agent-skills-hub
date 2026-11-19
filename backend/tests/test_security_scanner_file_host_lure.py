"""file_host_archive_lure: a link straight to an archive or program on a file-sharing host.

Positives are the shape the 2026-11-18 dry run found on all 870 hits: a copy of a real
project's README plus a "GET" badge to a .rar on Dropbox (the ai--manus / GitHub-Copilot-app
campaign). Negatives are what real projects do with the same hosts: share a folder or a
page, or link a binary from GitHub releases.
"""

from types import SimpleNamespace

import pytest

from app.services.security_scanner import FILE_HOST_FLAG, SecurityScanner

# The copies carry bought stars and the original's MIT license.
CLONE = {"author_name": "LumiVikinggard89137", "stars": 682, "license": "MIT",
         "repo_full_name": "LumiVikinggard89137/ai--manus", "homepage_url": ""}


def scan(readme: str, **overrides):
    skill = SimpleNamespace(readme_content=readme, **{**CLONE, **overrides})
    return SecurityScanner().scan_single(skill)


def flagged(readme: str) -> bool:
    return FILE_HOST_FLAG in scan(readme)[1]


GET_BADGE = ("[![GET](https://img.shields.io/badge/GET%20%E2%80%94%20Manus-0078D6?style=for-the-badge)]"
             "(https://www.dropbox.com/scl/fi/7otex5g3in9c38g1ney7u/Manus_Studio.rar?rlkey=tr3w&st=5pgm&dl=1)")


@pytest.mark.parametrize("link", [
    GET_BADGE,
    "[Download](https://www.mediafire.com/file/abc123/Setup.exe)",
    '<a href="https://mega.nz/file/Setup.zip">Get it</a>',
    "[app](https://dl.dropboxusercontent.com/s/xyz/Tool.7z)",
])
def test_a_link_to_an_archive_on_a_file_host_is_rejected(link):
    grade, flags = scan(f"# AI Manus\n\nAI Manus is a general-purpose AI Agent system.\n\n{link}\n")
    assert flags.count(FILE_HOST_FLAG) == 1
    # Stars and a license don't soften it: both are what the campaign fakes.
    assert grade == "reject"


def test_an_official_org_is_downgraded_to_unsafe_as_for_every_reject_rule():
    assert scan(GET_BADGE, author_name="anthropics", repo_full_name="anthropics/x")[0] == "unsafe"


def test_it_counts_once_however_many_links():
    _grade, flags = scan("\n\n".join([GET_BADGE] * 3))
    assert flags.count(FILE_HOST_FLAG) == 1


@pytest.mark.parametrize("readme", [
    # A shared folder or page on the same host: datasets, slides, model weights.
    "[Dataset](https://www.dropbox.com/scl/fo/abc/h?rlkey=x&dl=0)",
    "[Slides](https://drive.google.com/file/d/1AbC/view)",
    # Binaries from GitHub releases are what a download link should point at.
    "[Download](https://github.com/someone/tool/releases/download/v1.0/Tool.zip)",
    # Another host serving a zip is not a file-sharing host.
    "[Download](https://example.org/files/Tool.zip)",
    # Shown as code, the link is being documented, not offered.
    f"Lures look like this:\n\n```markdown\n{GET_BADGE}\n```\n",
    f"A lure README adds one line: `{GET_BADGE}`.",
])
def test_folders_releases_and_quoted_links_do_not_count(readme):
    assert not flagged(readme)


def test_the_flag_is_described_as_critical():
    assert SecurityScanner.get_flag_severity(FILE_HOST_FLAG) == "critical"
    assert "file-sharing host" in SecurityScanner.get_flag_description(FILE_HOST_FLAG)
