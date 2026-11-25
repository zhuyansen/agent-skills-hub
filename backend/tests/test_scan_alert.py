"""A broken scan mails once per incident, not on every sync (three a day).

The first note mails and opens a scan-alert issue; while it is open, notes go to it as comments;
the first clean scan closes it. A failed sync says nothing about the scan and changes nothing.
"""
import pytest

import scan_alert

NOTE = "The scanner raised on 1 README(s)...\n70894 crbnos/carbon: ValueError: Invalid IPv6 URL"


@pytest.mark.parametrize("note, issue, sync_ok, action", [
    (NOTE, None, True, "mail"),
    (NOTE, "12", True, "comment"),
    ("", "12", True, "close"),
    ("", None, True, "nothing"),
    (NOTE, None, False, "nothing"),
    ("", "12", False, "nothing"),  # a sync that died before the scan is not a clean scan
])
def test_decide(note, issue, sync_ok, action):
    assert scan_alert.decide(note, issue, sync_ok) == action


@pytest.fixture
def run(monkeypatch, tmp_path):
    calls = {"gh": [], "mail": []}
    alert = tmp_path / "scan-alert.txt"
    for key, value in {"SCAN_ALERT_FILE": str(alert), "GITHUB_REPOSITORY": "o/r", "RUN_URL": "https://run",
                       "SYNC_OUTCOME": "success"}.items():
        monkeypatch.setenv(key, value)

    def start(note, issue):
        if note:
            alert.write_text(note)
        monkeypatch.setattr(scan_alert, "gh", lambda *a: calls["gh"].append(a) or (issue or "" if a[:2] == ("issue", "list") else ""))
        monkeypatch.setattr(scan_alert, "send_mail", lambda note, url: calls["mail"].append(note))
        scan_alert.main()
        return calls
    return start


def test_the_first_alert_mails_and_opens_the_issue(run):
    calls = run(NOTE, None)
    assert calls["mail"] == [NOTE]
    assert [a[:2] for a in calls["gh"]] == [("issue", "list"), ("label", "create"), ("issue", "create")]


def test_a_repeat_only_comments(run):
    calls = run(NOTE, "12")
    assert calls["mail"] == []
    assert calls["gh"][-1][:3] == ("issue", "comment", "12")


def test_a_clean_scan_closes_the_issue(run):
    calls = run("", "12")
    assert calls["mail"] == []
    assert calls["gh"][-1][:3] == ("issue", "close", "12")
