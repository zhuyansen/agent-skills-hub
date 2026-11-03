/**
 * The home page's crawlable skill lists, written into dist/index.html at build time from the rows
 * the skill-page build already fetched. The React home page renders its lists only in the browser,
 * so a crawler that runs no JavaScript (most AI crawlers) saw categories and scenarios in the
 * pre-hydration copy but not one skill, while agentskillshub.dev, which outranks us for our own
 * name, ships its whole directory in the HTML (2026-11-03).
 *
 * The lists link only to skill pages that ask to be indexed, and leave out NSFW repos, which stay
 * off every curated list (owner's rule, 2026-10-27).
 */
import { esc, isIndexedSkillPage } from "./shared-utils.mjs";

/** Where the lists go, inside the home copy between the SHELL-CONTENT markers of index.html. */
export const HOME_LISTS_MARKER = "<!--HOME-LISTS-->";

const LIST_SIZE = 10;
const PER_CATEGORY = 5;
const DESCRIPTION_LIMIT = 120;
const NSFW = /\bnsfw\b|porn|hentai|nude|erotic/i;
const CATEGORIES = ["mcp-server", "claude-skill", "codex-skill", "agent-tool"];

/** Headings and intros of the English home page and of its Chinese twin at /zh/. */
const COPY = {
  en: {
    rising: ["Rising now", "The repositories gaining stars fastest right now."],
    rated: ["Highest rated", "The highest quality scores in the directory."],
    category: (label) => [`Most-starred ${label}`, `The most-starred ${label} in the directory.`],
    labels: { "mcp-server": "MCP servers", "claude-skill": "Claude skills", "codex-skill": "Codex skills", "agent-tool": "agent tools" },
    stars: "stars",
  },
  zh: {
    rising: ["正在走红", "近期 Star 涨得最快的仓库。"],
    rated: ["评分最高", "目录里质量评分最高的项目。"],
    category: (label) => [`Star 最多的${label}`, `目录里 Star 最多的${label}。`],
    labels: { "mcp-server": " MCP 服务器", "claude-skill": " Claude 技能", "codex-skill": " Codex 技能", "agent-tool": " Agent 工具" },
    stars: "Star",
  },
};

/** Topics arrive from the REST API as one string; a test or another caller may pass an array. */
const topicsText = (topics) => (Array.isArray(topics) ? topics.join(" ") : String(topics ?? ""));
const isNsfw = (s) => NSFW.test(`${s.repo_full_name} ${s.description ?? ""} ${topicsText(s.topics)}`);
const hasPage = (s) => s.repo_full_name.split("/").length === 2 && isIndexedSkillPage(s);
const listable = (s) => hasPage(s) && !isNsfw(s);

function shortDescription(text) {
  const t = (text ?? "").replace(/\s+/g, " ").trim();
  return t.length > DESCRIPTION_LIMIT ? `${t.slice(0, DESCRIPTION_LIMIT - 1).trimEnd()}…` : t;
}

function itemHtml(s, copy) {
  const about = shortDescription(s.description);
  return `<li><a href="/skill/${esc(s.repo_full_name)}/">${esc(s.repo_full_name)}</a>` +
    `${about ? ` — ${esc(about)}` : ""} (${s.stars.toLocaleString("en-US")} ${copy.stars})</li>`;
}

function sectionHtml([heading, intro], rows, copy) {
  if (!rows.length) return "";
  const items = rows.map((s) => itemHtml(s, copy)).join("");
  return `<section><h2>${heading}</h2><p>${intro}</p><ol>${items}</ol></section>`;
}

/** The `n` rows highest on `key` (above zero), ties broken by stars. */
function top(rows, key, n) {
  return rows
    .filter((s) => (s[key] ?? 0) > 0)
    .sort((a, b) => b[key] - a[key] || b.stars - a.stars)
    .slice(0, n);
}

/** The lists for `skills`, in English or Chinese (`lang` "en" or "zh"): rising now, highest
 *  rated, and the most starred of each main category. */
export function homeListsHtml(skills, lang = "en") {
  const copy = COPY[lang];
  const rows = skills.filter(listable);
  const categories = CATEGORIES.map((category) => sectionHtml(
    copy.category(copy.labels[category]),
    top(rows.filter((s) => s.category === category), "stars", PER_CATEGORY),
    copy,
  ));
  return [
    sectionHtml(copy.rising, top(rows, "star_momentum", LIST_SIZE), copy),
    sectionHtml(copy.rated, top(rows, "score", LIST_SIZE), copy),
    ...categories,
  ].filter(Boolean).join("\n        ");
}

/** `html` with the lists in place of the marker; unchanged when the marker is missing. A function
 *  replacement, so a "$&" in some description is written as is. */
export function stampHomeLists(html, listsHtml) {
  return html.replace(HOME_LISTS_MARKER, () => listsHtml);
}
