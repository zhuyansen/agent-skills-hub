/**
 * Redirect pages at the /skill/ URLs of repositories' old names (scripts/skill-redirects.mjs says
 * why). Runs after generate-skill-pages.mjs, so an old name that has a row again keeps the page
 * that script wrote for it.
 *
 *   dist/skill/<old owner>/<old repo>/index.html   -> /skill/<owner>/<repo>/
 *
 * Not in any sitemap: generate-sitemap.mjs lists catalog rows, and an old name has none.
 *
 * Run: node scripts/generate-skill-redirects.mjs  (after generate-skill-pages.mjs)
 */
import { existsSync, mkdirSync, writeFileSync } from "fs";
import { join } from "path";
import { fetchSkillRedirects, stubsToWrite, redirectStubHtml } from "./skill-redirects.mjs";

const DIST = "dist";
const pageDir = (fullName) => join(DIST, "skill", ...fullName.split("/"));

async function main() {
  const redirects = await fetchSkillRedirects();
  const stubs = stubsToWrite(redirects, (name) => existsSync(join(pageDir(name), "index.html")));
  for (const [from, to] of stubs) {
    mkdirSync(pageDir(from), { recursive: true });
    writeFileSync(join(pageDir(from), "index.html"), redirectStubHtml(to));
  }
  console.log(`  ✓ ${stubs.length} redirect pages at old repository names (${redirects.length} redirects)`);
}

main().catch((err) => {
  console.error("Failed to generate skill redirect pages:", err);
  process.exit(1);
});
