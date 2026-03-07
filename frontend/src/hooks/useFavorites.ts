import { useCallback, useSyncExternalStore } from "react";

const STORAGE_KEY = "ash_favorites";

// External store for cross-component reactivity
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

// Cache snapshot to maintain referential stability (required by useSyncExternalStore)
let cachedRaw: string | null = null;
let cachedSnapshot: number[] = [];
const EMPTY: number[] = [];

function getSnapshot(): number[] {
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

function getServerSnapshot(): number[] {
  return EMPTY;
}

function setFavorites(ids: number[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
  // Update cache immediately so next getSnapshot() returns consistent ref
  cachedRaw = localStorage.getItem(STORAGE_KEY);
  cachedSnapshot = ids;
  emitChange();
}

export function useFavorites() {
  const favorites = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const isFavorite = useCallback(
    (skillId: number) => favorites.includes(skillId),
    [favorites],
  );

  const toggleFavorite = useCallback(
    (skillId: number) => {
      const current = getSnapshot();
      if (current.includes(skillId)) {
        setFavorites(current.filter((id) => id !== skillId));
      } else {
        setFavorites([...current, skillId]);
      }
    },
    [],
  );

  const clearFavorites = useCallback(() => {
    setFavorites([]);
  }, []);

  return { favorites, isFavorite, toggleFavorite, clearFavorites };
}
