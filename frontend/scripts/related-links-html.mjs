/**
 * HTML for the recently-added and random link blocks (related-links.mjs picks them) and for the
 * line under a static page that links the A–Z directory (generate-browse-pages.mjs).
 */
import { esc, starsK } from "./shared-utils.mjs";
import { displayName } from "../src/lib/repoBrand.mjs";
import { BROWSE_PATH } from "./browse-pages.mjs";

const LINK = "color:#4f46e5;text-decoration:none";
const MUTED = "color:#94a3b8;font-size:13px";

function skillItem(s) {
  return `
          <li style="margin:4px 0"><a href="/skill/${esc(s.repo_full_name)}/" style="${LINK}">${esc(displayName(s.repo_full_name, s.repo_name))}</a> <span style="${MUTED}">⭐ ${starsK(s.stars)}</span></li>`;
}

function section(title, intro, items) {
  return `<section style="margin-top:20px">
        <h2 style="font-size:18px;color:#1e293b;margin-bottom:8px">${title}</h2>
        <p style="color:#64748b;font-size:14px;margin-bottom:8px">${intro}</p>
        <ul style="list-style:none;padding:0">${items.map(skillItem).join("")}
        </ul>
      </section>`;
}

/** The two blocks on a /skill/ page, in the page's language (`c` is skillCopy(lang)). */
export function skillLinkBlocks({ recent, random }, c, catText) {
  return [
    recent.length ? section(c.recentTitle(catText), c.recentIntro, recent) : "",
    random.length ? section(c.randomTitle, c.randomIntro, random) : "",
  ].filter(Boolean).join("\n      ");
}

/** The same two blocks on an /audit/ page (English, like the rest of it). */
export function auditLinkBlocks({ recent, random }, catLabel, gradeLabel) {
  const item = (r) => `<li><a href="/audit/${esc(r.repo_full_name)}/" style="${LINK}">Is ${esc(displayName(r.repo_full_name, r.repo_name))} safe?</a> <span style="color:#94a3b8">— ${gradeLabel(r)} · ★ ${starsK(r.stars)}</span></li>`;
  const block = (title, list) => `
    <h2 style="font-size:18px;margin:24px 0 8px">${title}</h2>
    <ul style="line-height:1.9;color:#475569;padding-left:20px;font-size:14px">
      ${list.map(item).join("\n      ")}
    </ul>`;
  return [
    recent.length ? block(`Recently added ${esc(catLabel)} audits`, recent) : "",
    random.length ? block("More security audits", random) : "",
  ].join("");
}

/** The line under a static page that links the A–Z directory. `labels` = [skills, audits]. */
export function browseFooter([skills, audits], style = "") {
  return `<p style="margin:24px 0 0;padding-top:12px;border-top:1px solid #e2e8f0;font-size:13px;color:#64748b${style}">
        <a href="${BROWSE_PATH}#skills" style="${LINK}">${skills}</a> &middot; <a href="${BROWSE_PATH}#audits" style="${LINK}">${audits}</a>
      </p>`;
}

/** The two related lists as JSON for <meta name="ash:related">, which the React page reads. */
export function relatedMeta({ recent, random }) {
  const row = (s) => [s.repo_full_name, displayName(s.repo_full_name, s.repo_name), s.stars || 0];
  if (!recent.length && !random.length) return "";
  return `\n  <meta name="ash:related" content="${esc(JSON.stringify({ recent: recent.map(row), random: random.map(row) }))}" />`;
}
