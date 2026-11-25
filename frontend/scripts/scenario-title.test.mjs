import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { buildScenarioTitle, TITLE_MAX } from "./scenario-title.mjs";

const SCENARIOS = JSON.parse(readFileSync(new URL("./scenario-keywords.json", import.meta.url), "utf8"));
const KINDS = JSON.parse(readFileSync(new URL("./scenario-kinds.json", import.meta.url), "utf8"));
const RUNS = JSON.parse(readFileSync(new URL("./scenario-runs.json", import.meta.url), "utf8"));

test("leads with Best and includes tested + graded counts when they fit", () => {
  const title = buildScenarioTitle({
    scenario: { slug: "claude-code-skills", title: "Claude Code Skills" },
    itemCount: 792,
    canClaim: true,
    testedCount: 39,
    year: 2026,
  });
  assert.equal(title, "Best Claude Code Skills (2026): 39 Tested, 792 Graded");
  assert.ok(title.length <= TITLE_MAX);
});

test("appends Tools when a bare title has no noun, but avoids Tools Tools or Agents Tools", () => {
  const scraping = buildScenarioTitle({
    scenario: { slug: "web-scraping", title: "Web Scraping" },
    itemCount: 10,
    canClaim: true,
    year: 2026,
  });
  assert.match(scraping, /^Best Web Scraping Tools \(2026\)/);
  assert.ok(scraping.length <= TITLE_MAX);

  const voice = buildScenarioTitle({
    scenario: { slug: "voice-agent", title: "Voice Agents" },
    itemCount: 30,
    canClaim: true,
    year: 2026,
  });
  assert.match(voice, /^Best Voice Agents \(2026\)/);
  assert.doesNotMatch(voice, /Agents Tools/);
  assert.ok(voice.length <= TITLE_MAX);
});

test("never duplicates Best prefix when subject already starts with Best", () => {
  const title = buildScenarioTitle({
    scenario: { slug: "demo", title: "Best AI Coding Skills" },
    itemCount: 25,
    canClaim: true,
    year: 2026,
  });
  assert.doesNotMatch(title, /^Best Best/i);
  assert.ok(title.length <= TITLE_MAX);
});

test("gracefully clamps an ultra-long serp_subject to <= TITLE_MAX", () => {
  const title = buildScenarioTitle({
    scenario: {
      slug: "ultra-long",
      title: "Ultra",
      serp_subject: "Enterprise Kubernetes Distributed Observability Tracing & Telemetry MCP Servers",
    },
    itemCount: 42,
    canClaim: true,
    year: 2026,
  });
  assert.ok(title.length <= TITLE_MAX, `got ${title.length}: ${title}`);
});

test("every live scenario in scenario-keywords.json gets a clean Best title <= 60 chars", () => {
  const live = SCENARIOS.filter((s) => !s.retired);
  assert.ok(live.length >= 30);
  for (const scenario of live) {
    const itemCount = KINDS[scenario.slug]
      ? Object.keys(KINDS[scenario.slug].repos || {}).length
      : scenario.match?.max_results || 10;
    const testedCount = RUNS[scenario.slug]
      ? Object.keys(RUNS[scenario.slug].runs || {}).length
      : 0;
    const title = buildScenarioTitle({
      scenario,
      itemCount,
      canClaim: true,
      testedCount,
      year: 2026,
    });
    assert.ok(title.startsWith("Best "), `${scenario.slug}: expected Best prefix, got "${title}"`);
    assert.ok(title.length <= TITLE_MAX, `${scenario.slug}: ${title.length} > ${TITLE_MAX}: "${title}"`);
    assert.doesNotMatch(title, /\bTools Tools\b|\bBest Best\b/i, `${scenario.slug}: "${title}"`);
    assert.ok(title.includes("(2026)"), `${scenario.slug}: missing year in "${title}"`);
  }
});
