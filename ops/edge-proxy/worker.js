/**
 * Cloudflare Worker edge proxy for agentskillshub.top.
 *
 * Adds two agent-readiness capabilities that GitHub Pages cannot provide directly:
 *   1. RFC 8288 Link response headers on the homepage pointing to /llms.txt,
 *      /index.md, and /.well-known/mcp/server-card.json.
 *   2. Content negotiation for `Accept: text/markdown` on `/` (serves /index.md
 *      with `Content-Type: text/markdown; charset=utf-8` and `Vary: Accept`).
 */

const HOME_LINK_HEADER = [
  '</llms.txt>; rel="describedby"; type="text/plain"',
  '</index.md>; rel="alternate"; type="text/markdown"',
  '</.well-known/mcp/server-card.json>; rel="service-desc"; type="application/json"',
].join(", ");

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

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const isRead = request.method === "GET" || request.method === "HEAD";
    if (isRead && isHomepagePath(url.pathname) && prefersMarkdown(request.headers.get("Accept"))) {
      const mdResponse = await serveMarkdownHome(request, url);
      if (mdResponse) return mdResponse;
    }

    const originResponse = await fetch(request);
    if (!isHomepagePath(url.pathname)) return originResponse;

    const headers = new Headers(originResponse.headers);
    headers.set("Link", HOME_LINK_HEADER);
    appendVaryAccept(headers);
    return new Response(originResponse.body, {
      status: originResponse.status,
      statusText: originResponse.statusText,
      headers,
    });
  },
};
