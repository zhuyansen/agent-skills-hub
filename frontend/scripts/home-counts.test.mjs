/**
 * scripts/home-counts.mjs: the build counts the catalog total, the graded rows and the graded share
 * of each star tier, writes them only into the places marked for them, and every other number on
 * the home page stays as written.
 *
 * Run: node --test scripts/home-counts.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { homeCountTexts, percentDown, plusThousands, stampHomeCounts } from "./home-counts.mjs";

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
