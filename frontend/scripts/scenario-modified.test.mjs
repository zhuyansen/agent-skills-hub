/**
 * scripts/scenario-modified.mjs: a /best/ page is dated the day its fingerprint changes,
 * keeps its date while it holds, and starts from its declared date when there is no
 * live record. No network: fetch is stubbed.
 *
 * Run: node --test scripts/scenario-modified.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  declaredDateIn, fingerprint, loadLiveModified, nextModified,
} from "./scenario-modified.mjs";

const TODAY = "2026-11-02";
const seed = (slug) => ({ "anti-slop": "2026-10-07" })[slug] ?? null;

test("fingerprint ignores key order but not values", () => {
  assert.equal(fingerprint({ a: 1, b: [2, { c: 3, d: 4 }] }), fingerprint({ b: [2, { d: 4, c: 3 }], a: 1 }));
  assert.notEqual(fingerprint({ a: 1 }), fingerprint({ a: 2 }));
});

test("a page whose fingerprint holds keeps its date", () => {
  const live = { "anti-slop": { fp: "aaa", date: "2026-10-31" } };
  assert.deepEqual(nextModified(live, { "anti-slop": "aaa" }, TODAY, seed)["anti-slop"],
    { fp: "aaa", date: "2026-10-31" });
});

test("a changed page and a new page are dated today", () => {
  const live = { "anti-slop": { fp: "aaa", date: "2026-10-31" } };
  const pages = nextModified(live, { "anti-slop": "bbb", "new-page": "ccc" }, TODAY, seed);
  assert.equal(pages["anti-slop"].date, TODAY);
  assert.equal(pages["new-page"].date, TODAY);
});

test("with no live record every page starts from its declared date", () => {
  const pages = nextModified(null, { "anti-slop": "aaa", "no-date": "bbb" }, TODAY, seed);
  assert.deepEqual(pages, { "anti-slop": { fp: "aaa", date: "2026-10-07" }, "no-date": { fp: "bbb", date: null } });
});

test("declaredDateIn picks the latest declared date and drops the build date", () => {
  const html = `{"lastReviewed": "2026-10-07"} {"dateModified":"${TODAY}"} {"dateModified":"2026-09-30"}`;
  assert.equal(declaredDateIn(html, TODAY), "2026-10-07");
  assert.equal(declaredDateIn(`{"dateModified":"${TODAY}"}`, TODAY), null);
});

const reply = (status, body) => ({ status, ok: status === 200, json: async () => body });
const noWait = async () => {};

test("loadLiveModified reads the published pages", async () => {
  const pages = { "anti-slop": { fp: "aaa", date: "2026-10-31" } };
  assert.deepEqual(await loadLiveModified("https://x.test", async () => reply(200, { version: 1, pages }), noWait), pages);
});

test("loadLiveModified is null when the site has no record yet", async () => {
  assert.equal(await loadLiveModified("https://x.test", async () => reply(404), noWait), null);
});

test("loadLiveModified retries a failing request, then gives up with null", async () => {
  let calls = 0;
  const failing = async () => { calls++; throw new Error("offline"); };
  assert.equal(await loadLiveModified("https://x.test", failing, noWait), null);
  assert.equal(calls, 3);
  calls = 0;
  const flaky = async () => (++calls < 2 ? reply(503) : reply(200, { pages: {} }));
  assert.deepEqual(await loadLiveModified("https://x.test", flaky, noWait), {});
});
