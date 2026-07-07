// Thin, type-safe wrapper over the GA4 gtag installed in index.html
// (G-0F5GCX6MCV). Fires custom conversion events so the funnel is visible in
// GA — read daily by the analytics-daily GitHub Actions sweep.
//
// No-ops safely when gtag is absent (SSR/prerender, ad-blockers, tests), so
// call sites never need to guard.

type EventParams = Record<string, string | number | boolean | undefined>;

declare global {
  interface Window {
    gtag?: (command: "event", eventName: string, params?: EventParams) => void;
  }
}

export function trackEvent(name: string, params?: EventParams): void {
  if (typeof window === "undefined" || typeof window.gtag !== "function")
    return;
  window.gtag("event", name, params);
}
