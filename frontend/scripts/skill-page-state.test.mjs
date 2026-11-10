import { test } from "node:test";
import assert from "node:assert/strict";
import { loadingSkillPage, skillPageFor, skillPageReducer } from "../src/lib/skillPageState.mjs";

const run = (events, from) => events.reduce(skillPageReducer, from);
const A = "owner/a";
const B = "owner/b";

test("a loading page settles as ready, redirecting or failed", () => {
  const loading = loadingSkillPage(A);
  assert.deepEqual(run([{ type: "loaded", key: A, detail: { id: 1 } }], loading), { kind: "ready", key: A, detail: { id: 1 } });
  assert.deepEqual(run([{ type: "moved", key: A, to: "owner/new" }], loading), { kind: "redirecting", key: A, to: "owner/new" });
  assert.deepEqual(run([{ type: "failed", key: A, message: "boom" }], loading), { kind: "failed", key: A, message: "boom" });
});

test("a late answer for the page left behind does not replace the current page", () => {
  const onB = run([{ type: "requested", key: B }], loadingSkillPage(A));
  assert.deepEqual(run([{ type: "loaded", key: A, detail: { id: 1 } }], onB), loadingSkillPage(B));
  assert.deepEqual(run([{ type: "failed", key: A, message: "boom" }], onB), loadingSkillPage(B));
  const readyB = run([{ type: "loaded", key: B, detail: { id: 2 } }], onB);
  assert.deepEqual(run([{ type: "failed", key: A, message: "boom" }], readyB), readyB);
});

test("a settled page does not settle twice", () => {
  const ready = run([{ type: "loaded", key: A, detail: { id: 1 } }], loadingSkillPage(A));
  assert.deepEqual(run([{ type: "failed", key: A, message: "late" }], ready), ready);
});

test("opening the same skill again starts over", () => {
  const failed = run([{ type: "failed", key: A, message: "boom" }], loadingSkillPage(A));
  assert.deepEqual(run([{ type: "requested", key: A }], failed), loadingSkillPage(A));
});

test("the state of the previous page reads as loading for the next one", () => {
  const readyA = { kind: "ready", key: A, detail: { id: 1 } };
  assert.deepEqual(skillPageFor(readyA, B), loadingSkillPage(B));
  assert.equal(skillPageFor(readyA, A), readyA);
});
