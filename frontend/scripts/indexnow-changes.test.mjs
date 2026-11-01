/**
 * scripts/indexnow-changes.mjs: which sitemap URLs a deploy sends to IndexNow. No network: only
 * the parsing and comparing are tested.
 *
 * Run: node --test scripts/indexnow-changes.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { diffSnapshots, mergeEntries, recentUrls, sitemapLocs, urlEntries } from "./indexnow-changes.mjs";

const SITE = "https://example.test";

test("sitemapLocs reads each sub-sitemap of an index, with or without a lastmod", () => {
  const xml = `<sitemapindex>
  <sitemap>
    <loc>${SITE}/sitemap-top.xml</loc>
    <lastmod>2026-10-31</lastmod>
  </sitemap>
  <sitemap>
    <loc>${SITE}/sitemap-categories.xml</loc>
  </sitemap>
</sitemapindex>`;
  assert.deepEqual(sitemapLocs(xml), [`${SITE}/sitemap-top.xml`, `${SITE}/sitemap-categories.xml`]);
});

test("urlEntries pairs each loc with its own lastmod and skips hreflang alternates", () => {
  const xml = `<urlset xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>${SITE}/best/a/</loc>
    <xhtml:link rel="alternate" hreflang="zh" href="${SITE}/best/a/zh/"/>
  </url>
  <url>
    <loc>${SITE}/skill/o/r/</loc>
    <lastmod>2026-10-30</lastmod>
  </url>
</urlset>`;
  assert.deepEqual(urlEntries(xml), { [`${SITE}/best/a/`]: null, [`${SITE}/skill/o/r/`]: "2026-10-30" });
});

test("mergeEntries keeps the newer lastmod of a URL listed in two sub-sitemaps", () => {
  const merged = mergeEntries([{ a: null, b: "2026-10-01" }, { a: "2026-10-20", b: "2026-09-01" }]);
  assert.deepEqual(merged, { a: "2026-10-20", b: "2026-10-01" });
});

test("diffSnapshots finds added, re-dated and dropped URLs and nothing else", () => {
  const prev = { same: "2026-10-01", redated: "2026-10-01", undated: null, gone: "2026-09-01" };
  const next = { same: "2026-10-01", redated: "2026-10-31", undated: null, fresh: "2026-11-01" };
  assert.deepEqual(diffSnapshots(prev, next), { added: ["fresh"], updated: ["redated"], dropped: ["gone"] });
});

test("diffSnapshots is empty when nothing changed", () => {
  const snap = { a: "2026-10-01", b: null };
  assert.deepEqual(diffSnapshots(snap, { ...snap }), { added: [], updated: [], dropped: [] });
});

test("recentUrls keeps lastmods within the window and skips undated URLs", () => {
  const next = { old: "2026-10-29", edge: "2026-10-30", today: "2026-11-01", none: null };
  assert.deepEqual(recentUrls(next, "2026-11-01", 2), ["edge", "today"]);
});
