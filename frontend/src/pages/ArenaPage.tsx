import { useCallback, useEffect, useMemo, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { supabase } from "../lib/supabase";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { useI18n } from "../i18n/I18nContext";

/**
 * /arena/ — anonymous skill PK voting.
 *
 * Flow: pick scenario → DB returns 2 random matching skills → user picks winner →
 * vote inserted (anon RLS). Daily dedup via voter_hash + (pair, day) UNIQUE.
 *
 * voter_hash = SHA-256(localStorage UUID), generated once per browser. Lets
 * server enforce "one vote per pair per day per voter" without ever seeing IP
 * or login state.
 */

interface ArenaSkill {
  id: number;
  repo_full_name: string;
  repo_name: string;
  author_avatar_url: string | null;
  author_name: string;
  stars: number;
  description: string | null;
  language: string | null;
  tags: string[] | null;
}

interface LeaderRow {
  scenario_tag: string;
  skill_id: number;
  repo_full_name: string;
  repo_name: string;
  author_avatar_url: string | null;
  stars: number;
  description: string | null;
  language: string | null;
  wins: number;
  losses: number;
  battles: number;
  win_rate: number;
}

const SCENARIOS: ReadonlyArray<{
  tag: string;
  label: string;
  emoji: string;
  zh: string;
  description: string;
}> = [
  {
    tag: "code-agent",
    label: "Code Agent",
    emoji: "👨‍💻",
    zh: "代码 Agent",
    description: "Coding copilots, autonomous coders",
  },
  {
    tag: "agent-memory",
    label: "Memory",
    emoji: "🧠",
    zh: "记忆系统",
    description: "Long-term memory for agents",
  },
  {
    tag: "browser",
    label: "Browser",
    emoji: "🌐",
    zh: "浏览器",
    description: "Browser automation & scraping",
  },
  {
    tag: "voice",
    label: "Voice",
    emoji: "🎙",
    zh: "语音",
    description: "TTS, STT, voice agents",
  },
  {
    tag: "mcp",
    label: "MCP Server",
    emoji: "🔌",
    zh: "MCP 服务器",
    description: "Model Context Protocol servers",
  },
  {
    tag: "skill",
    label: "Skill / Plugin",
    emoji: "🧩",
    zh: "技能 / 插件",
    description: "Claude / Codex / Gemini skills",
  },
];

const VOTER_KEY = "ash_arena_voter";
const VOTED_PAIRS_KEY = "ash_arena_voted_pairs"; // localStorage cache to skip already-voted pairs today

/** Generate or load a stable voter ID, then SHA-256 it. */
async function getVoterHash(): Promise<string> {
  let raw = localStorage.getItem(VOTER_KEY);
  if (!raw) {
    raw = crypto.randomUUID();
    localStorage.setItem(VOTER_KEY, raw);
  }
  const buf = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(raw),
  );
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

/** Track which pair_keys the user already voted on today (client-side cache to skip them). */
function getVotedPairsToday(): Set<string> {
  try {
    const raw = localStorage.getItem(VOTED_PAIRS_KEY);
    if (!raw) return new Set();
    const parsed = JSON.parse(raw) as { date: string; pairs: string[] };
    const today = new Date().toISOString().slice(0, 10);
    if (parsed.date !== today) return new Set();
    return new Set(parsed.pairs);
  } catch {
    return new Set();
  }
}

function recordVotedPair(pairKey: string): void {
  const today = new Date().toISOString().slice(0, 10);
  const existing = getVotedPairsToday();
  existing.add(pairKey);
  localStorage.setItem(
    VOTED_PAIRS_KEY,
    JSON.stringify({ date: today, pairs: [...existing] }),
  );
}

function pairKey(a: number, b: number, scenario: string): string {
  return `${scenario}:${Math.min(a, b)}-${Math.max(a, b)}`;
}

export function ArenaPage() {
  const { lang } = useI18n();
  const [scenario, setScenario] = useState<string>(SCENARIOS[0].tag);
  const [pair, setPair] = useState<[ArenaSkill, ArenaSkill] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [voteCount, setVoteCount] = useState(0);
  const [leaderboard, setLeaderboard] = useState<LeaderRow[]>([]);
  const [voterHash, setVoterHash] = useState<string>("");
  const [totalVotes, setTotalVotes] = useState(0);

  const currentScenario = useMemo(
    () => SCENARIOS.find((s) => s.tag === scenario) || SCENARIOS[0],
    [scenario],
  );

  // Load voter hash once on mount
  useEffect(() => {
    getVoterHash().then(setVoterHash);
  }, []);

  /** Fetch a fresh random pair for the current scenario. */
  const fetchPair = useCallback(async () => {
    if (!supabase) return;
    setLoading(true);
    setError(null);

    try {
      // Pull a small random sample then pick 2 distinct that the user hasn't voted on today.
      // Using `.contains("tags", [scenario])` for GIN index; cap to stars>=50 for quality.
      const { data, error: fetchErr } = await supabase
        .from("skills")
        .select(
          "id,repo_full_name,repo_name,author_avatar_url,author_name,stars,description,language,tags",
        )
        .contains("tags", [scenario])
        .gte("stars", 50)
        .order("id", { ascending: false })
        .limit(80);

      if (fetchErr) throw fetchErr;
      if (!data || data.length < 2) {
        setError(
          lang === "zh"
            ? "该场景候选项不足"
            : "Not enough candidates for this scenario",
        );
        setPair(null);
        return;
      }

      const voted = getVotedPairsToday();
      // Try up to 25 random pairs to find one not yet voted today
      for (let attempt = 0; attempt < 25; attempt++) {
        const i = Math.floor(Math.random() * data.length);
        let j = Math.floor(Math.random() * data.length);
        while (j === i) j = Math.floor(Math.random() * data.length);
        const a = data[i] as ArenaSkill;
        const b = data[j] as ArenaSkill;
        if (!voted.has(pairKey(a.id, b.id, scenario))) {
          setPair([a, b]);
          return;
        }
      }
      // All pairs in this batch already voted → pick anyway (server will reject dup)
      setPair([data[0] as ArenaSkill, data[1] as ArenaSkill]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to load pair";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [scenario, lang]);

  /** Refresh leaderboard for current scenario. */
  const fetchLeaderboard = useCallback(async () => {
    if (!supabase) return;
    const { data } = await supabase
      .from("v_arena_leaderboard")
      .select("*")
      .eq("scenario_tag", scenario)
      .order("battles", { ascending: false })
      .order("win_rate", { ascending: false })
      .limit(10);
    setLeaderboard((data as LeaderRow[]) || []);
  }, [scenario]);

  /** Total vote count for current scenario. */
  const fetchVoteCount = useCallback(async () => {
    if (!supabase) return;
    const { count } = await supabase
      .from("arena_votes")
      .select("*", { count: "exact", head: true })
      .eq("scenario_tag", scenario);
    setTotalVotes(count || 0);
  }, [scenario]);

  useEffect(() => {
    void fetchPair();
    void fetchLeaderboard();
    void fetchVoteCount();
  }, [fetchPair, fetchLeaderboard, fetchVoteCount]);

  const submitVote = async (winner: ArenaSkill, loser: ArenaSkill) => {
    if (!supabase || !voterHash || submitting) return;
    setSubmitting(true);
    try {
      const { error: insErr } = await supabase.from("arena_votes").insert({
        winner_id: winner.id,
        loser_id: loser.id,
        scenario_tag: scenario,
        voter_hash: voterHash,
      });
      // 23505 = duplicate key (already voted today) — silently move on
      if (insErr && insErr.code !== "23505") {
        throw insErr;
      }
      recordVotedPair(pairKey(winner.id, loser.id, scenario));
      setVoteCount((v) => v + 1);
      setTotalVotes((v) => v + 1);
      // Refresh leaderboard every 3 votes (not every time, to keep it snappy)
      if ((voteCount + 1) % 3 === 0) {
        void fetchLeaderboard();
      }
      void fetchPair();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Vote failed";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const skipPair = () => {
    if (pair) {
      // Don't penalize, just remember to skip until tomorrow
      recordVotedPair(pairKey(pair[0].id, pair[1].id, scenario));
    }
    void fetchPair();
  };

  return (
    <>
      <Helmet>
        <title>
          {lang === "zh"
            ? "AI Skill 竞技场 — 投票选出最佳工具 | Agent Skills Hub"
            : "AI Skill Arena — Vote for the Best Tool | Agent Skills Hub"}
        </title>
        <meta
          name="description"
          content={
            lang === "zh"
              ? "匿名投票：在 6 个场景下，挑选你认为更好的 AI Agent 技能。无登录、每天每对一票。"
              : "Anonymous voting: pick the better AI agent skill across 6 scenarios. No login. One vote per pair per day."
          }
        />
      </Helmet>

      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <SiteHeader />

        <main className="max-w-6xl mx-auto px-4 py-8">
          {/* Hero */}
          <div className="text-center mb-8">
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-2">
              {lang === "zh" ? "AI Skill 竞技场" : "AI Skill Arena"} 🥊
            </h1>
            <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              {lang === "zh"
                ? "在 6 个场景下匿名投票。挑选你认为更好的工具。无登录，每天每对最多一票。"
                : "Anonymous voting across 6 scenarios. Pick the tool you'd actually use. No login. One vote per pair per day."}
            </p>
          </div>

          {/* Scenario tabs */}
          <div className="flex flex-wrap justify-center gap-2 mb-6">
            {SCENARIOS.map((s) => {
              const active = s.tag === scenario;
              return (
                <button
                  key={s.tag}
                  onClick={() => setScenario(s.tag)}
                  className={
                    "px-4 py-2 rounded-full text-sm font-medium transition-colors " +
                    (active
                      ? "bg-indigo-600 text-white shadow-md"
                      : "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700 hover:border-indigo-400")
                  }
                >
                  <span className="mr-1">{s.emoji}</span>
                  {lang === "zh" ? s.zh : s.label}
                </button>
              );
            })}
          </div>

          {/* Stats bar */}
          <div className="flex justify-center gap-6 mb-6 text-sm">
            <div className="text-gray-600 dark:text-gray-400">
              <span className="font-bold text-gray-900 dark:text-white">
                {totalVotes.toLocaleString()}
              </span>{" "}
              {lang === "zh" ? "总投票" : "total votes"}
            </div>
            <div className="text-gray-600 dark:text-gray-400">
              <span className="font-bold text-indigo-600 dark:text-indigo-400">
                {voteCount}
              </span>{" "}
              {lang === "zh" ? "你的投票" : "your votes"}
            </div>
            <div className="text-gray-500 dark:text-gray-500 italic">
              {currentScenario.description}
            </div>
          </div>

          {/* PK pair */}
          {error && (
            <div className="mb-4 p-4 rounded-lg bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center min-h-[300px]">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-500" />
            </div>
          ) : pair ? (
            <div className="relative">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
                <ArenaCard
                  skill={pair[0]}
                  side="left"
                  onVote={() => submitVote(pair[0], pair[1])}
                  disabled={submitting}
                  lang={lang}
                />
                <ArenaCard
                  skill={pair[1]}
                  side="right"
                  onVote={() => submitVote(pair[1], pair[0])}
                  disabled={submitting}
                  lang={lang}
                />
              </div>

              {/* "VS" badge in the middle (desktop only) */}
              <div className="hidden md:flex absolute inset-0 items-center justify-center pointer-events-none">
                <div className="bg-gradient-to-br from-orange-500 to-red-500 text-white font-bold text-xl rounded-full w-14 h-14 flex items-center justify-center shadow-lg ring-4 ring-white dark:ring-gray-950">
                  VS
                </div>
              </div>

              {/* Skip button */}
              <div className="text-center mt-6">
                <button
                  onClick={skipPair}
                  disabled={submitting}
                  className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 underline-offset-2 hover:underline"
                >
                  {lang === "zh" ? "跳过这对 →" : "Skip this pair →"}
                </button>
              </div>
            </div>
          ) : null}

          {/* Leaderboard */}
          <section className="mt-12">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              {lang === "zh"
                ? `🏆 ${currentScenario.zh} 场景排行榜`
                : `🏆 ${currentScenario.label} Leaderboard`}
            </h2>
            {leaderboard.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
                {lang === "zh"
                  ? "暂无投票数据 — 你来当第一个投票者！"
                  : "No votes yet — be the first to vote!"}
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-400 uppercase text-xs">
                    <tr>
                      <th className="px-4 py-3 text-left">#</th>
                      <th className="px-4 py-3 text-left">
                        {lang === "zh" ? "工具" : "Tool"}
                      </th>
                      <th className="px-4 py-3 text-right">
                        {lang === "zh" ? "胜" : "Wins"}
                      </th>
                      <th className="px-4 py-3 text-right">
                        {lang === "zh" ? "负" : "Losses"}
                      </th>
                      <th className="px-4 py-3 text-right">
                        {lang === "zh" ? "胜率" : "Win Rate"}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                    {leaderboard.map((row, idx) => (
                      <tr
                        key={row.skill_id}
                        className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                      >
                        <td className="px-4 py-3 font-bold text-gray-400">
                          {idx === 0
                            ? "🥇"
                            : idx === 1
                              ? "🥈"
                              : idx === 2
                                ? "🥉"
                                : idx + 1}
                        </td>
                        <td className="px-4 py-3">
                          <Link
                            to={`/skill/${row.repo_full_name}/`}
                            className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 hover:underline"
                          >
                            {row.author_avatar_url && (
                              <img
                                src={row.author_avatar_url}
                                alt=""
                                className="w-6 h-6 rounded-full"
                                loading="lazy"
                              />
                            )}
                            <span className="font-medium">{row.repo_name}</span>
                            <span className="text-gray-400 text-xs">
                              ★ {row.stars.toLocaleString()}
                            </span>
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-right text-green-600 dark:text-green-400 font-mono">
                          {row.wins}
                        </td>
                        <td className="px-4 py-3 text-right text-red-500 dark:text-red-400 font-mono">
                          {row.losses}
                        </td>
                        <td className="px-4 py-3 text-right font-mono font-semibold">
                          {(row.win_rate * 100).toFixed(0)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Footer note */}
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-8 text-center max-w-xl mx-auto">
            {lang === "zh"
              ? "投票完全匿名 — 我们只存一个不可逆的浏览器哈希用于去重，不记录 IP 或登录信息。"
              : "Votes are fully anonymous — we only store an irreversible browser hash for daily dedup. No IP or login data is recorded."}
          </p>
        </main>

        <SiteFooter />
      </div>
    </>
  );
}

interface ArenaCardProps {
  skill: ArenaSkill;
  side: "left" | "right";
  onVote: () => void;
  disabled: boolean;
  lang: string;
}

function ArenaCard({ skill, onVote, disabled, lang }: ArenaCardProps) {
  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 flex flex-col hover:border-indigo-400 dark:hover:border-indigo-500 transition-colors">
      <div className="flex items-center gap-3 mb-3">
        {skill.author_avatar_url && (
          <img
            src={skill.author_avatar_url}
            alt={skill.author_name}
            className="w-10 h-10 rounded-full"
            loading="lazy"
          />
        )}
        <div className="min-w-0 flex-1">
          <Link
            to={`/skill/${skill.repo_full_name}/`}
            className="block text-lg font-bold text-gray-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 truncate"
          >
            {skill.repo_name}
          </Link>
          <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
            {skill.author_name} · ★ {skill.stars.toLocaleString()}
            {skill.language && ` · ${skill.language}`}
          </div>
        </div>
      </div>

      <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed flex-1 line-clamp-4 min-h-[80px]">
        {skill.description ||
          (lang === "zh" ? "（无描述）" : "(no description)")}
      </p>

      <button
        onClick={onVote}
        disabled={disabled}
        className="mt-4 w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
      >
        {lang === "zh" ? "选这个 ✓" : "Pick this ✓"}
      </button>
    </div>
  );
}
