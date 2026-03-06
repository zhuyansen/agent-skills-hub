import { useCallback, useEffect, useRef, useState } from "react";
import { fetchCategories, fetchStats } from "../api/client";
import type { CategoryCount, Stats } from "../types/skill";

export function useStats() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [categories, setCategories] = useState<CategoryCount[]>([]);
  const fetchId = useRef(0);

  const load = useCallback(() => {
    const id = ++fetchId.current;
    fetchStats()
      .then((s) => { if (id === fetchId.current) setStats(s); })
      .catch(console.error);
    fetchCategories()
      .then((c) => { if (id === fetchId.current) setCategories(c); })
      .catch(console.error);
  }, []);

  useEffect(() => { load(); }, [load]);

  return { stats, categories, refetchStats: load };
}
