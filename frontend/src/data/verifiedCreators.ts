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
 * Seed list — these are Hub's hand-picked founding verified creators.
 * Real commercial verification happens via the /verified-creator/ application page.
 */
export const VERIFIED_CREATORS: VerifiedCreator[] = [
  // Real commercialization cases referenced in the strategic article
  {
    github: "lovstudio",
    name: "南川 (lovstudio)",
    since: "2026-04",
    tier: "founding",
    tagline:
      "Agent Skill 商业化三角不可能定理作者。Lovstudio pro-skills 年费会员制。",
    contact: { website: "https://lovstudio.ai/agent" },
  },
  {
    github: "tw93",
    name: "tw93",
    since: "2026-04",
    tier: "founding",
    tagline: "Waza 系列 Skill 作者。Pake、kami 等项目创作者。",
    contact: { x: "@HiTw93" },
  },
  {
    github: "antfu",
    name: "Anthony Fu",
    since: "2026-04",
    tier: "founding",
    tagline: "Vue/Nuxt/Vite 核心维护者。antfu/skills 作者。",
    contact: { x: "@antfu7", website: "https://antfu.me" },
  },
  {
    github: "garrytan",
    name: "Garry Tan",
    since: "2026-04",
    tier: "founding",
    tagline: "YC CEO。gstack Claude Code 15 Skill 工程团队框架。",
    contact: { x: "@garrytan" },
  },
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
