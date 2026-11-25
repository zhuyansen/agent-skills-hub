import { test } from "node:test";
import assert from "node:assert/strict";
import {
  skillTitle,
  fallbackTitle,
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

test("a short English skill description is padded with security grade context", () => {
  const d = skillDescription("Skills", "My Claude Code skills", [], { grade: "safe", quality: 78 });
  assert.ok(d.length >= DESCRIPTION_MIN_WIDTH && d.length <= DESCRIPTION_LIMIT, `${d.length}: ${d}`);
  assert.match(d, /Security grade: SAFE \(78\/100\)\.$/);
});

test("a short ungraded English skill description gets the audit fallback", () => {
  const d = skillDescription("Unity-Skills", "Unity skills", [], { grade: null, quality: null });
  assert.ok(d.length >= DESCRIPTION_MIN_WIDTH && d.length <= DESCRIPTION_LIMIT, `${d.length}: ${d}`);
  assert.match(d, /Agent Skills Hub\.$/);
});

test("a normal-length or CJK skill description is not padded", () => {
  const normal = skillDescription("nginx-ui", "Yet another WebUI for Nginx, built with Go and Vue", [], { grade: "safe", quality: 80 });
  assert.ok(!normal.includes("Security grade:"), normal);

  const zh = skillDescription("Skills", "专为大模型与 AI 编程助手打造的中文技能集合与工作流模板", [], { grade: "safe", quality: 80 });
  assert.ok(!zh.includes("Security grade:"), zh);
});
