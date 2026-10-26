/**
 * A scenario page's `explainer` (scenario-keywords.json): what the thing is, then the
 * few entries to start with, one heading each, right after the quick pick.
 *
 * Google's AI Overview for "ppt skill" (10-26) took its opening definition from a
 * "What is a Claude PPT skill?" section and its list from the five H3s under "The best
 * Claude PPT skills" on an open-design.ai post; our page had no definition and was cited
 * for one card's description. This gives the page the same two shapes, with our test
 * results as the reason for each pick.
 *
 *   "explainer": {
 *     "what": { "h2": "...", "h2_zh": "...", "text": "...", "text_zh": "..." },
 *     "top": { "h2": "...", "h2_zh": "...", "note": "...", "note_zh": "...",
 *              "items": [{ "repo": "owner/name", "line": "...", "line_zh": "..." }] }
 *   }
 */
import { SITE, esc, starsK, biAttrs } from "./shared-utils.mjs";

const P_STYLE = "color:var(--bp-text-secondary);line-height:1.8;font-size:15px;margin:0 0 12px";
const H3_STYLE = "font-size:17px;margin:18px 0 6px";

function para(en, zh, style = P_STYLE) {
  return `<p style="${style}" ${biAttrs(en, zh || en)}>${esc(en)}</p>`;
}

function whatHtml(w) {
  return `<section id="what-is" style="margin:32px 0">
        <h2 class="bp-section-title" ${biAttrs(w.h2, w.h2_zh || w.h2)}>${esc(w.h2)}</h2>
        ${para(w.text, w.text_zh)}
      </section>`;
}

// A listed repo the page no longer carries (renamed, removed) is skipped, not linked to a 404.
function itemHtml(item, i, byRepo) {
  const s = byRepo.get(item.repo.toLowerCase());
  if (!s) return "";
  const link = `<a href="${SITE}/skill/${esc(s.repo_full_name)}/" style="color:var(--bp-link);text-decoration:none">${esc(s.repo_name)}</a>`;
  const meta = `<span style="color:var(--bp-text-muted);font-size:13px;font-weight:400"> ★ ${starsK(s.stars)}</span>`;
  return `<h3 style="${H3_STYLE}">${i + 1}. ${link}${meta}</h3>
        ${para(item.line, item.line_zh)}`;
}

function topHtml(t, skills) {
  const byRepo = new Map(skills.map((s) => [s.repo_full_name.toLowerCase(), s]));
  const items = t.items.map((item, i) => itemHtml(item, i, byRepo)).filter(Boolean);
  if (!items.length) return "";
  const note = t.note ? para(t.note, t.note_zh, `${P_STYLE};font-size:13px`) : "";
  return `<section id="top-picks" style="margin:32px 0">
        <h2 class="bp-section-title" ${biAttrs(t.h2, t.h2_zh || t.h2)}>${esc(t.h2)}</h2>
        ${items.join("\n        ")}
        ${note}
      </section>`;
}

/** Both sections, or "" when the scenario has no explainer. */
export function explainerHtml(scenario, skills) {
  const e = scenario.explainer;
  if (!e) return "";
  return [e.what ? whatHtml(e.what) : "", e.top ? topHtml(e.top, skills) : ""].filter(Boolean).join("\n      ");
}
