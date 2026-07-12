import { useCallback, useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { supabase } from "../lib/supabase";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { useI18n } from "../i18n/I18nContext";

const KEY_STORAGE = "pro_key";
const CLUB_URL = "https://jasonzhu.ai/club";

interface BoardRow {
  submission_id: number;
  repo_full_name: string;
  note: string | null;
  votes: number;
  security_grade: string | null;
  stars: number | null;
  category: string | null;
  description: string | null;
}

const GRADE_STYLE: Record<string, string> = {
  safe: "text-green-700 dark:text-green-400",
  caution: "text-amber-700 dark:text-amber-400",
  unsafe: "text-red-600 dark:text-red-400",
  reject: "text-red-700 dark:text-red-300",
};

function medal(rank: number): string {
  return ["🥇", "🥈", "🥉"][rank] ?? `#${rank + 1}`;
}

export default function ProBoardPage() {
  const { lang } = useI18n();
  const zh = lang === "zh";
  const [memberKey, setMemberKey] = useState(
    () => localStorage.getItem(KEY_STORAGE) ?? "",
  );
  const [rows, setRows] = useState<BoardRow[]>([]);
  const [repo, setRepo] = useState("");
  const [note, setNote] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  const saveKey = (v: string) => {
    setMemberKey(v);
    localStorage.setItem(KEY_STORAGE, v);
  };

  const loadBoard = useCallback(async () => {
    if (!supabase) return;
    const { data } = await supabase.rpc("pro_board", { p_limit: 50 });
    setRows((data ?? []) as BoardRow[]);
  }, []);

  useEffect(() => {
    loadBoard();
  }, [loadBoard]);

  const errText = (code?: string, m?: string): string => {
    const s = `${code ?? ""} ${m ?? ""}`;
    if (s.includes("42501") || s.includes("invalid_or_expired_key"))
      return zh ? "会员 Key 无效或已过期。" : "Member key invalid or expired.";
    if (s.includes("not_safe_grade") || s.includes("23514"))
      return zh
        ? "只有安全评级为 SAFE 的仓库才能上榜。"
        : "Only SAFE-graded repos are eligible.";
    if (s.includes("not_in_catalog") || s.includes("P0002"))
      return zh
        ? "该仓库还没被收录 —— 先去首页 Submit 提交,评级后再来提名。"
        : "Not indexed yet — submit it on the homepage first, then nominate.";
    if (s.includes("bad_repo_format") || s.includes("22023"))
      return zh
        ? "格式不对,请填 owner/repo 或 GitHub URL。"
        : "Bad format — use owner/repo or a GitHub URL.";
    return zh ? "操作失败,请重试。" : "Failed — please retry.";
  };

  const submit = async () => {
    if (!supabase || !memberKey) {
      setMsg(zh ? "先填会员 Key。" : "Enter your member key first.");
      return;
    }
    if (!repo.trim()) return;
    setBusy(true);
    setMsg("");
    const { error } = await supabase.rpc("pro_submit", {
      p_key: memberKey,
      p_repo: repo.trim(),
      p_note: note.trim() || null,
    });
    setBusy(false);
    if (error) {
      setMsg(errText(error.code, error.message));
      return;
    }
    setRepo("");
    setNote("");
    setMsg(
      zh ? "✅ 已上榜,并计入你的一票。" : "✅ On the board, your vote counted.",
    );
    loadBoard();
  };

  const vote = async (id: number) => {
    if (!supabase || !memberKey) {
      setMsg(zh ? "投票需要会员 Key。" : "Voting needs a member key.");
      return;
    }
    const { error } = await supabase.rpc("pro_vote", {
      p_key: memberKey,
      p_submission_id: id,
    });
    if (error) {
      setMsg(errText(error.code, error.message));
      return;
    }
    loadBoard();
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Helmet>
        <title>Pro Picks — 会员精选榜 · Agent Skills Hub</title>
        <meta
          name="description"
          content="Pro members nominate and vote for the best agent skills. Top 3 each week get featured on our socials. Only SAFE-graded repos are eligible."
        />
        <meta name="robots" content="noindex" />
      </Helmet>
      <SiteHeader />

      <main className="max-w-3xl mx-auto px-4 py-10">
        <h1 className="text-2xl font-bold mb-1 text-gray-900 dark:text-white">
          {zh ? "⭐ 会员精选榜" : "⭐ Pro Picks"}
        </h1>
        <p className="text-sm text-gray-500 mb-2">
          {zh
            ? "会员提名 + 投票选出最好用的 skill。每周 top 3 由我们转发到社媒。"
            : "Members nominate and vote for the best skills. Top 3 each week get reposted on our socials."}
        </p>
        <p className="text-xs text-gray-400 mb-6">
          {zh
            ? "只有安全评级为 SAFE 的仓库才能上榜 —— 用安全把关,才配被推荐。"
            : "Only SAFE-graded repos are eligible — vetted before promoted."}
        </p>

        {/* member key + nominate */}
        <div className="mb-6 p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
          {!memberKey && (
            <p className="text-sm text-gray-500 mb-3">
              {zh
                ? "提名和投票是会员权益。"
                : "Nominating and voting are member benefits."}{" "}
              <a
                href={CLUB_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 dark:text-indigo-400 font-semibold hover:underline"
              >
                {zh ? "加入会员 →" : "Join the club →"}
              </a>
            </p>
          )}
          <input
            type="password"
            value={memberKey}
            onChange={(e) => saveKey(e.target.value)}
            placeholder={zh ? "会员 Key(ash_pro_…)" : "Member key (ash_pro_…)"}
            className="w-full mb-2 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
          />
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              value={repo}
              onChange={(e) => setRepo(e.target.value)}
              placeholder={
                zh
                  ? "提名:owner/repo 或 GitHub URL"
                  : "Nominate: owner/repo or GitHub URL"
              }
              className="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
            />
            <input
              value={note}
              onChange={(e) => setNote(e.target.value.slice(0, 280))}
              placeholder={
                zh ? "一句推荐理由(可选)" : "Why it's good (optional)"
              }
              className="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm"
            />
            <button
              onClick={submit}
              disabled={busy}
              className="px-5 py-2 rounded-lg bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-500 disabled:opacity-50"
            >
              {zh ? "提名" : "Nominate"}
            </button>
          </div>
          {msg && (
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">
              {msg}
            </p>
          )}
        </div>

        {/* board */}
        <ol className="space-y-2">
          {rows.map((r, i) => (
            <li
              key={r.submission_id}
              className={`flex items-start gap-3 p-3 rounded-xl border ${
                i < 3
                  ? "border-amber-300 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-950/20"
                  : "border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900"
              }`}
            >
              <span className="text-lg w-8 text-center shrink-0">
                {medal(i)}
              </span>
              <div className="flex-1 min-w-0">
                <Link
                  to={`/skill/${r.repo_full_name}/`}
                  className="font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  {r.repo_full_name}
                </Link>
                <span
                  className={`ml-2 text-xs font-medium ${GRADE_STYLE[(r.security_grade ?? "").toLowerCase()] ?? "text-gray-400"}`}
                >
                  {(r.security_grade ?? "?").toUpperCase()}
                </span>
                {r.stars != null && (
                  <span className="ml-2 text-xs text-gray-400">
                    ★ {r.stars.toLocaleString()}
                  </span>
                )}
                {r.note && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5 truncate">
                    “{r.note}”
                  </p>
                )}
              </div>
              <button
                onClick={() => vote(r.submission_id)}
                className="shrink-0 flex flex-col items-center px-3 py-1 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 transition-colors"
                title={zh ? "投一票" : "Upvote"}
              >
                <span className="text-sm">▲</span>
                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                  {r.votes}
                </span>
              </button>
            </li>
          ))}
          {rows.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-8">
              {zh
                ? "还没有提名 —— 来当第一个。"
                : "No nominations yet — be the first."}
            </p>
          )}
        </ol>

        <p className="text-xs text-gray-400 mt-6 text-center">
          <Link to="/pro/" className="hover:underline">
            {zh ? "← 回 Pro 深度搜索" : "← Back to Pro deep search"}
          </Link>
        </p>
      </main>
      <SiteFooter />
    </div>
  );
}
