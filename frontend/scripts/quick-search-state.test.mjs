import { test } from "node:test";
import assert from "node:assert/strict";
import { CLOSED_QUICK_SEARCH, activeItem, quickSearchReducer, quickSearchView } from "../src/lib/quickSearchState.mjs";

const run = (events, from = CLOSED_QUICK_SEARCH) => events.reduce(quickSearchReducer, from);
const A = [{ id: 1 }, { id: 2 }];

test("typing opens the dropdown and waits; the answer shows the rows", () => {
  const waiting = run([{ type: "typed", query: "mcp" }]);
  assert.equal(quickSearchView(waiting), "searching");
  assert.equal(quickSearchView(run([{ type: "resolved", query: "mcp", items: A }], waiting)), "results");
  assert.equal(quickSearchView(run([{ type: "resolved", query: "mcp", items: [] }], waiting)), "none");
});

test("an answer to an earlier query does not replace the current one", () => {
  const s = run([{ type: "typed", query: "mc" }, { type: "typed", query: "mcp" }, { type: "resolved", query: "mc", items: A }]);
  assert.equal(quickSearchView(s), "searching");
  assert.deepEqual(s.items, []);
});

test("an answer that comes after the input was cleared is dropped", () => {
  const s = run([{ type: "typed", query: "mcp" }, { type: "cleared" }, { type: "resolved", query: "mcp", items: A }]);
  assert.deepEqual(s, CLOSED_QUICK_SEARCH);
});

test("a failed request keeps the last list", () => {
  const s = run([{ type: "typed", query: "a" }, { type: "resolved", query: "a", items: A }, { type: "typed", query: "ab" }, { type: "failed", query: "ab" }]);
  assert.equal(quickSearchView(s), "results");
  assert.deepEqual(s.items, A);
});

test("an emptied input shows the empty view, not 'no results'", () => {
  const s = run([{ type: "typed", query: "a" }, { type: "resolved", query: "a", items: A }, { type: "typed", query: "  " }]);
  assert.equal(quickSearchView(s), "empty");
  assert.deepEqual(s.items, []);
});

test("the highlight stays inside the rows and only moves when rows are shown", () => {
  const shown = run([{ type: "typed", query: "a" }, { type: "resolved", query: "a", items: A }]);
  const down = run([{ type: "moved", delta: 1 }, { type: "moved", delta: 1 }, { type: "moved", delta: 1 }], shown);
  assert.equal(down.active, 1);
  assert.deepEqual(activeItem(down), A[1]);
  assert.equal(run([{ type: "moved", delta: -1 }, { type: "moved", delta: -1 }, { type: "moved", delta: -1 }], down).active, -1);
  const waiting = run([{ type: "typed", query: "ab" }], shown);
  assert.equal(run([{ type: "moved", delta: 1 }], waiting).active, -1);
  assert.equal(activeItem(run([{ type: "hovered", index: 0 }, { type: "closed" }], shown)), null);
});

test("closing keeps the rows for the next focus", () => {
  const s = run([{ type: "typed", query: "a" }, { type: "resolved", query: "a", items: A }, { type: "closed" }, { type: "opened" }]);
  assert.equal(quickSearchView(s), "results");
});
