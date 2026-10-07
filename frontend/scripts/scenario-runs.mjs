/**
 * End-to-end test results on a scenario page's cards (scenario-runs.json, written from
 * ops/ppt-runs/results.json). Each tested skill was installed in a throwaway sandbox and
 * used by Claude Code to build a deck from the same brief; the card shows what came back
 * (can you edit it, how much rework before you hand it over, how long it took) and links
 * to the rendered slides. Skills that could not run say why.
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
const REWORK = {
  "touch-ups": ["Ready after touch-ups", "小修即可交付"],
  "one round": ["Needs one round of edits", "要改一轮"],
  substantial: ["Needs substantial rework", "要大改"],
};

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
  const bits = [EDITABLE[r.editable], REWORK[r.rework], [`${r.minutes} min`, `${r.minutes} 分钟`]].filter(Boolean).map(part);
  if (r.extra_claims) bits.push(part(["added claims not in the brief", "加了测试题里没有的说法"]));
  if (r.note) bits.unshift(part([r.note, r.note_zh || r.note]));   // e.g. a converter tested on another skill's deck
  const see = `<a href="${esc(run.dir + r.sheet)}" target="_blank" rel="noopener" ${biAttrs("See the slides →", "看实测幻灯片 →")}>See the slides →</a>`;
  return `<div class="bp-sc-run">🧪 ${label} ${bits.join(" · ")} · ${see}</div>`;
}
