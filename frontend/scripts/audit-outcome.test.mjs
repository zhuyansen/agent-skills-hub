// What /analyzer/ shows when the live GitHub read fails (src/lib/auditOutcome.mjs).
// Run: node --test scripts/audit-outcome.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  auditOutcome,
  githubFailureReason,
  parseStoredFlags,
  usableIndexedGrade,
} from "../src/lib/auditOutcome.mjs";

const graded = { security_grade: "safe" };

test("a GitHub answer is graded live, catalog row or not", () => {
  assert.deepEqual(auditOutcome({ ok: true }, graded), { kind: "live" });
  assert.deepEqual(auditOutcome({ ok: true }, null), { kind: "live" });
});

test("a rate-limited read falls back to the catalog's grade", () => {
  // 2026-11-18..25: 43 of 48 failed scans were on a repo the catalog had already graded.
  const limited = { ok: false, status: 403, rateRemaining: "0" };
  assert.deepEqual(auditOutcome(limited, graded), { kind: "index", reason: "rate_limited" });
});

test("network failures and GitHub 5xx also fall back", () => {
  assert.deepEqual(auditOutcome({ ok: false, status: 0 }, graded), { kind: "index", reason: "network" });
  assert.deepEqual(auditOutcome({ ok: false, status: 502 }, graded), { kind: "index", reason: "github_error" });
});

test("a repo GitHub says is gone is not given its old grade", () => {
  assert.deepEqual(auditOutcome({ ok: false, status: 404 }, graded), { kind: "error", reason: "not_found" });
});

test("with no usable catalog grade the failure stays an error", () => {
  const limited = { ok: false, status: 429 };
  assert.deepEqual(auditOutcome(limited, null), { kind: "error", reason: "rate_limited" });
  assert.deepEqual(auditOutcome(limited, { security_grade: "unknown" }), { kind: "error", reason: "rate_limited" });
  assert.deepEqual(auditOutcome(limited, { security_grade: null }), { kind: "error", reason: "rate_limited" });
});

test("a 403 is a rate limit only when GitHub says so; otherwise the repo is blocked", () => {
  assert.equal(githubFailureReason({ status: 403, rateRemaining: "0" }), "rate_limited");
  assert.equal(githubFailureReason({ status: 403, rateRemaining: "41", retryAfter: "60" }), "rate_limited");
  assert.equal(githubFailureReason({ status: 429, rateRemaining: null }), "rate_limited");
  // Quota left and no Retry-After: "Repository access blocked". 451 is a takedown.
  assert.equal(githubFailureReason({ status: 403, rateRemaining: "41" }), "blocked");
  assert.equal(githubFailureReason({ status: 451, rateRemaining: "41" }), "blocked");
  assert.equal(githubFailureReason({ status: 404, rateRemaining: null }), "not_found");
  assert.equal(githubFailureReason({ status: 0, rateRemaining: null }), "network");
  assert.equal(githubFailureReason({ status: 503, rateRemaining: null }), "github_error");
});

test("a blocked or taken-down repo is not given its old grade", () => {
  assert.deepEqual(auditOutcome({ ok: false, status: 451 }, graded), { kind: "error", reason: "blocked" });
  assert.deepEqual(auditOutcome({ ok: false, status: 403, rateRemaining: "12" }, graded), { kind: "error", reason: "blocked" });
});

test("a repo the catalog marks gone keeps the error, whatever GitHub said", () => {
  // Review of this change: a deleted repo (repo_status 'gone', migration 022) seen from a
  // rate-limited IP would otherwise show its old "Safe".
  const gone = { security_grade: "safe", repo_status: "gone" };
  assert.deepEqual(auditOutcome({ ok: false, status: 403, rateRemaining: "0" }, gone), { kind: "error", reason: "rate_limited" });
  assert.deepEqual(auditOutcome({ ok: false, status: 0 }, gone), { kind: "error", reason: "network" });
  const unchecked = { security_grade: "safe", repo_status: "unknown" };
  assert.deepEqual(auditOutcome({ ok: false, status: 0 }, unchecked), { kind: "index", reason: "network" });
});

test("only real verdicts can stand in for a live scan", () => {
  for (const g of ["safe", "caution", "unsafe", "reject"]) assert.equal(usableIndexedGrade({ security_grade: g }), g);
  for (const g of ["unknown", "", null, undefined, "SAFE"]) assert.equal(usableIndexedGrade({ security_grade: g }), null);
  assert.equal(usableIndexedGrade(null), null);
});

test("stored flags read from JSON text or an array, junk reads as none", () => {
  assert.deepEqual(parseStoredFlags('["pipe_to_shell","sensitive_env_vars"]'), ["pipe_to_shell", "sensitive_env_vars"]);
  assert.deepEqual(parseStoredFlags(["pipe_to_shell"]), ["pipe_to_shell"]);
  assert.deepEqual(parseStoredFlags("[]"), []);
  assert.deepEqual(parseStoredFlags(null), []);
  assert.deepEqual(parseStoredFlags("not json"), []);
  assert.deepEqual(parseStoredFlags('{"a":1}'), []);
  assert.deepEqual(parseStoredFlags('["ok", 3, null]'), ["ok"]);
});
