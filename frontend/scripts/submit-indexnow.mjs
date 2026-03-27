#!/usr/bin/env node
/**
 * IndexNow submission script — proactively notify search engines about new/updated pages.
 * Supports Bing, Yandex, and search engines that support the IndexNow protocol.
 * Google does not support IndexNow but we submit to Bing which shares with partners.
 *
 * Usage:
 *   node scripts/submit-indexnow.mjs                    # submit all indexed URLs
 *   node scripts/submit-indexnow.mjs --recent 7         # only URLs updated in last 7 days
 *   node scripts/submit-indexnow.mjs --dry-run          # preview without submitting
 *
 * Requires: INDEXNOW_KEY env var (or auto-generates a key file)
 */

import { readFileSync, writeFileSync, existsSync } from "fs";
import { join } from "path";
import { randomUUID } from "crypto";

const SITE = "https://agentskillshub.top";
const DIST = "dist";
const INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow";

function parseArgs() {
  const args = process.argv.slice(2);
  return {
    dryRun: args.includes("--dry-run"),
    recentDays: args.includes("--recent")
      ? parseInt(args[args.indexOf("--recent") + 1] || "7", 10)
      : 0,
  };
}

function getOrCreateKey() {
  const keyFile = join(DIST, "indexnow-key.txt");
  let key = process.env.INDEXNOW_KEY;
  if (!key) {
    if (existsSync(keyFile)) {
      key = readFileSync(keyFile, "utf-8").trim();
    } else {
      key = randomUUID().replace(/-/g, "");
      console.log(`Generated new IndexNow key: ${key}`);
    }
  }
  // Write key verification file (required by IndexNow protocol)
  writeFileSync(join(DIST, `${key}.txt`), key);
  writeFileSync(keyFile, key);
  return key;
}

function extractUrlsFromSitemap(sitemapPath) {
  if (!existsSync(sitemapPath)) return [];
  const content = readFileSync(sitemapPath, "utf-8");
  const urls = [];
  const locRegex = /<loc>(.*?)<\/loc>/g;
  const lastmodRegex = /<lastmod>(.*?)<\/lastmod>/g;
  let locMatch, lastmodMatch;
  while ((locMatch = locRegex.exec(content)) !== null) {
    lastmodMatch = lastmodRegex.exec(content);
    urls.push({
      url: locMatch[1],
      lastmod: lastmodMatch ? lastmodMatch[1] : null,
    });
  }
  return urls;
}

async function submitBatch(urls, key) {
  const BATCH_SIZE = 10000; // IndexNow allows up to 10k per request
  let submitted = 0;

  for (let i = 0; i < urls.length; i += BATCH_SIZE) {
    const batch = urls.slice(i, i + BATCH_SIZE);
    const payload = {
      host: "agentskillshub.top",
      key,
      keyLocation: `${SITE}/${key}.txt`,
      urlList: batch,
    };

    const res = await fetch(INDEXNOW_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    submitted += batch.length;
    console.log(`Batch ${Math.floor(i / BATCH_SIZE) + 1}: ${res.status} ${res.statusText} (${batch.length} URLs)`);

    if (res.status !== 200 && res.status !== 202) {
      const text = await res.text().catch(() => "");
      console.error(`  Error: ${text}`);
    }
  }

  return submitted;
}

async function main() {
  const { dryRun, recentDays } = parseArgs();

  // Collect URLs from all sitemaps
  const sitemapFiles = ["sitemap-top.xml", "sitemap-mid.xml", "sitemap-rest.xml", "sitemap-categories.xml", "sitemap-static.xml"];
  let allUrls = [];

  for (const file of sitemapFiles) {
    const entries = extractUrlsFromSitemap(join(DIST, file));
    allUrls.push(...entries);
  }

  console.log(`Found ${allUrls.length} total URLs in sitemaps`);

  // Filter by recency if requested
  if (recentDays > 0) {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - recentDays);
    const cutoffStr = cutoff.toISOString().split("T")[0];
    allUrls = allUrls.filter((u) => u.lastmod && u.lastmod >= cutoffStr);
    console.log(`Filtered to ${allUrls.length} URLs updated in last ${recentDays} days`);
  }

  const urlStrings = allUrls.map((u) => u.url);

  if (dryRun) {
    console.log(`\n[DRY RUN] Would submit ${urlStrings.length} URLs:`);
    urlStrings.slice(0, 10).forEach((u) => console.log(`  ${u}`));
    if (urlStrings.length > 10) console.log(`  ... and ${urlStrings.length - 10} more`);
    return;
  }

  const key = getOrCreateKey();
  console.log(`Using IndexNow key: ${key.slice(0, 8)}...`);

  const submitted = await submitBatch(urlStrings, key);
  console.log(`\nDone: ${submitted} URLs submitted to IndexNow`);
}

main().catch(console.error);
