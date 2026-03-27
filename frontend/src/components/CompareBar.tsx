import { useNavigate } from "react-router-dom";
import { useCompare } from "../hooks/useCompare";
import { useI18n } from "../i18n/I18nContext";

export function CompareBar() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const { items, removeFromCompare, clearCompare } = useCompare();

  if (items.length === 0) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-3">
        {/* Compare chips */}
        <div className="flex items-center gap-2 flex-1 min-w-0 overflow-x-auto">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400 shrink-0">
            {t("compare.title")} ({items.length}/3)
          </span>
          {items.map((item) => (
            <div
              key={item.id}
              className="flex items-center gap-1.5 px-2.5 py-1.5 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-full text-xs shrink-0"
            >
              <img src={item.author_avatar_url} alt={item.author_name} className="w-4 h-4 rounded-full" />
              <span className="text-blue-700 dark:text-blue-300 font-medium max-w-24 truncate">{item.repo_name}</span>
              <button
                onClick={() => removeFromCompare(item.id)}
                className="ml-0.5 text-blue-400 dark:text-blue-500 hover:text-blue-600 dark:hover:text-blue-300 cursor-pointer"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={clearCompare}
            className="px-3 py-1.5 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors cursor-pointer"
          >
            {t("compare.clear")}
          </button>
          <button
            onClick={() => {
              const ids = items.map((i) => i.id).join(",");
              navigate(`/compare?ids=${ids}`);
            }}
            disabled={items.length < 2}
            className="px-4 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {t("compare.button")}
          </button>
        </div>
      </div>
    </div>
  );
}
