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
 *     "top": { "h2": "...", "h2_zh": "...", "note": "...", "note_zh": "...", "numbered": false,
 *              "items": [{ "repo": "owner/name", "label": "optional shown name", "line": "...", "line_zh": "..." }] }
 *   }
 *
 * `numbered: false` drops the "1." in front of each pick: for a list that is not a ranking, such
 * as the image generation picks, chosen from the test for a look of their own.
 */
import { SITE, esc, starsK, biAttrs } from "./shared-utils.mjs";
import { modelsHtml, baselineHtml, pickFigureHtml } from "./scenario-image-test.mjs";

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
// `label` overrides the shown name when the repo name alone says nothing (scenario-labs/skills is "skills").
// With a test run that published pictures (the image page), each pick shows what it drew.
function itemHtml(item, rank, s, run) {
  const link = `<a href="${SITE}/skill/${esc(s.repo_full_name)}/" style="color:var(--bp-link);text-decoration:none">${esc(item.label || s.repo_name)}</a>`;
  const meta = `<span style="color:var(--bp-text-muted);font-size:13px;font-weight:400"> ★ ${starsK(s.stars)}</span>`;
  return `<h3 style="${H3_STYLE}">${rank}${link}${meta}</h3>
        ${para(item.line, item.line_zh)}${pickFigureHtml(run, s.repo_full_name)}`;
}

function topHtml(t, skills, run) {
  const byRepo = new Map(skills.map((s) => [s.repo_full_name.toLowerCase(), s]));
  // Numbered by position among the picks the page still carries, so a dropped one leaves no gap.
  const kept = t.items.map((item) => [item, byRepo.get(item.repo.toLowerCase())]).filter(([, s]) => s);
  const items = kept.map(([item, s], i) => itemHtml(item, t.numbered === false ? "" : `${i + 1}. `, s, run));
  if (!items.length) return "";
  const note = t.note ? para(t.note, t.note_zh, `${P_STYLE};font-size:13px`) : "";
  return `<section id="top-picks" style="margin:32px 0">
        <h2 class="bp-section-title" ${biAttrs(t.h2, t.h2_zh || t.h2)}>${esc(t.h2)}</h2>
        ${baselineHtml(run)}
        ${items.join("\n        ")}
        ${note}
      </section>`;
}

/** The sections, or "" when the scenario has no explainer. A test run with a model line-up (the image
 *  page) puts it between the definition and the picks: which model to use comes before which skill. */
export function explainerHtml(scenario, skills, run = null) {
  const e = scenario.explainer;
  if (!e) return "";
  return [e.what ? whatHtml(e.what) : "", modelsHtml(run), e.top ? topHtml(e.top, skills, run) : ""].filter(Boolean).join("\n      ");
}
