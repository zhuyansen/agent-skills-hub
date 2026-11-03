/**
 * scripts/home-lists.mjs: the build writes crawlable skill lists into the home page's
 * pre-hydration copy, linking only to indexable skill pages and never to NSFW repos.
 *
 * Run: node --test scripts/home-lists.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { HOME_LISTS_MARKER, homeListsHtml, stampHomeLists } from "./home-lists.mjs";

const skill = (name, extra = {}) => ({
  repo_full_name: name, description: `About ${name}`, stars: 1_000, score: 70,
  star_momentum: 5, category: "mcp-server", topics: [], ...extra,
});

test("lists link to indexable skill pages only", () => {
  const html = homeListsHtml([
    skill("acme/indexed"),
    skill("acme/under-the-floor", { stars: 499 }),
    skill("acme/odd/name"),
  ]);
  assert.match(html, /href="\/skill\/acme\/indexed\/"/);
  assert.doesNotMatch(html, /under-the-floor|odd\/name/);
});

test("NSFW repos stay off the lists, by name, description or topic", () => {
  const html = homeListsHtml([
    skill("acme/clean"),
    skill("acme/qwen21-nsfw-pose-skill"),
    skill("acme/plain", { description: "Generates hentai art" }),
    skill("acme/tagged", { topics: ["nsfw"] }),
    skill("acme/tagged-text", { topics: '["art","nsfw"]' }),
  ]);
  assert.match(html, /acme\/clean/);
  assert.doesNotMatch(html, /nsfw-pose|acme\/plain|acme\/tagged/);
});

test("descriptions are escaped and trimmed", () => {
  const html = homeListsHtml([skill("acme/x", { description: `<script>alert(1)</script> ${"word ".repeat(60)}` })]);
  assert.doesNotMatch(html, /<script>/);
  assert.match(html, /&lt;script&gt;/);
  assert.match(html, /…\s*\(1,000 stars\)/);
});

test("a list with nothing above zero is left out", () => {
  const html = homeListsHtml([skill("acme/flat", { star_momentum: 0 })]);
  assert.doesNotMatch(html, /Rising now/);
  assert.match(html, /Highest rated/);
  assert.equal(homeListsHtml([]), "");
});

test("the Chinese twin gets Chinese headings over the same skills", () => {
  const rows = [skill("acme/a"), skill("acme/b", { category: "claude-skill" })];
  const zh = homeListsHtml(rows, "zh");
  assert.match(zh, /<h2>正在走红<\/h2>/);
  assert.match(zh, /<h2>Star 最多的 Claude 技能<\/h2>/);
  assert.match(zh, /\(1,000 Star\)/);
  assert.equal(zh.match(/<li>/g).length, homeListsHtml(rows).match(/<li>/g).length);
});

test("stampHomeLists fills the marker and writes $ sequences as is", () => {
  assert.equal(stampHomeLists(`a${HOME_LISTS_MARKER}b`, "<p>$& $1</p>"), "a<p>$& $1</p>b");
  assert.equal(stampHomeLists("no marker", "<p>x</p>"), "no marker");
});

test("index.html carries the marker inside the home copy", () => {
  const html = readFileSync(new URL("../index.html", import.meta.url), "utf-8");
  const start = html.indexOf("<!--SHELL-CONTENT-START-->");
  const end = html.indexOf("<!--SHELL-CONTENT-END-->");
  const at = html.indexOf(HOME_LISTS_MARKER);
  assert.ok(start < at && at < end, "marker sits between the SHELL-CONTENT markers");
});
