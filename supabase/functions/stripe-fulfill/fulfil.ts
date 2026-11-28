/**
 * Instant fulfilment of Agent Skills Hub orders, from Stripe's webhook.
 *
 * Until 2026-11-26 orders were fulfilled only by ops/stripe/poll_stripe.py on a GitHub cron
 * "every 30 minutes". GitHub runs scheduled jobs late: the first early-bird Pro order (paid
 * 03:44 UTC) got its key at 04:19, and the poll before it had last run at 22:26 the day before.
 * Stripe now calls this function the moment a checkout completes. The poll stays as the
 * fallback and leaves orders younger than WEBHOOK_WINDOW_SECONDS to this function.
 *
 * Same rules and order as poll_stripe.process_session, so either path records an order the
 * same way: key (issue_pro_key, idempotent per order), buyer email, operator alert, GitHub
 * issue labelled `order` (what both paths treat as "done"), then one PostHog purchase.
 * The subscription expiry is left to the poll, which syncs every subscription on each run.
 */

export type Session = {
  id: string;
  livemode?: boolean;
  payment_status?: string;
  payment_link?: string | null;
  client_reference_id?: string | null;
  metadata?: Record<string, string> | null;
  customer_details?: { email?: string | null } | null;
  amount_total?: number | null;
  currency?: string | null;
  created?: number;
};

export type Sku = "pro" | "cigate" | "fasttrack" | "sponsor" | "deep_audit";

export const EARLY_BIRD_LINK = "plink_1UchmqC0OZ4h2np2kGFSR5Qr";
export const EARLY_BIRD_LIMIT = 100;
export const WEBHOOK_WINDOW_SECONDS = 600;
/** Stripe's own default tolerance for a signed timestamp. */
export const SIGNATURE_TOLERANCE_SECONDS = 300;

export const PAYMENT_LINK_SKUS: Record<string, Sku> = {
  "plink_1Uci7YC0OZ4h2np2hIc1ZLGo": "pro", // $49/yr standard
  [EARLY_BIRD_LINK]: "pro", // $29/yr early bird
  "plink_1UchmwC0OZ4h2np2J1kAJkOW": "fasttrack", // $49 one-time
  "plink_1UchmyC0OZ4h2np253XNPeHj": "cigate", // $49/mo
};

const PREFIXES: [string, Sku, string][] = [
  ["pro--", "pro", "pro-member"],
  ["cigate--", "cigate", "team-ci-gate"],
  ["fasttrack--", "fasttrack", "(not provided)"],
  ["sponsor--", "sponsor", "homepage-rail"],
];
const META_SKUS = new Set(["pro", "fasttrack", "cigate", "sponsor", "deep_audit"]);

/** "pro--web__ph_<id>" -> ["pro--web", "<id>"]. */
export function splitClientRef(raw: string | null | undefined): [string, string] {
  const ref = (raw || "").trim();
  const at = ref.indexOf("__ph_");
  return at < 0 ? [ref, ""] : [ref.slice(0, at).trim(), ref.slice(at + 5).trim()];
}

/** The Stripe account also sells other products: only sessions that are provably ours. */
export function isOurs(s: Session): boolean {
  const [ref] = splitClientRef(s.client_reference_id);
  return Boolean(s.payment_link && s.payment_link in PAYMENT_LINK_SKUS)
    || s.metadata?.source === "agentskillshub"
    || PREFIXES.some(([p]) => ref.startsWith(p));
}

/** [sku, target] as poll_stripe.classify_session, or null for another product's session. */
export function classify(s: Session): [Sku, string] | null {
  if (!isOurs(s)) return null;
  const [ref] = splitClientRef(s.client_reference_id);
  const metaSku = String(s.metadata?.sku || "").toLowerCase();
  if (META_SKUS.has(metaSku)) {
    const target = ref.includes("--") ? ref.split("--").slice(1).join("--").replaceAll("--", "/") : (ref || "(self-serve)");
    return [metaSku as Sku, target];
  }
  for (const [prefix, sku, fallback] of PREFIXES) {
    if (ref.startsWith(prefix)) return [sku, ref.slice(prefix.length).replaceAll("--", "/") || fallback];
  }
  const linkSku = s.payment_link ? PAYMENT_LINK_SKUS[s.payment_link] : undefined;
  if (!linkSku) return null;
  const fallback = PREFIXES.find(([, sku]) => sku === linkSku)?.[2] ?? "";
  return [linkSku, ref ? ref.replaceAll("--", "/") : fallback];
}

/** The member_keys note issue_pro_key records, as poll_stripe.issue_member_key picks it. */
export function keyNote(s: Session, sku: Sku): string {
  if (sku === "cigate") return "cigate-team-49";
  const early = s.payment_link === EARLY_BIRD_LINK || (!s.payment_link && (s.amount_total || 0) <= 3000);
  return early ? "pro-usd-29" : "pro-usd-49";
}

export function maskEmail(email: string): string {
  if (!email.includes("@")) return "(none)";
  const [local, domain] = email.split("@", 2);
  return `${local.slice(0, 1)}***@${domain}`;
}

export function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);
}

const HEX = (bytes: ArrayBuffer) => [...new Uint8Array(bytes)].map((b) => b.toString(16).padStart(2, "0")).join("");

/** Stripe-Signature check: "t=<unix>,v1=<hex hmac of `${t}.${body}`>", within the tolerance. */
export async function verifySignature(secret: string, header: string | null, body: string, now: number): Promise<boolean> {
  if (!secret || !header) return false;
  const parts = header.split(",").map((p) => p.split("=", 2) as [string, string]);
  const t = Number(parts.find(([k]) => k === "t")?.[1]);
  const signatures = parts.filter(([k]) => k === "v1").map(([, v]) => v);
  if (!Number.isFinite(t) || Math.abs(now - t) > SIGNATURE_TOLERANCE_SECONDS || !signatures.length) return false;
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const expected = HEX(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(`${t}.${body}`)));
  return signatures.some((sig) => timingSafeEqual(sig, expected));
}

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}
