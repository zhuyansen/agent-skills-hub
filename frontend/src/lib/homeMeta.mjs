/**
 * The home page's titles and where its Chinese twin lives. Shared by the React home page (what
 * Google indexes, since it renders JS) and scripts/generate-home-zh.mjs (what non-JS crawlers
 * and AI bots read at /zh/), so the two versions of the page can never disagree.
 *
 * Both titles lead with the site name run together, "AgentSkillsHub": Google gives one site
 * name to one global site, and agentskillshub.dev holds "Agent Skills Hub" (index.html, 11-03).
 */

export const ZH_HOME_PATH = "/zh/";

export const HOME_TITLE = "AgentSkillsHub — Claude Skills Marketplace, Security-Graded";

export const ZH_HOME_TITLE = "AgentSkillsHub —— Claude Skills 市场，热门 Skill 均有安全评级";

/** Whether `pathname` is the Chinese twin. GitHub Pages sends /zh to /zh/; a client-side route may not. */
export const isZhHomePath = (pathname) => pathname === ZH_HOME_PATH || pathname === "/zh";
