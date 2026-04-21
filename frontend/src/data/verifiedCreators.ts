/**
 * Verified Creators — Hub-认证的付费 Skill 作者名单。
 * 基于 2026-04-21 的 AgentSkillsHub 战略文章。
 *
 * 加入方式：https://agentskillshub.top/verified-creator/
 * 年费：¥999/年（首批早鸟价 ¥699/年）
 *
 * 认证权益：
 * - 详情页 ✓ 认证徽章
 * - Trending 榜轻微加权
 * - 作者主页定制（咨询/订阅/社群入口）
 * - 月度数据报表（访问量、转化、来源）
 */

export interface VerifiedCreator {
  /** GitHub username (lowercase, matches author_name field in skills table) */
  github: string;
  /** Display name */
  name: string;
  /** Year verified since */
  since: string;
  /** Creator tier */
  tier: "founding" | "pro" | "basic";
  /** Short tagline shown on creator card */
  tagline?: string;
  /** Contact channels */
  contact?: {
    x?: string;
    email?: string;
    wechat?: string;
    website?: string;
  };
}

/**
 * Real Verified Creators only. NEVER add someone here without their explicit consent.
 *
 * Entries must satisfy ALL of:
 *   1. Creator has applied via /verified-creator/ (email or DM to @GoSailGlobal)
 *   2. Creator has paid the annual fee OR been explicitly gifted founding status
 *   3. Hub has replied and confirmed admission (with tier, tagline, contact channels
 *      they want publicly shown)
 *
 * Unauthorized listing = privacy violation + misrepresentation. Never bulk-seed.
 */
export const VERIFIED_CREATORS: VerifiedCreator[] = [
  // No verified creators yet. The program just launched on 2026-04-21 and is
  // invitation-only for the first cohort. Creators who apply and are admitted
  // will appear here (one entry per creator, with their consented contact info).
];

/**
 * Lowercase lookup for O(1) badge check.
 */
export const VERIFIED_CREATORS_SET: Set<string> = new Set(
  VERIFIED_CREATORS.map((c) => c.github.toLowerCase()),
);

export function isVerifiedCreator(
  githubUsername: string | null | undefined,
): boolean {
  if (!githubUsername) return false;
  return VERIFIED_CREATORS_SET.has(githubUsername.toLowerCase());
}

export function getVerifiedCreator(
  githubUsername: string | null | undefined,
): VerifiedCreator | undefined {
  if (!githubUsername) return undefined;
  return VERIFIED_CREATORS.find(
    (c) => c.github.toLowerCase() === githubUsername.toLowerCase(),
  );
}
