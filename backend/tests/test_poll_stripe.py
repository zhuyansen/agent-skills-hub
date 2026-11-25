"""Unit tests for ops/stripe/poll_stripe.py multi-SKU fulfillment & redaction."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest

POLL_PATH = Path(__file__).resolve().parents[2] / "ops" / "stripe" / "poll_stripe.py"
SPEC = importlib.util.spec_from_file_location("poll_stripe", POLL_PATH)
assert SPEC and SPEC.loader
poll_stripe = importlib.util.module_from_spec(SPEC)
sys.modules["poll_stripe"] = poll_stripe
SPEC.loader.exec_module(poll_stripe)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Every outbound call in poll_stripe goes through http_json. A test that does not stub it
    fails here instead of reaching Stripe, Resend, GitHub or the live PostHog project: from
    2026-11-18 to 11-25 each local run of this file posted a fake $0 `purchase_completed`."""
    def refuse(url, *args, **kwargs):
        # pytest.fail raises a BaseException: send_posthog_purchase's best-effort
        # `except Exception` would swallow an AssertionError and let the test pass.
        pytest.fail(f"unexpected network call in a unit test: {url}")
    monkeypatch.setattr(poll_stripe, "http_json", refuse)


def record_http(monkeypatch, replies=None):
    """Stub http_json; return the list of (url, body) it receives. `replies` maps a URL suffix to a reply."""
    calls = []
    def fake_http(url, headers, data=None, method="GET"):
        calls.append((url, json.loads(data.decode()) if data else None))
        return next((r for suffix, r in (replies or {}).items() if url.endswith(suffix)), {})
    monkeypatch.setattr(poll_stripe, "http_json", fake_http)
    return calls


def live_session(**extra):
    return {"id": "cs_live_a1", "livemode": True, "amount_total": 4900, "currency": "usd",
            "client_reference_id": "fasttrack--owner--repo", **extra}


def test_classify_session_skus():
    assert poll_stripe.classify_session({"client_reference_id": "pro--hub-member"}) == ("pro", "hub-member")
    assert poll_stripe.classify_session({"client_reference_id": "cigate--acme--skills"}) == ("cigate", "acme/skills")
    assert poll_stripe.classify_session({"client_reference_id": "fasttrack--foo--bar"}) == ("fasttrack", "foo/bar")
    assert poll_stripe.classify_session({"client_reference_id": "owner--repo"}) is None
    assert poll_stripe.classify_session({"mode": "subscription"}) is None


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


def test_standard_link_classified():
    assert poll_stripe.classify_session({"payment_link": "plink_1Uci7YC0OZ4h2np2hIc1ZLGo"}) == ("pro", "pro-member")


def test_subscription_periods_and_cancellation():
    from datetime import datetime
    def stamp(sub):
        return datetime.fromisoformat(poll_stripe.subscription_expiry(sub)).timestamp()
    sub = {"status": "active", "items": {"data": [{"current_period_start": 1800000000, "current_period_end": 1802592000}]}}
    assert stamp(sub) == 1802592000 + poll_stripe.GRACE_SECONDS
    assert stamp(dict(sub, cancel_at_period_end=True)) == 1802592000
    assert stamp(dict(sub, cancel_at=1802000000)) == 1802000000
    assert stamp(dict(sub, status="past_due")) == 1800000000 + poll_stripe.GRACE_SECONDS
    assert stamp(dict(sub, status="canceled", ended_at=1801000000)) == 1801000000
    assert stamp({"status": "active", "current_period_end": 1802592000}) == 1802592000 + poll_stripe.GRACE_SECONDS


def test_missing_subscription_period_fails_closed():
    import pytest
    with pytest.raises(ValueError):
        poll_stripe.subscription_expiry({"status": "active"})


def test_stripe_pagination_includes_old_sessions(monkeypatch):
    urls = []
    def fake_http(url, headers):
        urls.append(url)
        if len(urls) == 1:
            return {"data": [{"id": "cs_old", "created": 1, "payment_status": "paid"}], "has_more": True}
        return {"data": [{"id": "cs_new", "payment_status": "paid"}], "has_more": False}
    monkeypatch.setattr(poll_stripe, "http_json", fake_http)
    assert len(poll_stripe.stripe_sessions()) == 2
    assert "starting_after=cs_old" in urls[1]
    assert "created" not in urls[0]


def test_sync_ignores_other_products(monkeypatch):
    bodies = []
    def fake_http(url, headers, data, method):
        body = json.loads(data)
        bodies.append(body)
        return {"status": "ok", "received": len(body["p_items"]), "updated": 1}
    monkeypatch.setattr(poll_stripe, "http_json", fake_http)
    sub = {"status": "active", "current_period_end": 1802592000}
    poll_stripe.sync_subscriptions([
        {"id": "cs_ours", "mode": "subscription", "client_reference_id": "cigate--team", "subscription": sub},
        {"id": "cs_other", "mode": "subscription", "subscription": sub},
    ])
    assert [i["order_id"] for i in bodies[0]["p_items"]] == ["cs_ours"]


def test_old_ticketed_order_still_synced(monkeypatch):
    old = {"id": "cs_old", "created": 1, "client_reference_id": "pro--old"}
    synced = []
    monkeypatch.setattr(poll_stripe, "STRIPE_KEY", "test")
    monkeypatch.setattr(poll_stripe, "stripe_sessions", lambda: [old])
    monkeypatch.setattr(poll_stripe, "existing_order_ids", lambda: {"cs_old"})
    monkeypatch.setattr(poll_stripe, "sync_subscriptions", lambda sessions: synced.extend(sessions))
    monkeypatch.setattr(poll_stripe, "process_session", lambda s: (_ for _ in ()).throw(AssertionError("old order replayed")))
    assert poll_stripe.main() == 0
    assert synced == [old]


def test_alert_failure_does_not_mark_order_done(monkeypatch):
    import pytest
    monkeypatch.setattr(poll_stripe, "issue_member_key", lambda *a: None)
    monkeypatch.setattr(poll_stripe, "sync_subscriptions", lambda *a: None)
    monkeypatch.setattr(poll_stripe, "send_alert", lambda *a: (_ for _ in ()).throw(TimeoutError()))
    monkeypatch.setattr(poll_stripe, "create_issue", lambda *a: (_ for _ in ()).throw(AssertionError("marked done")))
    with pytest.raises(TimeoutError):
        poll_stripe.process_session({"id": "cs_test", "client_reference_id": "fasttrack--repo"})


def test_discounted_standard_price_not_counted_as_early(monkeypatch):
    bodies = []
    monkeypatch.setattr(poll_stripe, "SUPABASE_URL", "https://example.test")
    monkeypatch.setattr(poll_stripe, "SUPABASE_ANON_KEY", "test")
    monkeypatch.setattr(poll_stripe, "ISSUE_SECRET", "test")
    def fake_http(url, headers, data, method):
        bodies.append(json.loads(data))
        return {"status": "already_issued"}
    monkeypatch.setattr(poll_stripe, "http_json", fake_http)
    poll_stripe.issue_member_key({"id": "cs_discount", "payment_link": "plink_1Uci7YC0OZ4h2np2hIc1ZLGo", "amount_total": 2400}, "pro", "a@example.com")
    assert bodies[0]["p_note"] == "pro-usd-49"


def test_test_mode_session_never_reaches_posthog():
    # Unit-test fixtures and Stripe test-mode sessions carry no livemode=True, so they are never revenue.
    assert poll_stripe.send_posthog_purchase({"id": "cs_test", "client_reference_id": "fasttrack--repo"}, "fasttrack") is False
    assert poll_stripe.send_posthog_purchase({"id": "cs_test_a1", "livemode": False}, "pro") is False


def test_live_purchase_reported_once_after_the_order_is_recorded(monkeypatch):
    monkeypatch.setattr(poll_stripe, "RESEND_KEY", "re_test")
    monkeypatch.setattr(poll_stripe, "EMAIL_FROM", "hub@agentskillshub.top")
    monkeypatch.setattr(poll_stripe, "sync_subscriptions", lambda *a: None)
    calls = record_http(monkeypatch, {"/issues": {"html_url": "https://github.com/o/r/issues/1"}})
    poll_stripe.process_session(live_session())
    urls = [u for u, _ in calls]
    captures = [i for i, u in enumerate(urls) if u == poll_stripe.POSTHOG_CAPTURE_URL]
    issue = next(i for i, u in enumerate(urls) if u.endswith("/issues"))
    assert len(captures) == 1 and captures[0] > issue
    props = calls[captures[0]][1]["properties"]
    assert props["$insert_id"] == "cs_live_a1" and props["revenue"] == 49.0


def test_failed_alert_sends_no_purchase_event(monkeypatch):
    # No issue yet means the next run retries this order; reporting it now would count it twice.
    calls = record_http(monkeypatch)
    monkeypatch.setattr(poll_stripe, "sync_subscriptions", lambda *a: None)
    monkeypatch.setattr(poll_stripe, "send_alert", lambda *a: (_ for _ in ()).throw(TimeoutError()))
    with pytest.raises(TimeoutError):
        poll_stripe.process_session(live_session())
    assert poll_stripe.POSTHOG_CAPTURE_URL not in [u for u, _ in calls]
