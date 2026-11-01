#!/usr/bin/env node
/**
 * Which live URLs to send to IndexNow after a deploy: those added, re-dated or dropped since the
 * last run. Until 2026-11-01 every deploy sent all ~4,500 sitemap URLs twice (the build ran
 * submit-indexnow.mjs, then the deploy workflow sent the live sitemaps to three endpoints), three
 * or more times a day. Bing asks for the URLs that changed, sent as they change.
 *
 * Reads the live sitemap index and every sub-sitemap it lists, compares them with the snapshot
 * the previous run left at <snapshot.json> (the deploy workflow keeps it in the Actions cache),
 * writes the URLs to send to <urls.txt> and overwrites <snapshot.json> with what it read. With
 * no snapshot (first run, evicted cache) it sends the URLs whose lastmod is within FALLBACK_DAYS.
 * A sitemap that cannot be read exits non-zero before anything is written, so the next run
 * compares against the older snapshot and nothing is lost.
 *
 * Run:  node scripts/indexnow-changes.mjs <snapshot.json> <urls.txt>
 * Test: node --test scripts/indexnow-changes.test.mjs
 */
import { existsSync, readFileSync, writeFileSync } from "fs";
import { pathToFileURL } from "url";

const SITE = "https://agentskillshub.top";
const FALLBACK_DAYS = 2;
const FETCH_TIMEOUT_MS = 30_000;
const DAY_MS = 86_400_000;

/** The <loc> of each <sitemap> in a sitemap index. */
export function sitemapLocs(indexXml) {
  return [...indexXml.matchAll(/<sitemap>\s*<loc>([^<]+)<\/loc>/g)].map((m) => m[1].trim());
}

/** url -> lastmod (YYYY-MM-DD or null) for each <url> of a urlset; hreflang alternates are not entries. */
export function urlEntries(urlsetXml) {
  const entries = {};
  for (const [, block] of urlsetXml.matchAll(/<url>([\s\S]*?)<\/url>/g)) {
    const loc = block.match(/<loc>([^<]+)<\/loc>/)?.[1].trim();
    if (loc) entries[loc] = block.match(/<lastmod>(\d{4}-\d{2}-\d{2})/)?.[1] ?? null;
  }
  return entries;
}

/** One snapshot from several sub-sitemaps; a URL listed in two keeps its newer lastmod. */
export function mergeEntries(parts) {
  const merged = {};
  for (const part of parts) {
    for (const [url, lastmod] of Object.entries(part)) {
      const seen = merged[url];
      merged[url] = seen === undefined || (lastmod ?? "") > (seen ?? "") ? lastmod : seen;
    }
  }
  return merged;
}

/** URLs added, re-dated and dropped between two snapshots. */
export function diffSnapshots(prev, next) {
  const urls = Object.keys(next);
  return {
    added: urls.filter((url) => !Object.hasOwn(prev, url)),
    updated: urls.filter((url) => Object.hasOwn(prev, url) && prev[url] !== next[url]),
    dropped: Object.keys(prev).filter((url) => !Object.hasOwn(next, url)),
  };
}

/** Without a previous snapshot: the URLs whose lastmod is within `days` before `today`. */
export function recentUrls(next, today, days) {
  const since = new Date(Date.parse(today) - days * DAY_MS).toISOString().slice(0, 10);
  return Object.keys(next).filter((url) => next[url] !== null && next[url] >= since);
}

async function fetchText(url) {
  // A fresh query string gets past the CDN copy of the files the deploy just replaced.
  const res = await fetch(`${url}?v=${Date.now()}`, { signal: AbortSignal.timeout(FETCH_TIMEOUT_MS) });
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  return res.text();
}

async function liveSnapshot() {
  const subs = sitemapLocs(await fetchText(`${SITE}/sitemap.xml`));
  if (subs.length === 0) throw new Error("the sitemap index lists no sub-sitemaps");
  return mergeEntries(await Promise.all(subs.map(async (loc) => urlEntries(await fetchText(loc)))));
}

async function main(snapshotPath, urlsPath) {
  const next = await liveSnapshot();
  const prev = existsSync(snapshotPath) ? JSON.parse(readFileSync(snapshotPath, "utf-8")).urls : null;
  const today = new Date().toISOString().slice(0, 10);
  const diff = prev ? diffSnapshots(prev, next) : null;
  const urls = (diff ? [...diff.added, ...diff.updated, ...diff.dropped] : recentUrls(next, today, FALLBACK_DAYS)).sort();
  writeFileSync(urlsPath, urls.map((url) => `${url}\n`).join(""));
  writeFileSync(snapshotPath, JSON.stringify({ taken: new Date().toISOString(), urls: next }));
  const why = diff
    ? `added ${diff.added.length}, re-dated ${diff.updated.length}, dropped ${diff.dropped.length}`
    : `no previous snapshot, so the ${urls.length} with a lastmod in the last ${FALLBACK_DAYS} days`;
  console.log(`${Object.keys(next).length} URLs in the live sitemaps; to send: ${urls.length} (${why})`);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [snapshotPath, urlsPath] = process.argv.slice(2);
  main(snapshotPath, urlsPath).catch((err) => {
    console.error(err.message);
    process.exit(1);
  });
}
