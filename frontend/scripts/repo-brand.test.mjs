// A repo named only for its kind ("skills", "mcp") is titled, headed and linked by its brand.
// OpenSEO audit, 2026-11-25: the Remotion entry, titled "skills by remotion-dev: Agent Skills",
// had 5 impressions in 28 days while another directory's "Remotion | ClaudeSkills" was #1 for
// "remotion skill". See src/lib/repoBrand.mjs.
import { test } from "node:test";
import assert from "node:assert/strict";
import { brandedName, displayName } from "../src/lib/repoBrand.mjs";
import { skillTitle, brandedHeading, displayWidth, TITLE_MAX_WIDTH, TITLE_FALLBACK } from "../src/lib/skillMeta.mjs";
import { auditTitle } from "./audit-meta.mjs";

test("a listed owner's generic repo is named by its brand", () => {
  assert.equal(brandedName("remotion-dev/skills"), "Remotion Skills");
  assert.equal(brandedName("anthropics/skills"), "Anthropic Skills");
  assert.equal(brandedName("vercel-labs/agent-skills"), "Vercel Agent Skills");
  assert.equal(brandedName("awslabs/mcp"), "AWS MCP");
  assert.equal(brandedName("MicrosoftDocs/mcp"), "Microsoft Learn MCP");
});

test("a brand that already ends with the kind is not doubled", () => {
  assert.equal(brandedName("BrowserMCP/mcp"), "Browser MCP");
});

test("an unlisted owner, or a repo with a name of its own, keeps its name", () => {
  assert.equal(brandedName("someone/skills"), null);
  assert.equal(brandedName("remotion-dev/remotion"), null);
  assert.equal(displayName("someone/skills", "skills"), "skills");
  assert.equal(displayName("remotion-dev/skills", "skills"), "Remotion Skills");
});

test("the title leads with the brand", () => {
  const t = skillTitle("anthropics/skills", "skills", "Public repository for Agent Skills");
  assert.equal(t, "Anthropic Skills: Public repository for Agent Skills");
  assert.ok(displayWidth(t) <= TITLE_MAX_WIDTH, t);
});

test("a description that only repeats the brand gives way to the fallback", () => {
  assert.equal(skillTitle("remotion-dev/skills", "skills", "Agent Skills"), `Remotion Skills: ${TITLE_FALLBACK}`);
});

test("the heading names the brand and the repo", () => {
  assert.equal(brandedHeading("remotion-dev/skills", "skills", "Agent Skills"), "Remotion Skills (remotion-dev/skills)");
  assert.equal(brandedHeading("awslabs/mcp", "mcp", "Open source MCP Servers for AWS"),
    "AWS MCP (awslabs/mcp): Open source MCP Servers for AWS");
  assert.equal(brandedHeading("someone/skills", "skills", "Agent Skills"), null);
});

test("the audit page asks about the brand", () => {
  const t = auditTitle({ repo_name: "skills", repo_full_name: "remotion-dev/skills" }, new Set(["skills"]));
  assert.equal(t, "Is Remotion Skills Safe? Security Audit");
  assert.ok(displayWidth(t) <= TITLE_MAX_WIDTH, t);
});

test("a sub-skill keeps its own name, not its parent's brand", () => {
  assert.equal(displayName("anthropics/skills", "pptx"), "pptx");
  assert.equal(brandedName("anthropics/skills/pptx"), null);
});

test("a kind that starts with the brand's last word is not doubled", () => {
  assert.equal(brandedName("BrowserMCP/mcp-server"), "Browser MCP Server");
});

test("a description in another script is kept", () => {
  assert.equal(skillTitle("anthropics/skills", "skills", "Anthropic 官方 Skills 仓库"), "Anthropic Skills: Anthropic 官方 Skills 仓库");
});

test("people searched by handle keep the handle", () => {
  assert.equal(brandedName("antfu/skills"), null);
  assert.equal(brandedName("mattpocock/skills"), "Matt Pocock Skills");
});
