import test from "node:test";
import assert from "node:assert/strict";
import worker, {
  prefersMarkdown,
  classifyAiCrawler,
  classifyAiReferral,
  isIpv4InCidrs,
  verifyBotIp,
  logEdgeSignal,
  auditFallbackPath,
} from "./worker.js";

test("prefersMarkdown respects Accept quality values", () => {
  assert.equal(prefersMarkdown("text/markdown"), true);
  assert.equal(prefersMarkdown("text/markdown, text/html;q=0.9"), true);
  assert.equal(prefersMarkdown("text/html, text/markdown;q=0.5"), false);
  assert.equal(prefersMarkdown("text/html,application/xhtml+xml,*/*;q=0.8"), false);
  assert.equal(prefersMarkdown(null), false);
});

test("classifyAiCrawler distinguishes training, ai_search, and user_triggered bots", () => {
  assert.deepEqual(classifyAiCrawler("GPTBot/1.0 (+https://openai.com/gptbot)"), {
    bot: "GPTBot",
    provider: "OpenAI",
    purpose: "training",
  });
  assert.deepEqual(classifyAiCrawler("Mozilla/5.0 OAI-SearchBot/1.0"), {
    bot: "OAI-SearchBot",
    provider: "OpenAI",
    purpose: "ai_search",
  });
  assert.deepEqual(classifyAiCrawler("ChatGPT-User/1.0"), {
    bot: "ChatGPT-User",
    provider: "OpenAI",
    purpose: "user_triggered",
  });
  assert.deepEqual(classifyAiCrawler("PerplexityBot/1.0"), {
    bot: "PerplexityBot",
    provider: "Perplexity",
    purpose: "ai_search",
  });
  assert.deepEqual(classifyAiCrawler("Claude-SearchBot/1.0"), {
    bot: "Claude-SearchBot",
    provider: "Anthropic",
    purpose: "ai_search",
  });
  assert.equal(classifyAiCrawler("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"), null);
});

test("classifyAiReferral detects major AI engines", () => {
  assert.deepEqual(classifyAiReferral("https://chatgpt.com/c/123"), {
    engine: "chatgpt",
    host: "chatgpt.com",
  });
  assert.deepEqual(classifyAiReferral("https://www.perplexity.ai/search?q=skills"), {
    engine: "perplexity",
    host: "www.perplexity.ai",
  });
  assert.equal(classifyAiReferral("https://google.com/search?q=test"), null);
});

test("isIpv4InCidrs and verifyBotIp validate official CIDR prefixes accurately", () => {
  assert.equal(isIpv4InCidrs("132.196.86.42", ["132.196.86.0/24"]), true);
  assert.equal(isIpv4InCidrs("132.196.87.1", ["132.196.86.0/24"]), false);
  assert.equal(verifyBotIp("GPTBot", "132.196.86.42"), "verified");
  assert.equal(verifyBotIp("GPTBot", "1.2.3.4"), "unverified_ip");
  assert.equal(verifyBotIp("ClaudeBot", "1.2.3.4"), "no_cidr_list");
});

test("logEdgeSignal deduplicates KV writes per key", async () => {
  const store = new Map();
  let puts = 0;
  const kv = {
    async get(k) { return store.has(k) ? store.get(k) : null; },
    async put(k, v) { puts += 1; store.set(k, v); },
  };
  const sig = { key: "crawl|2026-11-21|GPTBot|/best/code-review/", payload: { bot: "GPTBot" } };
  assert.equal(await logEdgeSignal(kv, sig), true);
  assert.equal(await logEdgeSignal(kv, sig), false);
  assert.equal(puts, 1);
});

test("fetch serves Link header and logs AI bot via waitUntil", async () => {
  const origFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response("<html>ok</html>", {
    status: 200,
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
  const store = new Map();
  const kv = {
    async get(k) { return store.has(k) ? store.get(k) : null; },
    async put(k, v) { store.set(k, v); },
  };
  const pending = [];
  const ctx = { waitUntil(p) { pending.push(p); } };
  try {
    const req = new Request("https://agentskillshub.top/", {
      headers: {
        Accept: "text/html",
        "User-Agent": "GPTBot/1.0 (+https://openai.com/gptbot)",
        "CF-Connecting-IP": "132.196.86.10",
      },
    });
    const resp = await worker.fetch(req, { AI_CRAWL_KV: kv }, ctx);
    await Promise.all(pending);
    assert.equal(resp.status, 200);
    assert.match(resp.headers.get("Link") || "", /llms\.txt/);
    assert.equal(store.size, 1);
    const saved = JSON.parse([...store.values()][0]);
    assert.equal(saved.bot, "GPTBot");
    assert.equal(saved.ip_status, "verified");
  } finally {
    globalThis.fetch = origFetch;
  }
});

test("an audit path maps to the same repo's skill page", () => {
  assert.equal(auditFallbackPath("/audit/bitwarden/mcp-server/"), "/skill/bitwarden/mcp-server/");
  assert.equal(auditFallbackPath("/audit/bitwarden/mcp-server"), "/skill/bitwarden/mcp-server/");
  assert.equal(auditFallbackPath("/audit/"), null);
  assert.equal(auditFallbackPath("/audit/a/b/c/"), null);
  assert.equal(auditFallbackPath("/best/code-review/"), null);
});

test("Bingbot is checked against Bing's published ranges", () => {
  assert.equal(verifyBotIp("Bingbot", "157.55.39.10"), "verified");
  assert.equal(verifyBotIp("Bingbot", "1.2.3.4"), "unverified_ip");
});

/** worker.fetch against a fake origin: `pages` maps a path to its status. */
async function fetchThrough(path, pages, method = "GET") {
  const origFetch = globalThis.fetch;
  const asked = [];
  globalThis.fetch = async (input, init = {}) => {
    const u = new URL(typeof input === "string" ? input : input.url);
    asked.push(`${init.method || (typeof input === "string" ? "GET" : input.method)} ${u.pathname}`);
    return new Response("x", { status: pages[u.pathname] ?? 404 });
  };
  try {
    const req = new Request(`https://agentskillshub.top${path}`, { method, headers: { "User-Agent": "Mozilla/5.0 (compatible; bingbot/2.0)" } });
    return { resp: await worker.fetch(req, {}, { waitUntil() {} }), asked };
  } finally {
    globalThis.fetch = origFetch;
  }
}

test("a gone audit page with a skill page answers 301 to it", async () => {
  const { resp, asked } = await fetchThrough("/audit/bitwarden/mcp-server/", { "/skill/bitwarden/mcp-server/": 200 });
  assert.equal(resp.status, 301);
  assert.equal(resp.headers.get("Location"), "https://agentskillshub.top/skill/bitwarden/mcp-server/");
  assert.deepEqual(asked, ["GET /audit/bitwarden/mcp-server/", "HEAD /skill/bitwarden/mcp-server/"]);
});

test("a gone audit page without a skill page stays 404; live pages and other routes pass through", async () => {
  assert.equal((await fetchThrough("/audit/gone/repo/", {})).resp.status, 404);
  const live = await fetchThrough("/audit/joone/loz/", { "/audit/joone/loz/": 200, "/skill/joone/loz/": 200 });
  assert.equal(live.resp.status, 200);
  assert.deepEqual(live.asked, ["GET /audit/joone/loz/"]);
  const best = await fetchThrough("/best/retired-page/", { "/skill/best/retired-page/": 200 });
  assert.equal(best.resp.status, 404);
  assert.deepEqual(best.asked, ["GET /best/retired-page/"]);
  assert.equal((await fetchThrough("/audit/x/y/", { "/skill/x/y/": 200 }, "POST")).resp.status, 404);
});
