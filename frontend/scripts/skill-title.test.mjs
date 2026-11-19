import { test } from "node:test";
import assert from "node:assert/strict";
import { skillTitle, displayWidth, TITLE_MAX_WIDTH } from "../src/lib/skillMeta.mjs";

test("a short repo keeps its owner", () => {
  const t = skillTitle("anthropics/skills", "skills", "Public repository for Agent Skills");
  assert.match(t, /^skills by anthropics: /);
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
  assert.ok(displayWidth(t) <= TITLE_MAX_WIDTH + 4, t);
});
