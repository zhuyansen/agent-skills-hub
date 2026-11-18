/**
 * Cloudflare Worker reverse proxy for PostHog (anti-adblock + first-party telemetry).
 *
 * Routes:
 *   /static/*  -> https://us-assets.i.posthog.com/static/*
 *   /*         -> https://us.i.posthog.com/*
 *
 * Preserves client IP in X-Forwarded-For for accurate GeoIP country attribution
 * and strips cookies so no site/third-party cookies leak upstream.
 */

const ALLOWED_ORIGINS = new Set([
  "https://agentskillshub.top",
  "https://www.agentskillshub.top",
  "http://localhost:5173",
  "http://127.0.0.1:5173",
]);

function corsHeaders(request) {
  const origin = request.headers.get("Origin") || "";
  const allowOrigin = ALLOWED_ORIGINS.has(origin) ? origin : "https://agentskillshub.top";
  return {
    "Access-Control-Allow-Origin": allowOrigin,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  };
}

export default {
  async fetch(request, env, ctx) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(request) });
    }

    const apiHost = (env.POSTHOG_API_HOST || "us.i.posthog.com").trim();
    const assetHost = (env.POSTHOG_ASSET_HOST || "us-assets.i.posthog.com").trim();

    const url = new URL(request.url);
    const pathname = url.pathname;
    const isAsset = pathname.startsWith("/static/");
    const upstreamHost = isAsset ? assetHost : apiHost;

    // Static assets can be cached at the Cloudflare edge
    if (isAsset && request.method === "GET") {
      const cache = caches.default;
      const cacheKey = new Request(url.toString(), request);
      const cached = await cache.match(cacheKey);
      if (cached) return cached;

      const upstreamUrl = `https://${upstreamHost}${pathname}${url.search}`;
      const res = await fetch(upstreamUrl, { method: "GET" });
      const headers = new Headers(res.headers);
      headers.set("Access-Control-Allow-Origin", "*");
      const out = new Response(res.body, { status: res.status, headers });
      if (res.ok) ctx.waitUntil(cache.put(cacheKey, out.clone()));
      return out;
    }

    const upstreamUrl = `https://${upstreamHost}${pathname}${url.search}`;
    const headers = new Headers(request.headers);
    headers.delete("cookie");
    headers.delete("host");

    const clientIp = request.headers.get("CF-Connecting-IP");
    if (clientIp) {
      headers.set("X-Forwarded-For", clientIp);
    }

    const init = {
      method: request.method,
      headers,
    };
    if (request.method !== "GET" && request.method !== "HEAD") {
      init.body = request.body;
    }

    const upstreamRes = await fetch(upstreamUrl, init);
    const outHeaders = new Headers(upstreamRes.headers);
    for (const [k, v] of Object.entries(corsHeaders(request))) {
      outHeaders.set(k, v);
    }
    return new Response(upstreamRes.body, {
      status: upstreamRes.status,
      headers: outHeaders,
    });
  },
};
