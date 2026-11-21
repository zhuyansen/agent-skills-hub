import { test } from "node:test";
import assert from "node:assert/strict";
import { countNoun, authorDescription, authorTitle } from "../src/lib/authorMeta.mjs";
import { TITLE_MAX_WIDTH, displayWidth } from "../src/lib/skillMeta.mjs";

test("the site name goes first when the title is too long", () => {
  assert.equal(authorTitle("open-webui", 4, 4), "open-webui — Top 4 AI Agent Skills (Security-Graded)");
});

test("a short name with no safe skill keeps the site name", () => {
  assert.equal(authorTitle("tw93", 12, 0), "tw93 — Top 12 AI Agent Skills · Agent Skills Hub");
});

test("a long name drops the security note next", () => {
  const t = authorTitle("NateBJones-Projects-Long", 7, 7);
  assert.equal(t, "NateBJones-Projects-Long — Top 7 AI Agent Skills");
  assert.ok(displayWidth(t) <= TITLE_MAX_WIDTH, t);
});

test("one skill is not a top list", () => {
  assert.equal(authorTitle("0x4m4", 1, 1), "0x4m4 — 1 AI Agent Skill (Security-Graded)");
});

test("no count while the page is loading", () => {
  assert.equal(authorTitle("0x4m4", 0, 0), "0x4m4 — AI Agent Skills · Agent Skills Hub");
});

test("a wide name is measured by display width", () => {
  const t = authorTitle("歸藏的人工智能工具箱和技能合集工作室", 12, 3);
  assert.ok(displayWidth(t) <= TITLE_MAX_WIDTH, `${displayWidth(t)}: ${t}`);
});

test("the description counts one skill in the singular", () => {
  assert.equal(
    authorDescription("0x4m4", 1, 1, 13667),
    "0x4m4's AI agent skills: 1 open-source skill or MCP server, 13,667+ GitHub stars, 1 security-verified safe. Quality-scored on AgentSkillsHub.",
  );
});

test("the description leaves the stars out when the caller has no total", () => {
  assert.equal(
    authorDescription("anthropics", 8, 8),
    "anthropics's AI agent skills: 8 open-source skills & MCP servers, 8 security-verified safe. Quality-scored on AgentSkillsHub.",
  );
});

test("countNoun", () => {
  assert.equal(countNoun(1, "Skill", "Skills"), "1 Skill");
  assert.equal(countNoun(1234, "Skill", "Skills"), "1,234 Skills");
});

test("an author page with one or two Skills is noindex", async () => {
  const { authorIndexable } = await import("../src/lib/authorMeta.mjs");
  assert.equal(authorIndexable(1, null), false);
  assert.equal(authorIndexable(2, {}), false);
  assert.equal(authorIndexable(3, null), true);
});

test("a Master with a bio, or a Verified Creator, keeps an indexed page", async () => {
  const { authorIndexable } = await import("../src/lib/authorMeta.mjs");
  assert.equal(authorIndexable(1, { bio: "Builds Claude skills for lawyers." }), true);
  assert.equal(authorIndexable(2, { is_verified: true }), true);
  assert.equal(authorIndexable(1, { bio: "", is_verified: false }), false);
});
