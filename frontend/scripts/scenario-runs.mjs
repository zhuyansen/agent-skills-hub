/**
 * End-to-end test results on a scenario page's cards (scenario-runs.json, written from
 * ops/ppt-runs/results.json). Each tested skill was installed in a throwaway sandbox and
 * used by Claude Code to build a deck from the same brief; the card shows what came back
 * (can you edit it, how much rework before you hand it over, how long it took) and links
 * to the rendered slides. Skills that could not run say why.
 * Runs of type "slop" (the anti-slop page, ops/slop-runs) show instead how human the
 * rewrite reads, the layer it reached, AI-leaning structure features removed, whether
 * the facts survived and, for detectors, what the report flagged.
 */
import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { esc, biAttrs } from "./shared-utils.mjs";

const RUNS_PATH = join(dirname(fileURLToPath(import.meta.url)), "scenario-runs.json");
const RUNS = existsSync(RUNS_PATH) ? JSON.parse(readFileSync(RUNS_PATH, "utf-8")) : {};

const EDITABLE = {
  native: ["Editable PPTX", "原生可编辑 PPTX"],
  hybrid: ["Image layers with editable text", "图片底 + 可编辑文字"],
  image: ["Slides are images: text not editable", "整页是图片：文字不能改"],
  browser: ["Editable in the browser", "浏览器里可改"],
  pdf: ["PDF", "PDF"],
};
// Editability levels after SlidesGen-Bench's PEI (arXiv 2601.09487), found by ops/ppt-runs/pei.py.
const PEI = [
  ["L0 · nothing editable", "L0 · 不可编辑"],
  ["L1 · text editable", "L1 · 文字可改"],
  ["L2 · + drawn shapes", "L2 · + 矢量图形"],
  ["L3 · + structure", "L3 · + 结构化"],
  ["L4 · + native charts/tables", "L4 · + 原生图表/表格"],
  ["L5 · + animation", "L5 · + 动画"],
];
const pct = (x) => `${Math.round(x * 100)}%`;

const REWORK = {
  "touch-ups": ["Ready after touch-ups", "小修即可交付"],
  "one round": ["Needs one round of edits", "要改一轮"],
  substantial: ["Needs substantial rework", "要大改"],
};

const LAYER = {
  structure: ["Changed structure", "改到了结构"],
  phrasing: ["Changed wording, not structure", "改了措辞，没改结构"],
  surface: ["Changed words and punctuation only", "只改了用词和标点"],
  none: ["Changed nothing that matters", "没改到实质"],
};

/** The test-result phrases for a humanizer or detector run. */
function slopBits(r) {
  const bits = [];
  if (r.reads_human != null) {
    bits.push([`Reads human ${r.reads_human}/5`, `像人写 ${r.reads_human}/5`], LAYER[r.deepest] || LAYER.none);
    if (r.structure_removed) bits.push([`removed ${r.structure_removed} AI-leaning structure feature${r.structure_removed > 1 ? "s" : ""}`, `去掉 ${r.structure_removed} 个 AI 结构特征`]);
    if (r.facts_kept) bits.push(["kept every fact", "事实全保留"]);
  }
  if (r.flags) bits.push([`flagged ${r.flags.flags} (${r.flags.structure} about structure)`, `报出 ${r.flags.flags} 处（其中结构 ${r.flags.structure} 处）`]);
  bits.push([`${r.minutes} min`, `${r.minutes} 分钟`]);
  return bits;
}

/** The test-result phrases for a deck: rework, editability level, rubric score, time. */
function pptBits(r) {
  const rubric = r.checklist != null ? [`content rubric ${pct(r.checklist)}`, `内容检查单 ${pct(r.checklist)}`] : null;
  const pei = r.pei != null ? [`Editability ${PEI[r.pei][0]}`, `可编辑性 ${PEI[r.pei][1]}`] : EDITABLE[r.editable];
  return [REWORK[r.rework], pei, rubric, [`${r.minutes} min`, `${r.minutes} 分钟`]];
}

/** The page's test run, or null. */
export function runsFor(slug) {
  return RUNS[slug] || null;
}

function part([en, zh]) {
  return `<span ${biAttrs(en, zh)}>${esc(en)}</span>`;
}

/** The "Tested" line for one card, or "" when the skill was not in the run. */
export function runLineHtml(run, skill) {
  const r = run?.runs?.[skill.repo_full_name];
  if (!r) return "";
  const label = part([`Tested ${run.date}:`, `${run.date} 实测：`]);
  if (!r.ran) return `<div class="bp-sc-run bp-sc-run--no">🧪 ${part(["Not run in our test:", "未能实测："])} ${part([r.reason, r.reason_zh || r.reason])}</div>`;
  const slop = run.type === "slop";
  const bits = (slop ? slopBits(r) : pptBits(r)).filter(Boolean).map(part);
  if (r.extra_claims) bits.push(part(["added claims not in the brief", "加了测试题里没有的说法"]));
  if (r.note) bits.unshift(part([r.note, r.note_zh || r.note]));   // e.g. a converter tested on another skill's deck
  const [en, zh] = slop ? ["See before and after →", "看改写前后 →"] : ["See the slides →", "看实测幻灯片 →"];
  const see = `<a href="${esc(run.dir + r.sheet)}" target="_blank" rel="noopener" ${biAttrs(en, zh)}>${esc(en)}</a>`;
  return `<div class="bp-sc-run">🧪 ${label} ${bits.join(" · ")} · ${see}</div>`;
}

// ---- The page's test-results section: every tested skill in one comparable table ----

const REWORK_RANK = { "touch-ups": 0, "one round": 1, substantial: 2 };
const name = (repo) => repo.split("/")[1];
const cell = (en, zh = en, cls = "") => `<td${cls ? ` class="${cls}"` : ""} ${biAttrs(String(en), String(zh))}>${esc(String(en))}</td>`;
const cellC = (cls, en, zh = en) => cell(en, zh, cls);
const head = (cols) => `<tr>${cols.map(([en, zh]) => `<th ${biAttrs(en, zh)}>${esc(en)}</th>`).join("")}</tr>`;

function skillCell(repo, r) {
  const note = r.note ? `<br><span class="bp-tr-note" ${biAttrs(r.note, r.note_zh || r.note)}>${esc(r.note)}</span>` : "";
  return `<td class="bp-tr-skill"><b>${esc(name(repo))}</b> <span class="bp-tr-mute">★ ${(r.stars || 0).toLocaleString("en-US")}</span>${note}</td>`;
}

function evidenceLink(run, r, [en, zh]) {
  return `<a href="${esc(run.dir + r.sheet)}" target="_blank" rel="noopener" ${biAttrs(en, zh)}>${esc(en)}</a>`;
}

function pptRow(run, repo, r) {
  // The thumbnail is the deck's routes slide (r.thumb, from ops/ppt-runs/compare.py), so the column compares like with like.
  const thumb = `<a href="${esc(run.dir + r.sheet)}" target="_blank" rel="noopener"><img src="${esc(run.dir + "thumbs/" + (r.thumb || r.sheet))}" alt="${esc(name(repo))} slides" width="120" height="68" loading="lazy"></a>`;
  return `<tr>${skillCell(repo, r)}
    ${cellC(`bp-tr-${(r.rework || "").replace(" ", "-")}`, ...(REWORK[r.rework] || ["-"]))}${cell(...(r.pei != null ? PEI[r.pei] : EDITABLE[r.editable] || ["-"]))}
    ${cellC("bp-tr-num", r.checklist != null ? pct(r.checklist) : "-")}${cellC("bp-tr-num", `${r.minutes} min`, `${r.minutes} 分钟`)}<td>${thumb}</td></tr>`;
}

function pptTable(run, rows) {
  // A converter (r.note) did another task, so it sits after the ranked rows.
  // Rework first (the cost of handing it over), then editability, then the content rubric:
  // the rubric barely separates decks (10 of 26 at 100%), editability and rework do.
  rows.sort(([, a], [, b]) => Boolean(a.note) - Boolean(b.note) || (REWORK_RANK[a.rework] ?? 9) - (REWORK_RANK[b.rework] ?? 9)
    || (b.pei ?? -1) - (a.pei ?? -1) || (b.checklist ?? -1) - (a.checklist ?? -1));
  const cols = [["Skill", "Skill"], ["Before handing over", "交付前"], ["Editability (PEI)", "可编辑性（PEI）"], ["Content rubric", "内容检查单"], ["Time", "耗时"], ["Slides", "幻灯片"]];
  return `<thead>${head(cols)}</thead><tbody>${rows.map(([repo, r]) => pptRow(run, repo, r)).join("")}</tbody>`;
}

function slopRow(run, repo, r) {
  const rewrote = r.reads_human != null;
  const layer = rewrote ? (LAYER[r.deepest] || LAYER.none) : ["Detector only", "只检测"];
  const flags = r.flags ? [`${r.flags.flags} (${r.flags.structure} structure)`, `${r.flags.flags}（结构 ${r.flags.structure}）`] : ["-"];
  return `<tr>${skillCell(repo, r)}
    ${cellC("bp-tr-num", rewrote ? `${r.reads_human}/5` : "-")}${cell(...layer)}${cellC("bp-tr-num", rewrote ? r.structure_removed : "-")}
    ${cellC("bp-tr-num", ...(rewrote ? (r.facts_kept ? ["All kept", "全保留"] : ["Lost some", "有丢失"]) : ["-"]))}${cell(...flags)}
    <td class="bp-tr-num">${evidenceLink(run, r, ["Before / after", "改写前后"])}</td></tr>`;
}

function slopTable(run, rows) {
  rows.sort(([, a], [, b]) => (b.reads_human ?? -1) - (a.reads_human ?? -1) || (b.flags?.structure || 0) - (a.flags?.structure || 0));
  const cols = [["Skill", "Skill"], ["Reads human", "像人写"], ["Layer reached", "改到哪层"], ["AI structure removed", "去掉的 AI 结构"],
    ["Facts", "事实"], ["Detector flags", "检测报出"], ["Evidence", "证据"]];
  return `<thead>${head(cols)}</thead><tbody>${rows.map(([repo, r]) => slopRow(run, repo, r)).join("")}</tbody>`;
}

/** Side-by-side images above the table (run.compare): the same slide from every deck. */
function compareHtml(run) {
  return (run.compare || []).map((c) => `<figure class="bp-tr-compare">
      <a href="${esc(run.dir + c.src)}" target="_blank" rel="noopener"><img src="${esc(run.dir + c.src)}" alt="${esc(c.en)}" loading="lazy"></a>
      <figcaption ${biAttrs(c.en, c.zh || c.en)}>${esc(c.en)}</figcaption>
    </figure>`).join("");
}

function notRunHtml(entries) {
  if (!entries.length) return "";
  const items = entries.map(([repo, r]) => `<li><b>${esc(name(repo))}</b>: <span ${biAttrs(r.reason, r.reason_zh || r.reason)}>${esc(r.reason)}</span></li>`);
  return `<details class="bp-tr-notrun"><summary ${biAttrs(`Not run (${entries.length})`, `未能实测（${entries.length}）`)}>Not run (${entries.length})</summary><ul>${items.join("")}</ul></details>`;
}

/** The "Test results" section: all tested skills side by side, best first; "" without a run. */
export function runsSectionHtml(run) {
  if (!run) return "";
  const all = Object.entries(run.runs);
  const ran = all.filter(([, r]) => r.ran);
  const table = run.type === "slop" ? slopTable(run, ran) : pptTable(run, ran);
  const [what, whatZh] = run.type === "slop"
    ? ["each rewrote the same three texts (an English post, a Chinese post, a short story)", "每个改写同样的三份文本（英文文章、中文文章、短篇小说）"]
    : ["each built a deck from the same brief", "每个按同一份测试题做一份 deck"];
  const intro = [`We ran ${all.length} of these skills on ${run.date} and ${ran.length} ran: ${what} in a throwaway sandbox, driven by ${run.agent}, judged by ${run.judge}.`,
    `${run.date} 我们实跑了其中 ${all.length} 个，跑成 ${ran.length} 个：${whatZh}，在用完即删的沙箱里由 ${run.agent} 调用，${run.judge} 评审。`];
  return `<section id="test-results" class="bp-tr">
    <h2 class="bp-section-title" ${biAttrs("Test results: the skills side by side", "实测对比：同一任务下的效果")}>Test results: the skills side by side</h2>
    <p class="bp-tr-intro" ${biAttrs(...intro)}>${esc(intro[0])}</p>
    ${compareHtml(run)}
    <div class="bp-table-wrap"><table class="bp-table bp-tr-table">${table}</table></div>
    ${notRunHtml(all.filter(([, r]) => !r.ran))}
    <p class="bp-tr-mute"><a href="${esc(run.results)}" target="_blank" rel="noopener" ${biAttrs("All results and scripts →", "全部结果和脚本 →")}>All results and scripts →</a></p>
  </section>`;
}
