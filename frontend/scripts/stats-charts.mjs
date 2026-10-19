/**
 * Charts for the /stats/ page, as static HTML + SVG (no runtime script).
 *
 * The line chart draws only the lines in SVG (stretched to the plot box, with
 * non-scaling strokes); axis ticks, points and end labels are HTML placed by
 * percentage, so text keeps its size from phone to desktop. Every chart has a data
 * table next to it, and every point and bar a native tooltip.
 */
import { esc, biSpan, biAttrs } from "./shared-utils.mjs";

const PLOT_SCALE = 1000;          // SVG user units across and down the plot box
const TICK_COUNT = 4;             // gridlines above zero
const END_LABEL_MIN_GAP = 8;      // % of plot height; closer end labels are dropped

export const fmt = (n) => Number(n).toLocaleString("en-US");
export const pct = (part, whole) => (whole ? (100 * part) / whole : 0).toFixed(1);
const compact = (n) => (n >= 1000 ? `${+(n / 1000).toFixed(1)}K` : String(n));

/** A round axis top above `max`, with TICK_COUNT equal steps. */
function niceScale(max) {
  const raw = Math.max(max, 1) / TICK_COUNT;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 3, 4, 5, 10].map((m) => m * mag).find((s) => s >= raw);
  return { top: step * TICK_COUNT, ticks: Array.from({ length: TICK_COUNT + 1 }, (_, i) => i * step) };
}

const xAt = (i, n) => (n > 1 ? (100 * i) / (n - 1) : 50);
const yAt = (v, top) => 100 - (100 * v) / top;

function yAxis(ticks, top) {
  const labels = ticks.map((t) => `<span style="top:${yAt(t, top)}%">${compact(t)}</span>`).join("");
  const grid = ticks.map((t) => {
    const y = (yAt(t, top) * PLOT_SCALE) / 100;
    return `<line x1="0" x2="${PLOT_SCALE}" y1="${y}" y2="${y}"/>`;
  }).join("");
  return { labels, grid };
}

function seriesPath(s, n, top) {
  const pts = s.values.map((v, i) => `${(xAt(i, n) * PLOT_SCALE) / 100},${(yAt(v, top) * PLOT_SCALE) / 100}`);
  return `<polyline class="st-series" style="--c:${s.color}" points="${pts.join(" ")}"/>`;
}

function seriesDots(s, months, top) {
  return s.values.map((v, i) => `<span class="st-dot" style="--c:${s.color};left:${xAt(i, months.length)}%;top:${yAt(v, top)}%" title="${esc(`${months[i].key} · ${s.label}: ${fmt(v)}`)}"></span>`).join("");
}

/** End labels sit beside the last points; when two would touch, the legend carries them. */
function endLabels(series, top) {
  const ends = series.map((s) => ({ s, y: yAt(s.values.at(-1), top) })).sort((a, b) => a.y - b.y);
  if (ends.some((e, i) => i && e.y - ends[i - 1].y < END_LABEL_MIN_GAP)) return "";
  return ends.map(({ s, y }) => `<span class="st-end" style="top:${y}%">${biSpan(s.label, s.zh)} ${fmt(s.values.at(-1))}</span>`).join("");
}

function legend(series) {
  return `<div class="st-legend">${series.map((s) => `<span><i class="st-key" style="--c:${s.color}"></i>${biSpan(s.label, s.zh)}</span>`).join("")}</div>`;
}

function xAxis(months) {
  return months.map((m, i) => `<span class="${i % 2 ? "st-odd" : ""}" style="left:${xAt(i, months.length)}%" ${biAttrs(m.en, m.zh)}>${esc(m.en)}</span>`).join("");
}

/** Multi-series line chart. months: [{key, en, zh}] axis labels; series: [{label, zh, color, values}] */
export function lineChart(months, series, aria) {
  const { top, ticks } = niceScale(Math.max(...series.flatMap((s) => s.values)));
  const axis = yAxis(ticks, top);
  const ends = endLabels(series, top);
  return `<figure class="st-chart${ends ? "" : " st-noends"}" role="img" aria-label="${esc(aria)}">
    ${legend(series)}
    <div class="st-plot-wrap">
      <div class="st-yaxis">${axis.labels}</div>
      <div class="st-plot">
        <svg viewBox="0 0 ${PLOT_SCALE} ${PLOT_SCALE}" preserveAspectRatio="none" aria-hidden="true"><g class="st-grid">${axis.grid}</g>${series.map((s) => seriesPath(s, months.length, top)).join("")}</svg>
        ${series.map((s) => seriesDots(s, months, top)).join("")}
      </div>
      <div class="st-ends">${ends}</div>
    </div>
    <div class="st-xaxis">${xAxis(months)}</div>
  </figure>`;
}

/** Horizontal bars for one measure. rows: [{label, zh, value, color?, note?}] */
export function barList(rows, { total } = {}) {
  const max = Math.max(...rows.map((r) => r.value), 1);
  const items = rows.map((r) => {
    const share = total ? ` · ${pct(r.value, total)}%` : "";
    const tip = `${r.label}: ${fmt(r.value)}${share}`;
    return `<li class="st-bar" title="${esc(tip)}">
      <span class="st-bar-label">${biSpan(r.label, r.zh)}</span>
      <span class="st-bar-track"><span class="st-bar-fill" style="width:${(100 * r.value) / max}%${r.color ? `;--c:${r.color}` : ""}"></span></span>
      <span class="st-bar-value">${fmt(r.value)}${share}</span>
    </li>`;
  });
  return `<ul class="st-bars">${items.join("")}</ul>`;
}

/** The data behind a chart, folded under it. headers: [[en, zh]], rows: [[cells]] */
export function dataTable(headers, rows) {
  const head = headers.map(([en, zh]) => `<th>${biSpan(en, zh)}</th>`).join("");
  const body = rows.map((r) => `<tr>${r.map((c) => `<td>${typeof c === "number" ? fmt(c) : esc(c)}</td>`).join("")}</tr>`).join("");
  return `<details class="st-details"><summary>${biSpan("Data table", "数据表")}</summary>
    <div class="st-table-wrap"><table class="st-table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div></details>`;
}
