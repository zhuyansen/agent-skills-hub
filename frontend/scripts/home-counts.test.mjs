/**
 * scripts/home-counts.mjs: the build writes the catalog total and the graded count only into the
 * places marked for them, and every other "X,000+" on the home page stays as written.
 *
 * Run: node --test scripts/home-counts.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { plusThousands, stampHomeCounts } from "./home-counts.mjs";

const COUNTS = { total: 258_901, graded: 112_345 };
const ANY_COUNT = /\b\d{1,3}(?:,\d{3})+\+/g;

test("plusThousands rounds down to the thousand", () => {
  assert.equal(plusThousands(258_901), "258,000+");
  assert.equal(plusThousands(24_999), "24,000+");
  assert.equal(plusThousands(1_000_000), "1,000,000+");
});

test("the three description tags take the total", () => {
  const html = [
    '<meta name="description" content="Hub: 186,000+ skills, graded." />',
    '<meta property="og:description" content="Hub: 186,000+ skills, graded." />',
    '<meta name="twitter:description" content="Hub: 186,000+ skills, graded." />',
  ].join("\n");
  const out = stampHomeCounts(html, COUNTS);
  assert.equal(out.match(/Hub: 258,000\+ skills/g).length, 3);
});

test("a marked span takes the count it names", () => {
  const html = 'indexes <span data-count="total">229,000+</span> repos, <span data-count="graded">24,000+</span> graded';
  assert.equal(
    stampHomeCounts(html, COUNTS),
    'indexes <span data-count="total">258,000+</span> repos, <span data-count="graded">112,000+</span> graded',
  );
});

test("an unmarked count stays as written", () => {
  const html = '"description": "Security grades for 130,000+ skills", over 1,000+ stars, <h1>186,000+ tools</h1>';
  assert.equal(stampHomeCounts(html, COUNTS), html);
});

test("on index.html, the only count left as written is the Dataset's 130,000+", () => {
  const html = readFileSync(new URL("../index.html", import.meta.url), "utf-8");
  const stamped = new Set([plusThousands(COUNTS.total), plusThousands(COUNTS.graded)]);
  const left = stampHomeCounts(html, COUNTS).match(ANY_COUNT).filter((c) => !stamped.has(c));
  assert.deepEqual(left, ["130,000+"]);
});
