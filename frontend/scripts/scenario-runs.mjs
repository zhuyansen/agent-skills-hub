/**
 * End-to-end test results on a scenario page's cards (scenario-runs.json, written from
 * ops/ppt-runs/results.json). Each tested skill was installed in a throwaway sandbox and
 * used by Claude Code to build a deck from the same brief; the card shows what came back
 * (can you edit it, how much rework before you hand it over, how long it took) and links
 * to the rendered slides. Skills that could not run say why.
 * Runs of type "slop" (the anti-slop page, ops/slop-runs) show instead how human the
 * rewrite reads, the layer it reached, AI-leaning structure features removed, whether
 * the facts survived and, for detectors, what the report flagged.
 * Runs of type "table" carry their own columns, cells and card phrases (written by the
 * test's evidence.py), so a new kind of test needs no code here.
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

// Skill managers (ops/skillmgr-runs): what the tool did when asked to install a skill that
// ships a `curl | sh` setup script, best first.
const RISKY = {
  refused: ["Warned about the curl | sh script and did not install by default", "对 curl | sh 脚本发出警告，默认不安装"],
  warned: ["Warned about the curl | sh script, installed it anyway", "对 curl | sh 脚本发出警告，但照装"],
  source: ["Installed a skill with a curl | sh script, showing only its source", "带 curl | sh 脚本的 skill 照装，只显示了来源"],
  silent: ["Installed a skill with a curl | sh script without a word", "带 curl | sh 脚本的 skill 一声不吭就装了"],
};
const RISKY_SHORT = {
  refused: ["Warned, not installed by default", "警告，默认不装"], warned: ["Warned, installed anyway", "警告了，照装"],
  source: ["Showed the source only, installed", "只显示来源，照装"], silent: ["Installed without a word", "一声不吭就装了"],
};
const RISKY_RANK = { refused: 0, warned: 1, source: 2, silent: 3 };
const SYNCS = { true: ["Yes", "能"], false: ["No", "不能"], "needs-agent": ["Only to agents already installed", "只同步到已安装的 agent"] };

/** The test-result phrases for a skill manager. */
function mgrBits(r) {
  return [RISKY[r.risky], r.prunes ? ["removes skills cleanly", "能删干净"] : ["cannot remove installed skills", "删不掉已装的 skill"],
    r.syncs === true ? ["syncs to Codex", "能同步到 Codex"] : null,
    r.extra_tokens != null ? [`+${r.extra_tokens} tokens per session for 20 skills`, `装 20 个 skill 每次会话多 ${r.extra_tokens} token`] : null];
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
  const label = part(run.line_label || [`Tested ${run.date}:`, `${run.date} 实测：`]);
  if (!r.ran) return `<div class="bp-sc-run bp-sc-run--no">🧪 ${part(run.not_run_line || (run.type === "skillmgr" ? ["Our test could not judge it:", "这轮实测评不了："] : ["Not run in our test:", "未能实测："]))} ${part([r.reason, r.reason_zh || r.reason])}</div>`;
  const slop = run.type === "slop";
  const mgr = run.type === "skillmgr";
  const own = run.type === "table";
  const bits = (own ? r.bits : mgr ? mgrBits(r) : slop ? slopBits(r) : pptBits(r)).filter(Boolean).map(part);
  if (r.extra_claims) bits.push(part(["added claims not in the brief", "加了测试题里没有的说法"]));
  if (r.note) bits.unshift(part([r.note, r.note_zh || r.note]));   // e.g. a converter tested on another skill's deck
  const [en, zh] = own ? run.see : mgr ? ["See the run →", "看实测过程 →"] : slop ? ["See before and after →", "看改写前后 →"] : ["See the slides →", "看实测幻灯片 →"];
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

function pptRow(run, repo, r, rank) {
  // The thumbnail is the deck's routes slide (r.thumb, from ops/ppt-runs/compare.py), so the column compares like with like.
  const thumb = `<a href="${esc(run.dir + r.sheet)}" target="_blank" rel="noopener"><img src="${esc(run.dir + "thumbs/" + (r.thumb || r.sheet))}" alt="${esc(name(repo))} slides" width="120" height="68" loading="lazy"></a>`;
  return `<tr><td class="bp-tr-rank">${r.note ? "" : rank}</td>${skillCell(repo, r)}
    ${cellC(`bp-tr-${(r.rework || "").replace(" ", "-")}`, ...(REWORK[r.rework] || ["-"]))}${cell(...(r.pei != null ? PEI[r.pei] : EDITABLE[r.editable] || ["-"]))}
    ${cellC("bp-tr-num", r.checklist != null ? pct(r.checklist) : "-")}${cellC("bp-tr-num", `${r.minutes} min`, `${r.minutes} 分钟`)}<td>${thumb}</td></tr>`;
}

function pptTable(run, rows) {
  // A converter (r.note) did another task, so it sits after the ranked rows.
  // Rework first (the cost of handing it over), then editability, then the content rubric:
  // the rubric barely separates decks (10 of 26 at 100%), editability and rework do.
  rows.sort(([, a], [, b]) => Boolean(a.note) - Boolean(b.note) || (REWORK_RANK[a.rework] ?? 9) - (REWORK_RANK[b.rework] ?? 9)
    || (b.pei ?? -1) - (a.pei ?? -1) || (b.checklist ?? -1) - (a.checklist ?? -1));
  const cols = [["#", "#"], ["Skill", "Skill"], ["Before handing over", "交付前"], ["Editability (PEI)", "可编辑性（PEI）"], ["Content rubric", "内容检查单"], ["Time", "耗时"], ["Slides", "幻灯片"]];
  return `<thead>${head(cols)}</thead><tbody>${rows.map(([repo, r], i) => pptRow(run, repo, r, i + 1)).join("")}</tbody>`;
}

function slopRow(run, repo, r, rank) {
  const rewrote = r.reads_human != null;
  const layer = rewrote ? (LAYER[r.deepest] || LAYER.none) : ["Detector only", "只检测"];
  const flags = r.flags ? [`${r.flags.flags} (${r.flags.structure} structure)`, `${r.flags.flags}（结构 ${r.flags.structure}）`] : ["-"];
  return `<tr><td class="bp-tr-rank">${rank}</td>${skillCell(repo, r)}
    ${cellC("bp-tr-num", rewrote ? `${r.reads_human}/5` : "-")}${cell(...layer)}${cellC("bp-tr-num", rewrote ? r.structure_removed : "-")}
    ${cellC("bp-tr-num", ...(rewrote ? (r.facts_kept ? ["All kept", "全保留"] : ["Lost some", "有丢失"]) : ["-"]))}${cell(...flags)}
    <td class="bp-tr-num">${evidenceLink(run, r, ["Before / after", "改写前后"])}</td></tr>`;
}

function slopTable(run, rows) {
  rows.sort(([, a], [, b]) => (b.reads_human ?? -1) - (a.reads_human ?? -1) || (b.flags?.structure || 0) - (a.flags?.structure || 0));
  const cols = [["#", "#"], ["Skill", "Skill"], ["Reads human", "像人写"], ["Layer reached", "改到哪层"], ["AI structure removed", "去掉的 AI 结构"],
    ["Facts", "事实"], ["Detector flags", "检测报出"], ["Evidence", "证据"]];
  return `<thead>${head(cols)}</thead><tbody>${rows.map(([repo, r], i) => slopRow(run, repo, r, i + 1)).join("")}</tbody>`;
}

/** Side-by-side images above the table (run.compare): the same slide from every deck. */
function compareHtml(run) {
  return (run.compare || []).map((c) => `<figure class="bp-tr-compare">
      <a href="${esc(run.dir + c.src)}" target="_blank" rel="noopener"><img src="${esc(run.dir + c.src)}" alt="${esc(c.en)}" loading="lazy"></a>
      <figcaption ${biAttrs(c.en, c.zh || c.en)}>${esc(c.en)}</figcaption>
    </figure>`).join("");
}

function mgrRow(run, repo, r, rank) {
  const cls = r.risky === "refused" ? "bp-tr-touch-ups" : r.risky === "silent" ? "bp-tr-substantial" : "";
  return `<tr><td class="bp-tr-rank">${rank}</td>${skillCell(repo, r)}
    ${cellC(cls, ...(RISKY_SHORT[r.risky] || ["-"]))}${cellC(r.prunes ? "" : "bp-tr-substantial", ...(r.prunes ? ["Yes", "能"] : ["No", "不能"]))}
    ${cell(...(SYNCS[String(r.syncs)] || ["-"]))}${cellC("bp-tr-num", r.extra_tokens != null ? `+${r.extra_tokens}` : "-")}
    <td class="bp-tr-num">${evidenceLink(run, r, ["The run", "实测过程"])}</td></tr>`;
}

function mgrTable(run, rows) {
  rows.sort(([, a], [, b]) => (RISKY_RANK[a.risky] ?? 9) - (RISKY_RANK[b.risky] ?? 9) || Number(b.prunes) - Number(a.prunes)
    || Number(b.syncs === true) - Number(a.syncs === true) || (b.stars || 0) - (a.stars || 0));
  const cols = [["#", "#"], ["Tool", "工具"], ["Skill with a curl | sh script", "遇到带 curl | sh 脚本的 skill"], ["Removes cleanly", "能删干净"],
    ["Syncs to Codex", "同步到 Codex"], ["Tokens per session, 20 skills", "20 个 skill 每次会话多占"], ["Evidence", "证据"]];
  return `<thead>${head(cols)}</thead><tbody>${rows.map(([repo, r], i) => mgrRow(run, repo, r, i + 1)).join("")}</tbody>`;
}

/** One table of a "table" run: rows in the order the data gives them, cells as written. */
function ownTable(run, rows, columns = run.columns) {
  const cols = [["#", "#"], run.name_col || ["Skill", "Skill"], ...columns, ["Evidence", "证据"]];
  const body = rows.map(([repo, r], i) => `<tr><td class="bp-tr-rank">${i + 1}</td>${skillCell(repo, r)}
    ${r.cells.map(([en, zh, cls]) => cell(en, zh ?? en, cls ? `bp-tr-${cls}` : "")).join("")}
    <td class="bp-tr-num">${evidenceLink(run, r, run.evidence || ["The run", "实测过程"])}</td></tr>`).join("");
  return `<div class="bp-table-wrap"><table class="bp-table bp-tr-table"><thead>${head(cols)}</thead><tbody>${body}</tbody></table></div>`;
}

/** A "table" run's tables: one, or one per group (run.groups) with its own heading and ranks. */
function ownTables(run, ran) {
  if (!run.groups) return ownTable(run, ran);
  return run.groups.map((g) => `<h3 class="bp-tr-group" ${biAttrs(...g.title)}>${esc(g.title[0])}</h3>
    ${ownTable(run, ran.filter(([, r]) => r.group === g.id), run.group_columns?.[g.id])}`).join("");
}

/** "Which one to install": the test's answer, above the table (run.verdict). */
function verdictHtml(run) {
  const v = run.verdict;
  if (!v) return "";
  const medals = ["🥇", "🥈", "🥉"];
  const picks = v.picks.map((p, i) => `<li><span class="bp-tr-medal">${medals[i] || "•"}</span>
      <div><strong ${biAttrs(...p.role)}>${esc(p.role[0])}</strong>: <a href="/skill/${esc(p.repo)}/"><b>${esc(name(p.repo))}</b></a>
      <span class="bp-tr-mute">★ ${((run.runs[p.repo] || {}).stars || 0).toLocaleString("en-US")}</span>${p.install && !p.install.startsWith("see") ? ` <code>${esc(p.install)}</code>` : ""}
      <br><span ${biAttrs(...p.why)}>${esc(p.why[0])}</span></div></li>`).join("");
  const avoid = (v.avoid || []).map((a) => `<b>${esc(name(a.repo))}</b> (<span ${biAttrs(...a.why)}>${esc(a.why[0])}</span>)`).join("; ");
  return `<div class="bp-tr-verdict">
      <h3 ${biAttrs(...(v.title || ["Which one to install", "到底装哪个"]))}>${esc((v.title || ["Which one to install"])[0])}</h3>
      <ol>${picks}</ol>
      ${avoid ? `<p><strong ${biAttrs(...(v.avoid_label || ["Not recommended:", "不建议："]))}>${esc((v.avoid_label || ["Not recommended:"])[0])}</strong> ${avoid}.</p>` : ""}
      <p ${biAttrs(...v.caveat)}>${esc(v.caveat[0])}</p>
      <p class="bp-tr-mute" ${biAttrs(...v.rule)}>${esc(v.rule[0])}</p>
    </div>`;
}

function notRunHtml(entries, label = ["Not run", "未能实测"]) {
  if (!entries.length) return "";
  const items = entries.map(([repo, r]) => `<li><b>${esc(name(repo))}</b>: <span ${biAttrs(r.reason, r.reason_zh || r.reason)}>${esc(r.reason)}</span></li>`);
  return `<details class="bp-tr-notrun"><summary ${biAttrs(`${label[0]} (${entries.length})`, `${label[1]}（${entries.length}）`)}>${esc(label[0])} (${entries.length})</summary><ul>${items.join("")}</ul></details>`;
}

/** The "Test results" section: all tested skills side by side, best first; "" without a run. */
export function runsSectionHtml(run) {
  if (!run) return "";
  const all = Object.entries(run.runs);
  const ran = all.filter(([, r]) => r.ran);
  const mgr = run.type === "skillmgr";
  const own = run.type === "table";
  const table = own ? "" : mgr ? mgrTable(run, ran) : run.type === "slop" ? slopTable(run, ran) : pptTable(run, ran);
  const [what, whatZh] = run.type === "slop"
    ? ["each rewrote the same three texts (an English post, a Chinese post, a short story)", "每个改写同样的三份文本（英文文章、中文文章、短篇小说）"]
    : ["each built a deck from the same brief", "每个按同一份测试题做一份 deck"];
  const intro = own ? run.intro : mgr
    ? [`We ran ${all.length} of these tools on ${run.date}; ${ran.length} could be judged. Each got the same job in a throwaway sandbox, driven by ${run.agent}: install 20 test skills, install one more that ships a curl | sh setup script, remove all but five, and give those five to Codex. What is on disk and how many tokens Claude Code loads were measured after each step.`,
       `${run.date} 我们实跑了其中 ${all.length} 个，${ran.length} 个可以评判。每个在用完即删的沙箱里由 ${run.agent} 调用，做同一件事：装 20 个测试 skill，再装一个带 curl | sh 安装脚本的 skill，然后删到只剩 5 个，并把这 5 个同步给 Codex。每一步之后都测了磁盘上有什么、Claude Code 加载了多少 token。`]
    : [`We ran ${all.length} of these skills on ${run.date} and ${ran.length} ran: ${what} in a throwaway sandbox, driven by ${run.agent}, judged by ${run.judge}.`,
       `${run.date} 我们实跑了其中 ${all.length} 个，跑成 ${ran.length} 个：${whatZh}，在用完即删的沙箱里由 ${run.agent} 调用，${run.judge} 评审。`];
  return `<section id="test-results" class="bp-tr">
    <h2 class="bp-section-title" ${biAttrs(...(run.title || ["Test results: the skills side by side", "实测对比：同一任务下的效果"]))}>${esc((run.title || ["Test results: the skills side by side"])[0])}</h2>
    <p class="bp-tr-intro" ${biAttrs(...intro)}>${esc(intro[0])}</p>
    ${verdictHtml(run)}
    ${compareHtml(run)}
    ${own && run.finding ? `<p class="bp-tr-intro"><strong ${biAttrs("What we found:", "发现：")}>What we found:</strong> <span ${biAttrs(...run.finding)}>${esc(run.finding[0])}</span>${run.control ? ` <a href="${esc(run.dir + run.control.sheet)}" target="_blank" rel="noopener" ${biAttrs("See the control run →", "看对照组 →")}>See the control run →</a>` : ""}</p>` : ""}
    ${own ? ownTables(run, ran) : `<div class="bp-table-wrap"><table class="bp-table bp-tr-table">${table}</table></div>`}
    ${notRunHtml(all.filter(([, r]) => !r.ran), run.not_run_label || (mgr ? ["Ran, but this test could not judge them", "跑了，但这轮实测评不了"] : undefined))}
    <p class="bp-tr-mute"><a href="${esc(run.results)}" target="_blank" rel="noopener" ${biAttrs("All results and scripts →", "全部结果和脚本 →")}>All results and scripts →</a></p>
  </section>`;
}
