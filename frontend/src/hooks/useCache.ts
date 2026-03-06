/**
 * localStorage-based cache with sync-aware invalidation.
 *
 * Cache entries store: { data, lastSyncAt, cachedAt }
 * On subsequent loads, if `lastSyncAt` from the server changed, cache is refreshed.
 */

const PREFIX = "ash_v6_";

interface CacheEntry<T> {
  data: T;
  lastSyncAt: string | null;
  cachedAt: number;
}

export function cacheGet<T>(key: string): CacheEntry<T> | null {
  try {
    const raw = localStorage.getItem(PREFIX + key);
    if (!raw) return null;
    return JSON.parse(raw) as CacheEntry<T>;
  } catch {
    return null;
  }
}

export function cacheSet<T>(key: string, data: T, lastSyncAt: string | null): void {
  try {
    const entry: CacheEntry<T> = { data, lastSyncAt, cachedAt: Date.now() };
    localStorage.setItem(PREFIX + key, JSON.stringify(entry));
  } catch {
    // localStorage full — silently ignore
  }
}

export function cacheClear(): void {
  const keysToRemove: string[] = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key?.startsWith(PREFIX)) keysToRemove.push(key);
  }
  keysToRemove.forEach((k) => localStorage.removeItem(k));
}
