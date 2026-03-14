import { useCachedQuery } from "./useCachedQuery";
import { fetchStats } from "../api/client";
import type { Stats } from "../types/skill";

export function useStats() {
  const { data: stats, loading, refetch } = useCachedQuery<Stats>("stats_data", fetchStats);
  return { stats, categories: stats?.categories ?? [], refetchStats: refetch };
}
