// Thin, type-safe wrapper over GA4 gtag (G-0F5GCX6MCV) and PostHog (/ph.js).
// Fires custom conversion events so the funnel is visible in both GA and
// PostHog — read daily by the analytics-daily GitHub Actions sweep.
//
// No-ops safely when gtag/posthog are absent (SSR/prerender, ad-blockers, tests),
// so call sites never need to guard.

type EventParams = Record<string, string | number | boolean | undefined>;

declare global {
  interface Window {
    gtag?: (command: "event", eventName: string, params?: EventParams) => void;
    posthog?: {
      capture?: (eventName: string, params?: EventParams) => void;
    };
  }
}

export function trackEvent(name: string, params?: EventParams): void {
  if (typeof window === "undefined") return;
  if (typeof window.gtag === "function") {
    window.gtag("event", name, params);
  }
  if (typeof window.posthog?.capture === "function") {
    window.posthog.capture(name, params);
  }
}
