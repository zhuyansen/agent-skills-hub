/**
 * Cloudflare Worker edge proxy for agentskillshub.top.
 *
 * Capabilities:
 *   1. RFC 8288 Link response headers on the homepage pointing to /llms.txt,
 *      /index.md, and /.well-known/mcp/server-card.json.
 *   2. Content negotiation for `Accept: text/markdown` on `/` (serves /index.md
 *      with `Content-Type: text/markdown; charset=utf-8` and `Vary: Accept`).
 *   3. Lightweight AI crawler & AI referral edge telemetry (inspired by
 *      yaojingang/GEOInflow, MIT) with official IPv4 CIDR verification logged
 *      to Cloudflare Workers Analytics Engine (`AI_CRAWL_AE`, dataset
 *      `ash_ai_crawl_log`) for core pages (skipping `/audit/*`, zero KV writes).
 *   4. A 301 from an audit page the build no longer writes to the repo's skill
 *      page, which carries the same grade (auditGoneRedirect, 2026-11).
 */

import { OFFICIAL_BOT_CIDRS } from "./bot-ranges.js";

const HOME_LINK_HEADER = [
  '</llms.txt>; rel="describedby"; type="text/plain"',
  '</index.md>; rel="alternate"; type="text/markdown"',
  '</.well-known/mcp/server-card.json>; rel="service-desc"; type="application/json"',
].join(", ");

const AI_CRAWLER_RULES = [
  { pattern: /OAI-SearchBot/i, bot: "OAI-SearchBot", provider: "OpenAI", purpose: "ai_search" },
  { pattern: /ChatGPT-User/i, bot: "ChatGPT-User", provider: "OpenAI", purpose: "user_triggered" },
  { pattern: /GPTBot/i, bot: "GPTBot", provider: "OpenAI", purpose: "training" },
  { pattern: /Perplexity-User/i, bot: "Perplexity-User", provider: "Perplexity", purpose: "user_triggered" },
  { pattern: /PerplexityBot/i, bot: "PerplexityBot", provider: "Perplexity", purpose: "ai_search" },
  { pattern: /Claude-SearchBot/i, bot: "Claude-SearchBot", provider: "Anthropic", purpose: "ai_search" },
  { pattern: /Claude-User/i, bot: "Claude-User", provider: "Anthropic", purpose: "user_triggered" },
  { pattern: /ClaudeBot|anthropic-ai/i, bot: "ClaudeBot", provider: "Anthropic", purpose: "training" },
  { pattern: /Google-Extended/i, bot: "Google-Extended", provider: "Google", purpose: "training" },
  { pattern: /Googlebot/i, bot: "Googlebot", provider: "Google", purpose: "search_engine" },
  { pattern: /Bingbot/i, bot: "Bingbot", provider: "Microsoft", purpose: "search_engine" },
  { pattern: /Applebot-Extended/i, bot: "Applebot-Extended", provider: "Apple", purpose: "training" },
  { pattern: /Bytespider/i, bot: "Bytespider", provider: "ByteDance", purpose: "training" },
  { pattern: /meta-externalagent/i, bot: "Meta-ExternalAgent", provider: "Meta", purpose: "ai_search" },
];

const AI_REFERRAL_HOSTS = [
  { pattern: /(^|\.)chatgpt\.com$|(^|\.)chat\.openai\.com$/i, engine: "chatgpt" },
  { pattern: /(^|\.)perplexity\.ai$/i, engine: "perplexity" },
  { pattern: /(^|\.)claude\.ai$/i, engine: "claude" },
  { pattern: /(^|\.)gemini\.google\.com$/i, engine: "gemini" },
  { pattern: /(^|\.)copilot\.microsoft\.com$/i, engine: "copilot" },
  { pattern: /(^|\.)chat\.deepseek\.com$/i, engine: "deepseek" },
  { pattern: /(^|\.)doubao\.com$/i, engine: "doubao" },
  { pattern: /(^|\.)kimi\.moonshot\.cn$|(^|\.)kimi\.ai$/i, engine: "kimi" },
  { pattern: /(^|\.)grok\.com$/i, engine: "grok" },
];

/** Parses Accept header quality values to decide whether the client wants Markdown. */
export function prefersMarkdown(acceptHeader) {
  if (!acceptHeader) return false;
  const parts = acceptHeader.split(",").map((part) => part.trim().toLowerCase());
  let mdQuality = -1;
  let htmlQuality = -1;
  for (const part of parts) {
    const [media, ...params] = part.split(";").map((s) => s.trim());
    const qParam = params.find((p) => p.startsWith("q="));
    const q = qParam ? Number.parseFloat(qParam.slice(2)) : 1;
    const quality = Number.isFinite(q) ? q : 1;
    if (media === "text/markdown") mdQuality = Math.max(mdQuality, quality);
    if (media === "text/html") htmlQuality = Math.max(htmlQuality, quality);
  }
  return mdQuality > 0 && mdQuality >= htmlQuality;
}

export function classifyAiCrawler(userAgent) {
  if (!userAgent) return null;
  for (const rule of AI_CRAWLER_RULES) {
    if (rule.pattern.test(userAgent)) {
      return { bot: rule.bot, provider: rule.provider, purpose: rule.purpose };
    }
  }
  return null;
}

export function classifyAiReferral(referer) {
  if (!referer) return null;
  try {
    const host = new URL(referer).hostname;
    for (const rule of AI_REFERRAL_HOSTS) {
      if (rule.pattern.test(host)) return { engine: rule.engine, host };
    }
  } catch {
    return null;
  }
  return null;
}

function ipv4ToInt(ip) {
  if (!ip || typeof ip !== "string") return null;
  const parts = ip.trim().split(".");
  if (parts.length !== 4) return null;
  let out = 0;
  for (const part of parts) {
    if (!/^\d{1,3}$/.test(part)) return null;
    const n = Number(part);
    if (n < 0 || n > 255) return null;
    out = (out << 8) | n;
  }
  return out >>> 0;
}

export function isIpv4InCidrs(ip, cidrs) {
  const ipInt = ipv4ToInt(ip);
  if (ipInt === null || !Array.isArray(cidrs) || cidrs.length === 0) return false;
  for (const cidr of cidrs) {
    const [net, bitsStr] = cidr.split("/");
    const netInt = ipv4ToInt(net);
    const bits = Number(bitsStr);
    if (netInt === null || !Number.isInteger(bits) || bits < 0 || bits > 32) continue;
    const mask = bits === 0 ? 0 : (0xffffffff << (32 - bits)) >>> 0;
    if ((ipInt & mask) === (netInt & mask)) return true;
  }
  return false;
}

export function verifyBotIp(botName, clientIp) {
  const entry = OFFICIAL_BOT_CIDRS[botName];
  if (!entry || !entry.prefixes || entry.prefixes.length === 0) return "no_cidr_list";
  if (!clientIp) return "unknown_ip";
  if (clientIp.includes(":")) return "ipv6_unchecked";
  return isIpv4InCidrs(clientIp, entry.prefixes) ? "verified" : "unverified_ip";
}

function normalizePath(pathname) {
  if (!pathname) return "/";
  const clean = pathname.length > 180 ? pathname.slice(0, 180) : pathname;
  return clean === "/index.html" ? "/" : clean;
}

/**
 * Only core GEO/Sitemap routes emit edge telemetry. `/audit/*` stays routed on
 * the Worker exclusively for `auditGoneRedirect` (301 -> /skill/*) and is
 * skipped here so bulk crawler sweeps of audit pages never flood telemetry.
 */
export function isTelemetryPath(pathname) {
  const path = normalizePath(pathname);
  if (path === "/audit" || path.startsWith("/audit/")) return false;
  return (
    path === "/" ||
    path === "/best" ||
    path.startsWith("/best/") ||
    path.startsWith("/how-we-grade") ||
    path.startsWith("/ai-info") ||
    path.startsWith("/llms") ||
    path.startsWith("/sitemap")
  );
}

/**
 * Writes a structured edge telemetry point to Cloudflare Workers Analytics Engine.
 * Schema (dataset: ash_ai_crawl_log):
 *   indexes[0]: "<kind>:<actor>" (sampling key)
 *   blob1: kind ("crawl" | "ref")
 *   blob2: actor (bot name or referral engine)
 *   blob3: normalized path
 *   blob4: provider (crawl) or referer host (ref)
 *   blob5: purpose (training | ai_search | user_triggered | search_engine | referral)
 *   blob6: ip_status (verified | unverified_ip | no_cidr_list | ipv6_unchecked | unknown_ip | "")
 *   blob7: content-type
 *   double1: HTTP status code
 *   double2: 1 (hit counter)
 */
export function writeTelemetryPoint(ae, point) {
  if (!ae || typeof ae.writeDataPoint !== "function") return false;
  try {
    ae.writeDataPoint({
      indexes: [`${point.kind}:${point.actor}`.slice(0, 96)],
      blobs: [
        point.kind,
        point.actor,
        point.path,
        point.providerOrHost || "",
        point.purpose || "",
        point.ipStatus || "",
        point.ct || "",
      ],
      doubles: [Number(point.status) || 0, 1],
    });
    return true;
  } catch {
    return false;
  }
}

function scheduleTelemetry(env, _ctx, request, url, response) {
  const ae = env && env.AI_CRAWL_AE;
  if (!ae) return;
  const path = normalizePath(url.pathname);
  if (!isTelemetryPath(path)) return;

  const ua = request.headers.get("User-Agent") || "";
  const referer = request.headers.get("Referer") || "";
  const clientIp = request.headers.get("CF-Connecting-IP") || "";
  const status = response.status;
  const ct = (response.headers.get("Content-Type") || "").split(";")[0].trim();

  const crawler = classifyAiCrawler(ua);
  if (crawler) {
    writeTelemetryPoint(ae, {
      kind: "crawl",
      actor: crawler.bot,
      path,
      providerOrHost: crawler.provider,
      purpose: crawler.purpose,
      ipStatus: verifyBotIp(crawler.bot, clientIp),
      ct,
      status,
    });
  }

  const ref = classifyAiReferral(referer);
  if (ref) {
    writeTelemetryPoint(ae, {
      kind: "ref",
      actor: ref.engine,
      path,
      providerOrHost: ref.host,
      purpose: "referral",
      ipStatus: "",
      ct,
      status,
    });
  }
}

function estimateTokens(markdown) {
  return String(Math.max(1, Math.ceil(markdown.length / 4)));
}

function isHomepagePath(pathname) {
  return pathname === "/" || pathname === "/index.html";
}

function appendVaryAccept(headers) {
  const existing = headers.get("Vary");
  if (!existing) {
    headers.set("Vary", "Accept");
    return;
  }
  if (!existing.toLowerCase().includes("accept")) {
    headers.set("Vary", `${existing}, Accept`);
  }
}

async function serveMarkdownHome(request, url) {
  const mdUrl = new URL("/index.md", url.origin);
  const mdResp = await fetch(mdUrl.toString(), {
    method: request.method,
    headers: { "User-Agent": request.headers.get("User-Agent") || "agentskillshub-edge" },
  });
  if (!mdResp.ok) return null;
  const body = request.method === "HEAD" ? null : await mdResp.text();
  const headers = new Headers(mdResp.headers);
  headers.set("Content-Type", "text/markdown; charset=utf-8");
  headers.set("Link", HOME_LINK_HEADER);
  appendVaryAccept(headers);
  if (body !== null) headers.set("x-markdown-tokens", estimateTokens(body));
  return new Response(body, { status: mdResp.status, headers });
}

/** /skill/<owner>/<repo>/ for an /audit/<owner>/<repo>/ path, else null. */
export function auditFallbackPath(pathname) {
  const m = /^\/audit\/([^/]+)\/([^/]+)\/?$/.exec(pathname);
  return m ? `/skill/${m[1]}/${m[2]}/` : null;
}

/**
 * GitHub Pages answers 404 for an audit page the build stopped writing: since 2026-07-28 a repo
 * needs 500+ stars or a flagged grade to keep one, and grades move with every scan. Bingbot keeps
 * asking for those URLs: in the edge KV log for 11-22 to 11-25, 86 of its 293 audit fetches were
 * 404s, and 85 of those 86 repos still had a live skill page. Send a 301 to that
 * skill page, which shows the same grade, when it exists; otherwise the 404 stands.
 */
export async function auditGoneRedirect(url, originResponse) {
  if (originResponse.status !== 404) return null;
  const target = auditFallbackPath(url.pathname);
  if (!target) return null;
  const targetUrl = new URL(target, url.origin).toString();
  const probe = await fetch(targetUrl, { method: "HEAD", redirect: "manual" });
  return probe.status === 200 ? Response.redirect(targetUrl, 301) : null;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const isRead = request.method === "GET" || request.method === "HEAD";
    if (isRead && isHomepagePath(url.pathname) && prefersMarkdown(request.headers.get("Accept"))) {
      const mdResponse = await serveMarkdownHome(request, url);
      if (mdResponse) {
        scheduleTelemetry(env, ctx, request, url, mdResponse);
        return mdResponse;
      }
    }

    const originResponse = await fetch(request);
    if (!isHomepagePath(url.pathname)) {
      const moved = isRead ? await auditGoneRedirect(url, originResponse) : null;
      const response = moved || originResponse;
      scheduleTelemetry(env, ctx, request, url, response);
      return response;
    }

    const headers = new Headers(originResponse.headers);
    headers.set("Link", HOME_LINK_HEADER);
    appendVaryAccept(headers);
    const finalResp = new Response(originResponse.body, {
      status: originResponse.status,
      statusText: originResponse.statusText,
      headers,
    });
    scheduleTelemetry(env, ctx, request, url, finalResp);
    return finalResp;
  },
};
