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
const CATEGORIES = [
  ["mcp-server", "MCP servers"],
  ["claude-skill", "Claude skills"],
  ["codex-skill", "Codex skills"],
  ["agent-tool", "agent tools"],
];

/** Topics arrive from the REST API as one string; a test or another caller may pass an array. */
const topicsText = (topics) => (Array.isArray(topics) ? topics.join(" ") : String(topics ?? ""));
const isNsfw = (s) => NSFW.test(`${s.repo_full_name} ${s.description ?? ""} ${topicsText(s.topics)}`);
const hasPage = (s) => s.repo_full_name.split("/").length === 2 && isIndexedSkillPage(s);
const listable = (s) => hasPage(s) && !isNsfw(s);

function shortDescription(text) {
  const t = (text ?? "").replace(/\s+/g, " ").trim();
  return t.length > DESCRIPTION_LIMIT ? `${t.slice(0, DESCRIPTION_LIMIT - 1).trimEnd()}…` : t;
}

function itemHtml(s) {
  const about = shortDescription(s.description);
  return `<li><a href="/skill/${esc(s.repo_full_name)}/">${esc(s.repo_full_name)}</a>` +
    `${about ? ` — ${esc(about)}` : ""} (${s.stars.toLocaleString("en-US")} stars)</li>`;
}

function sectionHtml(heading, intro, rows) {
  if (!rows.length) return "";
  return `<section><h2>${heading}</h2><p>${intro}</p><ol>${rows.map(itemHtml).join("")}</ol></section>`;
}

/** The `n` rows highest on `key` (above zero), ties broken by stars. */
function top(rows, key, n) {
  return rows
    .filter((s) => (s[key] ?? 0) > 0)
    .sort((a, b) => b[key] - a[key] || b.stars - a.stars)
    .slice(0, n);
}

/** The lists for `skills`: rising now, highest rated, and the most starred of each main category. */
export function homeListsHtml(skills) {
  const rows = skills.filter(listable);
  const categories = CATEGORIES.map(([category, label]) => sectionHtml(
    `Most-starred ${label}`,
    `The most-starred ${label} in the directory.`,
    top(rows.filter((s) => s.category === category), "stars", PER_CATEGORY),
  ));
  return [
    sectionHtml("Rising now", "The repositories gaining stars fastest right now.", top(rows, "star_momentum", LIST_SIZE)),
    sectionHtml("Highest rated", "The highest quality scores in the directory.", top(rows, "score", LIST_SIZE)),
    ...categories,
  ].filter(Boolean).join("\n        ");
}

/** `html` with the lists in place of the marker; unchanged when the marker is missing. A function
 *  replacement, so a "$&" in some description is written as is. */
export function stampHomeLists(html, listsHtml) {
  return html.replace(HOME_LISTS_MARKER, () => listsHtml);
}
