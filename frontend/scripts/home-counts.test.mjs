/**
 * scripts/home-counts.mjs: the build counts the catalog total, the graded rows and the graded share
 * of each star tier, writes them only into the places marked for them, and every other number on
 * the home page stays as written. The hero's exact counts go into a JSON slot of their own.
 *
 * Run: node --test scripts/home-counts.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  catalogCounts, homeCountTexts, percentDown, plusThousands, stampCatalogCounts, stampHomeCounts,
} from "./home-counts.mjs";

const TEXTS = { total: "258,000+", graded: "125,000+", "graded-over-100": "99%", "graded-over-1000": "98%" };
const NUMBER = /\b\d{1,3}(?:,\d{3})+\+|\b\d+(?:\.\d+)?%/g;

const rows = (n, stars, security_grade) => Array.from({ length: n }, () => ({ stars, security_grade }));

test("plusThousands rounds down to the thousand", () => {
  assert.equal(plusThousands(258_901), "258,000+");
  assert.equal(plusThousands(24_999), "24,000+");
  assert.equal(plusThousands(1_000_000), "1,000,000+");
});

test("percentDown rounds down to a whole percent, without float error", () => {
  assert.equal(percentDown(10_584, 10_665), "99%");
  assert.equal(percentDown(29, 100), "29%");
  assert.equal(percentDown(2_460, 2_460), "100%");
});

test("homeCountTexts counts every row, the graded ones, and the graded share above each star tier", () => {
  const skills = [
    ...rows(1500, 10, "safe"), ...rows(1200, 10, null),
    ...rows(3, 500, "caution"), ...rows(1, 500, "unknown"), ...rows(1, 2000, "reject"),
  ];
  assert.deepEqual(homeCountTexts(skills), {
    total: "2,000+", graded: "1,000+", "graded-over-100": "80%", "graded-over-1000": "100%",
  });
});

test("the three description tags take the total", () => {
  const html = [
    '<meta name="description" content="Hub: 186,000+ skills, graded." />',
    '<meta property="og:description" content="Hub: 186,000+ skills, graded." />',
    '<meta name="twitter:description" content="Hub: 186,000+ skills, graded." />',
  ].join("\n");
  assert.equal(stampHomeCounts(html, TEXTS).match(/Hub: 258,000\+ skills/g).length, 3);
});

test("a marked span takes the text for its marker", () => {
  const html = '<span data-count="total">229,000+</span>, <span data-count="graded">24,000+</span> graded, '
    + '<span data-count="graded-over-100">93%</span> of those over 100 stars';
  assert.equal(
    stampHomeCounts(html, TEXTS),
    '<span data-count="total">258,000+</span>, <span data-count="graded">125,000+</span> graded, '
      + '<span data-count="graded-over-100">99%</span> of those over 100 stars',
  );
});

test("an unmarked number stays as written", () => {
  const html = '"description": "Security grades for 130,000+ skills", over 1,000+ stars, 26.1% flawed, <h1>186,000+ tools</h1>';
  assert.equal(stampHomeCounts(html, TEXTS), html);
});

test("a marker the build does not count fails loudly", () => {
  assert.throws(() => stampHomeCounts('<span data-count="graded-over-10">93%</span>', TEXTS), /graded-over-10/);
});

test("on index.html, the only numbers left as written are the Dataset's 130,000+ and the quoted 26.1%", () => {
  const html = readFileSync(new URL("../index.html", import.meta.url), "utf-8");
  const texts = { total: "987,000+", graded: "123,000+", "graded-over-100": "11%", "graded-over-1000": "22%" };
  const stamped = new Set(Object.values(texts));
  const left = stampHomeCounts(html, texts).match(NUMBER).filter((n) => !stamped.has(n));
  assert.deepEqual(left, ["130,000+", "26.1%"]);
});

const SLOT = /<script id="catalog-counts" type="application\/json">([^<]*)<\/script>/g;
const indexHtml = () => readFileSync(new URL("../index.html", import.meta.url), "utf-8");

test("catalogCounts counts every row and the rows in each category", () => {
  const skills = [
    ...rows(3, 10, null).map((s) => ({ ...s, category: "mcp-server" })),
    { stars: 10, category: "claude-skill" }, { stars: 10, category: null },
  ];
  assert.deepEqual(catalogCounts(skills), { total: 5, categories: { "mcp-server": 3, "claude-skill": 1 } });
});

test("index.html's one slot takes the counts as JSON, and nothing else on the page changes", () => {
  const html = indexHtml();
  const counts = { total: 258_901, categories: { "mcp-server": 100_123, "claude-skill": 34_500 } };
  const stamped = stampCatalogCounts(html, counts);
  const slots = [...stamped.matchAll(SLOT)];
  assert.equal(slots.length, 1);
  assert.deepEqual(JSON.parse(slots[0][1]), counts);
  assert.equal(stamped.replace(slots[0][1], "{}"), html);
});

test("stamping again replaces the counts in place", () => {
  const once = stampCatalogCounts(indexHtml(), { total: 1, categories: {} });
  const twice = stampCatalogCounts(once, { total: 2, categories: {} });
  assert.deepEqual([...twice.matchAll(SLOT)].map((m) => JSON.parse(m[1])), [{ total: 2, categories: {} }]);
});

test("no value can close the script element early", () => {
  const stamped = stampCatalogCounts(indexHtml(), { total: 1, categories: { "</script><b>": 1 } });
  const [slot] = [...stamped.matchAll(SLOT)];
  assert.deepEqual(JSON.parse(slot[1]), { total: 1, categories: { "</script><b>": 1 } });
});

test("a page without the slot fails loudly", () => {
  assert.throws(() => stampCatalogCounts("<head></head>", { total: 1, categories: {} }), /catalog-counts/);
});
