/**
 * A scenario page's `caution` section (scenario-keywords.json): repositories a reader
 * may land on by mistake, named so they can tell them from the original. First used on
 * ai-reverse-engineering (2026-10-13) for copies of morluto/rea.
 *
 *   "caution": { "h2", "body", "official": "owner/repo", "columns": [[en, zh], ...],
 *                "rows": [{ "repo", "stars", "note" }] }
 * Text fields have a `_zh` twin. Rows link to GitHub, not to a page of ours: these
 * repositories are deliberately not listed.
 */
import { esc, biAttrs } from "./shared-utils.mjs";

const bi = (o, key) => biAttrs(o[key], o[`${key}_zh`] || o[key]);

function row(r) {
  return `<tr>
          <td><a href="https://github.com/${esc(r.repo)}" target="_blank" rel="noopener nofollow">${esc(r.repo)}</a></td>
          <td style="text-align:right">${Number(r.stars).toLocaleString("en-US")}</td>
          <td ${bi(r, "note")}>${esc(r.note)}</td>
        </tr>`;
}

export function cautionHtml(scenario) {
  const c = scenario.caution;
  if (!c) return "";
  const head = c.columns.map(([en, zh]) => `<th ${biAttrs(en, zh)}>${esc(en)}</th>`).join("");
  return `
      <section id="copies" class="bp-aeo-section" style="margin:32px 0;padding:24px;background:var(--bp-bg-alt);border-radius:12px;border:1px solid var(--bp-border)">
        <h2 class="bp-section-title" style="font-size:20px;margin-bottom:12px" ${bi(c, "h2")}>${esc(c.h2)}</h2>
        <p ${bi(c, "body")}>${esc(c.body)}</p>
        <div class="bp-table-wrap"><table class="bp-table"><thead><tr>${head}</tr></thead><tbody>${c.rows.map(row).join("")}</tbody></table></div>
      </section>`;
}
