import { useEffect, useState } from "react";
import { fetchNewThisWeek } from "../api/client";
import { useI18n } from "../i18n/I18nContext";
import type { Skill } from "../types/skill";
import { formatStars, timeAgo } from "../utils/time";

interface Props {
  onShowDetail?: (skill: Skill) => void;
}

export function NewThisWeek({ onShowDetail }: Props) {
  const { t } = useI18n();
  const [items, setItems] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNewThisWeek(10)
      .then(setItems)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <section className="mb-10">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-lg">🆕</span>
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t("newThisWeek.title")}</h2>
        </div>
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-8 text-center text-gray-400 dark:text-gray-500">
          {t("detail.loading")}
        </div>
      </section>
    );
  }

  if (items.length === 0) return null;

  return (
    <section className="mb-10">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">🆕</span>
        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t("newThisWeek.title")}</h2>
        <span className="text-sm text-gray-400 dark:text-gray-500">{t("newThisWeek.subtitle")}</span>
      </div>
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden divide-y divide-gray-50 dark:divide-gray-800">
        {items.map((skill, i) => (
          <div
            key={skill.id}
            onClick={() => onShowDetail?.(skill)}
            className="flex items-center gap-3 px-4 py-3 hover:bg-green-50/40 dark:hover:bg-green-900/20 transition-colors cursor-pointer group"
          >
            <span className={`text-sm font-bold w-6 text-center ${i < 3 ? "text-green-600" : "text-gray-400 dark:text-gray-500"}`}>
              {i + 1}
            </span>
            <img
              src={skill.author_avatar_url}
              alt={skill.author_name}
              loading="lazy"
              width={28}
              height={28}
              className="w-7 h-7 rounded-full border border-gray-100 dark:border-gray-700"
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span
                  onClick={(e) => {
                    e.stopPropagation();
                    window.open(skill.repo_url, "_blank", "noopener");
                  }}
                  className="font-medium text-sm text-gray-900 dark:text-gray-100 hover:text-blue-600 hover:underline transition-colors truncate cursor-pointer"
                >
                  {skill.repo_name}
                </span>
                <span className="px-1.5 py-0.5 text-[9px] font-bold rounded bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400 border border-green-100 dark:border-green-800 shrink-0">
                  NEW
                </span>
              </div>
              <span className="text-xs text-gray-400 dark:text-gray-500">{skill.author_name}</span>
            </div>
            <span className="px-2 py-0.5 text-[10px] rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 hidden md:inline">
              {skill.category}
            </span>
            <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 w-16 justify-end">
              <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
              {formatStars(skill.stars)}
            </div>
            <span className="text-xs text-green-500 w-14 text-right hidden sm:block">
              {timeAgo(skill.first_seen)}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
