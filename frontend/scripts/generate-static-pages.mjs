/**
 * Copy dist/index.html into subdirectories for SPA routes that need
 * direct-access 200 status (instead of the 404.html SPA redirect).
 *
 * This gives us clean URLs, correct HTTP status codes, and proper SEO
 * without needing full pre-rendering.
 */

import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { join } from "path";

const DIST = "dist";
const STATIC_ROUTES = [
  {
    path: "verified-creator",
    title:
      "Verified Creator Program — AgentSkillsHub",
    description:
      "AgentSkillsHub Verified Creator program. For serious Skill authors who commercialize via consulting, subscriptions, or community. Authenticated badge, trending boost, creator analytics, leads channel.",
  },
  {
    path: "business",
    title: "For Business — AgentSkillsHub Enterprise Skill Directory",
    description:
      "Enterprise-grade AI Agent Skill directory with security audits, SBOM export, license compliance, and on-prem mirroring. Trusted source for Fortune 500 legal + security teams.",
  },
];

const indexHtml = readFileSync(join(DIST, "index.html"), "utf-8");

for (const route of STATIC_ROUTES) {
  // Customize title + description per route for better SEO
  let html = indexHtml
    .replace(
      /<title>[^<]+<\/title>/,
      `<title>${route.title}</title>`,
    )
    .replace(
      /<meta name="description" content="[^"]+"/,
      `<meta name="description" content="${route.description}"`,
    )
    .replace(
      /<link rel="canonical" href="[^"]+"/,
      `<link rel="canonical" href="https://agentskillshub.top/${route.path}/"`,
    );

  const outDir = join(DIST, route.path);
  mkdirSync(outDir, { recursive: true });
  writeFileSync(join(outDir, "index.html"), html);
  console.log(`  ✓ /${route.path}/index.html`);
}

console.log(`Static routes: ${STATIC_ROUTES.length} HTML files generated`);
