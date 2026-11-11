/**
 * scripts/github-list-chip.mjs: the chip that opens a guide's open-source list on GitHub.
 *
 * Run: node --test scripts/github-list-chip.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { listStars, chipLabel, githubListChip, MIN_STARS_SHOWN } from "./github-list-chip.mjs";

const CATALOG = [
  { repo_full_name: "zhuyansen/awesome-claude-video-skills", stars: 1907 },
  { repo_full_name: "zhuyansen/awesome-3d-skills", stars: 0 },
];
const VIDEO = "https://github.com/zhuyansen/awesome-claude-video-skills";

test("the list's stars come from the catalog, whatever the case or a trailing slash", () => {
  assert.equal(listStars(VIDEO, CATALOG), 1907);
  assert.equal(listStars("https://github.com/Zhuyansen/Awesome-Claude-Video-Skills/", CATALOG), 1907);
  assert.equal(listStars("https://github.com/zhuyansen/not-in-the-catalog", CATALOG), 0);
});

test("a list with enough stars asks for one and shows the count", () => {
  assert.deepEqual(chipLabel(1907), ["⭐ Star the list on GitHub · 1.9k ↗", "⭐ 去 GitHub 给合集点星 · 1.9k ↗"]);
  assert.match(chipLabel(MIN_STARS_SHOWN)[0], /Star the list/);
});

test("a list with few stars keeps the plain label, without a count", () => {
  assert.deepEqual(chipLabel(MIN_STARS_SHOWN - 1), ["⭐ Open-source list on GitHub ↗", "⭐ GitHub 上的开源合集 ↗"]);
  assert.deepEqual(chipLabel(0), chipLabel(42));
});

test("the chip links to the list and carries both languages; no list, no chip", () => {
  const html = githubListChip({ github_list: VIDEO }, CATALOG);
  assert.match(html, /href="https:\/\/github\.com\/zhuyansen\/awesome-claude-video-skills"/);
  assert.match(html, /data-zh="⭐ 去 GitHub 给合集点星 · 1\.9k ↗"/);
  assert.match(html, />⭐ Star the list on GitHub · 1\.9k ↗<\/a>$/);
  assert.equal(githubListChip({}, CATALOG), "");
});
