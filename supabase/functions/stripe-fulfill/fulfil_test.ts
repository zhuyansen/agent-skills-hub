// deno test supabase/functions/stripe-fulfill/
import { assert, assertEquals, assertRejects } from "jsr:@std/assert@1";
import { classify, EARLY_BIRD_LINK, keyNote, maskEmail, type Session, verifySignature } from "./fulfil.ts";
import { type Deps, processSession } from "./process.ts";

const SECRET = "whsec_test";
const NOW = 1_800_000_000;

async function sign(body: string, t = NOW, secret = SECRET): Promise<string> {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const mac = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(`${t}.${body}`));
  return `t=${t},v1=${[...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, "0")).join("")}`;
}

Deno.test("a body Stripe signed is accepted", async () => {
  assert(await verifySignature(SECRET, await sign("{}"), "{}", NOW));
});

Deno.test("a changed body, a wrong secret, an old timestamp or no header is refused", async () => {
  const header = await sign("{}");
  assert(!(await verifySignature(SECRET, header, '{"x":1}', NOW)));
  assert(!(await verifySignature("whsec_other", header, "{}", NOW)));
  assert(!(await verifySignature(SECRET, await sign("{}", NOW - 301), "{}", NOW)));
  assert(!(await verifySignature(SECRET, null, "{}", NOW)));
});

const order = (extra: Partial<Session> = {}): Session => ({
  id: "cs_live_a1", livemode: true, payment_status: "paid", payment_link: EARLY_BIRD_LINK,
  client_reference_id: "pro--web__ph_abc", customer_details: { email: "buyer@example.com" },
  amount_total: 2900, currency: "usd", created: NOW, ...extra,
});

Deno.test("sessions are classified as the poll classifies them", () => {
  assertEquals(classify(order()), ["pro", "web"]);
  assertEquals(classify(order({ client_reference_id: "cigate--acme--team", payment_link: null })), ["cigate", "acme/team"]);
  assertEquals(classify(order({ client_reference_id: null, payment_link: "plink_1UchmwC0OZ4h2np2J1kAJkOW" })), ["fasttrack", "(not provided)"]);
  assertEquals(classify(order({ client_reference_id: "x", metadata: { source: "agentskillshub", sku: "pro" } })), ["pro", "x"]);
});

Deno.test("another site's checkout on the shared Stripe account is not ours", () => {
  assertEquals(classify(order({ payment_link: "plink_someone_else", client_reference_id: "user_42" })), null);
});

Deno.test("the early-bird link records the $29 note", () => {
  assertEquals(keyNote(order(), "pro"), "pro-usd-29");
  assertEquals(keyNote(order({ payment_link: "plink_1Uci7YC0OZ4h2np2hIc1ZLGo", amount_total: 4900 }), "pro"), "pro-usd-49");
  assertEquals(keyNote(order(), "cigate"), "cigate-team-49");
  assertEquals(maskEmail("buyer@example.com"), "b***@example.com");
});

function stubDeps(over: Partial<Deps> = {}) {
  const calls: string[] = [];
  const deps: Deps = {
    orderRecorded: () => (calls.push("recorded?"), Promise.resolve(false)),
    issueKey: (_e, note, id) => (calls.push(`key ${note} ${id}`), Promise.resolve({ status: "issued", key: "ash_pro_X" })),
    storeClaim: (id, key, note) => (calls.push(`claim ${id} ${key} ${note}`), Promise.resolve(true)),
    sendEmail: (to, subject) => (calls.push(`mail ${to} ${subject}`), Promise.resolve(true)),
    alertEmail: "ops@example.com",
    earlyBirdSold: () => Promise.resolve(1),
    createIssue: (title) => (calls.push(`issue ${title}`), Promise.resolve("https://github.com/o/r/issues/9")),
    capturePurchase: () => (calls.push("posthog"), Promise.resolve(true)),
    ...over,
  };
  return { deps, calls };
}

Deno.test("a Pro order: key, buyer email, alert, issue, then one purchase event", async () => {
  const { deps, calls } = stubDeps();
  const out = await processSession(order(), deps);
  assertEquals(out, { done: true, sku: "pro", keyStatus: "issued_and_emailed", issueUrl: "https://github.com/o/r/issues/9" });
  assertEquals(calls, ["recorded?", "key pro-usd-29 cs_live_a1", "claim cs_live_a1 ash_pro_X pro-usd-29",
    "mail buyer@example.com Your Agent Skills Hub Pro Access Key",
    "mail ops@example.com 💰 29.00 USD [pro] 成交:web", "issue ⚡ Pro Membership — web", "posthog"]);
});

Deno.test("an order the poll or a retry already recorded is left alone", async () => {
  const { deps, calls } = stubDeps({ orderRecorded: () => Promise.resolve(true) });
  assertEquals(await processSession(order(), deps), { done: false, reason: "already_recorded" });
  assertEquals(calls, []);
});

Deno.test("test-mode, unpaid and other sites' sessions do nothing", async () => {
  const { deps, calls } = stubDeps();
  assertEquals((await processSession(order({ livemode: false }), deps)), { done: false, reason: "test_mode" });
  assertEquals((await processSession(order({ payment_status: "unpaid" }), deps)), { done: false, reason: "not_paid" });
  assertEquals((await processSession(order({ payment_link: "plink_x", client_reference_id: "u" }), deps)), { done: false, reason: "not_ours" });
  assertEquals(calls, []);
});

Deno.test("a key issued earlier (a retry) sends no second buyer email", async () => {
  const { deps, calls } = stubDeps({ issueKey: () => Promise.resolve({ status: "already_issued" }) });
  const out = await processSession(order(), deps);
  assert(out.done && out.keyStatus === "already_issued");
  assert(!calls.some((c) => c.startsWith("mail buyer@")));
});

Deno.test("a Fast-Track order gets no key", async () => {
  const { deps, calls } = stubDeps();
  const out = await processSession(order({ payment_link: "plink_1UchmwC0OZ4h2np2J1kAJkOW", client_reference_id: "fasttrack--o--r" }), deps);
  assert(out.done && out.keyStatus === "n/a");
  assert(!calls.some((c) => c.startsWith("key")));
});

Deno.test("a Sponsor rail order alerts ops and opens a placement issue with no key", async () => {
  const { deps, calls } = stubDeps();
  const out = await processSession(order({ payment_link: null, client_reference_id: "sponsor--Acme--left__ph_abc", amount_total: 6900 }), deps);
  assertEquals(out, { done: true, sku: "sponsor", keyStatus: "n/a", issueUrl: "https://github.com/o/r/issues/9" });
  assert(!calls.some((c) => c.startsWith("key")));
  assert(calls.includes("mail ops@example.com 💰 69.00 USD [sponsor] 成交:Acme/left"));
  assert(calls.includes("issue ⭐ Homepage Rail Sponsor — Acme/left"));
});

Deno.test("a failed alert stops before the issue and the purchase event, so Stripe's retry redoes them", async () => {
  const { deps, calls } = stubDeps({ sendEmail: (to) => Promise.resolve(to !== "ops@example.com") });
  await assertRejects(() => processSession(order(), deps));
  assert(!calls.some((c) => c.startsWith("issue") || c === "posthog"));
});

Deno.test("the key is kept for the success page even when the email fails", async () => {
  const { deps, calls } = stubDeps({ sendEmail: (to) => Promise.resolve(to === "ops@example.com") });
  const out = await processSession(order(), deps);
  assert(out.done && out.keyStatus === "issued_manual_email_needed");
  assert(calls.includes("claim cs_live_a1 ash_pro_X pro-usd-29"));
});

Deno.test("a sealed key opens with the same secret only", async () => {
  const { sealKey, openKey } = await import("../_shared/claim.ts");
  const secret = btoa(String.fromCharCode(...crypto.getRandomValues(new Uint8Array(32))));
  const other = btoa(String.fromCharCode(...crypto.getRandomValues(new Uint8Array(32))));
  const sealed = await sealKey("ash_pro_secret", secret);
  assertEquals(await openKey(sealed, secret), "ash_pro_secret");
  await assertRejects(() => openKey(sealed, other));
});

Deno.test("a key that could not be kept for the success page is called out in the alert and issue", async () => {
  const { deps } = stubDeps({ storeClaim: () => Promise.resolve(false) });
  const out = await processSession(order(), deps);
  assert(out.done && out.keyStatus === "issued_and_emailed+success_page_failed");
});
