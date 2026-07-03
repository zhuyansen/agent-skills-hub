/**
 * Generate static SVG security-grade badges for all skills.
 * Output: dist/badge/{owner}/{repo}.svg
 * Usage in README: [![Security-graded by Agent Skills Hub](https://agentskillshub.top/badge/{owner}/{repo}.svg)](https://agentskillshub.top/skill/{owner}/{repo}/)
 *
 * The right segment shows the skill's security grade (SAFE / CAUTION / UNSAFE /
 * REJECT / UNAUDITED), color-coded — a trust signal the author can embed, and a
 * distributed backlink for every repo that adopts it.
 */

import { mkdirSync, writeFileSync } from "fs";
import { dirname } from "path";
import { SUPABASE_URL, SUPABASE_ANON_KEY, fetchAllSkills } from "./shared-utils.mjs";

const DIST = "dist";

// security_grade → badge label + color. Unknown/missing → UNAUDITED (honest gray).
const GRADE_STYLE = {
  safe: { text: "SAFE", color: "#16a34a" },
  caution: { text: "CAUTION", color: "#ca8a04" },
  unsafe: { text: "UNSAFE", color: "#dc2626" },
  reject: { text: "REJECT", color: "#991b1b" },
};
function gradeStyle(grade) {
  return GRADE_STYLE[grade] || { text: "UNAUDITED", color: "#6b7280" };
}

function makeBadgeSvg(grade) {
  const label = "Agent Skills Hub";
  const g = gradeStyle(grade);

  // Approximate text widths (6.5px/char left, 7px/char right).
  const labelWidth = Math.max(label.length * 6.5 + 16, 118);
  const gradeWidth = Math.max(g.text.length * 7 + 18, 60);
  const totalWidth = labelWidth + gradeWidth;

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${totalWidth}" height="20" role="img" aria-label="Agent Skills Hub security grade: ${g.text}">
  <title>Agent Skills Hub security grade: ${g.text}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="${totalWidth}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="${labelWidth}" height="20" fill="#4f46e5"/>
    <rect x="${labelWidth}" width="${gradeWidth}" height="20" fill="${g.color}"/>
    <rect width="${totalWidth}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text aria-hidden="true" x="${labelWidth / 2}" y="15" fill="#010101" fill-opacity=".3">${label}</text>
    <text x="${labelWidth / 2}" y="14">${label}</text>
    <text aria-hidden="true" x="${labelWidth + gradeWidth / 2}" y="15" fill="#010101" fill-opacity=".3">${g.text}</text>
    <text x="${labelWidth + gradeWidth / 2}" y="14">${g.text}</text>
  </g>
</svg>`;
}

async function main() {
  console.log("🏷️  Generating badges...");

  const skills = await fetchAllSkills();
  console.log(`   Loaded ${skills.length} skills`);

  // Badges only for the quality catalog (stars >= 5, same cut as the CLI
  // search index). Unfiltered this wrote 127K SVG files — the single biggest
  // dist bloat, and file COUNT is what makes the Pages artifact upload slow.
  // <5★ repos have no audience to embed a badge; BadgeEmbed gates its UI on
  // the same threshold so nobody gets handed a 404 snippet.
  const MIN_STARS_FOR_BADGE = 5;

  let count = 0;
  let skippedLowStars = 0;
  for (const skill of skills) {
    const fullName = skill.repo_full_name;
    if (!fullName || !fullName.includes("/")) continue;
    if ((skill.stars || 0) < MIN_STARS_FOR_BADGE) {
      skippedLowStars++;
      continue;
    }

    const svg = makeBadgeSvg(skill.security_grade);
    const outPath = `${DIST}/badge/${fullName}.svg`;

    mkdirSync(dirname(outPath), { recursive: true });
    writeFileSync(outPath, svg, "utf-8");
    count++;
  }

  console.log(`   ✅ Generated ${count} badges → dist/badge/ (skipped ${skippedLowStars} below ${MIN_STARS_FOR_BADGE}★)`);
}

main().catch((e) => {
  // Non-fatal: badges are a nice-to-have, and the source query intermittently
  // hits Supabase 57014 (statement timeout) in CI. A transient timeout on a
  // non-critical artifact must not fail the whole deploy (same policy as RSS).
  console.warn(`⚠️  Badge generation failed (non-fatal): ${e.message}`);
});
