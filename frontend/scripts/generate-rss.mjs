/**
 * Generate RSS feeds at build time.
 * Output:
 *   dist/feed.xml          — Latest 30 newly indexed skills
 *   dist/feed-trending.xml — Weekly trending Top 20 (star velocity)
 */

import { writeFileSync } from "fs";
import { SUPABASE_URL, SUPABASE_ANON_KEY, SITE, esc } from "./shared-utils.mjs";

function rfc822(dateStr) {
  if (!dateStr) return "";
  return new Date(dateStr).toUTCString();
}

function starsK(n) {
  if (!n) return "0";
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : `${n}`;
}

function buildRss(title, description, link, items) {
  const itemsXml = items
    .map(
      (item) => `    <item>
      <title>${esc(item.title)}</title>
      <link>${item.link}</link>
      <guid isPermaLink="true">${item.link}</guid>
      <description>${esc(item.description)}</description>
      <pubDate>${item.pubDate}</pubDate>
      <category>${esc(item.category)}</category>
    </item>`
    )
    .join("\n");

  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>${esc(title)}</title>
    <description>${esc(description)}</description>
    <link>${link}</link>
    <atom:link href="${link}/feed.xml" rel="self" type="application/rss+xml"/>
    <language>en</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <ttl>480</ttl>
${itemsXml}
  </channel>
</rss>`;
}

async function fetchJson(url) {
  const resp = await fetch(url, {
    headers: {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
    },
  });
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}: ${url}`);
  return resp.json();
}

async function main() {
  console.log("📡 Generating RSS feeds...");

  // 1. feed.xml — latest 30 new skills
  const newSkills = await fetchJson(
    `${SUPABASE_URL}/rest/v1/skills?select=repo_full_name,repo_name,author_name,description,stars,category,first_seen&order=first_seen.desc&limit=30&stars=gte.20`
  );

  const newItems = newSkills.map((s) => ({
    title: `${s.repo_name} by ${s.author_name} — ★ ${starsK(s.stars)}`,
    link: `${SITE}/skill/${s.repo_full_name}/`,
    description: `${s.description || "No description"} | Category: ${s.category} | Stars: ${s.stars}`,
    pubDate: rfc822(s.first_seen),
    category: s.category || "uncategorized",
  }));

  const feedXml = buildRss(
    "Agent Skills Hub — New Skills",
    "Latest AI agent tools, MCP servers, and Claude skills indexed on Agent Skills Hub",
    SITE,
    newItems
  );
  writeFileSync("dist/feed.xml", feedXml, "utf-8");
  console.log(`   ✅ feed.xml — ${newItems.length} items`);

  // 2. feed-trending.xml — weekly trending top 20
  const today = new Date().toISOString().slice(0, 10);
  const trending = await fetchJson(
    `${SUPABASE_URL}/rest/v1/weekly_trending_snapshots?select=repo_full_name,repo_name,author_name,description,stars,star_velocity,category,week_start,week_end&week_end=lte.${today}&order=week_end.desc,star_velocity.desc&limit=20`
  );

  const trendItems = trending.map((s, i) => {
    const vel =
      s.star_velocity >= 1000
        ? `${(s.star_velocity / 1000).toFixed(1)}k/day`
        : `${Math.round(s.star_velocity)}/day`;
    return {
      title: `#${i + 1} ${s.repo_name} — ★ ${starsK(s.stars)} (${vel})`,
      link: `${SITE}/skill/${s.repo_full_name}/`,
      description: `${s.description || ""} | Velocity: ${vel} | Stars: ${s.stars}`,
      pubDate: rfc822(s.week_end),
      category: s.category || "uncategorized",
    };
  });

  const trendXml = buildRss(
    "Agent Skills Hub — Weekly Trending",
    "Top 20 fastest-growing AI agent tools by star velocity, updated weekly",
    SITE,
    trendItems
  );
  writeFileSync("dist/feed-trending.xml", trendXml, "utf-8");
  console.log(`   ✅ feed-trending.xml — ${trendItems.length} items`);
}

main().catch((e) => {
  console.error("RSS generation failed:", e);
  process.exit(1);
});
