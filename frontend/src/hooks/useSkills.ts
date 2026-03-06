import { useCallback, useEffect, useRef, useState } from "react";
import { fetchSkills } from "../api/client";
import type { PaginatedSkills, SkillsQueryParams } from "../types/skill";

const DEFAULT_PARAMS: SkillsQueryParams = {
  page: 1,
  page_size: 20,
  sort_by: "score",
  sort_order: "desc",
};

export function useSkills() {
  const [params, setParams] = useState<SkillsQueryParams>(DEFAULT_PARAMS);
  const [data, setData] = useState<PaginatedSkills | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fetchId = useRef(0);

  useEffect(() => {
    const id = ++fetchId.current;
    setLoading(true);
    setError(null);

    fetchSkills(params)
      .then((result) => {
        if (id === fetchId.current) setData(result);
      })
      .catch((err) => {
        if (id === fetchId.current) setError(err.message);
      })
      .finally(() => {
        if (id === fetchId.current) setLoading(false);
      });
  }, [params]);

  const updateParams = useCallback((update: Partial<SkillsQueryParams>) => {
    setParams((prev) => ({
      ...prev,
      ...update,
      page: update.page ?? 1, // reset to page 1 on filter change
    }));
  }, []);

  const setPage = useCallback((page: number) => {
    setParams((prev) => ({ ...prev, page }));
  }, []);

  const refetch = useCallback(() => {
    setParams((prev) => ({ ...prev }));
  }, []);

  return { data, loading, error, params, updateParams, setPage, refetch };
}
