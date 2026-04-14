import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { supabase } from "../lib/supabase";
import { useI18n } from "../i18n/I18nContext";

interface RelatedSkill {
  repo_full_name: string;
  repo_name: string;
  description: string | null;
  stars: number;
  author_avatar_url: string;
  category: string;
}

interface Props {
  category: string;
  currentRepo: string;
  stars: number;
}

const MAX_RELATED = 6;

export function RelatedSkills({ category, currentRepo, stars }: Props) {
  const { t } = useI18n();
  const [skills, setSkills] = useState<RelatedSkill[]>([]);

  useEffect(() => {
    if (!supabase || !category) return;

    const starMin = Math.max(0, Math.floor(stars * 0.2));
    const starMax = Math.ceil(stars * 5);

    supabase
      .from("skills")
      .select(
        "repo_full_name,repo_name,description,stars,author_avatar_url,category",
      )
      .eq("category", category)
      .neq("repo_full_name", currentRepo)
      .gte("stars", starMin)
      .lte("stars", starMax)
      .order("stars", { ascending: false })
      .limit(MAX_RELATED)
      .then(({ data }) => {
        if (data && data.length > 0) {
          setSkills(data);
        }
      });
  }, [category, currentRepo, stars]);

  if (skills.length === 0) return null;

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-5 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide">
          {t("detail.relatedSkills") || "Related Skills"}
        </h3>
        <Link
          to={`/category/${category}/`}
          className="text-xs text-blue-500 hover:text-blue-600 dark:text-blue-400"
        >
          {t("detail.viewAll") || "View all"} →
        </Link>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {skills.map((s) => (
          <Link
            key={s.repo_full_name}
            to={`/skill/${s.repo_full_name}/`}
            className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
          >
            <img
              src={s.author_avatar_url}
              alt={`${s.repo_name} author avatar`}
              className="w-8 h-8 rounded-full shrink-0"
            />
            <div className="flex-1 min-w-0">
              <span className="text-sm font-medium text-gray-900 dark:text-gray-100 block truncate">
                {s.repo_name}
              </span>
              <span className="text-xs text-gray-400 dark:text-gray-500 line-clamp-2">
                {s.description || s.repo_full_name}
              </span>
              <span className="text-xs text-amber-500 mt-1 inline-block">
                ★ {s.stars.toLocaleString()}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
