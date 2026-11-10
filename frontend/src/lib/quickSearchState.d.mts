export interface QuickSearchState<T> {
  open: boolean;
  query: string;
  phase: "empty" | "searching" | "done";
  items: T[];
  active: number;
}
export type QuickSearchEvent<T> =
  | { type: "typed"; query: string }
  | { type: "resolved"; query: string; items: T[] }
  | { type: "failed"; query: string }
  | { type: "opened" }
  | { type: "closed" }
  | { type: "moved"; delta: number }
  | { type: "hovered"; index: number }
  | { type: "cleared" };
export type QuickSearchView = "closed" | "empty" | "searching" | "results" | "none";
export const CLOSED_QUICK_SEARCH: QuickSearchState<never>;
export function quickSearchView<T>(state: QuickSearchState<T>): QuickSearchView;
export function activeItem<T>(state: QuickSearchState<T>): T | null;
export function quickSearchReducer<T>(state: QuickSearchState<T>, event: QuickSearchEvent<T>): QuickSearchState<T>;
