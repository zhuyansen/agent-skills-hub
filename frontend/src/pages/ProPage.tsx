import { useCallback, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { supabase } from "../lib/supabase";
import type { Skill } from "../types/skill";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { useI18n } from "../i18n/I18nContext";

const KEY_STORAGE = "pro_key";
const CATEGORIES = [
  "mcp-server",
  "claude-skill",
  "codex-skill",
  "agent-tool",
  "ai-skill",
  "llm-plugin",
];
const GRADES = ["safe", "caution", "unsafe", "reject", "unknown"];
const CLUB_URL = "https://jasonzhu.ai/club";

type GateState = "idle" | "unauthorized" | "backend_missing" | "error";

interface RpcError {
  code?: string;
  message?: string;
}

function classifyError(err: RpcError): GateState {
  const msg = err.message ?? "";
  if (err.code === "42501" || msg.includes("invalid_or_expired_key"))
    return "unauthorized";
  if (err.code === "PGRST202" || msg.includes("Could not find the function"))
    return "backend_missing";
  return "error";
}

function toCsv(rows: Skill[]): string {
  const cols = [
    "repo_full_name",
    "stars",
    "category",
    "security_grade",
    "quality_score",
    "repo_url",
    "description",
  ] as const;
  const esc = (v: unknown) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const lines = rows.map((r) => cols.map((c) => esc(r[c])).join(","));
  return [cols.join(","), ...lines].join("\n");
}

function download(name: string, mime: string, content: string): void {
  const url = URL.createObjectURL(new Blob([content], { type: mime }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

function UpgradeCard({ zh }: { zh: boolean }) {
  return (
    <div className="max-w-xl mx-auto mt-10 p-8 rounded-2xl border border-indigo-200 dark:border-indigo-900 bg-indigo-50 dark:bg-indigo-950/40 text-center">
      <h2 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">
        {zh ? "Pro 深度搜索是会员权益" : "Pro search is a member benefit"}
      </h2>
      <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">
        {zh
          ? "README 全文检索 · 200 条/页 · CSV/JSON 导出 · API 调用"
          : "Full README search · 200 results/page · CSV/JSON export · API access"}
      </p>
      <p className="text-lg font-semibold my-3 text-indigo-700 dark:text-indigo-300">
        ¥599/{zh ? "年" : "yr"}
        <span className="ml-2 text-sm font-normal">
          {zh ? "早鸟 ¥299" : "early bird ¥299"}
        </span>
      </p>
      <a
        href={CLUB_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-block px-6 py-2.5 rounded-lg bg-indigo-600 text-white font-semibold hover:bg-indigo-500 transition-colors"
      >
        {zh ? "加入会员,领取 Key →" : "Join the club to get a key →"}
      </a>
    </div>
  );
}

function ResultRow({ s }: { s: Skill }) {
  return (
    <tr className="border-b border-gray-100 dark:border-gray-800">
      <td className="py-2 pr-3">
        <Link
          to={`/skill/${s.repo_full_name}/`}
          className="text-indigo-600 dark:text-indigo-400 hover:underline"
        >
          {s.repo_full_name}
        </Link>
      </td>
      <td className="py-2 pr-3">{s.security_grade ?? "—"}</td>
      <td className="py-2 pr-3">{s.stars?.toLocaleString() ?? 0}</td>
      <td className="py-2 pr-3">{s.category}</td>
      <td className="py-2 text-gray-500 max-w-md truncate">{s.description}</td>
    </tr>
  );
}

export default function ProPage() {
  const { lang } = useI18n();
  const zh = lang === "zh";
  const [memberKey, setMemberKey] = useState(
    () => localStorage.getItem(KEY_STORAGE) ?? "",
  );
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [grade, setGrade] = useState("");
  const [rows, setRows] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(false);
  const [gate, setGate] = useState<GateState>("idle");
  const [searched, setSearched] = useState(false);

  const saveKey = (v: string) => {
    setMemberKey(v);
    localStorage.setItem(KEY_STORAGE, v);
  };

  const runSearch = useCallback(async () => {
    if (!supabase || !memberKey) {
      setGate("unauthorized");
      return;
    }
    setLoading(true);
    setGate("idle");
    const { data, error } = await supabase.rpc("pro_search", {
      p_key: memberKey,
      p_query: query || null,
      p_category: category || null,
      p_min_security: grade || null,
      p_limit: 200,
    });
    setLoading(false);
    setSearched(true);
    if (error) {
      setRows([]);
      setGate(classifyError(error));
      return;
    }
    setRows((data ?? []) as Skill[]);
  }, [memberKey, query, category, grade]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Helmet>
        <title>Pro Search — Agent Skills Hub</title>
        <meta
          name="description"
          content="Member-only deep search: full README-text search across 130,000+ agent skills and MCP servers, 200 results per page, CSV/JSON export, API access."
        />
        <meta name="robots" content="noindex" />
      </Helmet>
      <SiteHeader />

      <main className="max-w-5xl mx-auto px-4 py-10">
        <h1 className="text-2xl font-bold mb-1 text-gray-900 dark:text-white">
          {zh ? "Pro 深度搜索" : "Pro deep search"}
        </h1>
        <p className="text-sm text-gray-500 mb-6">
          {zh
            ? "README 全文 · 组合筛选 · 200 条/页 · 导出 —— 基础搜索永远免费,这里只做深水区。"
            : "Full README text · combined filters · 200/page · export. Basic search stays free — this is the deep end."}
        </p>

        <div className="flex flex-col sm:flex-row gap-2 mb-3">
          <input
            type="password"
            value={memberKey}
            onChange={(e) => saveKey(e.target.value)}
            placeholder={zh ? "会员 Key(ash_pro_…)" : "Member key (ash_pro_…)"}
            className="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
          />
        </div>
        <div className="flex flex-col sm:flex-row gap-2 mb-4">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && runSearch()}
            placeholder={
              zh
                ? "深度搜索,例:sandbox escape mitigation"
                : "Deep query, e.g. sandbox escape mitigation"
            }
            className="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
          />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
          >
            <option value="">{zh ? "全部分类" : "All categories"}</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <select
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
            className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
          >
            <option value="">{zh ? "全部评级" : "All grades"}</option>
            {GRADES.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
          <button
            onClick={runSearch}
            disabled={loading}
            className="px-5 py-2 rounded-lg bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-500 disabled:opacity-50"
          >
            {loading ? "…" : zh ? "搜索" : "Search"}
          </button>
        </div>

        {gate === "unauthorized" && <UpgradeCard zh={zh} />}
        {gate === "backend_missing" && (
          <p className="text-sm text-amber-600 mt-6">
            {zh
              ? "Pro 搜索后端尚未开通,稍后再试。"
              : "Pro search backend not enabled yet — check back soon."}
          </p>
        )}
        {gate === "error" && (
          <p className="text-sm text-red-500 mt-6">
            {zh ? "搜索出错,请重试。" : "Search failed — please retry."}
          </p>
        )}

        {rows.length > 0 && (
          <>
            <div className="flex items-center gap-3 mb-2 text-sm">
              <span className="text-gray-500">
                {rows.length} {zh ? "条结果" : "results"}
              </span>
              <button
                onClick={() =>
                  download("pro-search.csv", "text/csv", toCsv(rows))
                }
                className="text-indigo-600 dark:text-indigo-400 hover:underline"
              >
                CSV
              </button>
              <button
                onClick={() =>
                  download(
                    "pro-search.json",
                    "application/json",
                    JSON.stringify(rows, null, 2),
                  )
                }
                className="text-indigo-600 dark:text-indigo-400 hover:underline"
              >
                JSON
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left text-gray-700 dark:text-gray-300">
                <thead className="text-xs uppercase text-gray-400">
                  <tr>
                    <th className="py-2 pr-3">Repo</th>
                    <th className="py-2 pr-3">Grade</th>
                    <th className="py-2 pr-3">★</th>
                    <th className="py-2 pr-3">Category</th>
                    <th className="py-2">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((s) => (
                    <ResultRow key={s.id} s={s} />
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        {searched && rows.length === 0 && gate === "idle" && (
          <p className="text-sm text-gray-500 mt-6">
            {zh ? "没有命中结果。" : "No results."}
          </p>
        )}
      </main>
      <SiteFooter />
    </div>
  );
}
