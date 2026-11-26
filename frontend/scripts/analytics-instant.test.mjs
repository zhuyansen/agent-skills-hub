// Checkout clicks go to PostHog at once, with the page they came from; other events stay batched.
// 2026-11-26: the first early-bird Pro buyer's /pro/ pageview and pro_checkout_click never
// arrived (mobile, checkout opens in a new tab, the batched queue was never sent).
import { test, beforeEach } from "node:test";
import assert from "node:assert/strict";

const calls = [];
beforeEach(() => {
  calls.length = 0;
  globalThis.window = { location: { pathname: "/pro/" }, posthog: { capture: (...args) => calls.push(args) } };
});
const { trackEvent, INSTANT_EVENTS } = await import("../src/lib/analytics.ts");

test("a checkout click is sent at once and names its page", () => {
  trackEvent("pro_checkout_click", { sku: "pro", price: "$29/yr" });
  assert.deepEqual(calls, [["pro_checkout_click", { sku: "pro", price: "$29/yr", from_path: "/pro/" },
    { transport: "sendBeacon", send_instantly: true }]]);
});

test("every checkout button the site has is on the list", () => {
  for (const name of ["pro_checkout_click", "cigate_checkout_click", "fasttrack_checkout_click", "audit_pro_upsell_click"]) {
    assert.ok(INSTANT_EVENTS.has(name), name);
  }
});

test("other events keep PostHog's batching", () => {
  trackEvent("pro_search_run", { results: 3 });
  assert.deepEqual(calls, [["pro_search_run", { results: 3 }]]);
});
