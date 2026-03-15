import { useI18n } from "../i18n/I18nContext";
import type { SkillsQueryParams } from "../types/skill";

interface Props {
  sortBy: string;
  sortOrder: string;
  onSortByChange: (value: SkillsQueryParams["sort_by"]) => void;
  onSortOrderChange: (value: "asc" | "desc") => void;
}

export function SortControls({ sortBy, sortOrder, onSortByChange, onSortOrderChange }: Props) {
  const { t } = useI18n();
  return (
    <div className="flex items-center gap-2">
      <select
        value={sortBy}
        onChange={(e) => onSortByChange(e.target.value as SkillsQueryParams["sort_by"])}
        className="px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="score">Score</option>
        <option value="stars">Stars</option>
        <option value="quality_score">{t("sort.qualityScore")}</option>
        <option value="star_momentum">{t("sort.momentum")}</option>
        <option value="last_commit_at">Last Updated</option>
        <option value="created_at">Created</option>
      </select>
      <button
        onClick={() => onSortOrderChange(sortOrder === "desc" ? "asc" : "desc")}
        className="p-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        title={sortOrder === "desc" ? "Descending" : "Ascending"}
      >
        {sortOrder === "desc" ? (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          </svg>
        )}
      </button>
    </div>
  );
}
