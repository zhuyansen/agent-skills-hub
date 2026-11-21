import test from "node:test";
import assert from "node:assert/strict";
import { dayDescription, isNote, plainTrend, trendHtml, trendOf } from "./daily-meta.mjs";
import { DESCRIPTION_LIMIT, displayWidth } from "../src/lib/skillMeta.mjs";

const items = (names) => names.map((name) => ({ repo: `owner/${name}` }));
const TEN = items(["three-live", "mixamo-llm-mocap", "loopcut", "d", "e", "f", "g", "h", "i", "j"]);

// The daily report writes its trend line with Markdown emphasis. Until 2026-11-20 the page and
// its description printed the asterisks (31 of 37 days with a trend).
const TREND = "3D 与 CAD 占 **4 席**（three-live、mixamo-llm-mocap），视频生产占 **3 席**；克隆集群又有 **55 仓**，全部拦下。";

test("plainTrend drops the emphasis marks and keeps the words", () => {
  assert.equal(plainTrend("围绕**本地交互、会话衔接**减少成本"), "围绕本地交互、会话衔接减少成本");
  assert.equal(plainTrend("no emphasis here"), "no emphasis here");
});

test("trendHtml writes emphasis as <strong> and escapes the rest", () => {
  assert.equal(trendHtml("占 **4 席**，A & B <x>"), "占 <strong>4 席</strong>，A &amp; B &lt;x&gt;");
});

test("a description with a trend has no asterisks and fits a results page", () => {
  const desc = dayDescription({ date: "2026-11-09", items: TEN, trend: TREND });
  assert.doesNotMatch(desc, /\*/);
  assert.ok(displayWidth(desc) <= DESCRIPTION_LIMIT, `${displayWidth(desc)}: ${desc}`);
});

test("a description with a trend still says what the page is and for which day", () => {
  const desc = dayDescription({ date: "2026-11-09", items: TEN, trend: TREND });
  assert.match(desc, /^3D 与 CAD 占 4 席/);
  assert.match(desc, / — top 10 new AI agent skills & MCP servers on 2026-11-09, security-graded\.$/);
});

test("a short trend is kept whole", () => {
  const desc = dayDescription({ date: "2026-10-25", items: TEN, trend: "**6 席**标新" });
  assert.equal(desc, "6 席标新 — top 10 new AI agent skills & MCP servers on 2026-10-25, security-graded.");
});

test("without a trend the description names the first picks", () => {
  const desc = dayDescription({ date: "2026-07-14", items: items(["luopan", "clawk", "okf", "d", "e"]), trend: "" });
  assert.equal(
    desc,
    "Top 5 new open-source AI agent skills & MCP servers on 2026-07-14, ranked by star velocity: luopan, clawk, okf. Security-graded.",
  );
});

test("long repo names give way before the description runs past a results page", () => {
  const long = items(["claude-fable-5-free-desktop-app", "ponytail-lite", "xiaohu-ip-studio", "d", "e", "f", "g", "h", "i", "j"]);
  const desc = dayDescription({ date: "2026-06-29", items: long, trend: "" });
  assert.ok(displayWidth(desc) <= DESCRIPTION_LIMIT, `${displayWidth(desc)}: ${desc}`);
  assert.match(desc, /ranked by star velocity: claude-fable-5-free-desktop-app/);
  assert.match(desc, /\. Security-graded\.$/);
});

test("a cut that leaves a quotation open ends before the quotation", () => {
  // The trend of 2026-10-15: the first phrase break inside the budget falls within the quotation.
  const trend = '**10 席**全标 🆕、**8 席**建仓不满 4 天；"直接打分、不生成文本"的 Jev 系决策模型一口气占 **3 席**（Jeva 本体、视频版 VideoJev、爬虫 jevcrawl）。';
  const desc = dayDescription({ date: "2026-10-15", items: TEN, trend });
  assert.match(desc, /^10 席全标 🆕、8 席建仓不满 4 天 — top 10 new/);
  assert.doesNotMatch(desc, /"/);
});

test("a quotation that fits is kept, marks and all", () => {
  const desc = dayDescription({ date: "2026-10-15", items: TEN, trend: '主线是"MCP 当插座"，占 5 席' });
  assert.match(desc, /^主线是"MCP 当插座"，占 5 席 — top 10 new/);
});

test("a trend that opens with a quotation too long to fit keeps what the cut left", () => {
  const trend = '"把智能体接进具体工作台、让它直接在终端和浏览器里完成任务而不是停在对话框里、再把结果写回文档和表格"是今天的主线';
  const desc = dayDescription({ date: "2026-10-15", items: TEN, trend });
  assert.match(desc, /^"把智能体接进具体工作台/);
  assert.ok(displayWidth(desc) <= DESCRIPTION_LIMIT, `${displayWidth(desc)}: ${desc}`);
});

test("a cut is not moved back to a quotation that would leave only a stub", () => {
  const trend = '主线是"把智能体接进具体工作台、让它直接在终端和浏览器里完成任务而不是停在对话框里、再把结果写回文档"';
  const desc = dayDescription({ date: "2026-10-15", items: TEN, trend });
  assert.doesNotMatch(desc, /^主线是 — /);
  assert.match(desc, /^主线是"把智能体接进具体工作台/);
});

test("a trend that fits is never cut, even with a stray quotation mark", () => {
  const desc = dayDescription({ date: "2026-10-15", items: TEN, trend: '5 席是 12" 屏幕上的工具' });
  assert.match(desc, /^5 席是 12" 屏幕上的工具 — top 10 new/);
});

// The archive's three kinds of line under a date. Until 2026-11-20 a trend line that mentioned
// stars or a pace ("137★/天") was not taken as the trend: 85 of 122 days lost their summary, and
// such a line, or a note, with something shaped like owner/repo in it became a pick. 55 day pages
// listed one ("10/10" linking to github.com/10/10 on 2026-07-21, "owner/repo" on 2026-09-22).
const TREND_WITH_STARS = "🎯 今日趋势：velocity 榜 10/10 全部两周内新建,媒体/创作生产工具霸榜——图生 3D(img2threejs 以 137★/天断层领跑)";
const NOTE = "> 注：去重范围=与全部历史推荐零重复，比对 1,429 个 owner/repo——48h 内 ≥20★ 共 64 条";
const PICK = "1. howznguyen/phonedesk — 🆕 把旧手机变成电脑控制面板（40★ 19.6/day）";

test("a labelled trend line is the trend, stars in it or not", () => {
  assert.equal(trendOf(TREND_WITH_STARS), "velocity 榜 10/10 全部两周内新建,媒体/创作生产工具霸榜——图生 3D(img2threejs 以 137★/天断层领跑)");
  assert.equal(trendOf("🎯 今日趋势：入选项目更重视落到实际工作中"), "入选项目更重视落到实际工作中");
  assert.equal(trendOf("> 趋势: three themes today"), "three themes today");
});

test("a bare target line is the trend only when it does not read as a pick", () => {
  assert.equal(trendOf("🎯 agent 基建占 6 席"), "agent 基建占 6 席");
  assert.equal(trendOf("🎯 owner/repo — 一个工具 ⭐524 145/day"), null);
});

test("a pick and a note are not the trend", () => {
  assert.equal(trendOf(PICK), null);
  assert.equal(trendOf(NOTE), null);
});

test("a note is a note in each form the archive writes it", () => {
  assert.ok(isNote(NOTE));
  assert.ok(isNote("（注：本日候选不足，放宽了窗口）"));
  assert.ok(isNote("(注: window widened)"));
  assert.ok(!isNote(PICK));
});
