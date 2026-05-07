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
  star_momentum?: number | null;
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

/** All recognized arena scenario tags — used by auto-classification. */
const ARENA_TAG_SET = new Set(SCENARIOS.map((s) => s.tag));

/**
 * Auto-classify a custom pair into the right scenario based on shared tags.
 *
 * Priority:
 *   1. If both skills carry the user-selected scenario tag → keep current.
 *   2. Else if both share another arena scenario tag → switch to that.
 *   3. Else → null (no clean fit; UI will warn the vote goes to current).
 */
function detectBestScenario(
  left: ArenaSkill | null,
  right: ArenaSkill | null,
  current: string,
): string | null {
  if (!left || !right) return null;
  const leftTags = new Set((left.tags || []).map((t) => t.toLowerCase()));
  const rightTags = new Set((right.tags || []).map((t) => t.toLowerCase()));
  const shared = [...leftTags].filter(
    (t) => rightTags.has(t) && ARENA_TAG_SET.has(t),
  );
  if (shared.includes(current)) return current;
  if (shared.length > 0) return shared[0];
  return null;
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
  // Custom Battle: user picks 2 specific skills instead of random
  const [customMode, setCustomMode] = useState(false);
  const [customLeft, setCustomLeft] = useState<ArenaSkill | null>(null);
  const [customRight, setCustomRight] = useState<ArenaSkill | null>(null);

  const currentScenario = useMemo(
    () => SCENARIOS.find((s) => s.tag === scenario) || SCENARIOS[0],
    [scenario],
  );

  /**
   * In Custom mode, the active scenario for the vote is auto-classified from
   * the picked pair's shared tags. Falls back to current selected scenario
   * if no clean tag overlap. Random mode just uses the selected scenario.
   */
  const detectedScenario = useMemo(
    () =>
      customMode ? detectBestScenario(customLeft, customRight, scenario) : null,
    [customMode, customLeft, customRight, scenario],
  );
  const effectiveScenario = detectedScenario ?? scenario;
  const detectedScenarioMeta = useMemo(
    () =>
      detectedScenario
        ? SCENARIOS.find((s) => s.tag === detectedScenario)
        : null,
    [detectedScenario],
  );
  const customClassifyState: "ok" | "switched" | "cross" | "incomplete" =
    !customMode || !customLeft || !customRight
      ? "incomplete"
      : detectedScenario === scenario
        ? "ok"
        : detectedScenario
          ? "switched"
          : "cross";

  // Load voter hash once on mount
  useEffect(() => {
    getVoterHash().then(setVoterHash);
  }, []);

  /** Fetch a fresh random pair for the current scenario.
   *
   * Pool quality strategy: combine "popular" + "currently surging" so the PK
   * matches actual viable contenders rather than long-tail noise. Two parallel
   * queries → 60 by stars + 40 by star_momentum → dedupe → random 2 from pool.
   */
  const fetchPair = useCallback(async () => {
    const sb = supabase;
    if (!sb) return;
    setLoading(true);
    setError(null);

    try {
      const COLS =
        "id,repo_full_name,repo_name,author_avatar_url,author_name,stars,description,language,tags,star_momentum";

      const [byStars, byMomentum] = await Promise.all([
        sb
          .from("skills")
          .select(COLS)
          .contains("tags", [scenario])
          .gte("stars", 100)
          .order("stars", { ascending: false })
          .limit(60),
        sb
          .from("skills")
          .select(COLS)
          .contains("tags", [scenario])
          .gte("stars", 50)
          .gt("star_momentum", 0)
          .order("star_momentum", { ascending: false })
          .limit(40),
      ]);

      if (byStars.error) throw byStars.error;

      // Dedupe by id, prefer the byStars row when same skill appears in both
      const merged = new Map<number, ArenaSkill>();
      for (const r of (byStars.data || []) as ArenaSkill[]) merged.set(r.id, r);
      for (const r of (byMomentum.data || []) as ArenaSkill[]) {
        if (!merged.has(r.id)) merged.set(r.id, r);
      }
      const pool = [...merged.values()];

      if (pool.length < 2) {
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
        const i = Math.floor(Math.random() * pool.length);
        let j = Math.floor(Math.random() * pool.length);
        while (j === i) j = Math.floor(Math.random() * pool.length);
        const a = pool[i];
        const b = pool[j];
        if (!voted.has(pairKey(a.id, b.id, scenario))) {
          setPair([a, b]);
          return;
        }
      }
      // All pairs in this batch already voted → pick anyway (server will reject dup)
      setPair([pool[0], pool[1]]);
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
    if (!customMode) void fetchPair();
    void fetchLeaderboard();
    void fetchVoteCount();
  }, [fetchPair, fetchLeaderboard, fetchVoteCount, customMode]);

  // Reset custom selections when scenario or mode changes
  useEffect(() => {
    setCustomLeft(null);
    setCustomRight(null);
  }, [scenario, customMode]);

  const submitVote = async (winner: ArenaSkill, loser: ArenaSkill) => {
    if (!supabase || !voterHash || submitting) return;
    setSubmitting(true);
    try {
      // In Custom mode, route the vote to the auto-classified scenario when
      // the picked pair's shared tags point to a different leaderboard.
      // Random mode always uses the selected scenario tab.
      const voteScenario = customMode ? effectiveScenario : scenario;
      const { error: insErr } = await supabase.from("arena_votes").insert({
        winner_id: winner.id,
        loser_id: loser.id,
        scenario_tag: voteScenario,
        voter_hash: voterHash,
      });
      // 23505 = duplicate key (already voted today) — silently move on
      if (insErr && insErr.code !== "23505") {
        throw insErr;
      }
      recordVotedPair(pairKey(winner.id, loser.id, voteScenario));
      setVoteCount((v) => v + 1);
      setTotalVotes((v) => v + 1);
      // Refresh leaderboard every 3 votes (not every time, to keep it snappy)
      if ((voteCount + 1) % 3 === 0) {
        void fetchLeaderboard();
      }
      if (customMode) {
        // After a custom vote, clear selections so user can pick a new pair
        setCustomLeft(null);
        setCustomRight(null);
      } else {
        void fetchPair();
      }
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

          {/* Mode toggle: Random vs Custom Battle */}
          <div className="flex justify-center gap-1 mb-6 p-1 bg-gray-100 dark:bg-gray-900 rounded-full max-w-xs mx-auto">
            <button
              onClick={() => setCustomMode(false)}
              className={
                "flex-1 px-4 py-1.5 text-sm font-medium rounded-full transition-colors " +
                (!customMode
                  ? "bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white")
              }
            >
              🎲 {lang === "zh" ? "随机" : "Random"}
            </button>
            <button
              onClick={() => setCustomMode(true)}
              className={
                "flex-1 px-4 py-1.5 text-sm font-medium rounded-full transition-colors " +
                (customMode
                  ? "bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white")
              }
            >
              🎯 {lang === "zh" ? "自选" : "Custom"}
            </button>
          </div>

          {/* PK pair */}
          {error && (
            <div className="mb-4 p-4 rounded-lg bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900 text-red-700 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          {customMode ? (
            <CustomBattle
              left={customLeft}
              right={customRight}
              onSelectLeft={setCustomLeft}
              onSelectRight={setCustomRight}
              onVote={(winner, loser) => submitVote(winner, loser)}
              submitting={submitting}
              lang={lang}
              classifyState={customClassifyState}
              detectedScenario={detectedScenarioMeta || null}
              currentScenario={currentScenario}
            />
          ) : loading ? (
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

// ──────────────────────────────────────────────────────────────────
// Custom Battle: search 2 skills + PK them directly
// ──────────────────────────────────────────────────────────────────

type ScenarioMeta = (typeof SCENARIOS)[number];

interface CustomBattleProps {
  left: ArenaSkill | null;
  right: ArenaSkill | null;
  onSelectLeft: (s: ArenaSkill | null) => void;
  onSelectRight: (s: ArenaSkill | null) => void;
  onVote: (winner: ArenaSkill, loser: ArenaSkill) => void;
  submitting: boolean;
  lang: string;
  classifyState: "ok" | "switched" | "cross" | "incomplete";
  detectedScenario: ScenarioMeta | null;
  currentScenario: ScenarioMeta;
}

function CustomBattle({
  left,
  right,
  onSelectLeft,
  onSelectRight,
  onVote,
  submitting,
  lang,
  classifyState,
  detectedScenario,
  currentScenario,
}: CustomBattleProps) {
  const ready = left && right && left.id !== right.id;
  return (
    <div className="relative">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
        <CustomSlot
          skill={left}
          onSelect={onSelectLeft}
          excludeId={right?.id}
          placeholder={lang === "zh" ? "搜索左侧工具…" : "Search left tool…"}
          onVote={ready ? () => onVote(left, right) : undefined}
          disabled={submitting}
          lang={lang}
        />
        <CustomSlot
          skill={right}
          onSelect={onSelectRight}
          excludeId={left?.id}
          placeholder={lang === "zh" ? "搜索右侧工具…" : "Search right tool…"}
          onVote={ready ? () => onVote(right, left) : undefined}
          disabled={submitting}
          lang={lang}
        />
      </div>

      {ready && (
        <div className="hidden md:flex absolute inset-0 items-center justify-center pointer-events-none">
          <div className="bg-gradient-to-br from-orange-500 to-red-500 text-white font-bold text-xl rounded-full w-14 h-14 flex items-center justify-center shadow-lg ring-4 ring-white dark:ring-gray-950">
            VS
          </div>
        </div>
      )}

      {/* Auto-classification banner — explains where the vote will be counted */}
      {classifyState === "switched" && detectedScenario && (
        <div className="mt-6 mx-auto max-w-2xl rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 px-4 py-3 text-sm text-emerald-800 dark:text-emerald-300 text-center">
          <span className="font-semibold">📍 Auto-classified:</span>{" "}
          {lang === "zh" ? "归入" : "vote will count toward"}{" "}
          <strong>
            {detectedScenario.emoji}{" "}
            {lang === "zh" ? detectedScenario.zh : detectedScenario.label}
          </strong>{" "}
          <span className="text-xs opacity-75">
            ({lang === "zh" ? "两个工具的标签共同点" : "based on shared tags"})
          </span>
        </div>
      )}
      {classifyState === "cross" && (
        <div className="mt-6 mx-auto max-w-2xl rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 px-4 py-3 text-sm text-amber-800 dark:text-amber-300 text-center">
          <span className="font-semibold">⚠️</span>{" "}
          {lang === "zh"
            ? `两个工具没有共同的场景标签，本次投票仍会归入 ${currentScenario.emoji} ${currentScenario.zh}（当前 tab）。`
            : `These two share no arena category. Vote will fall back to ${currentScenario.emoji} ${currentScenario.label} (current tab).`}
        </div>
      )}

      {!ready && (
        <p className="text-center mt-6 text-sm text-gray-500 dark:text-gray-400">
          {lang === "zh"
            ? "在两侧分别选一个工具，然后投票决出胜者。系统会按两个工具的共同标签自动归类。"
            : "Pick one tool on each side, then vote. The vote auto-routes to whichever scenario both tools share."}
        </p>
      )}
    </div>
  );
}

interface CustomSlotProps {
  skill: ArenaSkill | null;
  onSelect: (s: ArenaSkill | null) => void;
  excludeId?: number;
  placeholder: string;
  onVote?: () => void;
  disabled: boolean;
  lang: string;
}

function CustomSlot({
  skill,
  onSelect,
  excludeId,
  placeholder,
  onVote,
  disabled,
  lang,
}: CustomSlotProps) {
  if (skill) {
    return (
      <div className="bg-white dark:bg-gray-900 border-2 border-indigo-400 dark:border-indigo-500 rounded-xl p-5 flex flex-col">
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
          <button
            onClick={() => onSelect(null)}
            className="text-xs text-gray-400 hover:text-red-500 px-2"
            title={lang === "zh" ? "更换" : "Change"}
          >
            ✕
          </button>
        </div>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed flex-1 line-clamp-4 min-h-[80px]">
          {skill.description ||
            (lang === "zh" ? "（无描述）" : "(no description)")}
        </p>
        <button
          onClick={onVote}
          disabled={!onVote || disabled}
          className="mt-4 w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
        >
          {lang === "zh" ? "选这个 ✓" : "Pick this ✓"}
        </button>
      </div>
    );
  }
  return (
    <div className="bg-white dark:bg-gray-900 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-xl p-5 min-h-[260px] flex flex-col">
      <SkillSearch
        onSelect={onSelect}
        excludeId={excludeId}
        placeholder={placeholder}
        lang={lang}
      />
    </div>
  );
}

interface SkillSearchProps {
  onSelect: (s: ArenaSkill) => void;
  excludeId?: number;
  placeholder: string;
  lang: string;
}

function SkillSearch({
  onSelect,
  excludeId,
  placeholder,
  lang,
}: SkillSearchProps) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<ArenaSkill[]>([]);
  const [loading, setLoading] = useState(false);

  // Debounce search
  useEffect(() => {
    if (q.trim().length < 2 || !supabase) {
      setResults([]);
      return;
    }
    const handle = setTimeout(async () => {
      const sb = supabase;
      if (!sb) return;
      setLoading(true);
      try {
        const term = q.trim().replace(/[%_]/g, "");
        // Search by repo_full_name (e.g. "mem0ai/mem0") or repo_name ("mem0")
        const { data } = await sb
          .from("skills")
          .select(
            "id,repo_full_name,repo_name,author_avatar_url,author_name,stars,description,language,tags",
          )
          .or(`repo_full_name.ilike.%${term}%,repo_name.ilike.%${term}%`)
          .gte("stars", 50)
          .order("stars", { ascending: false })
          .limit(8);
        const filtered =
          excludeId !== undefined
            ? (data || []).filter((s) => s.id !== excludeId)
            : data || [];
        setResults(filtered as ArenaSkill[]);
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => clearTimeout(handle);
  }, [q, excludeId]);

  return (
    <div className="flex-1 flex flex-col">
      <input
        type="text"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder={placeholder}
        className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-900 dark:text-white"
        autoFocus
      />
      <div className="mt-2 flex-1 overflow-y-auto max-h-[200px]">
        {loading && (
          <div className="text-xs text-gray-500 py-2">
            {lang === "zh" ? "搜索中…" : "Searching…"}
          </div>
        )}
        {!loading && q.trim().length >= 2 && results.length === 0 && (
          <div className="text-xs text-gray-500 py-2">
            {lang === "zh" ? "没找到匹配的工具" : "No matches"}
          </div>
        )}
        {!loading && q.trim().length < 2 && (
          <div className="text-xs text-gray-400 py-2 italic">
            {lang === "zh"
              ? "至少输入 2 个字符开始搜索"
              : "Type at least 2 characters to search"}
          </div>
        )}
        <ul className="space-y-1">
          {results.map((s) => (
            <li key={s.id}>
              <button
                onClick={() => onSelect(s)}
                className="w-full text-left px-3 py-2 rounded-md hover:bg-indigo-50 dark:hover:bg-indigo-950/40 transition-colors flex items-center gap-2"
              >
                {s.author_avatar_url && (
                  <img
                    src={s.author_avatar_url}
                    alt=""
                    className="w-6 h-6 rounded-full flex-shrink-0"
                    loading="lazy"
                  />
                )}
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {s.repo_name}
                  </div>
                  <div className="text-xs text-gray-500 truncate">
                    {s.repo_full_name} · ★ {s.stars.toLocaleString()}
                  </div>
                </div>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
