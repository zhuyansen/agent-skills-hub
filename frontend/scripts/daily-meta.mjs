/**
 * Text of a /daily/<date>/ page that comes from the daily report's trend line
 * (generate-daily-pages.mjs): the trend as plain text and as HTML, and the meta description.
 *
 * The report writes emphasis as Markdown **bold**. Until 2026-11-20 the page printed the
 * asterisks in its body, its meta description and its share card (31 of the 37 days that had a
 * trend), and 56 of 126 descriptions ran past 160 characters, the longest at 531.
 *
 * It also says which archive line is the trend and which is a note (trendOf, isNote), so that
 * neither is read as a pick.
 */
import { DESCRIPTION_LIMIT, displayWidth, fitClause } from "../src/lib/skillMeta.mjs";
import { esc } from "./shared-utils.mjs";

const BOLD = /\*\*([^*]+)\*\*/g;
/** How many picks the description names when the day has no trend line. */
const NAMED_PICKS = 3;
/** Opening and closing marks of the quotations the report uses. */
const QUOTE_PAIRS = [['"', '"'], ["“", "”"], ["「", "」"], ["『", "』"]];
const TRAILING_BREAK = /[\s,;:，；：、]+$/u;
/** Text narrower than this before an open quotation reads as a stub ("主线是"). */
const MIN_LEAD_WIDTH = 12;

/** "🎯 今日趋势：…", "趋势: …" or "> 趋势：…": the label the daily report gives its summary line. */
const TREND_LABEL = /^(?:🎯\s*)?>?\s*(?:今日)?趋势\s*[:：]\s*/u;
const BARE_TARGET = /^🎯\s*/u;
/** What a pick carries: its stars or its pace. */
const PICK_MARK = /★|⭐|\/day/;
const NOTE_LINE = /^(?:>|（注|\(注)/u;

/**
 * The day's summary when `line` is the trend line, else null. A labelled line always is one, also
 * when it mentions stars or a pace ("以 137★/天领跑"). A bare "🎯 …" line is one unless it reads as
 * a pick, as before.
 */
export function trendOf(line) {
  if (TREND_LABEL.test(line)) return line.replace(TREND_LABEL, "").trim();
  if (BARE_TARGET.test(line) && !PICK_MARK.test(line)) return line.replace(BARE_TARGET, "").trim();
  return null;
}

/** An editor's note under the list ("> 注：…", "（注…", "(注…"). Ask after trendOf: "> 趋势：" is a trend. */
export const isNote = (line) => NOTE_LINE.test(line);

/** The trend line without its emphasis marks. */
export const plainTrend = (trend) => trend.replace(BOLD, "$1");

/** The trend line as HTML: escaped, emphasis as <strong>. */
export const trendHtml = (trend) => esc(trend).replace(BOLD, "<strong>$1</strong>");

/** Does `text` open a quotation with `open` and never close it? Straight quotes pair up by count. */
function leavesOpen(text, [open, close]) {
  if (open === close) return text.split(open).length % 2 === 0;
  return text.lastIndexOf(open) > text.lastIndexOf(close);
}

/**
 * A cut can land inside a quotation; the text then ends before that quotation opens. When that
 * would leave nothing, or only a stub, the cut stays where it was.
 */
function withoutOpenQuotation(text) {
  const pair = QUOTE_PAIRS.find((quotes) => leavesOpen(text, quotes));
  if (!pair) return text;
  const lead = text.slice(0, text.lastIndexOf(pair[0])).replace(TRAILING_BREAK, "");
  return displayWidth(lead) >= MIN_LEAD_WIDTH ? lead : text;
}

/** The trend within `budget`: whole when it fits, else cut at a break and not inside a quotation. */
function fitTrend(trend, budget) {
  const fitted = fitClause(trend, budget);
  return fitted === trend ? trend : withoutOpenQuotation(fitted);
}

/** "<trend> — top 10 new … on <date>": the trend is cut to what the rest leaves it. */
function trendDescription(day) {
  const tail = ` — top ${day.items.length} new AI agent skills & MCP servers on ${day.date}, security-graded.`;
  return fitTrend(plainTrend(day.trend), DESCRIPTION_LIMIT - displayWidth(tail)) + tail;
}

/** "Top 10 new … on <date>, ranked by star velocity: a, b, c." with as many names as fit, at least one. */
function listDescription(day) {
  const names = day.items.slice(0, NAMED_PICKS).map((item) => item.repo.split("/")[1]);
  const write = (shown) =>
    `Top ${day.items.length} new open-source AI agent skills & MCP servers on ${day.date}, ranked by star velocity: ${shown.join(", ")}. Security-graded.`;
  while (names.length > 1 && displayWidth(write(names)) > DESCRIPTION_LIMIT) names.pop();
  return write(names);
}

/** The page's meta description, within what a results page shows. */
export function dayDescription(day) {
  return day.trend ? trendDescription(day) : listDescription(day);
}
