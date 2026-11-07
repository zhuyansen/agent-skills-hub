/**
 * "The same passage, rewritten by each tool": what every rewriter did to three passages of the
 * test's texts, shown on the page itself (owner, 2026-11-07: the rewrites were one click away,
 * on separate before/after pages). The data comes from ops/slop-runs/passages.py
 * (scenario-passages.json): per passage, the original and, per tool, the changes as
 * ["=" | "-" | "+", text] segments, or `missing` when the rewrite cut the passage.
 * Without JavaScript all three passages show, one under another; with it, buttons switch them.
 */
import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { esc, biAttrs } from "./shared-utils.mjs";

const PATH = join(dirname(fileURLToPath(import.meta.url)), "scenario-passages.json");
const PASSAGES = existsSync(PATH) ? JSON.parse(readFileSync(PATH, "utf-8")) : {};
const COPY = {
  title: ["The same passage, rewritten by each tool", "同一段原文，各工具怎么改"],
  key: ["Struck through: taken out. Highlighted: put in. The score is how human the judge found the whole rewrite (1–5).",
    "划掉的是删掉的字，标绿的是加上的字。分数是评审给整篇改写打的「像不像人写」（1–5）。"],
  original: ["Original", "原文"],
  same: ["Left unchanged", "一字未改"],
  sameLine: (n, total) => [`Left it unchanged (${n} of ${total}):`, `一字未改（${total} 个里 ${n} 个）：`],
  cut: ["Not in the rewrite: cut or merged away", "改写稿里没有这一段：删掉了或并进了别处"],
};

/** A page's passages, or null. */
export function passagesFor(slug) {
  return PASSAGES[slug] || null;
}

const span = ([en, zh], cls) => `<span class="${cls}" ${biAttrs(en, zh)}>${esc(en)}</span>`;
const textHtml = (text) => esc(text).replace(/\n\n/g, "<br><br>").replace(/\n/g, "<br>");

function segHtml([kind, text]) {
  const t = textHtml(text);
  return kind === "-" ? `<del>${t}</del>` : kind === "+" ? `<ins>${t}</ins>` : t;
}

function badge(r) {
  if (r.missing) return span(COPY.cut, "bp-ps-badge bp-ps-flag");
  if (!r.changed) return span(COPY.same, "bp-ps-badge bp-ps-flag");
  const share = Math.round(r.changed * 100);
  return span([`${share}% changed`, `改动 ${share}%`], "bp-ps-badge");
}

function rewriteHtml(r) {
  const head = `<div class="bp-ps-head"><a href="/skill/${esc(r.repo)}/">${esc(r.repo.split("/")[1])}</a>
          <span class="bp-ps-score">${esc(String(r.score))}/5</span> ${badge(r)}</div>`;
  const note = r.note ? `<p class="bp-tr-note" ${biAttrs(...r.note)}>${esc(r.note[0])}</p>` : "";
  const body = r.missing ? "" : `<p class="bp-ps-text">${r.segments.map(segHtml).join("")}</p>`;
  return `<li>${head}${note}${body}</li>`;
}

/** The tools that left the passage as it was, on one line: the original above is their text. */
function sameLineHtml(rows) {
  const same = rows.filter((r) => !r.missing && !r.changed);
  if (!same.length) return "";
  const names = same.map((r) => `<a href="/skill/${esc(r.repo)}/">${esc(r.repo.split("/")[1])}</a> <span class="bp-ps-score">${esc(String(r.score))}/5</span>`);
  return `<p class="bp-ps-same">${span(COPY.sameLine(same.length, rows.length), "bp-ps-flag")} ${names.join(" · ")}</p>`;
}

function panelHtml(p) {
  return `<div class="bp-ps-panel" data-ps="${esc(p.id)}">
      <figure class="bp-ps-orig">
        <figcaption><span ${biAttrs(...COPY.original)}>${esc(COPY.original[0])}</span> · <span ${biAttrs(...p.label)}>${esc(p.label[0])}</span></figcaption>
        <p class="bp-ps-text">${textHtml(p.original)}</p>
        <p class="bp-tr-note" ${biAttrs(...p.note)}>${esc(p.note[0])}</p>
      </figure>
      ${sameLineHtml(p.rows)}
      <ol class="bp-ps-list">${p.rows.filter((r) => r.missing || r.changed).map(rewriteHtml).join("")}</ol>
    </div>`;
}

// Buttons switch passages; until this runs (or without JavaScript) every passage shows.
const SCRIPT = `<script>(function(){var b=document.querySelector(".bp-ps");if(!b)return;var t=b.querySelectorAll(".bp-ps-tabs button"),p=b.querySelectorAll(".bp-ps-panel");function show(id){t.forEach(function(x){x.setAttribute("aria-selected",String(x.dataset.ps===id))});p.forEach(function(x){x.hidden=x.dataset.ps!==id})}t.forEach(function(x){x.addEventListener("click",function(){show(x.dataset.ps)})});b.classList.add("bp-ps-js");show(t[0].dataset.ps)})();</script>`;

/** The block for a test-results section, or "" without passages. */
export function passagesHtml(passages) {
  if (!passages?.length) return "";
  const tabs = passages.map((p, i) =>
    `<button type="button" data-ps="${esc(p.id)}" aria-selected="${i === 0}" ${biAttrs(...p.label)}>${esc(p.label[0])}</button>`).join("");
  return `<div class="bp-ps">
    <h3 class="bp-tr-group" ${biAttrs(...COPY.title)}>${esc(COPY.title[0])}</h3>
    <p class="bp-tr-intro" ${biAttrs(...COPY.key)}>${esc(COPY.key[0])}</p>
    <div class="bp-ps-tabs">${tabs}</div>
    ${passages.map(panelHtml).join("\n    ")}
  </div>${SCRIPT}`;
}
