/**
 * The image generation page's test blocks (scenario-runs.json "image-generation", written by
 * ops/image-runs/evidence.py), so the results sit on the page and not one click away (owner,
 * 2026-11-07: "the results go on the page"; 2026-11-08: plan A).
 *
 * modelsHtml: the model line-up, one poster per model, in the explainer before the picks.
 * baselineHtml / pickFigureHtml: what Claude Code drew with no skill, then each pick's pictures.
 * imageTableHtml: every skill that made a picture, a strip of its pictures in each row, with a
 * filter by result; every row shows until the script runs (and without JavaScript).
 * Pictures are lazy-loaded with their size set, so nothing shifts as they arrive.
 */
import { esc, biAttrs } from "./shared-utils.mjs";

const span = ([en, zh]) => `<span ${biAttrs(en, zh)}>${esc(en)}</span>`;
const th = ([en, zh]) => `<th ${biAttrs(en, zh)}>${esc(en)}</th>`;
const link = (href, inner) => `<a href="${esc(href)}" target="_blank" rel="noopener">${inner}</a>`;

function img(run, p, alt) {
  return `<img src="${esc(run.dir + p.src)}" alt="${esc(alt)}" width="${p.w}" height="${p.h}" loading="lazy">`;
}

function modelRow(run, r) {
  const lines = r.lines == null ? "-" : `${r.lines}/6`;
  const cls = r.lines == null ? "" : r.lines === 6 ? " bp-tr-touch-ups" : " bp-tr-substantial";
  const note = r.note ? `<br><span class="bp-tr-note" ${biAttrs(...r.note)}>${esc(r.note[0])}</span>` : "";
  const time = r.seconds ? [`${r.seconds} s`, `${r.seconds} 秒`] : ["-", "-"];
  const poster = r.thumb ? link(run.dir + r.full, img(run, { src: r.thumb, w: r.w, h: r.h }, `The poster ${r.label} drew`)) : "";
  return `<tr><td class="bp-tr-skill"><b>${esc(r.label)}</b>${note}</td><td class="bp-tr-num${cls}">${lines}</td>
    <td class="bp-tr-num">${r.cost ? `$${r.cost.toFixed(3)}` : "-"}</td><td class="bp-tr-num" ${biAttrs(...time)}>${time[0]}</td><td class="bp-im-thumb">${poster}</td></tr>`;
}

/** The model line-up table, or "" on a page without one. */
export function modelsHtml(run) {
  const m = run?.models;
  if (!m) return "";
  return `<section id="models" style="margin:32px 0">
        <h2 class="bp-section-title" ${biAttrs(...m.title)}>${esc(m.title[0])}</h2>
        <p class="bp-tr-intro" ${biAttrs(...m.note)}>${esc(m.note[0])}</p>
        <div class="bp-table-wrap"><table class="bp-table bp-tr-table"><thead><tr>${m.columns.map(th).join("")}</tr></thead>
        <tbody>${m.rows.map((r) => modelRow(run, r)).join("")}</tbody></table></div>
      </section>`;
}

/** What Claude Code drew with no skill, above the picks, so each pick's look has something to differ from. */
export function baselineHtml(run) {
  const c = run?.control;
  if (!c?.pick) return "";
  return `<figure class="bp-im-pick">${link(run.dir + c.sheet, img(run, c.pick, "What Claude Code drew with no skill: the poster, a mascot and the bag"))}
        <figcaption>${span(c.caption)} ${link(run.dir + c.sheet, span(c.label))}</figcaption></figure>`;
}

/** A pick's poster, mascot and bag from the test, linking to all six; "" when it has none. */
export function pickFigureHtml(run, repo) {
  const r = run?.runs?.[repo];
  if (!r?.pick) return "";
  return `<figure class="bp-im-pick">${link(run.dir + r.sheet, img(run, r.pick, `${repo.split("/")[1]}: the poster, a mascot and the bag from our test`))}
        <figcaption>${link(run.dir + r.sheet, span(run.see))}</figcaption></figure>`;
}

function filterBar(run, ran) {
  const hits = (id) => ran.filter(([, r]) => id === "all" || r.group === id || (id === "own" && r.look === "own")).length;
  const buttons = run.filters.map((f, i) => {
    const n = hits(f.id);
    return `<button type="button" data-f="${esc(f.id)}" aria-pressed="${i === 0}" ${biAttrs(`${f.label[0]} (${n})`, `${f.label[1]}（${n}）`)}>${esc(f.label[0])} (${n})</button>`;
  });
  return `<div class="bp-im-filter" role="group" aria-label="Filter the results">${buttons.join("")}</div>`;
}

function imageRow(run, repo, r, shown) {
  const cells = r.cells.map(([en, zh, cls]) => `<td${cls ? ` class="bp-tr-${cls}"` : ""} ${biAttrs(en, zh ?? en)}>${esc(en)}</td>`).join("");
  const note = r.note ? `<span class="bp-tr-note" ${biAttrs(r.note, r.note_zh || r.note)}>${esc(r.note)}</span>` : "";   // a block in this table
  // Rules broken that the Text and Format columns do not show (text on the mascots, extra text): too long for the Result column.
  const issues = r.issues ? `<span class="bp-im-issue" ${biAttrs(...r.issues)}>${esc(r.issues[0])}</span>` : "";
  // The pictures sit under the name, not in a column of their own: a wide strip in the last column ran off
  // the edge of the table on a desktop screen (11-08 preview).
  const strip = r.strip ? `<a class="bp-im-strip" href="${esc(run.dir + r.sheet)}" target="_blank" rel="noopener">${img(run, r.strip, `${shown}: the pictures from our test`)}</a>` : "";
  return `<tr data-g="${esc(r.group)}" data-look="${esc(r.look || "")}"><td class="bp-tr-skill"><b>${esc(shown)}</b> <span class="bp-tr-mute">★ ${(r.stars || 0).toLocaleString("en-US")}</span>${issues}${note}${strip}</td>
    ${cells}</tr>`;
}

// Buttons show one result at a time; rows stay as they are until the script runs.
const FILTER_SCRIPT = `<script>(function(){var b=document.querySelector(".bp-im-filter");if(!b)return;var rows=document.querySelectorAll(".bp-im-table tbody tr");b.addEventListener("click",function(e){var t=e.target.closest("button");if(!t)return;var f=t.dataset.f;b.querySelectorAll("button").forEach(function(x){x.setAttribute("aria-pressed",String(x===t))});rows.forEach(function(r){r.hidden=!(f==="all"||r.dataset.g===f||(f==="own"&&r.dataset.look==="own"))})})})();</script>`;

/** The results table with its filter; rows that share a repo name ("gpt-image-2-skill") show the owner too. */
export function imageTableHtml(run, ran) {
  const count = {};
  for (const [repo] of ran) count[repo.split("/")[1]] = (count[repo.split("/")[1]] || 0) + 1;
  const shown = (repo) => (count[repo.split("/")[1]] > 1 ? repo : repo.split("/")[1]);
  const head = [run.name_col, ...run.columns].map(th).join("");
  const body = ran.map(([repo, r]) => imageRow(run, repo, r, shown(repo))).join("");
  return `${filterBar(run, ran)}<div class="bp-table-wrap"><table class="bp-table bp-tr-table bp-im-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>${FILTER_SCRIPT}`;
}
