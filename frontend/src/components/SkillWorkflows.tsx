import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";
import { supabase } from "../lib/supabase";

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

const WORKFLOW_META: Record<string, { icon: string; title_zh: string; title_en: string; description_zh: string; description_en: string; sort_order: number }> = {
  "claude-skill": { icon: "sparkles", title_zh: "Claude 技能", title_en: "Claude Skills", description_zh: "为 Claude 量身打造的实用技能", description_en: "Purpose-built skills for Claude", sort_order: 1 },
  "mcp-server": { icon: "server", title_zh: "MCP 服务器", title_en: "MCP Servers", description_zh: "模型上下文协议工具集合", description_en: "Model Context Protocol tool collection", sort_order: 2 },
  "ai-skill": { icon: "cpu", title_zh: "AI 技能", title_en: "AI Skills", description_zh: "跨平台 AI 技能与插件", description_en: "Cross-platform AI skills & plugins", sort_order: 3 },
  "agent-tool": { icon: "wrench", title_zh: "Agent 工具", title_en: "Agent Tools", description_zh: "AI Agent 框架与工具", description_en: "AI Agent frameworks & tools", sort_order: 4 },
  "codex-skill": { icon: "code", title_zh: "Codex 技能", title_en: "Codex Skills", description_zh: "OpenAI Codex 专属技能", description_en: "OpenAI Codex skills", sort_order: 6 },
  "llm-plugin": { icon: "puzzle", title_zh: "LLM 插件", title_en: "LLM Plugins", description_zh: "大语言模型插件与扩展", description_en: "LLM plugins & extensions", sort_order: 7 },
};

const iconPaths: Record<string, string> = {
  sparkles: "M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z",
  server: "M21.75 17.25v-.228a4.5 4.5 0 00-.12-1.03l-2.268-9.64a3.375 3.375 0 00-3.285-2.602H7.923a3.375 3.375 0 00-3.285 2.602l-2.268 9.64a4.5 4.5 0 00-.12 1.03v.228m19.5 0a3 3 0 01-3 3H5.25a3 3 0 01-3-3m19.5 0a3 3 0 00-3-3H5.25a3 3 0 00-3 3m16.5 0h.008v.008h-.008v-.008zm-3 0h.008v.008h-.008v-.008z",
  cpu: "M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 002.25-2.25V6.75a2.25 2.25 0 00-2.25-2.25H6.75A2.25 2.25 0 004.5 6.75v10.5a2.25 2.25 0 002.25 2.25zm.75-12h9v9h-9v-9z",
  wrench: "M11.42 15.17l-5.384 5.384a1.522 1.522 0 01-2.153-2.153l5.384-5.384m2.153 2.153l5.384-5.384a1.522 1.522 0 00-2.153-2.153L9.267 12.95m2.153 2.22a3.015 3.015 0 004.276 0 3.015 3.015 0 000-4.276",
  code: "M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5",
  puzzle: "M14.25 6.087c0-.355.186-.676.401-.959.221-.29.349-.634.349-1.003 0-1.036-1.007-1.875-2.25-1.875s-2.25.84-2.25 1.875c0 .369.128.713.349 1.003.215.283.401.604.401.959v0a.64.64 0 01-.657.643 48.39 48.39 0 01-4.163-.3c.186 1.613.293 3.25.315 4.907a.656.656 0 01-.658.663v0c-.355 0-.676-.186-.959-.401a1.647 1.647 0 00-1.003-.349c-1.036 0-1.875 1.007-1.875 2.25s.84 2.25 1.875 2.25c.369 0 .713-.128 1.003-.349.283-.215.604-.401.959-.401v0c.31 0 .555.26.532.57a48.039 48.039 0 01-.642 5.056c1.518.19 3.058.309 4.616.354a.64.64 0 00.657-.643v0c0-.355-.186-.676-.401-.959a1.647 1.647 0 01-.349-1.003c0-1.035 1.008-1.875 2.25-1.875 1.243 0 2.25.84 2.25 1.875 0 .369-.128.713-.349 1.003-.215.283-.4.604-.4.959v0c0 .333.277.599.61.58a48.1 48.1 0 005.427-.63 48.05 48.05 0 00.582-4.717.532.532 0 00-.533-.57v0c-.355 0-.676.186-.959.401-.29.221-.634.349-1.003.349-1.035 0-1.875-1.007-1.875-2.25s.84-2.25 1.875-2.25c.37 0 .713.128 1.003.349.283.215.604.401.959.401v0a.656.656 0 00.658-.663 48.422 48.422 0 00-.37-5.36c-1.886.342-3.81.574-5.766.689a.578.578 0 01-.61-.58v0z",
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const USE_SUPABASE = !!supabase && !API_BASE;

async function fetchWorkflowsFromSupabase(): Promise<WorkflowData[]> {
  if (!supabase) return [];
  const sb = supabase;

  const categories = Object.keys(WORKFLOW_META);

  // Parallel: 6 requests instead of 12 sequential (skills + count in same query)
  const results = await Promise.all(
    categories.map(async (cat) => {
      const { data: skills, count, error } = await sb
        .from("skills")
        .select("repo_name,repo_full_name,description,stars,score,quality_score,author_name", { count: "exact" })
        .eq("category", cat)
        .order("stars", { ascending: false })
        .limit(4);
      return { cat, skills, count, error };
    })
  );

  const workflows: WorkflowData[] = [];
  for (const { cat, skills, count, error } of results) {
    if (error || !skills || skills.length < 2) continue;
    const meta = WORKFLOW_META[cat];
    workflows.push({
      id: cat,
      icon: meta.icon,
      title_zh: meta.title_zh,
      title_en: meta.title_en,
      description_zh: meta.description_zh,
      description_en: meta.description_en,
      skill_count: count ?? skills.length,
      skills: skills.map((s) => ({
        repo_name: s.repo_name,
        repo_full_name: s.repo_full_name,
        description: s.description || "",
        stars: s.stars,
        score: s.score || s.quality_score || 0,
        author_name: s.author_name,
      })),
    });
  }

  workflows.sort((a, b) => (WORKFLOW_META[a.id]?.sort_order ?? 99) - (WORKFLOW_META[b.id]?.sort_order ?? 99));
  return workflows;
}

export function SkillWorkflows() {
  const { t, lang } = useI18n();
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<WorkflowData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (USE_SUPABASE) {
      fetchWorkflowsFromSupabase()
        .then((data) => { setWorkflows(data); setLoading(false); })
        .catch(() => setLoading(false));
    } else {
      fetch(`${API_BASE}/api/workflows`)
        .then((r) => r.json())
        .then((data) => { setWorkflows(data); setLoading(false); })
        .catch(() => setLoading(false));
    }
  }, []);

  if (loading || workflows.length === 0) return null;

  return (
    <section className="mb-10">
      <div className="mb-5">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"/></svg>
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{t("workflows.title")}</h2>
          <span className="text-sm text-gray-400 dark:text-gray-500">{t("workflows.subtitle")}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {workflows.map((wf) => (
          <div
            key={wf.id}
            className="bg-white dark:bg-gray-800/80 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:shadow-md hover:-translate-y-0.5 transition-all"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5 text-blue-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d={iconPaths[wf.icon] || iconPaths.sparkles} />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
                  {lang === "zh" ? wf.title_zh : wf.title_en}
                </h3>
                <p className="text-xs text-gray-400 dark:text-gray-500">
                  {lang === "zh" ? wf.description_zh : wf.description_en}
                  <span className="ml-2 text-gray-300 dark:text-gray-600">
                    {wf.skill_count} {lang === "zh" ? "个技能" : "skills"}
                  </span>
                </p>
              </div>
            </div>

            <div className="space-y-1.5">
              {wf.skills.map((skill, idx) => (
                <button
                  key={skill.repo_full_name}
                  onClick={() => navigate(`/skill/${skill.repo_full_name}/`)}
                  className="w-full flex items-center gap-2.5 p-2.5 rounded-lg hover:bg-blue-50 dark:hover:bg-gray-800 transition-colors group text-left"
                >
                  <span className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center text-[10px] font-bold shrink-0">
                    {idx + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium text-gray-800 dark:text-gray-200 group-hover:text-blue-600 transition-colors block truncate">
                      {skill.repo_name}
                    </span>
                    <span className="text-xs text-gray-400 dark:text-gray-500 block truncate">
                      {skill.description}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {skill.stars > 0 && (
                      <span className="text-xs text-gray-300 dark:text-gray-600 flex items-center gap-0.5">
                        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                        {skill.stars >= 1000 ? `${(skill.stars / 1000).toFixed(1)}k` : skill.stars}
                      </span>
                    )}
                    <svg className="w-3.5 h-3.5 text-gray-300 dark:text-gray-600 group-hover:text-blue-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              ))}
            </div>

            {/* View All link */}
            <div className="border-t border-gray-100 dark:border-gray-800 pt-3 mt-3">
              <button
                onClick={() => navigate(`/?tab=explore&category=${wf.id}`)}
                className="w-full flex items-center justify-center gap-1.5 text-sm text-blue-500 hover:text-blue-700 font-medium transition-colors cursor-pointer group"
              >
                {t("workflows.viewAll").replace("{count}", wf.skill_count.toLocaleString())}
                {" "}{lang === "zh" ? (wf.title_zh) : (wf.title_en)}
                <svg className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
