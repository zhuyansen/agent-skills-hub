export interface ProSearchFilters {
  query: string;
  category: string;
  grade: string;
}
export type ProSearchBlock = "unauthorized" | "trial_exhausted" | "too_slow" | "backend_missing" | "error";
export interface ProSearchShown<T> {
  rows: T[];
  filters: ProSearchFilters;
  exportable: boolean;
}
export type ProSearchState<T> =
  | { kind: "idle" }
  | { kind: "searching"; shown: ProSearchShown<T> | null }
  | { kind: "results"; shown: ProSearchShown<T> }
  | { kind: "blocked"; reason: ProSearchBlock; filters: ProSearchFilters; shown: ProSearchShown<T> | null };
export type ProSearchEvent<T> =
  | { type: "started" }
  | { type: "succeeded"; rows: T[]; filters: ProSearchFilters; exportable: boolean }
  | { type: "refused"; reason: ProSearchBlock; filters: ProSearchFilters }
  | { type: "held"; reason: ProSearchBlock }
  | { type: "bonus_granted" };
export interface ProSearchView<T> {
  loading: boolean;
  gate: ProSearchBlock | "idle";
  rows: T[];
  exportable: boolean;
  rowFilters: ProSearchFilters;
  refusedFilters: ProSearchFilters;
  nothingFound: boolean;
}
export const PRO_SEARCH_IDLE: { kind: "idle" };
export const NO_FILTERS: ProSearchFilters;
export function classifyProSearchError(err: { code?: string; message?: string }): ProSearchBlock;
export function proSearchReducer<T>(state: ProSearchState<T>, event: ProSearchEvent<T>): ProSearchState<T>;
export function proSearchView<T>(state: ProSearchState<T>): ProSearchView<T>;
