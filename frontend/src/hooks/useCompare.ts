import { useCallback, useSyncExternalStore } from "react";
import type { Skill } from "../types/skill";

const STORAGE_KEY = "ash_compare";
const MAX_COMPARE = 4;

// External store with cached snapshot (same pattern as useFavorites)
let listeners: (() => void)[] = [];
function emitChange() {
  listeners.forEach((l) => l());
}

function subscribe(listener: () => void) {
  listeners.push(listener);
  return () => {
    listeners = listeners.filter((l) => l !== listener);
  };
}

interface CompareItem {
  id: number;
  repo_name: string;
  repo_full_name: string;
  author_avatar_url: string;
  score: number;
}

let cachedRaw: string | null = null;
let cachedSnapshot: CompareItem[] = [];
const EMPTY: CompareItem[] = [];

function getSnapshot(): CompareItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw !== cachedRaw) {
      cachedRaw = raw;
      cachedSnapshot = raw ? JSON.parse(raw) : [];
    }
    return cachedSnapshot;
  } catch {
    return EMPTY;
  }
}

function getServerSnapshot(): CompareItem[] {
  return EMPTY;
}

function setCompareItems(items: CompareItem[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  cachedRaw = localStorage.getItem(STORAGE_KEY);
  cachedSnapshot = items;
  emitChange();
}

export function useCompare() {
  const items = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const isInCompare = useCallback(
    (skillId: number) => items.some((i) => i.id === skillId),
    [items],
  );

  const addToCompare = useCallback(
    (skill: Skill | CompareItem) => {
      const current = getSnapshot();
      if (current.length >= MAX_COMPARE) return false;
      if (current.some((i) => i.id === skill.id)) return false;
      setCompareItems([
        ...current,
        {
          id: skill.id,
          repo_name: skill.repo_name,
          repo_full_name: skill.repo_full_name,
          author_avatar_url: skill.author_avatar_url,
          score: skill.score,
        },
      ]);
      return true;
    },
    [],
  );

  const removeFromCompare = useCallback((skillId: number) => {
    const current = getSnapshot();
    setCompareItems(current.filter((i) => i.id !== skillId));
  }, []);

  const clearCompare = useCallback(() => {
    setCompareItems([]);
  }, []);

  const toggleCompare = useCallback(
    (skill: Skill | CompareItem) => {
      const current = getSnapshot();
      if (current.some((i) => i.id === skill.id)) {
        setCompareItems(current.filter((i) => i.id !== skill.id));
      } else if (current.length < MAX_COMPARE) {
        setCompareItems([
          ...current,
          {
            id: skill.id,
            repo_name: skill.repo_name,
            repo_full_name: skill.repo_full_name,
            author_avatar_url: skill.author_avatar_url,
            score: skill.score,
          },
        ]);
      }
    },
    [],
  );

  return {
    items,
    isInCompare,
    addToCompare,
    removeFromCompare,
    clearCompare,
    toggleCompare,
    maxCompare: MAX_COMPARE,
  };
}
