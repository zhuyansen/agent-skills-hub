/**
 * Which repos get a /skill/<owner>/<repo>/ page: 50 stars, or a scenario page that lists the
 * repo under that floor. generate-skill-pages.mjs writes the pages by this rule, and every page
 * that links to one asks it first: the path of a repo without a page answers 404.
 *
 * 2026-11-20: author pages (/author/, /organization/) linked every Skill they listed. Counted on
 * a full build: 308 of their 1,606 list links, on 170 of the 500 pages, led to a 404. Category
 * pages had the same fault until the OpenSEO audit of 2026-11-18 (18 of its 27 broken links).
 */
import { readFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";
import { MIN_STARS_FOR_PAGE, admittedByReview } from "./shared-utils.mjs";
import { reviewedOnlyRepos } from "./scenario-kinds.mjs";

const SCENARIOS_PATH = join(dirname(fileURLToPath(import.meta.url)), "scenario-keywords.json");

/** The scenario definitions, where a page admits a repo under the star floor. */
export function readScenarioDefs() {
  return JSON.parse(readFileSync(SCENARIOS_PATH, "utf-8"));
}

/**
 * Returns `hasPage(skill)`. A reviewed-only page lists every repo its review kept, under the
 * floor too, not only the ones in `admit_reviewed` (/best/seo-tools/ linked 7 of them to 404s,
 * 2026-10-17).
 */
export function skillPageRule(scenarioDefs = readScenarioDefs()) {
  const admitted = admittedByReview(scenarioDefs);
  for (const name of reviewedOnlyRepos(scenarioDefs)) admitted.add(name);
  return (skill) => {
    const name = skill.repo_full_name || "";
    if (name.split("/").length !== 2) return false;
    return (skill.stars || 0) >= MIN_STARS_FOR_PAGE || admitted.has(name.toLowerCase());
  };
}
