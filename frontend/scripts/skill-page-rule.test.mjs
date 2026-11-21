import { test } from "node:test";
import assert from "node:assert/strict";
import { readScenarioDefs, skillPageRule } from "./skill-page-rule.mjs";
import { MIN_STARS_FOR_PAGE } from "./shared-utils.mjs";

const repo = (name, stars) => ({ repo_full_name: name, stars });

test("a repo at the star floor has a page, one under it does not", () => {
  const hasPage = skillPageRule([]);
  assert.equal(hasPage(repo("open-webui/mcpo", MIN_STARS_FOR_PAGE)), true);
  assert.equal(hasPage(repo("Graphify-Labs/REAgraph", 11)), false);
  assert.equal(hasPage(repo("someone/no-stars-field", undefined)), false);
});

test("a repo a scenario page admits under the floor has a page, whatever its letter case", () => {
  const hasPage = skillPageRule([{ slug: "x", match: { admit_reviewed: ["Some-Owner/Tiny-Repo"] } }]);
  assert.equal(hasPage(repo("some-owner/tiny-repo", 3)), true);
  assert.equal(hasPage(repo("Some-Owner/Tiny-Repo", 3)), true);
  assert.equal(hasPage(repo("some-owner/other", 3)), false);
});

test("a name that is not owner/repo has no page", () => {
  const hasPage = skillPageRule([]);
  assert.equal(hasPage(repo("just-a-name", 9000)), false);
  assert.equal(hasPage(repo("a/b/c", 9000)), false);
});

test("the site's own scenario file loads", () => {
  const defs = readScenarioDefs();
  assert.ok(Array.isArray(defs) && defs.length > 50);
  assert.equal(typeof skillPageRule(defs), "function");
});
