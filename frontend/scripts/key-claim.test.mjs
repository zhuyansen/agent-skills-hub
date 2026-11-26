// The success page gets the key it paid for even when the buyer's email never arrives
// (2026-11-26: the first early-bird buyer's email domain stopped resolving).
import { test } from "node:test";
import assert from "node:assert/strict";
const { claimOnce, pollClaim, isSessionId, MAX_POLLS } = await import("../src/lib/keyClaim.ts");

const SID = "cs_live_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6";
const reply = (body, ok = true) => async () => ({ ok, json: async () => body });

test("only a Checkout Session id is a claim", () => {
  assert.ok(isSessionId(SID));
  for (const bad of [null, "", "cs_live_short", "pi_3Uftbt", `${SID}&x=1`]) assert.ok(!isSessionId(bad), String(bad));
});

test("ready, invalid and anything else (pending, errors, garbage) are told apart", async () => {
  assert.deepEqual(await claimOnce(SID, reply({ status: "ready", key: "ash_pro_k", note: "pro-usd-29" })),
    { status: "ready", key: "ash_pro_k", note: "pro-usd-29" });
  assert.deepEqual(await claimOnce(SID, reply({ status: "invalid" })), { status: "invalid" });
  assert.deepEqual(await claimOnce(SID, reply({ hello: 1 })), { status: "pending" });
  assert.deepEqual(await claimOnce(SID, async () => { throw new Error("offline"); }), { status: "pending" });
});

test("the page keeps asking until the webhook has stored the key", async () => {
  let calls = 0;
  const fetcher = async () => ({ json: async () => (++calls < 3 ? { status: "pending" } : { status: "ready", key: "k", note: "n" }) });
  const r = await pollClaim(SID, () => false, async () => {}, fetcher);
  assert.equal(r.status, "ready");
  assert.equal(calls, 3);
});

test("it gives up after MAX_POLLS and says so", async () => {
  let calls = 0;
  const r = await pollClaim(SID, () => false, async () => {}, async () => ({ json: async () => (calls++, { status: "pending" }) }));
  assert.deepEqual(r, { status: "timeout" });
  assert.equal(calls, MAX_POLLS);
});
