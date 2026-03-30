/**
 * Generate static SVG badges for all skills.
 * Output: dist/badge/{owner}/{repo}.svg
 * Usage in README: [![Listed on Agent Skills Hub](https://agentskillshub.top/badge/{owner}/{repo}.svg)](https://agentskillshub.top/skill/{owner}/{repo}/)
 */

import { mkdirSync, writeFileSync } from "fs";
import { dirname } from "path";
import { SUPABASE_URL, SUPABASE_ANON_KEY, fetchAllSkills } from "./shared-utils.mjs";

const DIST = "dist";

function starsLabel(stars) {
  if (stars >= 1000) return `${(stars / 1000).toFixed(1)}k`;
  return `${stars}`;
}

function makeBadgeSvg(repoName, stars, category) {
  const label = "Agent Skills Hub";
  const starsText = `★ ${starsLabel(stars)}`;

  // Calculate widths (approximate: 6.5px per char)
  const labelWidth = Math.max(label.length * 6.5 + 16, 110);
  const starsWidth = Math.max(starsText.length * 7 + 16, 52);
  const totalWidth = labelWidth + starsWidth;

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${totalWidth}" height="20" role="img" aria-label="${label}: ${starsText}">
  <title>${label}: ${starsText}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="${totalWidth}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="${labelWidth}" height="20" fill="#4f46e5"/>
    <rect x="${labelWidth}" width="${starsWidth}" height="20" fill="#ea580c"/>
    <rect width="${totalWidth}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text aria-hidden="true" x="${labelWidth / 2}" y="15" fill="#010101" fill-opacity=".3">${label}</text>
    <text x="${labelWidth / 2}" y="14">${label}</text>
    <text aria-hidden="true" x="${labelWidth + starsWidth / 2}" y="15" fill="#010101" fill-opacity=".3">${starsText}</text>
    <text x="${labelWidth + starsWidth / 2}" y="14">${starsText}</text>
  </g>
</svg>`;
}

async function main() {
  console.log("🏷️  Generating badges...");

  const skills = await fetchAllSkills();
  console.log(`   Loaded ${skills.length} skills`);

  let count = 0;
  for (const skill of skills) {
    const fullName = skill.repo_full_name;
    if (!fullName || !fullName.includes("/")) continue;

    const svg = makeBadgeSvg(skill.repo_name, skill.stars || 0, skill.category || "");
    const outPath = `${DIST}/badge/${fullName}.svg`;

    mkdirSync(dirname(outPath), { recursive: true });
    writeFileSync(outPath, svg, "utf-8");
    count++;
  }

  console.log(`   ✅ Generated ${count} badges → dist/badge/`);
}

main().catch((e) => {
  console.error("Badge generation failed:", e);
  process.exit(1);
});
