import test from "node:test";
import assert from "node:assert/strict";
import worker, { prefersMarkdown } from "./worker.js";

test("prefersMarkdown respects Accept quality weights", () => {
  assert.equal(prefersMarkdown("text/markdown"), true);
  assert.equal(prefersMarkdown("text/markdown, text/html;q=0.9"), true);
  assert.equal(prefersMarkdown("text/html, text/markdown;q=0.5"), false);
  assert.equal(prefersMarkdown("text/html,application/xhtml+xml,*/*;q=0.8"), false);
  assert.equal(prefersMarkdown(null), false);
});

test("worker serves Markdown for Accept: text/markdown and Link header for HTML", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (input) => {
    const url = typeof input === "string" ? input : input.url;
    if (url.endsWith("/index.md")) {
      return new Response("# Agent Skills Hub\n", {
        status: 200,
        headers: { "Content-Type": "text/plain" },
      });
    }
    return new Response("<html><body>Home</body></html>", {
      status: 200,
      headers: { "Content-Type": "text/html; charset=utf-8" },
    });
  };
  try {
    const mdRes = await worker.fetch(
      new Request("https://agentskillshub.top/", { headers: { Accept: "text/markdown" } }),
    );
    assert.equal(mdRes.headers.get("Content-Type"), "text/markdown; charset=utf-8");
    assert.match(mdRes.headers.get("Link") || "", /<\/llms\.txt>; rel="describedby"/);
    assert.match(mdRes.headers.get("Vary") || "", /Accept/);
    assert.equal(await mdRes.text(), "# Agent Skills Hub\n");

    const htmlRes = await worker.fetch(
      new Request("https://agentskillshub.top/", { headers: { Accept: "text/html" } }),
    );
    assert.equal(htmlRes.headers.get("Content-Type"), "text/html; charset=utf-8");
    assert.match(htmlRes.headers.get("Link") || "", /<\/index\.md>; rel="alternate"/);
    assert.match(htmlRes.headers.get("Vary") || "", /Accept/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
