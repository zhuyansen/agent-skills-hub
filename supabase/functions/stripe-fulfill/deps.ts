/** The real outside calls behind process.ts, configured from the function's secrets. */
import { createHash } from "node:crypto";
import type { Deps, KeyResult } from "./process.ts";
import { EARLY_BIRD_LINK, splitClientRef, type Session, type Sku } from "./fulfil.ts";

const env = (name: string, fallback = "") => Deno.env.get(name) ?? fallback;
const REPO = env("GH_REPO", "zhuyansen/agent-skills-hub");
const POSTHOG_KEY = env("POSTHOG_PROJECT_KEY", "phc_wCjMwyvaJQAHodWWKMeBWxoCmwo8puNJdyxKtomET8j5");
const POSTHOG_URL = "https://us.i.posthog.com/capture/";
const ISSUE_PAGE = 100;

async function json(url: string, init: RequestInit): Promise<Record<string, unknown> | Record<string, unknown>[]> {
  const res = await fetch(url, { ...init, headers: { "User-Agent": "AgentSkillsHub/1.0", ...init.headers } });
  if (!res.ok) throw new Error(`${new URL(url).host} answered ${res.status}`);
  const text = await res.text();
  return text.trim() ? JSON.parse(text) : {};
}

const github = (path: string, init: RequestInit = {}) => json(`https://api.github.com/repos/${REPO}${path}`, {
  ...init, headers: { Authorization: `Bearer ${env("GH_TOKEN")}`, Accept: "application/vnd.github+json", "Content-Type": "application/json" },
});

/** As poll_stripe.existing_order_ids: any issue labelled `order` whose body names the session. */
async function orderRecorded(sessionId: string): Promise<boolean> {
  for (let page = 1; ; page++) {
    const batch = await github(`/issues?labels=order&state=all&per_page=${ISSUE_PAGE}&page=${page}`) as { body?: string }[];
    if (batch.some((i) => (i.body || "").includes(sessionId))) return true;
    if (batch.length < ISSUE_PAGE) return false;
  }
}

async function issueKey(email: string, note: string, orderId: string): Promise<KeyResult> {
  const anon = env("SUPABASE_ANON_KEY");
  return await json(`${env("SUPABASE_URL")}/rest/v1/rpc/issue_pro_key`, {
    method: "POST",
    headers: { apikey: anon, Authorization: `Bearer ${anon}`, "Content-Type": "application/json" },
    body: JSON.stringify({ p_secret: env("AGENTSKILLSHUB_ISSUE_SECRET"), p_email: email, p_note: note, p_order_id: orderId }),
  }) as KeyResult;
}

async function sendEmail(to: string, subject: string, html: string): Promise<boolean> {
  try {
    await json("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${env("RESEND_API_KEY")}`, "Content-Type": "application/json" },
      body: JSON.stringify({ from: env("EMAIL_FROM"), to: [to], subject, html }),
    });
    return true;
  } catch (err) {
    console.warn(`email failed: ${(err as Error).message}`);
    return false;
  }
}

/** Early-bird keys issued so far, counted from member_keys (null when the count fails). */
async function earlyBirdSold(): Promise<number | null> {
  const service = env("SUPABASE_SERVICE_ROLE_KEY");
  const res = await fetch(`${env("SUPABASE_URL")}/rest/v1/member_keys?select=order_id&note=eq.pro-usd-29`, {
    method: "HEAD", headers: { apikey: service, Authorization: `Bearer ${service}`, Prefer: "count=exact", Range: "0-0" },
  });
  const total = Number(res.headers.get("content-range")?.split("/")[1]);
  return res.ok && Number.isFinite(total) ? total : null;
}

async function createIssue(title: string, body: string): Promise<string> {
  const out = await github("/issues", { method: "POST", body: JSON.stringify({ title, body, labels: ["order"] }) }) as { html_url?: string };
  return out.html_url || "";
}

/** The poll's purchase_completed, byte for byte in its properties; best-effort. */
async function capturePurchase(s: Session, sku: Sku): Promise<boolean> {
  const [, phId] = splitClientRef(s.client_reference_id);
  const cents = Number(s.amount_total || 0);
  const properties = {
    sku, revenue: Math.round(cents) / 100, amount_cents: cents, currency: (s.currency || "usd").toUpperCase(),
    is_early_bird: s.payment_link === EARLY_BIRD_LINK, attributed_to_session: Boolean(phId),
    source: "stripe_s2s", $geoip_disable: true, $insert_id: s.id,
  };
  const distinctId = phId || `stripe_${createHash("sha256").update(s.id).digest("hex").slice(0, 16)}`;
  const timestamp = new Date((s.created || Date.now() / 1000) * 1000).toISOString();
  try {
    await json(POSTHOG_URL, { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: POSTHOG_KEY, event: "purchase_completed", distinct_id: distinctId, timestamp, properties }) });
    return true;
  } catch (err) {
    console.warn(`PostHog capture failed for ${s.id}: ${(err as Error).message}`);
    return false;
  }
}

export const liveDeps: Deps = {
  orderRecorded, issueKey, sendEmail, earlyBirdSold, createIssue, capturePurchase,
  alertEmail: env("ALERT_EMAIL", "m17551076169@gmail.com"),
};
