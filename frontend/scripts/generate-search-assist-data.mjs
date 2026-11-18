#!/usr/bin/env node
/**
 * Writes src/data/search-assist.json for src/lib/searchAssist.mjs:
 *
 * - scenarios: search term → live scenario page, from scenario-keywords.json
 *   (title, seo_keyword, primary keywords, slug) and scenario-zh.json (title,
 *   keywords), plus ALIASES for terms visitors type that no config holds.
 * - vocab: words the typo fallback may correct to, most common first:
 *   search-vocab-observed.json (words from searches that found results,
 *   site_searches 10-31 → 11-17) followed by every word of the live scenarios.
 *
 * Run after editing scenario-keywords.json or scenario-zh.json:
 *   node scripts/generate-search-assist-data.mjs
 * `node --test scripts/search-assist.test.mjs` fails while the output is stale.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const DIR = dirname(fileURLToPath(import.meta.url));
const OUT = join(DIR, "..", "src", "data", "search-assist.json");

// Single words too generic to name one page: they match half the catalog.
const TOO_GENERIC = new Set([
  "ai", "agent", "agents", "claude", "codex", "code", "mcp", "skill", "skills", "tool", "tools",
  "server", "servers", "plugin", "plugins", "open source", "free", "best",
]);

// Terms from the search log that point at a page but appear in no config.
const ALIASES = {
  video: "claude-video-skills",
  videos: "claude-video-skills",
  "video edit": "claude-video-skills",
  "video editing": "claude-video-skills",
  "video cut": "claude-video-skills",
  "video skills": "claude-video-skills",
  视频: "claude-video-skills",
  剪辑: "claude-video-skills",
  motion: "animation-skills",
  animation: "animation-skills",
  "motion graphics": "animation-skills",
  "3d animation": "animation-skills",
  "2d animation": "animation-skills",
  动画: "animation-skills",
  ppt: "ppt-presentation",
  presentation: "ppt-presentation",
  slides: "ppt-presentation",
  design: "ai-design",
  ui: "ai-design",
  blender: "3d-mcp",
  unity: "3d-mcp",
  godot: "3d-mcp",
  telegram: "telegram-bot",
  obsidian: "obsidian-second-brain",
  seo: "seo-tools",
  hooks: "claude-code-hooks",
};

export function buildSearchAssist() {
  const scenarios = JSON.parse(readFileSync(join(DIR, "scenario-keywords.json"), "utf-8"));
  const zh = JSON.parse(readFileSync(join(DIR, "scenario-zh.json"), "utf-8"));
  const observed = JSON.parse(readFileSync(join(DIR, "search-vocab-observed.json"), "utf-8"));
  const live = scenarios.filter((s) => !s.retired);
  const link = (s) => ({ slug: s.slug, en: s.title, zh: zh[s.slug]?.t || s.title });
  const bySlug = Object.fromEntries(live.map((s) => [s.slug, s]));

  const table = {};
  const put = (term, s) => {
    const t = String(term || "").trim().toLowerCase().replace(/\s+/g, " ");
    if (t.length < 2 || TOO_GENERIC.has(t) || table[t]) return;
    table[t] = link(s);
  };
  for (const [term, slug] of Object.entries(ALIASES)) {
    if (!bySlug[slug]) throw new Error(`alias ${term} → ${slug}: no live scenario`);
    put(term, bySlug[slug]);
  }
  for (const s of live) {
    put(s.title, s);
    put(s.seo_keyword, s);
    put(s.slug.replace(/-/g, " "), s);
    for (const k of s.match?.primary_keywords || []) put(k, s);
    put(zh[s.slug]?.t, s);
    for (const k of zh[s.slug]?.k || []) put(k, s);
  }

  const vocab = [...observed];
  const seen = new Set(vocab);
  for (const s of live) {
    const text = [s.title, s.seo_keyword, ...(s.match?.primary_keywords || []), ...(s.match?.secondary_keywords || [])]
      .join(" ")
      .toLowerCase();
    for (const w of text.match(/[a-z][a-z0-9.+-]*[a-z0-9]/g) || []) {
      if (w.length >= 3 && !seen.has(w)) {
        seen.add(w);
        vocab.push(w);
      }
    }
  }
  const sorted = Object.fromEntries(Object.entries(table).sort(([a], [b]) => a.localeCompare(b)));
  return { scenarios: sorted, vocab };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const data = buildSearchAssist();
  writeFileSync(OUT, JSON.stringify(data) + "\n");
  console.log(`search-assist.json: ${Object.keys(data.scenarios).length} scenario terms, ${data.vocab.length} words`);
}
