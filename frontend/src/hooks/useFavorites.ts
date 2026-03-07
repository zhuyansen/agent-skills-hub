import { useCallback, useEffect, useSyncExternalStore } from "react";
import { useAuth } from "../contexts/AuthContext";
import { supabase } from "../lib/supabase";

const STORAGE_KEY = "ash_favorites";

// ═══ External store for cross-component reactivity ═══
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

// ═══ Supabase sync helpers ═══

async function syncFavoritesToSupabase(userId: string, skillIds: number[]) {
  if (!supabase) return;
  try {
    // Delete all existing favorites for this user
    await supabase.from("user_favorites").delete().eq("user_id", userId);
    // Insert new favorites
    if (skillIds.length > 0) {
      await supabase.from("user_favorites").insert(
        skillIds.map((sid) => ({ user_id: userId, skill_id: sid }))
      );
    }
  } catch {
    // Silent fail — localStorage is the primary source
  }
}

async function loadFavoritesFromSupabase(userId: string): Promise<number[] | null> {
  if (!supabase) return null;
  try {
    const { data, error } = await supabase
      .from("user_favorites")
      .select("skill_id")
      .eq("user_id", userId)
      .order("created_at", { ascending: true });
    if (error || !data) return null;
    return data.map((d) => d.skill_id);
  } catch {
    return null;
  }
}

export function useFavorites() {
  const favorites = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const { user } = useAuth();

  // On login: load favorites from Supabase and merge with localStorage
  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    loadFavoritesFromSupabase(user.id).then((remote) => {
      if (cancelled || !remote) return;
      const local = getSnapshot();
      // Merge: union of local + remote, deduplicated
      const merged = Array.from(new Set([...remote, ...local]));
      setFavorites(merged);
      // Sync merged set back to Supabase
      syncFavoritesToSupabase(user.id, merged);
    });
    return () => { cancelled = true; };
  }, [user]);

  const isFavorite = useCallback(
    (skillId: number) => favorites.includes(skillId),
    [favorites],
  );

  const toggleFavorite = useCallback(
    (skillId: number) => {
      const current = getSnapshot();
      let updated: number[];
      if (current.includes(skillId)) {
        updated = current.filter((id) => id !== skillId);
      } else {
        updated = [...current, skillId];
      }
      setFavorites(updated);
      // Sync to Supabase if logged in
      if (user) {
        syncFavoritesToSupabase(user.id, updated);
      }
    },
    [user],
  );

  const clearFavorites = useCallback(() => {
    setFavorites([]);
    if (user) {
      syncFavoritesToSupabase(user.id, []);
    }
  }, [user]);

  return { favorites, isFavorite, toggleFavorite, clearFavorites };
}
