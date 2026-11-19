import test from "node:test";
import assert from "node:assert/strict";
import { stampHomeCanonical, buildHomeMarkdown } from "./home-markdown.mjs";

test("stampHomeCanonical adds homepage canonical once before </head>", () => {
  const input = "<!doctype html><html><head><title>Home</title>\n  </head><body></body></html>";
  const once = stampHomeCanonical(input);
  assert.match(once, /<link rel="canonical" href="https:\/\/agentskillshub\.top\/" \/>/);
  assert.equal(stampHomeCanonical(once), once);
});

test("buildHomeMarkdown includes counts, MCP card, and legal links", () => {
  const md = buildHomeMarkdown({
    site: "https://agentskillshub.top",
    counts: { total: "270,000+", graded: "135,000+", gradedOver100: "99%", gradedOver1000: "99%" },
    indexCount: 51825,
    generatedDate: "2026-11-19",
  });
  assert.match(md, /^# Agent Skills Hub/m);
  assert.match(md, /270,000\+/);
  assert.match(md, /\/\.well-known\/mcp\/server-card\.json/);
  assert.match(md, /\/contact\//);
  assert.match(md, /\/terms\//);
});
