/**
 * USD self-serve Stripe Checkout config + fallback lead helpers.
 *
 * Payment Link URLs are read from Vite env vars (set in GitHub Actions repo
 * variables `VITE_STRIPE_*_PAYMENT_LINK`, never hardcoded to a foreign/CNY URL).
 * When a Payment Link is not yet configured in the build environment, UI cards
 * capture the buyer's email + repo/team context directly into `enterprise_leads`
 * via `submitEnterpriseLead` so purchase intent is never dropped.
 */

export const USD_PRICING = {
  proEarly: "$29/yr",
  proStandard: "$49/yr",
  fastTrack: "$49",
  ciGate: "$49/mo",
} as const;

export const CHECKOUT_LINKS = {
  proStandard: (import.meta.env.VITE_STRIPE_PRO_STANDARD_PAYMENT_LINK || "").trim(),
  pro: (import.meta.env.VITE_STRIPE_PRO_PAYMENT_LINK || "").trim(),
  fasttrack: (import.meta.env.VITE_STRIPE_FASTTRACK_PAYMENT_LINK || "").trim(),
  cigate: (import.meta.env.VITE_STRIPE_CIGATE_PAYMENT_LINK || "").trim(),
} as const;

export function sanitizeStripeRef(raw: string, prefix?: string): string {
  const combined = prefix ? `${prefix}--${raw}` : raw;
  return combined.replace(/[^a-zA-Z0-9_-]/g, "--").slice(0, 200);
}

export function buildStripeCheckoutUrl(
  baseUrl: string,
  opts?: { clientReferenceId?: string; prefilledEmail?: string },
): string {
  const trimmed = baseUrl.trim();
  if (!trimmed) return "";
  const params = new URLSearchParams();
  if (opts?.clientReferenceId) {
    params.set("client_reference_id", opts.clientReferenceId.slice(0, 200));
  }
  if (opts?.prefilledEmail?.trim()) {
    params.set("prefilled_email", opts.prefilledEmail.trim());
  }
  const qs = params.toString();
  if (!qs) return trimmed;
  const sep = trimmed.includes("?") ? "&" : "?";
  return `${trimmed}${sep}${qs}`;
}
