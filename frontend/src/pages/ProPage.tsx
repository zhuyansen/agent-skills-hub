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
const CLUB_URL = "https://jasonzhu.ai/zh/club";

// Public 3-use trial: visitors with no key of their own get a shared, revocable
// trial key (VITE_TRIAL_PRO_KEY) and TRIAL_LIMIT free searches, counted in
// localStorage. Client-side count is a conversion nudge, not a hard wall — the
// trial key is public-by-design; abuse is capped by revoking that one key.
const TRIAL_KEY = import.meta.env.VITE_TRIAL_PRO_KEY || "";
const TRIAL_LIMIT = 3;
const TRIAL_STORAGE = "pro_trial_used";

// Share-to-earn: sharing the page once raises the trial cap by SHARE_BONUS.
// One-time per browser (localStorage), same client-side-nudge philosophy.
const SHARE_BONUS = 3;
const SHARE_STORAGE = "pro_share_claimed";
const SHARE_URL = "https://agentskillshub.top/pro/?ref=share";

type GateState =
  "idle" | "unauthorized" | "trial_exhausted" | "backend_missing" | "error";

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

function UpgradeCard({
  zh,
  exhausted = false,
}: {
  zh: boolean;
  exhausted?: boolean;
}) {
  return (
    <div className="max-w-xl mx-auto mt-10 p-8 rounded-2xl border border-indigo-200 dark:border-indigo-900 bg-indigo-50 dark:bg-indigo-950/40 text-center">
      <h2 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">
        {exhausted
          ? zh
            ? `${TRIAL_LIMIT} 次免费试用已用完`
            : `You've used all ${TRIAL_LIMIT} free trial searches`
          : zh
            ? "Pro 深度搜索是会员权益"
            : "Pro search is a member benefit"}
      </h2>
      <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">
        {zh
          ? "README 全文检索 · 200 条/页 · CSV/JSON 导出 · API 调用"
          : "Full README search · 200 results/page · CSV/JSON export · API access"}
      </p>
      <p className="text-lg font-semibold my-3 text-indigo-700 dark:text-indigo-300">
        {zh ? "早鸟前 100 名 ¥199/年" : "First 100 members: ¥199/yr"}
        <span className="ml-2 text-sm font-normal">
          {zh ? "之后 ¥365/年" : "then ¥365/yr"}
        </span>
      </p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
        {zh
          ? "续费同价 —— 以哪个价加入,续费永远锁定哪个价"
          : "Renewals locked at your joining price, forever"}
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

const KEY_PLACEHOLDER = "ash_pro_你的key";

function CodeLine({ children }: { children: string }) {
  return (
    <code className="block w-full overflow-x-auto whitespace-pre rounded-lg bg-gray-100 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 px-3 py-2 text-xs font-mono text-gray-800 dark:text-gray-200">
      {children}
    </code>
  );
}

function UsageHelp({ zh }: { zh: boolean }) {
  return (
    <details className="mt-10 rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/40 px-5 py-4">
      <summary className="cursor-pointer text-sm font-semibold text-gray-900 dark:text-white select-none">
        {zh ? "三种用法 · 拿到 Key 后怎么用" : "Three ways to use your key"}
      </summary>
      <div className="mt-4 space-y-5 text-sm text-gray-700 dark:text-gray-300">
        <div>
          <p className="font-medium mb-1">
            {zh
              ? "① 网页端 —— 不用注册、不用登录"
              : "① Web — no signup, no login"}
          </p>
          <p className="text-gray-500 dark:text-gray-400">
            {zh
              ? "打开本页,把 Key 粘进上方输入框,即刻解锁全库深度搜索、社区精选榜与 Top 3 解读。Key 存在你本地浏览器,不上传。"
              : "Open this page, paste your key into the field above — instantly unlocks full-catalog deep search, the community board, and Top 3 picks. The key stays in your browser."}
          </p>
        </div>
        <div>
          <p className="font-medium mb-1">{zh ? "② CLI" : "② CLI"}</p>
          <CodeLine>{`ASH_PRO_KEY=${KEY_PLACEHOLDER} npx @agentskillshub/cli search "${zh ? "关键词" : "keyword"}"`}</CodeLine>
        </div>
        <div>
          <p className="font-medium mb-1">
            {zh ? "③ MCP(Claude Code)" : "③ MCP (Claude Code)"}
          </p>
          <CodeLine>{`claude mcp add agentskillshub -e ASH_PRO_KEY=${KEY_PLACEHOLDER} -- npx -y @agentskillshub/mcp`}</CodeLine>
          <p className="mt-1 text-gray-500 dark:text-gray-400">
            {zh
              ? "配好后,agent 会自动调用 pro_search 工具做全库深度检索。"
              : "Once added, the agent automatically uses the pro_search tool for deep-catalog retrieval."}
          </p>
        </div>
        <p className="text-xs text-gray-400 dark:text-gray-500 border-t border-gray-200 dark:border-gray-800 pt-3">
          {zh
            ? "把上面的 ash_pro_你的key 换成欢迎信里发给你的那把 Key。Key 是你的会员凭证,请勿公开分享。"
            : "Replace ash_pro_你的key with the key sent in your welcome email. It's your membership credential — don't share it publicly."}
        </p>
      </div>
    </details>
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
  const [trialUsed, setTrialUsed] = useState(() =>
    Number(localStorage.getItem(TRIAL_STORAGE) || 0),
  );
  const [shareClaimed, setShareClaimed] = useState(
    () => localStorage.getItem(SHARE_STORAGE) === "1",
  );
  const [shareMsg, setShareMsg] = useState("");

  const saveKey = (v: string) => {
    setMemberKey(v);
    localStorage.setItem(KEY_STORAGE, v);
  };

  const runSearch = useCallback(async () => {
    if (!supabase) {
      setGate("backend_missing");
      return;
    }
    // Own key → unlimited. No key → shared trial key, capped at TRIAL_LIMIT.
    const usingTrial = !memberKey;
    const activeKey = memberKey || TRIAL_KEY;
    if (!activeKey) {
      setGate("unauthorized");
      return;
    }
    const limit = TRIAL_LIMIT + (shareClaimed ? SHARE_BONUS : 0);
    if (usingTrial && trialUsed >= limit) {
      setGate("trial_exhausted");
      return;
    }
    setLoading(true);
    setGate("idle");
    const { data, error } = await supabase.rpc("pro_search", {
      p_key: activeKey,
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
    if (usingTrial) {
      const n = trialUsed + 1;
      setTrialUsed(n);
      localStorage.setItem(TRIAL_STORAGE, String(n));
    }
  }, [memberKey, query, category, grade, trialUsed, shareClaimed]);

  // Bonus credits ONLY on a genuine share to an external channel — a completed
  // native share sheet, or opening the X compose tab. A cancelled sheet or a
  // blocked popup grants nothing. Bonus is one-time; re-sharing still spreads
  // the link but adds no more credits.
  const grantShareBonus = useCallback(() => {
    if (shareClaimed) {
      setShareMsg(zh ? "已分享 —— 奖励每人一次" : "Already claimed — one-time");
      return;
    }
    setShareClaimed(true);
    localStorage.setItem(SHARE_STORAGE, "1");
    if (gate === "trial_exhausted") setGate("idle");
    setShareMsg(zh ? "分享成功 · +3 次已到账 🎉" : "Shared · +3 added 🎉");
  }, [shareClaimed, gate, zh]);

  const onShare = useCallback(async () => {
    const text = zh
      ? "13 万+ AI agent skill 的安全分级目录,Pro 深度搜索免费试:"
      : "Security-graded directory of 130k+ AI agent skills — try Pro deep search free:";
    if (navigator.share) {
      try {
        await navigator.share({
          title: "Agent Skills Hub Pro",
          text,
          url: SHARE_URL,
        });
        grantShareBonus(); // resolves only when a target was actually chosen
      } catch {
        setShareMsg(zh ? "未完成分享,未 +3" : "Share not completed — no bonus");
      }
      return;
    }
    const intent = `https://twitter.com/intent/tweet?text=${encodeURIComponent(
      text,
    )}&url=${encodeURIComponent(SHARE_URL)}`;
    const win = window.open(intent, "_blank", "noopener,noreferrer");
    if (win) grantShareBonus();
    else
      setShareMsg(
        zh ? "弹窗被拦截,请允许后重试" : "Popup blocked — allow it and retry",
      );
  }, [grantShareBonus, zh]);

  const trialActive = !memberKey && !!TRIAL_KEY;
  const effectiveLimit = TRIAL_LIMIT + (shareClaimed ? SHARE_BONUS : 0);
  const trialLeft = Math.max(0, effectiveLimit - trialUsed);

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
        <p className="text-sm mb-6">
          <a
            href="/pro/board/"
            className="text-amber-700 dark:text-amber-400 font-semibold hover:underline"
          >
            {zh
              ? "⭐ 会员精选榜 —— 提名 · 投票 · top3 每周转发 →"
              : "⭐ Pro Picks — nominate · vote · top 3 reposted weekly →"}
          </a>
        </p>

        <div className="flex flex-col sm:flex-row gap-2 mb-1">
          <input
            type="password"
            value={memberKey}
            onChange={(e) => saveKey(e.target.value)}
            placeholder={zh ? "会员 Key(ash_pro_…)" : "Member key (ash_pro_…)"}
            className="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
          />
        </div>
        {trialActive && (
          <div className="mb-4">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {trialLeft > 0 ? (
                zh ? (
                  <>
                    没有 Key?直接搜就行 —— 免费试用还剩{" "}
                    <b className="text-indigo-600 dark:text-indigo-400">
                      {trialLeft}
                    </b>{" "}
                    / {effectiveLimit} 次。想无限用?
                    <a
                      href={CLUB_URL}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 dark:text-indigo-400 hover:underline"
                    >
                      开通 Pro →
                    </a>
                  </>
                ) : (
                  <>
                    No key? Just search — {trialLeft} of {effectiveLimit} free
                    trials left.{" "}
                    <a
                      href={CLUB_URL}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 dark:text-indigo-400 hover:underline"
                    >
                      Go Pro →
                    </a>
                  </>
                )
              ) : zh ? (
                shareClaimed ? (
                  "免费试用已用完 —— 开通 Pro 无限深度搜索。"
                ) : (
                  "免费试用已用完 —— 分享 +3 次继续,或开通 Pro。"
                )
              ) : shareClaimed ? (
                "Free trials used up — go Pro for unlimited deep search."
              ) : (
                "Free trials used up — share for +3 more, or go Pro."
              )}
            </p>
            <div className="mt-1.5 flex items-center gap-3">
              <button
                onClick={onShare}
                className="text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
              >
                🔗{" "}
                {shareClaimed
                  ? zh
                    ? "再分享 →"
                    : "Share again →"
                  : zh
                    ? "分享得 +3 次搜索"
                    : "Share for +3 searches"}
              </button>
              {shareMsg && (
                <span className="text-xs text-green-600 dark:text-green-400">
                  {shareMsg}
                </span>
              )}
            </div>
          </div>
        )}
        {!trialActive && <div className="mb-4" />}
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
        {gate === "trial_exhausted" && (
          <>
            <UpgradeCard zh={zh} exhausted />
            {!shareClaimed && (
              <div className="text-center mt-3">
                <button
                  onClick={onShare}
                  className="text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  🔗{" "}
                  {zh
                    ? "先别走 —— 分享得 +3 次搜索"
                    : "Wait — share for +3 more"}
                </button>
              </div>
            )}
            {shareMsg && (
              <p className="text-center text-sm text-green-600 dark:text-green-400 mt-2">
                {shareMsg}
              </p>
            )}
          </>
        )}
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

        <UsageHelp zh={zh} />
      </main>
      <SiteFooter />
    </div>
  );
}
