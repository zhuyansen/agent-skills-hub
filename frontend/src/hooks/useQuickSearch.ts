import { useCallback, useEffect, useReducer, useRef } from "react";
import { fetchQuickSearch } from "../api/client";
import {
  CLOSED_QUICK_SEARCH, activeItem, quickSearchReducer, quickSearchView,
  type QuickSearchEvent, type QuickSearchState,
} from "../lib/quickSearchState.mjs";
import type { Skill } from "../types/skill";

const DEBOUNCE_MS = 200;
const RESULT_LIMIT = 6;

type State = QuickSearchState<Skill>;
const CLOSED: State = CLOSED_QUICK_SEARCH;
const reduce = (state: State, event: QuickSearchEvent<Skill>): State => quickSearchReducer(state, event);

/** The search dropdown shared by the hero and the catalog search bar (lib/quickSearchState.mjs).
 *  `containerRef` goes on the element that holds the input and the dropdown: a click outside closes it. */
export function useQuickSearch() {
  const [state, dispatch] = useReducer(reduce, CLOSED);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => () => clearTimeout(timer.current), []);

  useEffect(() => {
    const onMouseDown = (e: MouseEvent) => {
      if (!containerRef.current?.contains(e.target as Node)) dispatch({ type: "closed" });
    };
    document.addEventListener("mousedown", onMouseDown);
    return () => document.removeEventListener("mousedown", onMouseDown);
  }, []);

  const type = useCallback((query: string) => {
    clearTimeout(timer.current);
    dispatch({ type: "typed", query });
    if (!query.trim()) return;
    timer.current = setTimeout(() => {
      fetchQuickSearch(query, RESULT_LIMIT)
        .then((items) => dispatch({ type: "resolved", query, items }))
        .catch(() => dispatch({ type: "failed", query }));
    }, DEBOUNCE_MS);
  }, []);

  const clear = useCallback(() => {
    clearTimeout(timer.current);
    dispatch({ type: "cleared" });
  }, []);

  return {
    view: quickSearchView(state),
    items: state.items,
    active: state.active,
    activeItem: activeItem(state),
    containerRef,
    type,
    clear,
    open: useCallback(() => dispatch({ type: "opened" }), []),
    close: useCallback(() => dispatch({ type: "closed" }), []),
    move: useCallback((delta: number) => dispatch({ type: "moved", delta }), []),
    hover: useCallback((index: number) => dispatch({ type: "hovered", index }), []),
  };
}
