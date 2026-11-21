import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { shellHead } from "./shell-meta.mjs";

// The head of dist/index.html, cut down to the tags a shell rewrites.
const HOME = `<html><head>
<title>AgentSkillsHub — Claude Skills Marketplace, Security-Graded</title>
<meta name="description" content="Agent Skills Hub, the Claude skills marketplace." />
<meta property="og:title" content="AgentSkillsHub — Claude Skills Marketplace, Security-Graded" />
<meta property="og:description" content="Agent Skills Hub: a security-graded Claude skills marketplace." />
<meta property="og:type" content="website" />
<meta property="og:url" content="https://agentskillshub.top/" />
<meta property="og:site_name" content="AgentSkillsHub" />
<meta property="og:image" content="https://agentskillshub.top/og-image.png" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="AgentSkillsHub — Claude Skills Marketplace, Security-Graded" />
<meta name="twitter:description" content="Agent Skills Hub: a security-graded Claude skills marketplace." />
<link rel="alternate" type="text/markdown" href="https://agentskillshub.top/index.md" title="AgentSkillsHub (Markdown)" />
<link rel="describedby" type="text/plain" href="https://agentskillshub.top/llms.txt" title="LLMs.txt" />
<link rel="canonical" href="__CANONICAL__" />
</head><body></body></html>`;

const ANALYZER = {
  path: "analyzer",
  title: "Is This AI Skill or MCP Server Safe? Free Security Check",
  description: "Paste any GitHub repo URL for an instant security analysis.",
};

const attr = (html, selector) => html.match(new RegExp(`<meta ${selector} content="([^"]*)"`))?.[1];

test("a shell keeps its own title, description and canonical", () => {
  const html = shellHead(HOME, ANALYZER);
  assert.match(html, /<title>Is This AI Skill or MCP Server Safe\? Free Security Check<\/title>/);
  assert.equal(attr(html, 'name="description"'), ANALYZER.description);
  assert.match(html, /<link rel="canonical" href="https:\/\/agentskillshub\.top\/analyzer\/"/);
});

// A link preview is built from these tags without running JavaScript. Until 2026-11-20 every
// shell kept the home page's, so /analyzer/ and /enterprise/ unfurled as the home page.
test("a shell's share card names the shell, not the home page", () => {
  const html = shellHead(HOME, ANALYZER);
  assert.equal(attr(html, 'property="og:url"'), "https://agentskillshub.top/analyzer/");
  assert.equal(attr(html, 'property="og:title"'), ANALYZER.title);
  assert.equal(attr(html, 'name="twitter:title"'), ANALYZER.title);
  assert.equal(attr(html, 'property="og:description"'), ANALYZER.description);
  assert.equal(attr(html, 'name="twitter:description"'), ANALYZER.description);
});

test("the site name, card type and image stay the site's", () => {
  const html = shellHead(HOME, ANALYZER);
  assert.equal(attr(html, 'property="og:site_name"'), "AgentSkillsHub");
  assert.equal(attr(html, 'property="og:image"'), "https://agentskillshub.top/og-image.png");
  assert.equal(attr(html, 'name="twitter:card"'), "summary_large_image");
});

test("a nested path gets its own address", () => {
  const html = shellHead(HOME, { path: "verified-creator/apply", title: "Apply", description: "Apply for the badge." });
  assert.equal(attr(html, 'property="og:url"'), "https://agentskillshub.top/verified-creator/apply/");
});

test("share-card text is escaped for an attribute", () => {
  const html = shellHead(HOME, { path: "ci-gate", title: 'Skills & "MCP" Configs', description: "A <b> & more" });
  assert.equal(attr(html, 'property="og:title"'), "Skills &amp; &quot;MCP&quot; Configs");
  assert.equal(attr(html, 'property="og:description"'), "A &lt;b&gt; &amp; more");
});

test("a dollar sign in the copy is written as it is, in every tag", () => {
  const html = shellHead(HOME, { path: "pro", title: "Pro for $9 $&", description: "Costs $1 a day, $& all." });
  assert.match(html, /<title>Pro for \$9 \$&<\/title>/);
  assert.equal(attr(html, 'name="description"'), "Costs $1 a day, $& all.");
  assert.equal(attr(html, 'property="og:title"'), "Pro for $9 $&amp;");
  assert.equal(attr(html, 'property="og:description"'), "Costs $1 a day, $&amp; all.");
});

test("a shell does not offer the home page's Markdown twin as its own", () => {
  const html = shellHead(HOME, ANALYZER);
  assert.doesNotMatch(html, /text\/markdown/);
  assert.match(html, /rel="describedby"/);
});

// The fixture above is written by hand. This one is the real file: if index.html loses or
// rewrites one of these tags, a shell would quietly go back to the home page's card.
test("every tag a shell rewrites is in the real index.html", () => {
  const index = readFileSync(new URL("../index.html", import.meta.url), "utf-8")
    .replace("</head>", '<link rel="canonical" href="__CANONICAL__" />\n</head>');
  const html = shellHead(index, ANALYZER);
  assert.match(html, /<title>Is This AI Skill or MCP Server Safe\? Free Security Check<\/title>/);
  assert.equal(attr(html, 'name="description"'), ANALYZER.description);
  assert.match(html, /<link rel="canonical" href="https:\/\/agentskillshub\.top\/analyzer\/"/);
  for (const selector of ['property="og:title"', 'name="twitter:title"']) assert.equal(attr(html, selector), ANALYZER.title);
  for (const selector of ['property="og:description"', 'name="twitter:description"']) assert.equal(attr(html, selector), ANALYZER.description);
  assert.equal(attr(html, 'property="og:url"'), "https://agentskillshub.top/analyzer/");
  assert.doesNotMatch(html, /text\/markdown/);
});

test("a member page is marked noindex in the raw HTML", () => {
  assert.match(shellHead(HOME, { ...ANALYZER, noindex: true }), /<meta name="robots" content="noindex" \/>\n<\/head>/);
  assert.doesNotMatch(shellHead(HOME, ANALYZER), /name="robots"/);
});
