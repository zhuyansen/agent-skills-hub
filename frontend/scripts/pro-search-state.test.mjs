import { test } from "node:test";
import assert from "node:assert/strict";
import { NO_FILTERS, PRO_SEARCH_IDLE, classifyProSearchError, proSearchReducer, proSearchView } from "../src/lib/proSearchState.mjs";

const run = (events, from = PRO_SEARCH_IDLE) => events.reduce(proSearchReducer, from);
const F = { query: "mcp", category: "", grade: "safe" };
const ROWS = [{ id: 1 }];
const found = { type: "succeeded", rows: ROWS, filters: F, exportable: true };

test("a search waits, then shows its rows with the filters that produced them", () => {
  assert.equal(proSearchView(run([{ type: "started" }])).loading, true);
  const view = proSearchView(run([{ type: "started" }, found]));
  assert.deepEqual([view.loading, view.gate, view.rows, view.exportable, view.rowFilters, view.nothingFound], [false, "idle", ROWS, true, F, false]);
});

test("'no results' shows only for an answer with no rows", () => {
  assert.equal(proSearchView(PRO_SEARCH_IDLE).nothingFound, false);
  assert.equal(proSearchView(run([{ type: "started" }])).nothingFound, false);
  assert.equal(proSearchView(run([{ type: "started" }, { ...found, rows: [] }])).nothingFound, true);
  assert.equal(proSearchView(run([{ type: "started" }, { type: "refused", reason: "error", filters: F }])).nothingFound, false);
});

test("the last rows stay on screen while the next search runs", () => {
  const view = proSearchView(run([{ type: "started" }, found, { type: "started" }]));
  assert.deepEqual([view.loading, view.rows], [true, ROWS]);
});

test("a refusal from the server clears the rows and keeps the refused filters", () => {
  const view = proSearchView(run([{ type: "started" }, found, { type: "started" }, { type: "refused", reason: "too_slow", filters: F }]));
  assert.deepEqual([view.gate, view.rows, view.refusedFilters], ["too_slow", [], F]);
});

test("a refusal before the request keeps the rows on screen", () => {
  const view = proSearchView(run([{ type: "started" }, found, { type: "held", reason: "trial_exhausted" }]));
  assert.deepEqual([view.gate, view.rows, view.loading], ["trial_exhausted", ROWS, false]);
  assert.deepEqual(proSearchView(run([{ type: "held", reason: "backend_missing" }])).refusedFilters, NO_FILTERS);
});

test("a share bonus lifts a used-up trial and nothing else", () => {
  const held = run([{ type: "started" }, found, { type: "held", reason: "trial_exhausted" }]);
  assert.deepEqual(proSearchView(run([{ type: "bonus_granted" }], held)).gate, "idle");
  assert.deepEqual(proSearchView(run([{ type: "bonus_granted" }], held)).rows, ROWS);
  assert.deepEqual(run([{ type: "held", reason: "trial_exhausted" }, { type: "bonus_granted" }]), PRO_SEARCH_IDLE);
  const denied = run([{ type: "started" }, { type: "refused", reason: "unauthorized", filters: F }]);
  assert.equal(run([{ type: "bonus_granted" }], denied), denied);
});

test("server errors are classified by code or message", () => {
  assert.equal(classifyProSearchError({ code: "42501" }), "unauthorized");
  assert.equal(classifyProSearchError({ message: "trial_exhausted" }), "trial_exhausted");
  assert.equal(classifyProSearchError({ code: "57014" }), "too_slow");
  assert.equal(classifyProSearchError({ code: "PT422" }), "too_slow");
  assert.equal(classifyProSearchError({ code: "PGRST202" }), "backend_missing");
  assert.equal(classifyProSearchError({}), "error");
});
