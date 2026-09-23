"""Which rows get re-graded, and the rules fingerprint that forces a full pass."""
from pathlib import Path
from types import SimpleNamespace

from app.services import grade_refresh
from app.services.security_scanner import SecurityScanner


def test_fingerprint_is_the_rules_file(tmp_path: Path):
    f = tmp_path / "rules.py"
    f.write_text("PATTERN = 'a'\n")
    first = grade_refresh.fingerprint(f)
    assert first == grade_refresh.fingerprint(f) and len(first) == 16
    f.write_text("PATTERN = 'b'\n")
    assert grade_refresh.fingerprint(f) != first


def test_the_live_fingerprint_hashes_the_scanner_not_the_bookkeeping():
    scanner_file = Path(grade_refresh.security_scanner.__file__)
    assert grade_refresh.RULES_FINGERPRINT == grade_refresh.fingerprint(scanner_file)


def test_scan_full_env_forces_a_full_pass(monkeypatch):
    monkeypatch.setenv("SCAN_FULL", "1")
    assert grade_refresh.full_scan_reason(db=None) == "SCAN_FULL=1"  # decided before any query


def test_scan_all_no_longer_lives_in_the_rules_file():
    assert not hasattr(SecurityScanner, "scan_all")


def test_an_empty_readme_is_unknown_not_safe():
    skill = SimpleNamespace(readme_content="", author_name="x", stars=3, license=None,
                            repo_full_name="x/y", homepage_url="")
    assert SecurityScanner().scan_single(skill) == ("unknown", [])
