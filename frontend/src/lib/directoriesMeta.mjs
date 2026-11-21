/**
 * Where /agent-skills-directories/ lives, its title, description and dates. Shared by the static
 * generator (scripts/generate-directories-page.mjs), the React page (src/pages/DirectoriesPage.tsx),
 * the sitemap and the link from /how-we-grade/, so the two versions of the page never disagree.
 *
 * Kept apart from the page text (directoriesContent.mjs, directoryEntries.mjs): /how-we-grade/
 * links here, and its chunk should not carry this page's text.
 */

export const DIRECTORIES_PATH = "/agent-skills-directories/";
export const DIRECTORIES_URL = `https://agentskillshub.top${DIRECTORIES_PATH}`;

/**
 * How many directories the page compares, as its title states. scripts/directories-content.test.mjs
 * checks it against the entries in directoryEntries.mjs: change both together.
 */
export const COMPARED_COUNT = 15;

/** The day each directory's own pages were read. Re-read them all before changing it. */
export const FACTS_READ_ON = "2026-11-09";
const YEAR = FACTS_READ_ON.split("-")[0];

/** First published. */
export const DIRECTORIES_PUBLISHED = "2026-11-10";
/**
 * The Article's dateModified, which the sitemap reads as lastmod: bump it whenever the text
 * changes, never on a rebuild.
 */
export const DIRECTORIES_UPDATED = "2026-11-17";

/** The page's heading; the Chinese title adds the site name, the English one is shorter. */
export const DIRECTORIES_HEADLINE = {
  en: `Where to Find Agent Skills and MCP Servers: ${COMPARED_COUNT} Directories Compared (${YEAR})`,
  zh: `去哪找 Agent Skills 和 MCP 服务器：${COMPARED_COUNT} 个目录对比（${YEAR}）`,
};

export const DIRECTORIES_META = {
  en: {
    // Not the headline plus the site name: that ran 93 characters (OpenSEO audit 2026-11-18).
    title: `Agent Skills & MCP Server Directories: ${COMPARED_COUNT} Compared (${YEAR})`,
    description: `${COMPARED_COUNT} directories of agent skills and MCP servers, ours included, compared from their own pages: listings, security checks, paid options and agent access.`,
  },
  zh: {
    title: `${DIRECTORIES_HEADLINE.zh} | Agent Skills Hub`,
    description: `根据各站自己的页面，对比 ${COMPARED_COUNT} 个 agent skill 和 MCP 服务器目录（含本站）：收录什么、安全检查读什么、有哪些付费项、agent 能不能直接搜。`,
  },
};

/** The breadcrumb's name for the page. */
export const DIRECTORIES_LINK = { en: "Directories compared", zh: "目录对比" };
