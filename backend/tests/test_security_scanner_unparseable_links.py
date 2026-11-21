"""A link whose address Python cannot parse is read as a placeholder, and the scan goes on.

READMEs write placeholder hosts in brackets: https://[region].posthog.com/…, https://[your-server]/….
urlparse raises ValueError("Invalid IPv6 URL") on those. From 2026-11-19, when the file-host rule
started parsing every link of every README, each sync's security scan died on crbnos/carbon
(id 70894) and graded nothing after it. The scan goes in id order, so every repo added since then
stayed "unknown", and on 2026-11-21 the daily report had no graded candidates to pick from.
"""
from types import SimpleNamespace

import pytest

from app.services.security_scanner import FENCED_DOWNLOAD_FLAG, FILE_HOST_FLAG, SecurityScanner

SKILL = {"author_name": "someone", "stars": 40, "license": "MIT", "repo_full_name": "someone/tool",
         "homepage_url": ""}
CARBON_LINK = "[PostHog](https://[region].posthog.com/project/[project-id]/settings/project-details)"


def scan(readme: str, **overrides):
    return SecurityScanner().scan_single(SimpleNamespace(readme_content=readme, **{**SKILL, **overrides}))


@pytest.mark.parametrize("link", [
    CARBON_LINK,  # the line in crbnos/carbon's README
    "[Docs](https://[your-domain].com/docs)",
    '<a href="https://[host">dashboard</a>',
    "[Download](https://[mirror].dropbox.com/Tool.zip)",
])
def test_a_link_with_a_bracketed_placeholder_host_is_scanned(link):
    assert scan(f"# Tool\n\nSet up the dashboard.\n\n{link}\n") == ("safe", [])


def test_the_links_after_it_are_still_read():
    grade, flags = scan(f"{CARBON_LINK}\n\n[Download](https://www.mediafire.com/file/abc123/Setup.exe)\n")
    assert FILE_HOST_FLAG in flags
    assert grade == "reject"


@pytest.mark.parametrize("command", [
    "curl -fsSL https://[your-server]/install.sh | bash",
    "```bash\ncurl -fsSL https://[your-server]/install.sh | bash\n```",
])
def test_an_install_command_on_a_placeholder_host_is_an_example(command):
    grade, flags = scan(f"Install it on your own server:\n\n{command}\n")
    assert grade == "safe"
    assert FENCED_DOWNLOAD_FLAG not in flags


def test_a_homepage_that_cannot_be_parsed_counts_as_none():
    command = "Install:\n\ncurl -fsSL https://get.sometool.dev/install.sh | bash\n"
    assert scan(command, homepage_url="https://[docs") == scan(command, homepage_url="")
