/**
 * scripts/agent-file-counts.mjs: llms.txt and skill.md take the catalog numbers the home page
 * states, in exactly the sentences listed, and the build stops if one of those sentences is
 * reworded. Runs against the real public/ files, so rewording one fails here first.
 *
 * Run: node --test scripts/agent-file-counts.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  aboutKilo, homeCounts, kilo, kiloPlus, llmsRules, skillMdRules, stampRules,
} from "./agent-file-counts.mjs";

const COUNTS = { total: "301,000+", graded: "150,000+", "graded-over-100": "97%", "graded-over-1000": "96%" };
const INDEX_COUNT = 61_480;

const marker = (key, text) => `<span data-count="${key}">${text}</span>`;
const homeHtml = (counts) => Object.entries(counts).map(([key, text]) => marker(key, text)).join(" ");

test("homeCounts reads each marker, keeping the first of a repeated key", () => {
  const html = `${homeHtml(COUNTS)} ${marker("total", "999,000+")}`;
  assert.deepEqual(homeCounts(html), COUNTS);
});

test("homeCounts names the markers the home page is missing", () => {
  assert.throws(() => homeCounts(marker("total", "1,000+")), /graded, graded-over-100, graded-over-1000/);
});

test("the short forms skill.md uses", () => {
  assert.equal(kiloPlus("267,000+"), "267K+");
  assert.equal(kilo("132,000+"), "132K");
  assert.equal(aboutKilo(49_747), "50K");
  assert.equal(aboutKilo(21_499), "21K");
});

test("stampRules replaces only the number between the two captured parts", () => {
  const rules = [{ pattern: /(Directory of )[\d,]+\+( open-source)/, value: "301,000+" }];
  assert.equal(stampRules("Directory of 186,000+ open-source skills", rules, "t"), "Directory of 301,000+ open-source skills");
});

test("stampRules stops when a sentence is missing or appears twice", () => {
  const rules = [{ pattern: /(Directory of )[\d,]+\+( open-source)/, value: "1+" }];
  assert.throws(() => stampRules("A directory of skills", rules, "llms.txt"), /llms\.txt: .* found it 0 times/);
  const twice = "Directory of 1,000+ open-source. Directory of 2,000+ open-source.";
  assert.throws(() => stampRules(twice, rules, "llms.txt"), /found it 2 times/);
});

test("public/llms.txt takes every home page number and keeps the dataset's own size", () => {
  const stamped = stampRules(readFileSync("public/llms.txt", "utf8"), llmsRules(COUNTS), "llms.txt");
  assert.match(stamped, /Directory of 301,000\+ open-source/);
  assert.match(stamped, /of which 150,000\+ carry a rule-based security grade/);
  assert.match(stamped, /including 97% of skills over 100 stars and 96% over 1,000/);
  assert.match(stamped, /130,173 graded skills\/servers/);
});

test("public/skill.md takes the home page numbers and the CLI index size", () => {
  const stamped = stampRules(readFileSync("public/skill.md", "utf8"), skillMdRules(COUNTS, INDEX_COUNT), "skill.md");
  assert.match(stamped, / 301K\+ indexed skills/);
  assert.match(stamped, /of which ~150K carry a \*\*security grade\*\* \(including 97% of skills over 100 stars\)/);
  assert.match(stamped, /catalog of ~61K skills locally/);
  assert.match(stamped, /holds the ~61K with stars ≥ 5/);
});

test("stamping twice gives the same file", () => {
  const source = readFileSync("public/skill.md", "utf8");
  const once = stampRules(source, skillMdRules(COUNTS, INDEX_COUNT), "skill.md");
  assert.equal(stampRules(once, skillMdRules(COUNTS, INDEX_COUNT), "skill.md"), once);
});
