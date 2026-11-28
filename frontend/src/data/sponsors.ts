/**
 * TrustMRR-style left & right homepage sponsor rail inventory.
 *
 * Editorial neutrality rule:
 *   - Every paid external slot is explicitly labeled "Sponsored" and uses
 *     `rel="sponsored noopener noreferrer"`.
 *   - Sponsorship buys homepage visibility ONLY — never a SAFE grade, audit override,
 *     or organic ranking slot on /best/* guides.
 *
 * Unfilled paid seats automatically render sleek house cards (pointing to our own
 * internal tools/products) above the TrustMRR-style dashed "Advertise" card so the
 * desktop rails always look balanced and complete. Adding a paid sponsor to
 * `LEFT_SPONSORS` or `RIGHT_SPONSORS` seamlessly takes over a seat.
 */

export type SponsorTheme = "emerald" | "indigo" | "violet" | "rose" | "blue" | "amber" | "teal" | "sky";

export interface SponsorSlot {
  id: string;
  name: string;
  nameZh?: string;
  tagline: string;
  taglineZh?: string;
  url: string;
  /** Short 1–2 char monogram or icon label when no logoUrl is provided. */
  badge: string;
  /** Optional square icon URL (32x32). */
  logoUrl?: string;
  /** Tinted card surface theme (TrustMRR-style moody glass). */
  theme: SponsorTheme;
  /** True for paid external sponsors (adds rel="sponsored" & disclosure tag). */
  sponsored?: boolean;
}

export interface TopBannerConfig {
  badge: string;
  badgeZh: string;
  prefix: string;
  prefixZh: string;
  tagline: string;
  taglineZh: string;
  url: string;
  /** True when occupied by a paid external title sponsor (adds rel="sponsored"). */
  sponsored?: boolean;
}

/**
 * Full-width top announcement / title-sponsor bar (mcp.so style).
 * Swap to a paid brand (`sponsored: true`) whenever the top-banner slot sells.
 */
export const TOP_BANNER_SPONSOR: TopBannerConfig = {
  prefix: "Launch Promo",
  prefixZh: "限时特惠",
  badge: "Fast-Track $19",
  badgeZh: "48h 加急审核 $19",
  tagline: "48h priority security review (was $49) — or book a $69/mo homepage rail slot",
  taglineZh: "48 小时优先安全初审（原价 $49）· 或预订 $69/月 首页双侧边栏赞助位",
  url: "/submit/",
  sponsored: false,
};

export const SLOTS_PER_SIDE = 5;
export const TOTAL_SPONSOR_SLOTS = SLOTS_PER_SIDE * 2;

/** Paid external sponsors on the left rail (add here as slots sell). */
export const LEFT_SPONSORS: SponsorSlot[] = [];

/** Paid external sponsors on the right rail (add here as slots sell). */
export const RIGHT_SPONSORS: SponsorSlot[] = [];

/** Internal house cards shown in unsold left seats (replaced 1-for-1 as sponsors book). */
export const LEFT_HOUSE_CARDS: SponsorSlot[] = [
  {
    id: "house-analyzer",
    name: "Security Analyzer",
    nameZh: "免费安全审计",
    tagline: "Audit any GitHub skill or MCP server across 44 rules",
    taglineZh: "44 条规则一键扫描任意 GitHub Skill / MCP",
    url: "/analyzer/",
    badge: "🛡️",
    theme: "emerald",
  },
  {
    id: "house-fasttrack",
    name: "Fast-Track · $19",
    nameZh: "加急收录 · $19",
    tagline: "48h priority security review & verdict card (was $49)",
    taglineZh: "48 小时优先安全初审与实测卡片（原价 $49）",
    url: "/submit/",
    badge: "⚡",
    theme: "violet",
  },
  {
    id: "house-bluebook",
    name: "Agent Blue Book",
    nameZh: "Agent 蓝皮书",
    tagline: "Practical handbook for shipping safe AI skills",
    taglineZh: "构建安全 AI Agent Skill 的开源实战指南",
    url: "/book/",
    badge: "📘",
    theme: "blue",
  },
  {
    id: "house-daily",
    name: "Daily Top 10",
    nameZh: "每日精选 Top 10",
    tagline: "Fresh trending Claude skills & MCP servers every day",
    taglineZh: "每日严选高增长 Claude Skill 与 MCP 工具",
    url: "/daily/",
    badge: "🔥",
    theme: "teal",
  },
];

/** Internal house cards shown in unsold right seats (replaced 1-for-1 as sponsors book). */
export const RIGHT_HOUSE_CARDS: SponsorSlot[] = [
  {
    id: "house-pro",
    name: "Pro Security Board",
    nameZh: "Pro 安全看板",
    tagline: "Watchlists, drift alerts & CVE monitoring for teams",
    taglineZh: "团队监控列表、规则漂移告警与持续巡检",
    url: "/pro/",
    badge: "✦",
    theme: "rose",
  },
  {
    id: "house-cigate",
    name: "CI/CD Security Gate",
    nameZh: "CI/CD 安全门禁",
    tagline: "Block unsafe skills in GitHub Actions before merge",
    taglineZh: "合并前在 GitHub Actions 自动拦截高危 Skill",
    url: "/ci-gate/",
    badge: "🔒",
    theme: "indigo",
  },
  {
    id: "house-guides",
    name: "Tested Best Guides",
    nameZh: "实测场景榜单",
    tagline: "Hands-on benchmarks across video, PPT & coding",
    taglineZh: "视频、PPT、生图与编程全场景真机实测榜单",
    url: "/best/",
    badge: "★",
    theme: "amber",
  },
  {
    id: "house-compare",
    name: "Skill Compare",
    nameZh: "横向对比工具",
    tagline: "Compare any two skills across 9 quality dimensions",
    taglineZh: "按 9 项质量与安全维度横向对比同类 Skill",
    url: "/compare/",
    badge: "⚖️",
    theme: "sky",
  },
];
