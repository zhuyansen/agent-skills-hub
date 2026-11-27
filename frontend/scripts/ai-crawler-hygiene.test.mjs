import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parentSectionHtml } from "./sub-skills.mjs";

test("parentSectionHtml marks pre-rendered sub-skills section for client hydration guard", () => {
  const html = parentSectionHtml("owner/repo", [
    { slug: "s1", name: "Skill One", path: "skills/s1/SKILL.md", grade: "A", description: "desc", page: true },
  ]);
  assert.match(html, /data-ash-sub-skills="1"/);
});

test("robots.txt keeps /best-runs/*.html disallowed for general bots while allowing user-triggered AI assistants", () => {
  const robots = readFileSync(new URL("../public/robots.txt", import.meta.url), "utf-8");

  // Default wildcard stanza still blocks search/training bots from evidence HTML pages
  const wildcardBlock = robots.split(/User-agent:\s*ChatGPT-User/)[0];
  assert.match(wildcardBlock, /User-agent:\s*\*/);
  assert.match(wildcardBlock, /Disallow:\s*\/best-runs\/\*\.html\$/);

  // User-triggered AI assistants explicitly allowed to verify benchmark proof
  for (const ua of ["ChatGPT-User", "Claude-User", "Perplexity-User", "MistralAI-User", "DuckAssistBot"]) {
    assert.match(robots, new RegExp(`User-agent:\\s*${ua}`));
  }
  const assistantBlock = robots.slice(robots.indexOf("User-agent: ChatGPT-User"));
  assert.match(assistantBlock, /Allow:\s*\/best-runs\//);
  assert.match(assistantBlock, /Disallow:\s*\/\*?\?repo=/);
});
