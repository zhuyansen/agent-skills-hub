/**
 * scripts/llms-full.mjs: chrome stripping, HTML→text and file assembly, on synthetic pages
 * of both shapes (prose <main> and scenario no-<main>). No files.
 *
 * Run: node --test scripts/llms-full.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { contentHtml, htmlToText, buildLlmsFull } from "./llms-full.mjs";

const chrome = `<header id="site-header" class="bp-header"><a href="/">Agent Skills Hub</a></header>
<nav class="bp-nav-links"><a href="/best/">Best Tools</a></nav>`;
const footer = `<footer style="margin-top:48px">© 2026 Agent Skills Hub</footer>`;

test("contentHtml keeps prose <main> and drops scripts, styles, site header, nav, footer", () => {
  const html = `<html><head><style>.x{color:red}</style><script>var a=1;</script></head>
<body>${chrome}<div id="root"><div class="page"><main class="m">
<header class="ph"><h1>How we grade</h1></header><article><p>The 43 rules.</p></article>
</main></div></div>${footer}</body></html>`;
  const c = contentHtml(html);
  assert.match(c, /<h1>How we grade<\/h1>/);
  assert.match(c, /The 43 rules\./);
  assert.doesNotMatch(c, /site-header|bp-nav-links|© 2026|var a=1|color:red/);
});

test("contentHtml falls back to body for scenario pages without <main>", () => {
  const html = `<body>${chrome}<nav class="bp-breadcrumb">Home &gt; Best</nav>
<div id="root"><h1>Best Code Review Skills</h1><p>183 graded.</p></div>${footer}</body>`;
  const c = contentHtml(html);
  assert.match(c, /Best Code Review Skills/);
  assert.match(c, /183 graded\./);
  assert.doesNotMatch(c, /bp-breadcrumb|© 2026|Best Tools<\/a>/);
});

test("htmlToText keeps heading levels, dashes lists and pipe-joins table rows", () => {
  const html = `<body><main><h1>Title</h1><h2>Section</h2><h3>Sub</h3>
<ul><li>first</li><li>second</li></ul>
<table><thead><tr><th>Tool</th><th>Grade</th></tr></thead>
<tbody><tr><td>alpha</td><td>Safe</td></tr><tr><td>beta</td><td>Caution</td></tr></tbody></table>
<p>He said &quot;ok&quot; &amp; left.</p></main></body>`;
  const t = htmlToText(html);
  assert.match(t, /^# Title$/m);
  assert.match(t, /^## Section$/m);
  assert.match(t, /^### Sub$/m);
  assert.match(t, /^- first$/m);
  assert.match(t, /^Tool \| Grade$/m);
  assert.match(t, /^alpha \| Safe$/m);
  assert.match(t, /He said "ok" & left\./);
  assert.doesNotMatch(t, /<[^>]+>/);
});

test("htmlToText collapses blank lines and trims trailing pipe artifacts", () => {
  const t = htmlToText(`<body><main><p>a</p><div></div><div></div><p>b</p><table><tr><td>x</td><td></td></tr></table></main></body>`);
  assert.equal(t, "a\n\nb\n\nx");
});

test("htmlToText does not leak data-en/data-zh attributes whose values are raw HTML with '>'", () => {
  const html = `<body><section><h2 data-en="Who runs this" data-zh="谁在运营">Who runs this</h2>
<p data-en="<strong>Hub</strong> is built by <a href='https://x.com/GoSailGlobal'>Jason</a>." data-zh="<strong>Hub</strong> 由 <a href='https://x.com/GoSailGlobal'>Jason</a> 构建。"><strong>Hub</strong> is built by <a href="https://x.com/GoSailGlobal">Jason</a>.</p></section></body>`;
  const t = htmlToText(html);
  assert.equal(t, "## Who runs this\n\nHub is built by Jason.");
  assert.doesNotMatch(t, /data-zh|data-en|href|<strong>|构建/);
});

test("buildLlmsFull assembles header, per-page URL lines and skips empty pages", () => {
  const out = buildLlmsFull("https://x.test", [
    { path: "/best/a/", title: "Guide A", text: "Full text A." },
    { path: "/best/empty/", title: "Empty", text: "  " },
    { path: "/about/", title: "About", text: "Full text B." },
  ]);
  assert.match(out, /^# Agent Skills Hub — full text for AI agents/);
  assert.match(out, /Companion to https:\/\/x\.test\/llms\.txt/);
  assert.match(out, /# Guide A\n\nURL: https:\/\/x\.test\/best\/a\/\n\nFull text A\.\n\n---/);
  assert.match(out, /# About\n\nURL: https:\/\/x\.test\/about\//);
  assert.doesNotMatch(out, /Empty/);
});
