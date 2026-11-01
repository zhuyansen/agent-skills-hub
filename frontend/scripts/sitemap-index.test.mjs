/**
 * scripts/sitemap-index.mjs: each sub-sitemap's lastmod in the index is the newest of its URLs',
 * and a sub-sitemap whose URLs carry no date gets none. No files: `read` is stubbed.
 *
 * Run: node --test scripts/sitemap-index.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { buildSitemapIndex, newestLastmod } from "./sitemap-index.mjs";

const url = (loc, date) =>
  `  <url>\n    <loc>${loc}</loc>${date ? `\n    <lastmod>${date}</lastmod>` : ""}\n  </url>`;

test("newestLastmod picks the latest date, not the last one written", () => {
  const xml = [url("a", "2026-10-30"), url("b", "2026-10-31"), url("c", "2026-04-29")].join("\n");
  assert.equal(newestLastmod(xml), "2026-10-31");
});

test("newestLastmod reads the date part of a full timestamp", () => {
  assert.equal(newestLastmod(url("a", "2026-10-29T08:00:00+00:00")), "2026-10-29");
});

test("newestLastmod is null when no URL carries a date", () => {
  assert.equal(newestLastmod(url("a") + url("b")), null);
});

test("the index dates each sub-sitemap by its own URLs and leaves an undated one without", () => {
  const files = { "sitemap-book.xml": url("x", "2026-04-29"), "sitemap-categories.xml": url("y") };
  const xml = buildSitemapIndex("https://example.test", Object.keys(files), (f) => files[f]);
  assert.match(xml, /<loc>https:\/\/example\.test\/sitemap-book\.xml<\/loc>\n {4}<lastmod>2026-04-29<\/lastmod>/);
  assert.match(xml, /<loc>https:\/\/example\.test\/sitemap-categories\.xml<\/loc>\n {2}<\/sitemap>/);
  assert.equal(xml.match(/<lastmod>/g).length, 1);
});
