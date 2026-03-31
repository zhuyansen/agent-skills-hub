import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";
import { COMBO_RECIPES, type ComboRecipe } from "../data/combos";

interface ComboRecommendationProps {
  currentSkill: {
    repo_full_name: string;
    topics?: string;
    description?: string;
    repo_name?: string;
  };
}

function matchScore(recipe: ComboRecipe, tokens: string[]): number {
  let score = 0;
  for (const keyword of recipe.trigger_keywords) {
    const kw = keyword.toLowerCase();
    for (const token of tokens) {
      if (token.includes(kw) || kw.includes(token)) {
        score++;
      }
    }
  }
  return score;
}

export function ComboRecommendation({ currentSkill }: ComboRecommendationProps) {
  const { lang, t } = useI18n();

  const matchedCombos = useMemo(() => {
    // Build a searchable token list from the skill's metadata
    const parts: string[] = [];

    // repo full name tokens (e.g. "anthropics/claude-code" -> ["anthropics", "claude", "code"])
    if (currentSkill.repo_full_name) {
      parts.push(...currentSkill.repo_full_name.toLowerCase().split(/[/\-_]+/));
    }
    if (currentSkill.repo_name) {
      parts.push(...currentSkill.repo_name.toLowerCase().split(/[\-_]+/));
    }

    // topics (JSON string like '["mcp","agent"]')
    if (currentSkill.topics) {
      try {
        const topicsArr: string[] = JSON.parse(currentSkill.topics);
        for (const topic of topicsArr) {
          parts.push(...topic.toLowerCase().split(/[\-_]+/));
        }
      } catch {
        // not valid JSON, split as plain text
        parts.push(...currentSkill.topics.toLowerCase().split(/[\s,\-_]+/));
      }
    }

    // description words
    if (currentSkill.description) {
      parts.push(...currentSkill.description.toLowerCase().split(/[\s,.\-_/]+/));
    }

    const tokens = [...new Set(parts.filter(Boolean))];

    // Score each recipe and filter
    const scored = COMBO_RECIPES
      .map((recipe) => ({ recipe, score: matchScore(recipe, tokens) }))
      .filter(({ score }) => score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 2);

    return scored.map(({ recipe }) => recipe);
  }, [currentSkill]);

  if (matchedCombos.length === 0) return null;

  return (
    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-950/40 dark:to-purple-950/40 rounded-xl border border-indigo-200 dark:border-indigo-800 p-5 mb-6">
      <h3 className="text-xs font-medium text-indigo-500 dark:text-indigo-400 uppercase tracking-wide mb-4">
        {t("combo.title")}
      </h3>

      <div className="space-y-4">
        {matchedCombos.map((combo) => {
          const otherSkills = combo.skills.filter(
            (s) => s.toLowerCase() !== currentSkill.repo_full_name.toLowerCase(),
          );

          return (
            <div
              key={combo.id}
              className="bg-white/80 dark:bg-gray-900/60 rounded-lg p-4 border border-indigo-100 dark:border-indigo-800/50"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg">{combo.icon}</span>
                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  {lang === "zh" ? combo.name_zh : combo.name}
                </h4>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                {lang === "zh" ? combo.description_zh : combo.description}
              </p>

              <div className="flex flex-wrap gap-2">
                {otherSkills.map((fullName) => {
                  const repoName = fullName.split("/").pop() || fullName;
                  return (
                    <Link
                      key={fullName}
                      to={`/skill/${fullName}/`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-200 dark:hover:bg-indigo-800/60 transition-colors border border-indigo-200 dark:border-indigo-700"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                      </svg>
                      {repoName}
                    </Link>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      <p className="text-[10px] text-indigo-400 dark:text-indigo-500 mt-3">
        {t("combo.hint")}
      </p>
    </div>
  );
}
