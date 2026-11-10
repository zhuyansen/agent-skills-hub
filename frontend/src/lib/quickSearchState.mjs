/**
 * The search dropdown of the home page hero and the catalog search bar, as one state
 * (hooks/useQuickSearch.ts). Both kept it in four variables (open, searching, results, active
 * row) that could disagree: an answer to an earlier query replaced the list for the current one,
 * and a query the input had been given from outside read as "no results".
 *
 * `phase` says what the list is: "empty" (nothing typed), "searching" (the last list stays until
 * the answer comes), "done" (the answer to `query`; no rows means nothing matched).
 * Test: node --test scripts/quick-search-state.test.mjs
 */

export const CLOSED_QUICK_SEARCH = Object.freeze({ open: false, query: "", phase: "empty", items: [], active: -1 });

const NO_ROW = -1;

function typed(state, query) {
  if (!query.trim()) return { open: true, query, phase: "empty", items: [], active: NO_ROW };
  return { open: true, query, phase: "searching", items: state.items, active: NO_ROW };
}

/** An answer counts only for the query still being waited on. */
function answered(state, event, items) {
  if (state.phase !== "searching" || state.query !== event.query) return state;
  return { ...state, phase: "done", items, active: NO_ROW };
}

function moved(state, delta) {
  if (quickSearchView(state) !== "results") return state;
  const active = Math.max(NO_ROW, Math.min(state.active + delta, state.items.length - 1));
  return { ...state, active };
}

/** What the dropdown shows: "closed", "empty", "searching", "results" or "none". */
export function quickSearchView(state) {
  if (!state.open) return "closed";
  if (state.phase !== "done") return state.phase;
  return state.items.length > 0 ? "results" : "none";
}

/** The highlighted row, or null. */
export function activeItem(state) {
  return quickSearchView(state) === "results" && state.active >= 0 ? state.items[state.active] : null;
}

export function quickSearchReducer(state, event) {
  switch (event.type) {
    case "typed": return typed(state, event.query);
    case "resolved": return answered(state, event, event.items);
    case "failed": return answered(state, event, state.items);   // a failed request keeps the last list
    case "opened": return { ...state, open: true };
    case "closed": return { ...state, open: false, active: NO_ROW };
    case "moved": return moved(state, event.delta);
    case "hovered": return { ...state, active: event.index };
    case "cleared": return CLOSED_QUICK_SEARCH;
    default: return state;
  }
}
