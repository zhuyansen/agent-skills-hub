"""Unit tests for ops/stripe/poll_stripe.py multi-SKU fulfillment & redaction."""

import importlib.util
import json
from pathlib import Path
import sys

POLL_PATH = Path(__file__).resolve().parents[2] / "ops" / "stripe" / "poll_stripe.py"
SPEC = importlib.util.spec_from_file_location("poll_stripe", POLL_PATH)
assert SPEC and SPEC.loader
poll_stripe = importlib.util.module_from_spec(SPEC)
sys.modules["poll_stripe"] = poll_stripe
SPEC.loader.exec_module(poll_stripe)


def test_classify_session_skus():
    assert poll_stripe.classify_session({"client_reference_id": "pro--hub-member"}) == ("pro", "hub-member")
    assert poll_stripe.classify_session({"client_reference_id": "cigate--acme--skills"}) == ("cigate", "acme/skills")
    assert poll_stripe.classify_session({"client_reference_id": "fasttrack--foo--bar"}) == ("fasttrack", "foo/bar")
    assert poll_stripe.classify_session({"client_reference_id": "owner--repo"}) == ("deep_audit", "owner/repo")
    assert poll_stripe.classify_session({"mode": "subscription"}) == ("cigate", "team-ci-gate")


def test_pro_fulfillment_redacts_key_and_email_from_public_issue(monkeypatch):
    calls = []
    fake_issued_key = "ash_pro_" + "testkey1234567890"

    def fake_http(url, headers, data=None, method="GET"):
        body = json.loads(data.decode()) if data else None
        calls.append((url, method, body))
        if url.endswith("/rest/v1/rpc/issue_pro_key"):
            return {"status": "issued", "key": fake_issued_key, "note": "pro-usd-29"}
        if url.endswith("/issues"):
            return {"html_url": "https://github.com/zhuyansen/agent-skills-hub/issues/999"}
        return {}

    monkeypatch.setattr(poll_stripe, "http_json", fake_http)
    monkeypatch.setattr(poll_stripe, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(poll_stripe, "SUPABASE_ANON_KEY", "anon-key")
    monkeypatch.setattr(poll_stripe, "ISSUE_SECRET", "issue-secret")
    monkeypatch.setattr(poll_stripe, "RESEND_KEY", "re_test")
    monkeypatch.setattr(poll_stripe, "EMAIL_FROM", "hub@agentskillshub.top")
    monkeypatch.setattr(poll_stripe, "GH_TOKEN", "gh-token")

    session = {
        "id": "cs_test_12345",
        "amount_total": 2900,
        "currency": "usd",
        "payment_status": "paid",
        "client_reference_id": "pro--early-usd",
        "customer_details": {"email": "alice@acme.com"},
    }
    url = poll_stripe.process_session(session)
    assert url.endswith("/issues/999")

    # 1. RPC received exact order_id & pro-usd-29 note
    rpc_calls = [c for c in calls if "issue_pro_key" in c[0]]
    assert len(rpc_calls) == 1
    assert rpc_calls[0][2]["p_order_id"] == "cs_test_12345"
    assert rpc_calls[0][2]["p_note"] == "pro-usd-29"

    # 2. Buyer received plaintext key via Resend
    resend_calls = [c for c in calls if "api.resend.com" in c[0]]
    assert len(resend_calls) == 2
    buyer_mail = resend_calls[0][2]
    assert buyer_mail["to"] == ["alice@acme.com"]
    assert fake_issued_key in buyer_mail["html"]

    # 3. Public GitHub issue NEVER contains plaintext key or unmasked email
    gh_calls = [c for c in calls if "/issues" in c[0]]
    assert len(gh_calls) == 1
    issue_body = gh_calls[0][2]["body"]
    assert fake_issued_key not in issue_body
    assert "alice@acme.com" not in issue_body
    assert "a***@acme.com" in issue_body
    assert "issued_and_emailed" in issue_body
