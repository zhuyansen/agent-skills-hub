import test from "node:test";
import assert from "node:assert/strict";
import { zhTwin } from "./scenario-zh-page.mjs";

// The head of a built English /best/ page, cut down to the tags a twin rewrites.
const EN = `<html lang="en"><head>
<title>PPT Skills for Codex &amp; Claude Code: 259 Graded (2026)</title>
<meta name="description" content="259 ppt skills, independently security-graded." />
<meta property="og:title" content="PPT Skills for Codex &amp; Claude Code: 259 Graded (2026)" />
<meta property="og:description" content="259 ppt skills, independently security-graded." />
<meta property="og:url" content="https://agentskillshub.top/best/ppt-presentation/" />
<meta name="twitter:title" content="PPT Skills for Codex &amp; Claude Code: 259 Graded (2026)" />
<meta name="twitter:description" content="259 ppt skills, independently security-graded." />
<link rel="canonical" href="https://agentskillshub.top/best/ppt-presentation/" />
</head><body><h1 data-zh="最佳 PPT Skills">Best PPT Skills</h1><a href="/best/code-review/">x</a></body></html>`;

const twin = () =>
  zhTwin(EN, {
    enPath: "/best/ppt-presentation/",
    title: "最佳 Codex 与 Claude Code PPT Skills (2026)",
    description: "259 个 PPT Skill，逐个做了安全评级。",
    twinPaths: new Set(["/best/code-review/"]),
  });

const attr = (html, selector) => html.match(new RegExp(`<meta ${selector} content="([^"]*)"`))?.[1];

test("a twin's title, description and address are its own", () => {
  const html = twin();
  assert.match(html, /<html lang="zh-CN">/);
  assert.match(html, /<title>最佳 Codex 与 Claude Code PPT Skills \(2026\)<\/title>/);
  assert.equal(attr(html, 'name="description"'), "259 个 PPT Skill，逐个做了安全评级。");
  assert.equal(attr(html, 'property="og:url"'), "https://agentskillshub.top/best/ppt-presentation/zh/");
});

// X reads twitter:title and twitter:description before the og tags. Until 2026-11-20 a twin
// kept the English page's, so a Chinese page shared on X showed an English card.
test("a twin's card on X is in Chinese too", () => {
  const html = twin();
  assert.equal(attr(html, 'name="twitter:title"'), "最佳 Codex 与 Claude Code PPT Skills (2026)");
  assert.equal(attr(html, 'name="twitter:description"'), "259 个 PPT Skill，逐个做了安全评级。");
  assert.equal(attr(html, 'property="og:title"'), attr(html, 'name="twitter:title"'));
});

test("a link to a page that has a twin goes to the twin", () => {
  assert.match(twin(), /href="\/best\/code-review\/zh\/"/);
});
