// Thin, type-safe wrapper over GA4 gtag (G-0F5GCX6MCV) and PostHog (/ph.js).
// Fires custom conversion events so the funnel is visible in both GA and
// PostHog — read daily by the analytics-daily GitHub Actions sweep.
//
// No-ops safely when gtag/posthog are absent (SSR/prerender, ad-blockers, tests),
// so call sites never need to guard.

type EventParams = Record<string, string | number | boolean | undefined>;
type CaptureOptions = { transport?: "XHR" | "fetch" | "sendBeacon"; send_instantly?: boolean };

declare global {
  interface Window {
    gtag?: (command: "event", eventName: string, params?: EventParams) => void;
    posthog?: {
      capture?: (eventName: string, params?: EventParams, options?: CaptureOptions) => void;
      get_distinct_id?: () => string;
    };
  }
}

/** Clicks that send the visitor to Stripe or a sales form. PostHog batches events and sends
 *  them every few seconds; these open checkout in a new tab, and a phone suspends the tab left
 *  behind, so the batch never went out. On 2026-11-26 the first early-bird Pro buyer (mobile
 *  Brave) bought from /pro/, yet neither that pageview nor pro_checkout_click reached PostHog,
 *  only the server's purchase_completed. These go out at once, with the page they came from. */
export const INSTANT_EVENTS = new Set([
  "pro_checkout_click",
  "cigate_checkout_click",
  "fasttrack_checkout_click",
  "audit_pro_upsell_click",
  "audit_cigate_upsell_click",
  "org_audit_pro_click",
  "enterprise_cta_click",
  "ci_gate_hero_cta",
]);

const INSTANT: CaptureOptions = { transport: "sendBeacon", send_instantly: true };

export function trackEvent(name: string, params?: EventParams): void {
  if (typeof window === "undefined") return;
  const instant = INSTANT_EVENTS.has(name);
  if (typeof window.gtag === "function") {
    window.gtag("event", name, instant ? { ...params, transport_type: "beacon" } : params);
  }
  if (typeof window.posthog?.capture === "function") {
    if (instant) {
      // The pageview that led here may still be queued: name the page on the click itself.
      window.posthog.capture(name, { ...params, from_path: window.location.pathname }, INSTANT);
    } else {
      window.posthog.capture(name, params);
    }
  }
}
