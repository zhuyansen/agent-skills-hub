import { test } from "node:test";
import assert from "node:assert/strict";
import {
  skillTitle,
  fallbackTitle,
  fitClause,
  skillDescription,
  displayWidth,
  TITLE_MAX_WIDTH,
  DESCRIPTION_LIMIT,
  DESCRIPTION_MIN_WIDTH,
} from "../src/lib/skillMeta.mjs";

test("a short repo keeps its owner", () => {
  const t = skillTitle("someone/skills", "skills", "Public repository for Agent Skills");
  assert.match(t, /^skills by someone: /);
});

test("an owner that repeats the repo name is dropped", () => {
  const t = skillTitle("datamodel-code-generator/datamodel-code-generator", "datamodel-code-generator",
    "Generate Pydantic v2 models from OpenAPI and JSON Schema");
  assert.match(t, /^datamodel-code-generator: /);
});

test("a long repo name drops the owner so the title fits the budget", () => {
  const t = skillTitle("decodingai-magazine/building-a-coding-agent-from-scratch-course",
    "building-a-coding-agent-from-scratch-course", "Learn harness engineering by building a coding agent");
  assert.ok(!t.includes(" by decodingai-magazine"));
  assert.ok(displayWidth(t) <= TITLE_MAX_WIDTH, t);
});

test("an ultra-long repo name is truncated cleanly to TITLE_MAX_WIDTH", () => {
  const repo = "Assemblies-of-putative-SARS-CoV2-spike-encoding-mRNA-sequences-for-vaccines-BNT-162b2-and-mRNA-1273";
  const t = skillTitle(`NAalytics/${repo}`, repo, "mRNA sequence assemblies");
  assert.ok(displayWidth(t) <= TITLE_MAX_WIDTH, `${displayWidth(t)}: ${t}`);
  assert.ok(t.endsWith("…"), t);

  const gone = fallbackTitle(`NAalytics/${repo}`);
  assert.ok(displayWidth(gone) <= TITLE_MAX_WIDTH, `${displayWidth(gone)}: ${gone}`);
  assert.ok(gone.endsWith("…"), gone);
});

test("hyphenated compound words are not cut mid-compound (heydamir/unslop regression)", () => {
  const t = skillTitle(
    "heydamir/unslop",
    "unslop",
    "A Claude skill that turns vibecoded, AI-looking UI into a designed interface",
  );
  assert.ok(displayWidth(t) <= TITLE_MAX_WIDTH, `${displayWidth(t)}: ${t}`);
  assert.ok(!t.endsWith(", AI"), t);
  assert.ok(!t.endsWith("AI"), t);
  assert.ok(!t.endsWith("-"), t);
  assert.equal(t, "unslop by heydamir: A Claude skill");
});

test("fitClause backs up cleanly across hyphen, slash, and apostrophe joins", () => {
  assert.equal(fitClause("Fast tool for building open-source UI components", 28), "Fast tool for building");
  assert.equal(fitClause("Fast tool for building open-source UI components", 27), "Fast tool for building");
  assert.equal(fitClause("Automated workflow for CI/CD pipelines everywhere", 26), "Automated workflow");
  assert.equal(fitClause("Automated workflow for CI/CD pipelines everywhere", 25), "Automated workflow");
  assert.equal(fitClause("Clean agent templates that don't break in production", 31), "Clean agent templates");
  assert.equal(fitClause("Clean agent templates that don’t break in production", 31), "Clean agent templates");
});

test("skillDescription never leaks raw git clone or install commands/URLs", () => {
  const d = skillDescription(
    "bang-motion",
    "Generate motion graphics videos from React code with Claude Code",
    ["git clone https://github.com/bangtutorial/bang-motion.git", "npx bang-motion"],
    { grade: "safe", quality: 92, hasInstall: true },
  );
  assert.ok(!d.includes("git clone"), d);
  assert.ok(!d.includes("https://"), d);
  assert.ok(!d.includes("npx"), d);
  assert.ok(!d.includes("Install:"), d);
  assert.match(d, /^\[SAFE · 92\/100 · 44-rule audit\] bang-motion:/);
  assert.ok(d.endsWith("Setup & alternatives."), d);
  assert.ok(d.length <= DESCRIPTION_LIMIT, `${d.length}: ${d}`);
  assert.ok(displayWidth(d) <= DESCRIPTION_LIMIT, `${displayWidth(d)}: ${d}`);
});

test("skillDescription leads with security grade and respects length/width limits", () => {
  const unslop = skillDescription(
    "unslop",
    "A Claude skill that turns vibecoded, AI-looking UI into a designed interface",
    ["git clone https://github.com/heydamir/unslop.git"],
    { grade: "safe", quality: null, hasInstall: true },
  );
  assert.match(unslop, /^\[SAFE · 44-rule audit\] unslop:/);
  assert.ok(unslop.endsWith("Setup & alternatives."), unslop);
  assert.ok(unslop.length <= DESCRIPTION_LIMIT, `${unslop.length}: ${unslop}`);

  const caution = skillDescription(
    "risky-tool",
    "Runs shell commands directly from agent prompts with custom plugins",
    [],
    { grade: "caution", quality: 61, hasInstall: false },
  );
  assert.match(caution, /^\[CAUTION · 61\/100 · 44-rule audit\] risky-tool:/);
  assert.ok(caution.endsWith("Alternatives compared."), caution);
  assert.ok(caution.length <= DESCRIPTION_LIMIT, `${caution.length}: ${caution}`);
});

test("a short English skill description stays within DESCRIPTION_MIN_WIDTH..DESCRIPTION_LIMIT", () => {
  const graded = skillDescription("Skills", "My Claude Code skills", [], { grade: "safe", quality: 78 });
  assert.ok(graded.length >= DESCRIPTION_MIN_WIDTH && graded.length <= DESCRIPTION_LIMIT, `${graded.length}: ${graded}`);
  assert.match(graded, /^\[SAFE · 78\/100 · 44-rule audit\] Skills:/);

  const tiny = skillDescription("x", "AI tool", [], { grade: "safe", quality: null });
  assert.ok(displayWidth(tiny) >= DESCRIPTION_MIN_WIDTH && tiny.length <= DESCRIPTION_LIMIT, `${tiny.length}: ${tiny}`);
  assert.match(tiny, /Audited on Agent Skills Hub\.$/);
});

test("skillDescription stays clean when meta is omitted or grade is absent/unknown", () => {
  const omitted = skillDescription("Unity-Skills", "Unity skills");
  assert.ok(omitted.length >= DESCRIPTION_MIN_WIDTH && omitted.length <= DESCRIPTION_LIMIT, `${omitted.length}: ${omitted}`);
  assert.match(omitted, /^Unity-Skills: Unity skills\. Independent security audit & alternatives\.$/);

  const withInstall = skillDescription("Unity-Skills", "Unity skills", ["npx unity-skills"], { grade: null, quality: null, hasInstall: true });
  assert.ok(withInstall.length >= DESCRIPTION_MIN_WIDTH && withInstall.length <= DESCRIPTION_LIMIT, `${withInstall.length}: ${withInstall}`);
  assert.ok(!withInstall.includes("npx"), withInstall);
  assert.match(withInstall, /Independent security audit, setup & alternatives\.$/);

  const unknown = skillDescription("my-tool", "Agent helper for daily tasks", [], { grade: "unknown", quality: 50 });
  assert.ok(!unknown.startsWith("["), unknown);
  assert.ok(unknown.length <= DESCRIPTION_LIMIT, `${unknown.length}: ${unknown}`);
});

test("long, CJK, and markup-heavy skill descriptions are sanitized and cleanly bounded", () => {
  const longDesc = "A ".repeat(5) + "comprehensive multi-agent orchestration framework for building production-ready, open-source workflows across Claude Code, Codex, and Cursor with telemetry and sandboxed execution";
  const d = skillDescription("orchestrator", longDesc, ["git clone https://github.com/org/orchestrator.git"], {
    grade: "safe",
    quality: 88,
    hasInstall: true,
  });
  assert.ok(d.length <= DESCRIPTION_LIMIT, `${d.length}: ${d}`);
  assert.ok(displayWidth(d) <= DESCRIPTION_LIMIT, `${displayWidth(d)}: ${d}`);
  assert.match(d, /^\[SAFE · 44-rule audit\] orchestrator:/);
  assert.ok(!d.includes("git clone"), d);

  const zh = skillDescription("Skills", "专为大模型与 AI 编程助手打造的中文技能集合与工作流模板", [], { grade: "safe", quality: 80 });
  assert.match(zh, /^\[SAFE · 80\/100 · 44-rule audit\] Skills:/);
  assert.ok(zh.length <= DESCRIPTION_LIMIT, `${zh.length}: ${zh}`);
  assert.ok(displayWidth(zh) <= DESCRIPTION_LIMIT, `${displayWidth(zh)}: ${zh}`);

  const dirty = skillDescription(
    "my-skill",
    "🚀 my-skill: **Fast** [docs](https://example.com) tool https://github.com/a/b <b>here</b>",
    [],
    { grade: "safe" },
  );
  assert.ok(!dirty.includes("https://"), dirty);
  assert.ok(!dirty.includes("<b>"), dirty);
  assert.ok(!dirty.includes("🚀"), dirty);
  assert.ok(!dirty.includes("my-skill: my-skill:"), dirty);
  assert.ok(dirty.length <= DESCRIPTION_LIMIT, `${dirty.length}: ${dirty}`);
});

