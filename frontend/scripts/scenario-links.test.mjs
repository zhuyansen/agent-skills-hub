import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import {
  expandedRelatedScenarios,
  scenarioComparisons,
  resourcesFor,
  resourcesHtml,
  BLOG_GUIDES,
} from "./scenario-links.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCENARIOS = JSON.parse(readFileSync(new URL("./scenario-keywords.json", import.meta.url), "utf8"));
const PUBLIC_DIR = join(__dirname, "..", "public");

test("every BLOG_GUIDES href exists on disk under frontend/public/", () => {
  for (const post of BLOG_GUIDES) {
    const file = join(PUBLIC_DIR, ...post.href.split("/").filter(Boolean), "index.html");
    assert.ok(existsSync(file), `Missing blog file for ${post.href}: ${file}`);
  }
});

test("every live scenario expands to 8-10 live related /best/ links with zero retired or self links", () => {
  const live = SCENARIOS.filter((s) => !s.retired);
  for (const sc of live) {
    const rels = expandedRelatedScenarios(sc, SCENARIOS);
    assert.ok(rels.length >= 8, `${sc.slug}: expected >= 8 related guides, got ${rels.length}`);
    assert.ok(rels.length <= 10, `${sc.slug}: expected <= 10 related guides, got ${rels.length}`);
    const seen = new Set();
    for (const rel of rels) {
      assert.ok(!rel.retired, `${sc.slug} linked retired page ${rel.slug}`);
      assert.notEqual(rel.slug, sc.slug, `${sc.slug} linked itself`);
      assert.ok(!seen.has(rel.slug), `${sc.slug} duplicated ${rel.slug}`);
      seen.add(rel.slug);
    }
    // Curated direct live picks always stay first in exact order
    const directLive = (sc.related || [])
      .map((slug) => SCENARIOS.find((s) => s.slug === slug))
      .filter((r) => r && !r.retired);
    for (let i = 0; i < directLive.length; i++) {
      assert.equal(rels[i].slug, directLive[i].slug, `${sc.slug}: direct pick #${i} out of order`);
    }
  }
});

test("retired scenarios keep their original related list and get no resources block", () => {
  const retired = SCENARIOS.find((s) => s.retired);
  assert.ok(retired);
  assert.equal(resourcesHtml(retired), "");
  const rels = expandedRelatedScenarios(retired, SCENARIOS);
  assert.ok(rels.length <= (retired.related || []).length);
});

test("every live scenario gets topic-matched comparisons and >= 17 total thematic links", () => {
  const live = SCENARIOS.filter((s) => !s.retired);
  for (const sc of live) {
    const rels = expandedRelatedScenarios(sc, SCENARIOS);
    const comps = scenarioComparisons(sc, []);
    const res = resourcesFor(sc);
    assert.ok(comps.length >= 2, `${sc.slug}: expected >= 2 comparisons, got ${comps.length}`);
    assert.ok(res.length >= 5, `${sc.slug}: expected >= 5 resource links, got ${res.length}`);
    const total = rels.length + comps.length + res.length;
    assert.ok(total >= 17, `${sc.slug}: expected >= 17 thematic internal links, got ${total}`);
  }
});

test("direct repo comparisons are kept first without cluster bloat when >= 2 match", () => {
  const sc = SCENARIOS.find((s) => s.slug === "claude-video-skills");
  const skills = [
    { repo_full_name: "nexu-io/openmotion" },
    { repo_full_name: "heygen-com/hyperframes" },
    { repo_full_name: "remotion-dev/remotion" },
  ];
  const comps = scenarioComparisons(sc, skills);
  assert.deepEqual(
    comps.map((c) => c.slug),
    ["openmotion-vs-hyperframes", "openmotion-vs-remotion", "hyperframes-vs-remotion"],
  );
});
