import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { relatedScenarios } from "./scenario-related.mjs";

const ALL = [
  { slug: "cli-tools", title: "CLI Tools", related: ["git-tools", "refactoring", "no-such-page", "code-review"] },
  { slug: "refactoring", title: "Code Refactoring", related: ["cli-tools"] },
  { slug: "code-review", title: "Code Review", related: [] },
  { slug: "git-tools", title: "Git & Version Control", retired: true, related: ["cli-tools", "debugging"] },
  { slug: "debugging", title: "Debugging", retired: true, related: [] },
];
const bySlug = (slug) => ALL.find((s) => s.slug === slug);
const slugs = (list) => list.map((s) => s.slug);

// A retired page is noindex. Until 2026-11-20 live pages kept recommending them: 25 of the 107
// "Related Categories" links on live pages led to a retired page (all three on /best/cli-tools/),
// and 14 live pages were recommended by no other live page.
test("a live page recommends only live pages, in the order written", () => {
  assert.deepEqual(slugs(relatedScenarios(bySlug("cli-tools"), ALL)), ["refactoring", "code-review"]);
});

test("a slug with no page is skipped", () => {
  assert.ok(!slugs(relatedScenarios(bySlug("cli-tools"), ALL)).includes("no-such-page"));
});

test("a retired page keeps every page it named, retired ones too", () => {
  assert.deepEqual(slugs(relatedScenarios(bySlug("git-tools"), ALL)), ["cli-tools", "debugging"]);
});

test("a page with no related list recommends nothing", () => {
  assert.deepEqual(relatedScenarios({ slug: "x", title: "X" }, ALL), []);
});

test("every page a live page names in scenario-keywords.json exists and is another page", () => {
  const scenarios = JSON.parse(readFileSync(new URL("./scenario-keywords.json", import.meta.url), "utf-8"));
  const known = new Set(scenarios.map((s) => s.slug));
  for (const scenario of scenarios.filter((s) => !s.retired)) {
    for (const slug of scenario.related || []) {
      assert.ok(known.has(slug), `${scenario.slug} names "${slug}", which is not a page`);
      assert.notEqual(slug, scenario.slug, `${scenario.slug} names itself`);
    }
  }
});

const MIN_RELATED = 2;

test("every live page in scenario-keywords.json still recommends at least two live pages", () => {
  const scenarios = JSON.parse(readFileSync(new URL("./scenario-keywords.json", import.meta.url), "utf-8"));
  for (const scenario of scenarios.filter((s) => !s.retired)) {
    const shown = relatedScenarios(scenario, scenarios);
    assert.ok(shown.length >= MIN_RELATED, `${scenario.slug} recommends ${shown.length}: ${slugs(shown).join(", ")}`);
  }
});
