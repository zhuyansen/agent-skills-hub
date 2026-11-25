"""PostHog Query API (HogQL) fetcher — replaces Plausible and adds product-funnel + dimensional breakdowns.

Credentials (env vars or local files, gitignored):
  POSTHOG_API_KEY     (or ops/posthog/.api_key)    — Personal API Key (phx_..., scope: query:read)
  POSTHOG_PROJECT_ID  (or ops/posthog/.project_id) — Numeric project ID from PostHog Project Settings
  POSTHOG_HOST        (optional, default https://us.posthog.com)

Usage:
  python ops/posthog/fetch_posthog.py dump [--days 28]
"""
import json
import os
import sys
import time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def _read_cred(env_name, filename, default=""):
    val = (os.environ.get(env_name) or "").strip()
    if val:
        return val
    p = os.path.join(HERE, filename)
    if os.path.exists(p):
        return open(p).read().strip()
    return default


API_KEY = _read_cred("POSTHOG_API_KEY", ".api_key")
PROJECT_ID = _read_cred("POSTHOG_PROJECT_ID", ".project_id")
HOST = _read_cred("POSTHOG_HOST", ".host", "https://us.posthog.com").rstrip("/")

# Only Stripe live-mode orders are revenue: ops/stripe/poll_stripe.py sets $insert_id to the
# Checkout Session id, which starts with cs_live_ in live mode. From 2026-11-18 to 11-25 a unit
# test posted 12 fake `cs_test` purchases to this project; they leave the 28-day window ~12-23.
LIVE_PURCHASES_ONLY = (
    "(event != 'purchase_completed' "
    "OR startsWith(toString(properties.$insert_id), 'cs_live_'))"
)


def arg(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


def hogql(sess, query, name="query"):
    url = f"{HOST}/api/projects/{PROJECT_ID}/query/"
    body = {
        "query": {
            "kind": "HogQLQuery",
            "query": query,
        },
        "name": f"daily_sweep_{name}",
    }
    last = None
    for attempt in range(3):
        try:
            r = sess.post(url, json=body, timeout=60)
            if r.status_code in (429, 502, 503, 504) and attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            r.raise_for_status()
            data = r.json()
            cols = data.get("columns") or []
            rows = data.get("results") or []
            return [dict(zip(cols, row)) for row in rows]
        except requests.exceptions.RequestException as exc:
            last = exc
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
    raise last


def save(name, data):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"{name}.json")
    with open(p, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"  → {p} ({len(data)} rows)")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "dump"
    days = arg("--days", 28)

    if not API_KEY or not PROJECT_ID:
        print("PostHog 未配置 (缺少 POSTHOG_API_KEY / POSTHOG_PROJECT_ID)，跳过抓取。")
        return

    sess = requests.Session()
    sess.headers["Authorization"] = f"Bearer {API_KEY}"

    if cmd not in ("dump", "overview", "sources", "pages", "dimensions", "funnel"):
        sys.exit(__doc__)

    if cmd in ("overview", "dump"):
        rows = hogql(
            sess,
            f"""
            SELECT
                toDate(timestamp) AS day,
                countIf(event = '$pageview') AS pageviews,
                uniqExact(distinct_id) AS visitors,
                uniqExact($session_id) AS sessions
            FROM events
            WHERE timestamp >= now() - INTERVAL {days} DAY
              AND event = '$pageview'
            GROUP BY day
            ORDER BY day ASC
            """,
            name="overview",
        )
        save("overview", rows)

    if cmd in ("sources", "dump"):
        rows = hogql(
            sess,
            f"""
            SELECT
                coalesce(nullIf(properties.utm_source, ''), nullIf(properties.$referring_domain, ''), '(direct)') AS source,
                coalesce(nullIf(properties.utm_medium, ''), if(properties.$referring_domain != '' AND properties.$referring_domain IS NOT NULL, 'referral', '(none)')) AS medium,
                uniqExact($session_id) AS sessions,
                uniqExact(distinct_id) AS visitors,
                countIf(event = '$pageview') AS pageviews
            FROM events
            WHERE timestamp >= now() - INTERVAL {days} DAY
              AND event = '$pageview'
            GROUP BY source, medium
            ORDER BY sessions DESC
            LIMIT 40
            """,
            name="sources",
        )
        save("sources", rows)

    if cmd in ("pages", "dump"):
        rows = hogql(
            sess,
            f"""
            SELECT
                coalesce(nullIf(properties.$pathname, ''), '/') AS pathname,
                count() AS pageviews,
                uniqExact(distinct_id) AS visitors,
                uniqExact($session_id) AS sessions
            FROM events
            WHERE timestamp >= now() - INTERVAL {days} DAY
              AND event = '$pageview'
            GROUP BY pathname
            ORDER BY pageviews DESC
            LIMIT 30
            """,
            name="pages",
        )
        save("pages", rows)

    if cmd in ("dimensions", "dump"):
        # Growth breakdown matrix (diagram #11): first-touch entry_page_type x device x country
        # plus S2S purchase buyers & revenue joined by distinct_id.
        rows = hogql(
            sess,
            f"""
            WITH
                purchases AS (
                    SELECT
                        distinct_id,
                        count() AS orders,
                        sum(toFloatOrZero(toString(properties.revenue))) AS revenue_usd
                    FROM events
                    WHERE timestamp >= now() - INTERVAL {days} DAY
                      AND event IN ('purchase_completed', 'b2b_deal_won')
                      AND {LIVE_PURCHASES_ONLY}
                    GROUP BY distinct_id
                )
            SELECT
                coalesce(nullIf(properties.entry_page_type, ''), nullIf(properties.page_type, ''), 'unknown') AS page_type,
                coalesce(nullIf(properties.$device_type, ''), 'unknown') AS device,
                coalesce(nullIf(properties.$geoip_country_code, ''), '??') AS country,
                uniqExact($session_id) AS sessions,
                uniqExactIf($session_id, event = 'audit_run') AS audit_sessions,
                uniqExactIf($session_id, event IN ('enterprise_cta_click', 'enterprise_lead_submitted', 'pro_checkout_click', 'cigate_checkout_click', 'fasttrack_checkout_click', 'ci_gate_hero_cta', 'org_audit_pro_click')) AS commercial_sessions,
                uniqExactIf($session_id, event IN ('install_command_copied', 'copy_install')) AS install_copy_sessions,
                uniqExactIf(events.distinct_id, p.orders > 0) AS buyers,
                round(sumIf(p.revenue_usd, p.orders > 0) / greatest(uniqExactIf(events.distinct_id, p.orders > 0), 1), 2) AS avg_rev_hint
            FROM events
            LEFT JOIN purchases AS p ON events.distinct_id = p.distinct_id
            WHERE timestamp >= now() - INTERVAL {days} DAY
              AND event IN (
                '$pageview', 'audit_run', 'enterprise_cta_click',
                'enterprise_lead_submitted', 'pro_checkout_click',
                'cigate_checkout_click', 'fasttrack_checkout_click',
                'ci_gate_hero_cta', 'org_audit_pro_click',
                'install_command_copied', 'copy_install'
              )
            GROUP BY page_type, device, country
            HAVING sessions >= 5 OR buyers > 0
            ORDER BY buyers DESC, commercial_sessions DESC, audit_sessions DESC, sessions DESC
            LIMIT 50
            """,
            name="dimensions",
        )
        save("dimensions", rows)

    if cmd in ("funnel", "dump"):
        rows = hogql(
            sess,
            f"""
            SELECT
                event,
                count() AS events_28d,
                uniqExact(distinct_id) AS users_28d,
                countIf(timestamp >= now() - INTERVAL 7 DAY) AS events_7d,
                uniqExactIf(distinct_id, timestamp >= now() - INTERVAL 7 DAY) AS users_7d,
                round(sumIf(toFloatOrZero(toString(properties.revenue)), event IN ('purchase_completed', 'b2b_deal_won')), 2) AS revenue_28d_usd
            FROM events
            WHERE timestamp >= now() - INTERVAL {days} DAY
              AND event IN (
                '$pageview',
                'hero_guide_click',
                'install_command_copied',
                'copy_install',
                'newsletter_subscribe',
                'audit_run',
                'audit_lead_viewed',
                'audit_lead_started',
                'audit_lead_attempt',
                'audit_lead_submitted',
                'audit_pro_upsell_click',
                'audit_cigate_upsell_click',
                'free_tier_click',
                'enterprise_cta_click',
                'enterprise_form_viewed',
                'enterprise_form_started',
                'enterprise_lead_attempt',
                'enterprise_lead_submitted',
                'pro_checkout_click',
                'cigate_checkout_click',
                'fasttrack_checkout_click',
                'ci_gate_hero_cta',
                'ci_gate_copy_snippet',
                'org_audit_run',
                'org_audit_pro_click',
                'purchase_completed',
                'b2b_deal_won'
              )
              AND {LIVE_PURCHASES_ONLY}
            GROUP BY event
            ORDER BY users_28d DESC
            """,
            name="funnel",
        )
        save("funnel", rows)


if __name__ == "__main__":
    main()
