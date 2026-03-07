import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";

interface WorkflowSkill {
  repo_name: string;
  repo_full_name: string;
  description: string;
  stars: number;
  score: number;
  author_name: string;
}

interface WorkflowData {
  id: string;
  icon: string;
  title_zh: string;
  title_en: string;
  description_zh: string;
  description_en: string;
  skill_count: number;
  skills: WorkflowSkill[];
}

const iconPaths: Record<string, string> = {
  sparkles:
    "M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z",
  server:
    "M21.75 17.25v-.228a4.5 4.5 0 00-.12-1.03l-2.268-9.64a3.375 3.375 0 00-3.285-2.602H7.923a3.375 3.375 0 00-3.285 2.602l-2.268 9.64a4.5 4.5 0 00-.12 1.03v.228m19.5 0a3 3 0 01-3 3H5.25a3 3 0 01-3-3m19.5 0a3 3 0 00-3-3H5.25a3 3 0 00-3 3m16.5 0h.008v.008h-.008v-.008zm-3 0h.008v.008h-.008v-.008z",
  cpu: "M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 002.25-2.25V6.75a2.25 2.25 0 00-2.25-2.25H6.75A2.25 2.25 0 004.5 6.75v10.5a2.25 2.25 0 002.25 2.25zm.75-12h9v9h-9v-9z",
  wrench:
    "M11.42 15.17l-5.384 5.384a1.522 1.522 0 01-2.153-2.153l5.384-5.384m2.153 2.153l5.384-5.384a1.522 1.522 0 00-2.153-2.153L9.267 12.95m2.153 2.22a3.015 3.015 0 004.276 0 3.015 3.015 0 000-4.276",
  music:
    "M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3",
  code: "M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5",
  puzzle:
    "M14.25 6.087c0-.355.186-.676.401-.959.221-.29.349-.634.349-1.003 0-1.036-1.007-1.875-2.25-1.875s-2.25.84-2.25 1.875c0 .369.128.713.349 1.003.215.283.401.604.401.959v0a.64.64 0 01-.657.643 48.39 48.39 0 01-4.163-.3c.186 1.613.293 3.25.315 4.907a.656.656 0 01-.658.663v0c-.355 0-.676-.186-.959-.401a1.647 1.647 0 00-1.003-.349c-1.036 0-1.875 1.007-1.875 2.25s.84 2.25 1.875 2.25c.369 0 .713-.128 1.003-.349.283-.215.604-.401.959-.401v0c.31 0 .555.26.532.57a48.039 48.039 0 01-.642 5.056c1.518.19 3.058.309 4.616.354a.64.64 0 00.657-.643v0c0-.355-.186-.676-.401-.959a1.647 1.647 0 01-.349-1.003c0-1.035 1.008-1.875 2.25-1.875 1.243 0 2.25.84 2.25 1.875 0 .369-.128.713-.349 1.003-.215.283-.4.604-.4.959v0c0 .333.277.599.61.58a48.1 48.1 0 005.427-.63 48.05 48.05 0 00.582-4.717.532.532 0 00-.533-.57v0c-.355 0-.676.186-.959.401-.29.221-.634.349-1.003.349-1.035 0-1.875-1.007-1.875-2.25s.84-2.25 1.875-2.25c.37 0 .713.128 1.003.349.283.215.604.401.959.401v0a.656.656 0 00.658-.663 48.422 48.422 0 00-.37-5.36c-1.886.342-3.81.574-5.766.689a.578.578 0 01-.61-.58v0z",
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export function SkillWorkflows() {
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<WorkflowData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/workflows`)
      .then((r) => r.json())
      .then((data) => {
        setWorkflows(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading || workflows.length === 0) return null;

  return (
    <section className="mt-10">
      <div className="mb-6">
        <h2 className="text-lg font-bold text-gray-900">
          {t("workflows.title")}
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          {t("workflows.subtitle")}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {workflows.map((wf) => (
          <div
            key={wf.id}
            className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-3 mb-4">
              <svg
                className="w-6 h-6 text-blue-500 shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="1.5"
                  d={iconPaths[wf.icon] || iconPaths.sparkles}
                />
              </svg>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-gray-900">
                  {lang === "zh" ? wf.title_zh : wf.title_en}
                </h3>
                <p className="text-xs text-gray-500">
                  {lang === "zh" ? wf.description_zh : wf.description_en}
                  <span className="ml-2 text-gray-300">
                    {wf.skill_count} {lang === "zh" ? "个技能" : "skills"}
                  </span>
                </p>
              </div>
            </div>

            <div className="space-y-2">
              {wf.skills.map((skill, idx) => (
                <button
                  key={skill.repo_full_name}
                  onClick={() => navigate(`/skill/${skill.repo_full_name}`)}
                  className="w-full flex items-center gap-3 p-2.5 rounded-lg hover:bg-blue-50 transition-colors group text-left"
                >
                  <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold shrink-0">
                    {idx + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium text-gray-800 group-hover:text-blue-600 transition-colors block truncate">
                      {skill.repo_name}
                    </span>
                    <span className="text-xs text-gray-400 block truncate">
                      {skill.description}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {skill.stars > 0 && (
                      <span className="text-xs text-gray-300 flex items-center gap-0.5">
                        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                        {skill.stars >= 1000
                          ? `${(skill.stars / 1000).toFixed(1)}k`
                          : skill.stars}
                      </span>
                    )}
                    <svg
                      className="w-4 h-4 text-gray-300 group-hover:text-blue-500 transition-colors"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
