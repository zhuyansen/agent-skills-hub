"""The sync's clone-campaign cleanup and the build's filter must apply one rule.

The SQL itself was dry-run against the catalog on 2026-11-18 (898 rows: 758 ai-manus copies,
114 GitHub-Copilot-app, 21 Gemini-Config-Checker-, 5 Capri; Simpleyyt/ai-manus kept); the
rule's edge cases are tested on the JavaScript side (frontend/scripts/clone-campaigns.test.mjs).
"""

import re
from pathlib import Path

import pytest

from app.services import clone_campaigns

JS = (Path(__file__).resolve().parents[2] / "frontend" / "scripts" / "clone-campaigns.mjs").read_text()


@pytest.mark.parametrize("name", ["MIN_DESC", "MIN_OWNERS", "MIN_STARS", "ORIGINAL_LEAD_DAYS"])
def test_the_build_filter_uses_the_same_thresholds(name):
    js_value = int(re.search(rf"export const {name} = (\d+);", JS).group(1))
    assert js_value == getattr(clone_campaigns, name)


def test_delete_and_count_select_the_same_rows():
    assert clone_campaigns._CAMPAIGN_ROWS in clone_campaigns.DELETE_SQL
    assert clone_campaigns._CAMPAIGN_ROWS in clone_campaigns.COUNT_SQL


def test_the_readme_column_is_never_read():
    # A full-table scan that pulled readme_content would blow the sync's statement timeout.
    assert "readme" not in clone_campaigns._CAMPAIGN_ROWS
    assert "SELECT *" not in clone_campaigns._CAMPAIGN_ROWS
