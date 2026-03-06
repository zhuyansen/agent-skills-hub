/**
 * Generic cached query hook.
 *
 * 1. Has cache? → Return cached data immediately, then silently check for updates.
 * 2. No cache? → Show loading → fetch → cache → return.
 * 3. If lastSyncAt changed → refetch and update cache.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { sbFetchLastSyncAt } from "../api/supabaseClient";
import { supabase } from "../lib/supabase";
import { cacheGet, cacheSet } from "./useCache";

interface UseCachedQueryResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useCachedQuery<T>(
  cacheKey: string,
  fetcher: () => Promise<T>,
): UseCachedQueryResult<T> {
  const cached = cacheGet<T>(cacheKey);
  const [data, setData] = useState<T | null>(cached?.data ?? null);
  const [loading, setLoading] = useState(!cached);
  const [error, setError] = useState<string | null>(null);
  const fetchId = useRef(0);

  const doFetch = useCallback(
    async (silent = false) => {
      const id = ++fetchId.current;
      if (!silent) setLoading(true);

      try {
        // Get current lastSyncAt if supabase is available
        let lastSyncAt: string | null = null;
        if (supabase) {
          try {
            lastSyncAt = await sbFetchLastSyncAt();
          } catch {
            // ignore — use null
          }
        }

        // If we have cache and lastSyncAt hasn't changed, skip refetch
        if (silent && cached && cached.lastSyncAt === lastSyncAt && lastSyncAt !== null) {
          return;
        }

        const result = await fetcher();
        if (id === fetchId.current) {
          setData(result);
          setError(null);
          cacheSet(cacheKey, result, lastSyncAt);
        }
      } catch (err) {
        if (id === fetchId.current) {
          setError(err instanceof Error ? err.message : "Unknown error");
        }
      } finally {
        if (id === fetchId.current) setLoading(false);
      }
    },
    [cacheKey, fetcher, cached],
  );

  useEffect(() => {
    if (cached) {
      // We have cached data — silently check for updates in background
      doFetch(true);
    } else {
      // No cache — normal fetch
      doFetch(false);
    }
    // Only run on mount (cacheKey change)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cacheKey]);

  const refetch = useCallback(() => doFetch(false), [doFetch]);

  return { data, loading, error, refetch };
}
