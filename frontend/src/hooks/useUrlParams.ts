import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import type { SkillsQueryParams } from "../types/skill";

const DEFAULT_PARAMS: SkillsQueryParams = {
  page: 1,
  page_size: 20,
  sort_by: "score",
  sort_order: "desc",
};

/**
 * Syncs SkillsQueryParams with URL search parameters.
 * Enables shareable/bookmarkable filter URLs like:
 *   /?tab=explore&search=mcp&category=mcp-server&sort_by=stars&page=2
 */
export function useUrlParams() {
  const [searchParams, setSearchParams] = useSearchParams();

  const params: SkillsQueryParams = useMemo(() => {
    const page = parseInt(searchParams.get("page") || "1", 10);
    const page_size = parseInt(searchParams.get("page_size") || "20", 10);
    const sort_by = (searchParams.get("sort_by") || "score") as SkillsQueryParams["sort_by"];
    const sort_order = (searchParams.get("sort_order") || "desc") as SkillsQueryParams["sort_order"];
    const search = searchParams.get("search") || undefined;
    const category = searchParams.get("category") || undefined;
    const platform = searchParams.get("platform") || undefined;
    const size_category = searchParams.get("size_category") || undefined;

    return { page, page_size, sort_by, sort_order, search, category, platform, size_category };
  }, [searchParams]);

  const tab = (searchParams.get("tab") || "overview") as "overview" | "explore";

  const setTab = useCallback(
    (newTab: "overview" | "explore") => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        if (newTab === "overview") {
          next.delete("tab");
        } else {
          next.set("tab", newTab);
        }
        return next;
      }, { replace: true });
    },
    [setSearchParams],
  );

  const updateParams = useCallback(
    (update: Partial<SkillsQueryParams>) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        // Always keep tab=explore when we're updating explore params
        next.set("tab", "explore");

        for (const [key, value] of Object.entries(update)) {
          if (value === undefined || value === null || value === "") {
            next.delete(key);
          } else if (key === "page" && value === 1) {
            next.delete("page"); // Don't pollute URL with page=1
          } else {
            next.set(key, String(value));
          }
        }
        // Reset page to 1 on non-page filter changes
        if (!("page" in update)) {
          next.delete("page");
        }
        // Remove defaults to keep URL clean
        if (next.get("sort_by") === DEFAULT_PARAMS.sort_by) next.delete("sort_by");
        if (next.get("sort_order") === DEFAULT_PARAMS.sort_order) next.delete("sort_order");
        if (next.get("page_size") === String(DEFAULT_PARAMS.page_size)) next.delete("page_size");

        return next;
      }, { replace: true });
    },
    [setSearchParams],
  );

  const setPage = useCallback(
    (page: number) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        if (page <= 1) {
          next.delete("page");
        } else {
          next.set("page", String(page));
        }
        return next;
      }, { replace: true });
    },
    [setSearchParams],
  );

  return { params, tab, setTab, updateParams, setPage };
}
