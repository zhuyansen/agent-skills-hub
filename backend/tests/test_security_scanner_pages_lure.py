"""pages_download_lure: a download image button that leads to the owner's own GitHub Pages site.

Positives are the three shapes the 2026-11-09 full-catalog dry run found on 236 lure READMEs
(Mutakisa/game-slop-purge and its family). Negatives marked "catalog FP" are real projects a
broader version of the rule hit in that dry run: a download page on their own GitHub Pages,
linked as text, or a "downloads" counter badge.
"""

from types import SimpleNamespace

import pytest

from app.services.security_scanner import PAGES_DOWNLOAD_FLAG, SecurityScanner

# Tier 5 (few stars, no license): any high-risk flag makes it unsafe.
LURE = {"author_name": "someone", "stars": 73, "license": None, "repo_full_name": "someone/game-tool", "homepage_url": ""}


def scan(readme: str, **overrides):
    skill = SimpleNamespace(readme_content=readme, **{**LURE, **overrides})
    return SecurityScanner().scan_single(skill)


def flagged(readme: str, **overrides) -> bool:
    return PAGES_DOWNLOAD_FLAG in scan(readme, **overrides)[1]


SVG_BUTTON = ("[![Download](https://raw.githubusercontent.com/someone/game-tool/main/btn_3ca3d.svg)]"
              "(https://someone.github.io/game-tool/)")
SHIELDS_BUTTON = ("[![Download](https://img.shields.io/badge/Download%20Link-brightgreen?style=for-the-badge&logo=github)]"
                  "(https://someone.github.io/game-tool/)")
EMPTY_ALT_BADGE = "[![](https://img.shields.io/badge/Download-Release_Page-blue.svg)](https://someone.github.io)"


@pytest.mark.parametrize("button", [SVG_BUTTON, SHIELDS_BUTTON, EMPTY_ALT_BADGE])
def test_a_download_button_to_the_owners_pages_site_is_high_risk(button):
    grade, flags = scan(f"# Kill Game Slop\n\n{button}\n\nAn engine-agnostic agent skill.\n")
    assert flags.count(PAGES_DOWNLOAD_FLAG) == 1
    assert grade == "unsafe"


def test_it_counts_once_however_many_buttons():
    _grade, flags = scan("\n\n".join([SVG_BUTTON] * 4))
    assert flags.count(PAGES_DOWNLOAD_FLAG) == 1


def test_the_owner_matches_whatever_the_case():
    readme = "[![Download](https://x.test/b.svg)](https://Mutakisa.github.io/game-slop-purge/)"
    assert flagged(readme, repo_full_name="Mutakisa/game-slop-purge")


@pytest.mark.parametrize("stars, license, grade", [(150, "MIT", "caution"), (5000, "MIT", "caution")])
def test_a_licensed_project_with_a_track_record_gets_caution(stars, license, grade):
    assert scan(SVG_BUTTON, stars=stars, license=license)[0] == grade


@pytest.mark.parametrize("readme, repo", [
    # catalog FP: a desktop app's download page on its own GitHub Pages, linked as text.
    ('<a href="https://aofp.github.io/yume">Download</a>\n\n[Download](https://aofp.github.io/yume)', "aofp/yume"),
    # catalog FP: counter badges, not buttons.
    ("[![PDF downloads](https://img.shields.io/badge/PDF-downloads-blue)](https://jhljx.github.io/RecSys-Industrial-Book/)",
     "jhljx/RecSys-Industrial-Book"),
    ("[![Ecosystem PyPI downloads](https://img.shields.io/endpoint?url=x)](https://vaquarkhan.github.io/MCP-Bastion/integrations.html)",
     "vaquarkhan/MCP-Bastion"),
])
def test_text_links_and_counter_badges_do_not_count(readme, repo):
    assert not flagged(readme, repo_full_name=repo)


@pytest.mark.parametrize("readme", [
    # Someone else's GitHub Pages site.
    "[![Download](https://img.shields.io/badge/Download-blue)](https://jqlang.github.io/jq/download/)",
    # A release on GitHub is what a download button should point at.
    "[![Download](https://img.shields.io/badge/Download-v1.0-blue)](https://github.com/someone/game-tool/releases/latest)",
    # A docs badge to the project's own site says nothing about downloads.
    "[![Docs](https://img.shields.io/badge/docs-blue.svg)](https://someone.github.io/game-tool/)",
    # Shown as code, the button is being documented, not offered.
    f"Lures look like this:\n\n```markdown\n{SVG_BUTTON}\n```\n",
    f"A lure README is one line: `{SVG_BUTTON}`.",
])
def test_other_targets_and_quoted_buttons_do_not_count(readme):
    assert not flagged(readme)


def test_no_repository_name_means_no_owner_to_match():
    assert not flagged(SVG_BUTTON, repo_full_name="")


def test_the_flag_is_described_as_high_risk():
    assert SecurityScanner.get_flag_severity(PAGES_DOWNLOAD_FLAG) == "high"
    assert "GitHub Pages" in SecurityScanner.get_flag_description(PAGES_DOWNLOAD_FLAG)
