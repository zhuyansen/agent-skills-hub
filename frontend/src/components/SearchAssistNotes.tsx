import type { PaginatedSkills } from "../types/skill";
import { scenarioForTerm } from "../lib/searchAssist.mjs";
import SEARCH_ASSIST from "../data/search-assist.json";

/**
 * Notes above the search results (lib/searchAssist.mjs): the corrected spelling
 * the results are for, the reviewed /best/ page the term names, and for a GitHub
 * URL that is not in the catalog, a free scan of that repo instead.
 */
export function SearchAssistNotes({
  data,
  search,
  zh,
}: {
  data: PaginatedSkills;
  search: string;
  zh: boolean;
}) {
  const scenario = scenarioForTerm(data.corrected_to ?? search, SEARCH_ASSIST.scenarios);
  const unlistedRepo = data.github_repo && data.items.length === 0 ? data.github_repo : null;
  if (!data.corrected_to && !scenario && !unlistedRepo) return null;

  return (
    <div className="mb-4 space-y-2">
      {data.corrected_to && (
        <p className="text-sm text-[var(--text-2)]">
          {zh ? "显示的是 " : "Showing results for "}
          <b className="text-gray-900 dark:text-white">{data.corrected_to}</b>
          {zh
            ? `的结果，「${search}」没有找到匹配。`
            : ` — nothing matched “${search}”.`}
        </p>
      )}
      {unlistedRepo && (
        <a
          href={`/analyzer/?repo=${encodeURIComponent(unlistedRepo)}`}
          className="surface surface-hover block p-4 text-sm"
        >
          <b className="text-gray-900 dark:text-white">{unlistedRepo}</b>
          {zh
            ? " 还没收录。免费扫描这个仓库，看它的安全评级 →"
            : " isn't in the catalog yet. Scan it for free and get its security grade →"}
        </a>
      )}
      {scenario && (
        <a
          href={`/best/${scenario.slug}/`}
          className="surface surface-hover flex items-center justify-between gap-3 p-4"
        >
          <span className="min-w-0">
            <span className="block text-xs text-[var(--text-2)]">
              {zh ? "精选榜单 · 每个都有安全评级" : "Curated page · every pick security-graded"}
            </span>
            <span className="block font-semibold text-gray-900 dark:text-white truncate">
              {zh ? scenario.zh : scenario.en}
            </span>
          </span>
          <span className="flex-none text-sm font-medium text-indigo-600 dark:text-indigo-400">
            {zh ? "查看 →" : "Open →"}
          </span>
        </a>
      )}
    </div>
  );
}
