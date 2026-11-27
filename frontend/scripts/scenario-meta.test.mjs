import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { buildScenarioMetaDesc, clampMetaDesc, META_MAX } from "./scenario-meta.mjs";
import { RULE_COUNT } from "../src/lib/howWeGradeMeta.mjs";

const SCENARIOS = JSON.parse(readFileSync(new URL("./scenario-keywords.json", import.meta.url), "utf8"));
const RUNS = JSON.parse(readFileSync(new URL("./scenario-runs.json", import.meta.url), "utf8"));
const KINDS = JSON.parse(readFileSync(new URL("./scenario-kinds.json", import.meta.url), "utf8"));

const SUBJECT_NOUN = /\b(tools?|servers?|frameworks?|platforms?|integrations?|skills?|bots|alternatives)\b/i;

function descSubjectOf(scenario) {
  if (scenario.serp_subject) {
    return SUBJECT_NOUN.test(scenario.serp_subject)
      ? scenario.serp_subject
      : `${scenario.serp_subject} Tools`;
  }
  const hasNoun = /\b(tools?|servers?|frameworks?|platforms?|integrations?|skills?)\b/i.test(scenario.title);
  return (hasNoun ? scenario.title : `${scenario.title} Tools`).toLowerCase();
}

function bySlug(slug) {
  const s = SCENARIOS.find((x) => x.slug === slug);
  assert.ok(s, `missing scenario ${slug}`);
  return s;
}

test("explicit scenario.meta_description override wins and clamps cleanly to <= 155 chars", () => {
  const short = buildScenarioMetaDesc({
    scenario: { slug: "demo", title: "Demo", meta_description: "Custom hand-crafted SERP description." },
    itemCount: 20,
    canClaim: true,
    safeN: 18,
    flaggedN: 2,
    ruleCount: RULE_COUNT,
    year: 2026,
  });
  assert.equal(short, "Custom hand-crafted SERP description.");

  const longRaw =
    "Hand-crafted description that intentionally runs well beyond one hundred and fifty five characters so we can verify that clamping breaks cleanly at a word boundary without slicing words in half.";
  const clamped = buildScenarioMetaDesc({
    scenario: { slug: "demo", title: "Demo", meta_description: longRaw },
  });
  assert.ok(clamped.length <= META_MAX, `length ${clamped.length}: ${clamped}`);
  assert.doesNotMatch(clamped, /\bboundar…|\bcharact…|\bwithou…/);
});

test("tested scenarios with picks[0] name #1 tested pick within 155 chars and drop boilerplate", () => {
  const cases = [
    { slug: "ppt-presentation", itemCount: 259, safeN: 205, flaggedN: 54, expectedPick: "ppt-master" },
    { slug: "code-review", itemCount: 120, safeN: 95, flaggedN: 25, expectedPick: "code-review-skill" },
    { slug: "seo-tools", itemCount: 86, safeN: 68, flaggedN: 18, expectedPick: "aaron-marketing-skills" },
    { slug: "skill-management-tools", itemCount: 64, safeN: 52, flaggedN: 12, expectedPick: "asm" },
    { slug: "claude-video-skills", itemCount: 550, safeN: 420, flaggedN: 130, expectedPick: "explainroo" },
    { slug: "animation-skills", itemCount: 92, safeN: 78, flaggedN: 14, expectedPick: "gsap-skills" },
    { slug: "anti-slop", itemCount: 74, safeN: 61, flaggedN: 13, expectedPick: "sloptrim" },
    { slug: "ai-design", itemCount: 148, safeN: 120, flaggedN: 28, expectedPick: "taste-skill" },
    { slug: "claude-code-skills", itemCount: 792, safeN: 640, flaggedN: 152, expectedPick: "Anthropic Skills" },
  ];

  for (const c of cases) {
    const scenario = bySlug(c.slug);
    const run = RUNS[c.slug];
    assert.ok(run, `expected run for ${c.slug}`);
    const desc = buildScenarioMetaDesc({
      scenario,
      descSubject: descSubjectOf(scenario),
      itemCount: c.itemCount,
      canClaim: true,
      safeN: c.safeN,
      flaggedN: c.flaggedN,
      ruleCount: RULE_COUNT,
      topNames: "repo-a, repo-b, repo-c",
      run,
      year: 2026,
    });
    assert.ok(desc.length <= META_MAX, `${c.slug}: ${desc.length} > ${META_MAX}: "${desc}"`);
    assert.match(desc, /^Tested \d+/, `${c.slug}: expected Tested prefix, got "${desc}"`);
    assert.ok(desc.includes(`#1 ${c.expectedPick}`), `${c.slug}: expected #1 ${c.expectedPick} in "${desc}"`);
    assert.doesNotMatch(desc, /independently security-graded:/, `${c.slug}: old boilerplate found`);
    assert.ok(desc.includes("SAFE"), `${c.slug}: expected SAFE count in "${desc}"`);
  }
});

test("tested scenario with verdict.answer (image-generation, 130 runs) builds non-boilerplate hands-on summary", () => {
  const scenario = bySlug("image-generation");
  const run = RUNS["image-generation"];
  const desc = buildScenarioMetaDesc({
    scenario,
    descSubject: descSubjectOf(scenario),
    itemCount: 240,
    canClaim: true,
    safeN: 190,
    flaggedN: 50,
    ruleCount: RULE_COUNT,
    topNames: "baoyu-skills, nanobanana, flux-mcp",
    run,
    year: 2026,
  });
  assert.ok(desc.length <= META_MAX, `length ${desc.length}: "${desc}"`);
  assert.match(desc, /^Hands-on tested 130 /);
  assert.ok(desc.includes("SAFE"), `expected SAFE count in "${desc}"`);
  assert.doesNotMatch(desc, /independently security-graded:/);
  assert.doesNotMatch(desc, /…/, `expected complete clause without ellipsis, got "${desc}"`);
});

test("security-graded scenario without hands-on runs (refactoring) uses concise higher-signal format", () => {
  const scenario = bySlug("refactoring");
  const subject = descSubjectOf(scenario);
  const desc = buildScenarioMetaDesc({
    scenario,
    descSubject: subject,
    itemCount: 42,
    canClaim: true,
    safeN: 36,
    flaggedN: 6,
    ruleCount: RULE_COUNT,
    topNames: "refactor-agent, ast-grep-mcp, codemod-skill",
    run: null,
    year: 2026,
  });
  assert.ok(desc.length <= META_MAX, `length ${desc.length}: "${desc}"`);
  assert.ok(
    desc.startsWith(`42 ${subject} (2026): 36 SAFE, 6 flagged (${RULE_COUNT} rules).`),
    `unexpected format: "${desc}"`,
  );
  assert.match(desc, /Top picks?: refactor-agent/);
  assert.doesNotMatch(desc, /independently security-graded:/);
});

test("ungraded scenario without runs uses clean comparison fallback", () => {
  const desc = buildScenarioMetaDesc({
    scenario: { slug: "demo", title: "Demo Workflow" },
    descSubject: "demo workflow tools",
    itemCount: 15,
    canClaim: false,
    safeN: 0,
    flaggedN: 0,
    ruleCount: RULE_COUNT,
    topNames: "alpha, beta, gamma",
    run: null,
    year: 2026,
  });
  assert.ok(desc.length <= META_MAX);
  assert.equal(
    desc,
    "15 open-source demo workflow tools compared (2026): alpha, beta, gamma. Quality-scored and refreshed every 8h.",
  );
});

test("every live scenario in scenario-keywords.json gets a clean <= 155 char meta description", () => {
  const live = SCENARIOS.filter((s) => !s.retired);
  assert.ok(live.length >= 30);
  for (const scenario of live) {
    const itemCount = KINDS[scenario.slug]
      ? Object.keys(KINDS[scenario.slug].repos || {}).length
      : scenario.match?.max_results || 20;
    const safeN = Math.max(1, Math.round(itemCount * 0.8));
    const flaggedN = itemCount - safeN;
    const desc = buildScenarioMetaDesc({
      scenario,
      descSubject: descSubjectOf(scenario),
      itemCount,
      canClaim: true,
      safeN,
      flaggedN,
      ruleCount: RULE_COUNT,
      topNames: "alpha-skill, beta-mcp, gamma-cli",
      run: RUNS[scenario.slug] || null,
      year: 2026,
    });
    assert.ok(desc.length > 30, `${scenario.slug}: unexpectedly short "${desc}"`);
    assert.ok(desc.length <= META_MAX, `${scenario.slug}: ${desc.length} > ${META_MAX}: "${desc}"`);
    assert.doesNotMatch(desc, /independently security-graded:/, `${scenario.slug}: boilerplate "${desc}"`);
    // Ensure balanced parentheses (no truncated "(for a PowerPoint...")
    const opens = (desc.match(/\(/g) || []).length;
    const closes = (desc.match(/\)/g) || []).length;
    assert.equal(opens, closes, `${scenario.slug}: unbalanced parens in "${desc}"`);
  }
});

test("clampMetaDesc never cuts mid-word", () => {
  const input = "word1 word2 word3 " + "superlongtoken ".repeat(15);
  const out = clampMetaDesc(input, 60);
  assert.ok(out.length <= 60);
  assert.match(out, /superlongtoken…$/);
});
