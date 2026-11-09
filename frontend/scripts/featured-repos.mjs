/**
 * Skill pages under the index floor (shared-utils.mjs MIN_STARS_TO_INDEX) that ask to be indexed
 * anyway: the repos a live /best/ guide tested (scenario-runs.json, a run that ran) or recommends
 * (a test's picks, the guide's `explainer.top`, its `match.featured`). Such a page carries what no
 * other page has, the test result or the pick, where the 10-14 floor was set for template pages.
 * On 2026-11-09 Bing listed /skill/seyedehsanhadi/sloptrim/ (404 stars, first in the anti-slop
 * test) among "important pages" kept out by noindex. 2026-11-10: about 120 pages from 50 stars.
 *
 * A run that did not run, one skill tested inside a repo (`sub`), a repo its own page excludes
 * and a retired page do not count. The page floor (MIN_STARS_FOR_PAGE) still applies.
 * Test: node --test scripts/featured-repos.test.mjs
 */
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const HERE = dirname(fileURLToPath(import.meta.url));
const lower = (name) => name.toLowerCase();
const isRepo = (name) => typeof name === "string" && name.split("/").length === 2;

function excludedOn(scenario) {
  return new Set((scenario.match?.exclude_repos || []).map(lower));
}

function addRepos(out, names, dropped) {
  for (const name of names) {
    if (isRepo(name) && !dropped.has(lower(name))) out.add(lower(name));
  }
}

/** Tested (ran, as a whole repo) or picked in a test whose page is live. */
function fromRuns(runs, bySlug, out) {
  for (const [key, run] of Object.entries(runs)) {
    const scenario = bySlug.get(run.page || key);
    if (!scenario) continue;
    const ran = Object.entries(run.runs || {}).filter(([, r]) => r.ran && !r.sub).map(([repo]) => repo);
    const picks = (run.verdict?.picks || []).map((pick) => pick.repo);
    addRepos(out, [...ran, ...picks], excludedOn(scenario));
  }
}

/** Recommended by a live guide itself: its top list and its featured repos. */
function fromGuides(bySlug, out) {
  for (const scenario of bySlug.values()) {
    const top = (scenario.explainer?.top?.items || []).map((item) => item.repo);
    addRepos(out, [...top, ...(scenario.match?.featured || [])], excludedOn(scenario));
  }
}

/** Lowercased owner/repo of every repo a live guide tested or recommends. */
export function featuredRepos(runs, scenarios) {
  const bySlug = new Map(scenarios.filter((s) => !s.retired).map((s) => [s.slug, s]));
  const out = new Set();
  fromRuns(runs, bySlug, out);
  fromGuides(bySlug, out);
  return out;
}

let cached = null;

/** featuredRepos() over this build's scenario-runs.json and scenario-keywords.json, read once. */
export function featuredRepoSet() {
  if (!cached) {
    const read = (name) => JSON.parse(readFileSync(join(HERE, name), "utf-8"));
    cached = featuredRepos(read("scenario-runs.json"), read("scenario-keywords.json"));
  }
  return cached;
}

/** Whether a live guide tested or recommends this repo (owner/repo, any case). */
export const isFeaturedRepo = (name) => featuredRepoSet().has(lower(name || ""));
