/**
 * The Pro search page's search, as one state (pages/ProPage.tsx). The page kept it in `loading`,
 * `gate`, `searched`, `rows`, `exportable` and `lastFilters`, set one by one around the request.
 *
 *   idle       nothing searched yet
 *   searching  waiting; `shown` is the last result still on screen, or null
 *   results    `shown` is the answer: its rows (none means nothing matched), the filters that
 *              produced them, and whether they may be exported
 *   blocked    the search was refused for `reason`; `filters` are the ones refused. A refusal
 *              before the request (trial used up, no backend) keeps the rows on screen; one from
 *              the server clears them.
 *
 * Test: node --test scripts/pro-search-state.test.mjs
 */

export const PRO_SEARCH_IDLE = Object.freeze({ kind: "idle" });
export const NO_FILTERS = Object.freeze({ query: "", category: "", grade: "" });

const shownOf = (state) => state.shown ?? null;

/** Why the server refused, from its error (migrations 034 and 042 name the codes). */
export function classifyProSearchError(err) {
  const msg = err.message ?? "";
  if (err.code === "42501" || msg.includes("invalid_or_expired_key")) return "unauthorized";
  if (err.code === "PT429" || msg.includes("trial_exhausted")) return "trial_exhausted";
  // Stopped at the time limit before finding a row (042), or timed out (57014).
  if (err.code === "PT422" || err.code === "57014" || msg.includes("search_incomplete")) return "too_slow";
  if (err.code === "PGRST202" || msg.includes("Could not find the function")) return "backend_missing";
  return "error";
}

/** A share bonus lifts a used-up trial; any other state stays. */
function bonusGranted(state) {
  if (state.kind !== "blocked" || state.reason !== "trial_exhausted") return state;
  return state.shown ? { kind: "results", shown: state.shown } : PRO_SEARCH_IDLE;
}

export function proSearchReducer(state, event) {
  switch (event.type) {
    case "started": return { kind: "searching", shown: shownOf(state) };
    case "succeeded": return { kind: "results", shown: { rows: event.rows, filters: event.filters, exportable: event.exportable } };
    case "refused": return { kind: "blocked", reason: event.reason, filters: event.filters, shown: null };
    case "held": return { kind: "blocked", reason: event.reason, filters: shownOf(state)?.filters ?? NO_FILTERS, shown: shownOf(state) };
    case "bonus_granted": return bonusGranted(state);
    default: return state;
  }
}

/** What the page reads off the state. */
export function proSearchView(state) {
  const shown = shownOf(state);
  return {
    loading: state.kind === "searching",
    gate: state.kind === "blocked" ? state.reason : "idle",
    rows: shown?.rows ?? [],
    exportable: shown?.exportable ?? false,
    rowFilters: shown?.filters ?? NO_FILTERS,
    refusedFilters: state.kind === "blocked" ? state.filters : NO_FILTERS,
    nothingFound: state.kind === "results" && shown.rows.length === 0,
  };
}
