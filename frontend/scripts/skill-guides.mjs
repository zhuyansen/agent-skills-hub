/**
 * The /best/ guides a skill is listed on, for the "Featured in" line of its /skill/ page: the
 * static page shows the links, and <meta name="ash:best"> hands them to the React page that
 * Google renders (src/lib/prerenderedMeta.ts, src/components/FeaturedInGuides.tsx).
 *
 * Until 2026-11-07 only a guide's curated `featured` list counted, so a reviewed guide without
 * one got no link from its own skills: none of the 248 on /best/image-generation/ linked to it,
 * and /skill/heydamir/unslop/ (1,363 search impressions on 2026-11-04) did not link to
 * /best/anti-slop/. A reviewed guide's whole list counts now (scenario-kinds.json, less
 * `exclude_repos`), the way the guide itself lists it.
 */
import { esc } from "./shared-utils.mjs";

// No repo was on more than three guides when this was written; the cap keeps the line short.
const MAX_GUIDES = 3;

function guideOf(sc, zh) {
  return { slug: sc.slug, title: sc.title, titleZh: zh[sc.slug]?.t || sc.title };
}

/** Lowercased owner/repo of every repo a guide lists: its featured ones, and its reviewed list
 *  when it is a reviewed guide. Sub-skill keys (owner/repo/path) have pages of their own. */
function listedRepos(sc, kinds) {
  const dropped = new Set((sc.match?.exclude_repos || []).map((n) => n.toLowerCase()));
  const reviewed = sc.match?.reviewed_only ? Object.keys(kinds[sc.slug]?.repos || {}) : [];
  const names = [...(sc.match?.featured || []), ...reviewed].map((n) => n.toLowerCase());
  return new Set(names.filter((n) => n.split("/").length === 2 && !dropped.has(n)));
}

/** owner/repo (lowercased) → the live guides that list it, in scenario-keywords.json order. */
export function guidesIndex(scenarios, kinds, zh = {}) {
  const index = new Map();
  for (const sc of scenarios.filter((s) => !s.retired)) {
    for (const name of listedRepos(sc, kinds)) {
      if (!index.has(name)) index.set(name, []);
      index.get(name).push(guideOf(sc, zh));
    }
  }
  return index;
}

/** The static line in the page's language; "" when no guide lists the skill. */
export function guidesHtml(guides, lang, label) {
  if (!guides.length) return "";
  const links = guides.slice(0, MAX_GUIDES).map((g) =>
    `<a href="/best/${esc(g.slug)}/" style="color:#4f46e5;text-decoration:none">${esc(lang === "zh" ? g.titleZh : g.title)}</a>`);
  return `<p style="margin:0 0 16px;font-size:14px;color:#475569">
        ${label} ${links.join(" &middot; ")}
      </p>`;
}

/** The same guides for the React page, as a <meta> in the head; "" when none. */
export function guidesMeta(guides) {
  if (!guides.length) return "";
  return `\n  <meta name="ash:best" content="${esc(JSON.stringify(guides.slice(0, MAX_GUIDES)))}" />`;
}
