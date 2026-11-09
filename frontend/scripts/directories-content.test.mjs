/**
 * /agent-skills-directories/ (src/lib/directoriesContent.mjs, directoryEntries.mjs): the rules the
 * page was written under. Every directory names its sources; nobody is called the best, largest
 * or only anything, in either language; our catalog count comes from the build, never from the
 * text; Agent Skills Hub sits in its group instead of on top; links to other sites carry nofollow.
 *
 * Run: node --test scripts/directories-content.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { plusThousands } from "./home-counts.mjs";
import { prosePageHtml } from "./prose-page-html.mjs";
import { DIRECTORY_ENTRIES } from "../src/lib/directoryEntries.mjs";
import {
  countText, DIRECTORIES_TEXT, directoriesText, FIELD_KEYS, ORDERED_ENTRIES, SIZE_QUESTION, TOTAL,
} from "../src/lib/directoriesContent.mjs";
import { COMPARED_COUNT, DIRECTORIES_META, DIRECTORIES_PATH } from "../src/lib/directoriesMeta.mjs";
import { linkKind, NOFOLLOW_REL, SITE_ORIGIN } from "../src/lib/proseContent.mjs";

/** Every string in `node`, however deep. */
function strings(node) {
  if (typeof node === "string") return [node];
  if (Array.isArray(node)) return node.flatMap(strings);
  if (node === null || typeof node !== "object") return [];
  return Object.values(node).flatMap(strings);
}

const PAGE_STRINGS = strings([DIRECTORIES_TEXT, DIRECTORIES_META]);
/** The size question is asked in readers' words; its answer says why no directory is the largest. */
const CHECKED_STRINGS = PAGE_STRINGS.filter((s) => !SIZE_QUESTION.includes(s));

const SUPERLATIVES_EN =
  /\b(best|largest|biggest|most|only|leading|deepest|widest|broadest|fastest|safest|greatest|cheapest|number one)\b/i;
const SUPERLATIVES_ZH = /最|唯一|第一|首个|首家|领先|顶级|全网/;

test("every directory names at least one source, as a full https address", () => {
  for (const entry of DIRECTORY_ENTRIES) {
    assert.ok(entry.sources.length >= 1, `${entry.id} has no source`);
    for (const url of entry.sources) assert.match(url, /^https:\/\/[^\s()]+$/, `${entry.id}: ${url}`);
  }
});

test("every directory states every field, with English and Chinese", () => {
  const isText = (t) => typeof t === "string" ? t.length > 0 : t.length === 2 && t.every((s) => s.length > 0);
  for (const entry of DIRECTORY_ENTRIES) {
    for (const key of FIELD_KEYS) assert.ok(isText(entry[key].brief), `${entry.id}.${key}`);
    assert.ok(isText(entry.heading) && isText(entry.goodFor), entry.id);
  }
});

test("the title's count is the number of directories compared", () => {
  assert.equal(COMPARED_COUNT, DIRECTORY_ENTRIES.length);
  assert.match(DIRECTORIES_META.en.title, new RegExp(`: ${COMPARED_COUNT} Directories Compared \\(\\d{4}\\) \\| Agent Skills Hub$`));
  assert.match(DIRECTORIES_META.zh.title, new RegExp(`：${COMPARED_COUNT} 个目录对比（\\d{4}） \\| Agent Skills Hub$`));
});

test("no superlatives and no em dashes, in English or Chinese", () => {
  for (const s of CHECKED_STRINGS) {
    assert.doesNotMatch(s, SUPERLATIVES_EN, s);
    assert.doesNotMatch(s, SUPERLATIVES_ZH, s);
    assert.doesNotMatch(s, /—/, s);
  }
});

test("our catalog count is filled in from the build, never written into the text", () => {
  assert.ok(PAGE_STRINGS.some((s) => s.includes(TOTAL)), "the text has no place for the count");
  for (const s of PAGE_STRINGS) assert.doesNotMatch(s, /\b\d{1,3}(?:,\d{3})+\+/, s);
  for (const known of ["267,000", "186,000", "132,000"]) assert.ok(!PAGE_STRINGS.some((s) => s.includes(known)), known);
  const filled = strings(directoriesText("301,000+"));
  assert.ok(filled.some((s) => s.includes("301,000+ GitHub repos")));
  assert.ok(!filled.some((s) => s.includes(TOTAL)));
});

test("the React page states the count the way the home page does", () => {
  for (const n of [0, 999, 1000, 267_431, 1_292_103]) assert.equal(countText(n), plusThousands(n));
});

test("groups come in order, each by domain, and Agent Skills Hub is not first", () => {
  const kinds = ["skills", "mcp", "official"];
  assert.notEqual(ORDERED_ENTRIES[0].id, "agentskillshub-top");
  ORDERED_ENTRIES.slice(1).forEach((entry, i) => {
    const before = ORDERED_ENTRIES[i];
    const order = kinds.indexOf(before.kind) - kinds.indexOf(entry.kind);
    assert.ok(order < 0 || (order === 0 && before.domain < entry.domain), `${before.domain} before ${entry.domain}`);
  });
});

test("the table has a row for each directory, and each row links to the site", () => {
  const table = DIRECTORIES_TEXT.sections[0].blocks.find((block) => block.type === "table");
  assert.equal(table.rows.length, COMPARED_COUNT);
  for (const [site] of table.rows) assert.match(site[0], /^\[[^\]]+\]\((\/|https:\/\/)[^)]*\)/);
});

test("the disclosure opens the page and tells the two Agent Skills Hubs apart", () => {
  const [note] = DIRECTORIES_TEXT.lead;
  assert.equal(note.type, "note");
  const text = strings(note).join(" ");
  assert.match(text, /agentskillshub\.top is not agentskillshub\.dev/);
  assert.match(text, /No one paid/);
});

test("Chinese grade names are the ones the grade cards use", () => {
  const zh = PAGE_STRINGS.filter((s) => /[一-鿿]/.test(s)).join("\n");
  for (const name of ["安全", "注意", "风险", "拒绝", "未评级"]) assert.ok(zh.includes(name), name);
  for (const old of ["需注意", "不安全", "拒收", "未审核"]) assert.ok(!zh.includes(old), old);
});

test("the FAQ asks its five questions; the unread list names five sites and quotes Smithery", () => {
  const section = (id) => DIRECTORIES_TEXT.sections.find((s) => s.id === id);
  assert.equal(section("faq").blocks.filter((block) => block.type === "h3").length, 5);
  const unread = strings(section("not-compared")).join(" ");
  for (const site of ["SkillsMP", "PulseMCP", "mcpservers.org", "cursor.directory", "lobehub.com"]) assert.ok(unread.includes(site), site);
  assert.match(unread, /“now part of Arcade”/);
  assert.match(unread, /“214 servers”/);
});

test("links: app paths, this site's pages, and other sites", () => {
  assert.equal(linkKind("/enterprise/"), "route");
  assert.equal(linkKind("#faq"), "page");
  assert.equal(linkKind(`${SITE_ORIGIN}/about/`), "page");
  assert.equal(linkKind("https://glama.ai/mcp/servers"), "external");
});

const SHELL = `<html><head><title>x</title>
<meta name="description" content="x" /><meta property="og:title" content="x" />
<meta property="og:description" content="x" /><meta property="og:type" content="x" />
<meta property="og:url" content="x" /><meta name="twitter:title" content="x" />
<meta name="twitter:description" content="x" /></head>
<body><div id="root"><!--SHELL-CONTENT-START--><!--SHELL-CONTENT-END--></div></body></html>`;

test("the static page: other sites open in a new tab with nofollow, and it is an Article", () => {
  const html = prosePageHtml(SHELL, {
    ...DIRECTORIES_META.en, text: directoriesText("301,000+"), url: `${SITE_ORIGIN}${DIRECTORIES_PATH}`,
    published: "2026-11-10", modified: "2026-11-10", date: "2026-11-09", rel: NOFOLLOW_REL,
  });
  const links = [...html.matchAll(/<a href="([^"]+)"([^>]*)>/g)];
  const outbound = links.filter(([, href]) => href.startsWith("http") && !href.startsWith(SITE_ORIGIN));
  assert.ok(outbound.length > COMPARED_COUNT);
  for (const [tag, , attrs] of outbound) assert.equal(attrs, ` target="_blank" rel="${NOFOLLOW_REL}"`, tag);
  assert.match(html, /"@type":"Article"/);
  assert.doesNotMatch(html, /FAQPage/);
});

test("llms.txt lists the page under Key pages", () => {
  const llms = readFileSync("public/llms.txt", "utf8");
  const keyPages = llms.slice(llms.indexOf("## Key pages"), llms.indexOf("## Data & research"));
  assert.ok(keyPages.includes(`https://agentskillshub.top${DIRECTORIES_PATH}`));
});
