/**
 * scripts/skill-guides.mjs: a /skill/ page links to every live /best/ guide that lists the skill,
 * the guide's featured repos and, for a reviewed guide, its whole reviewed list.
 *
 * Run: node --test scripts/skill-guides.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { guidesHtml, guidesIndex, guidesMeta } from "./skill-guides.mjs";

const scenarios = [
  { slug: "image-generation", title: "Image Generation", match: { reviewed_only: true, exclude_repos: ["Spam/Repo"] } },
  { slug: "ppt-presentation", title: "PPT Skills", match: { reviewed_only: true, featured: ["hugohe3/ppt-master"] } },
  { slug: "keyword-page", title: "Keyword Page", match: { featured: ["Owner/Pinned"] } },
  { slug: "gone", title: "Retired", retired: true, match: { featured: ["Owner/Pinned"] } },
];
const kinds = {
  "image-generation": { repos: { "AgriciDaniel/banana-claude": "nano_banana", "spam/repo": "mcp", "Owner/Both": "mcp" } },
  "ppt-presentation": { repos: { "owner/both": "html", "anthropics/skills/skills/pptx": "pptx" } },
  "keyword-page": { repos: { "owner/unreviewed": "x" } },
};
const zh = { "image-generation": { t: "AI 生图 Skill" } };
const index = guidesIndex(scenarios, kinds, zh);

test("a reviewed guide links from every repo on its list, not only the featured ones", () => {
  assert.deepEqual(index.get("agricidaniel/banana-claude"),
    [{ slug: "image-generation", title: "Image Generation", titleZh: "AI 生图 Skill" }]);
  assert.deepEqual(index.get("hugohe3/ppt-master").map((g) => g.slug), ["ppt-presentation"]);
});

test("a repo on two guides gets both, in scenario order", () => {
  assert.deepEqual(index.get("owner/both").map((g) => g.slug), ["image-generation", "ppt-presentation"]);
});

test("excluded repos, sub-skill keys, unreviewed lists and retired guides give no link", () => {
  assert.equal(index.get("spam/repo"), undefined);
  assert.equal(index.get("anthropics/skills/skills/pptx"), undefined);
  assert.equal(index.get("owner/unreviewed"), undefined);
  assert.deepEqual(index.get("owner/pinned").map((g) => g.slug), ["keyword-page"]);
});

test("the zh title falls back to the English one", () => {
  assert.equal(index.get("hugohe3/ppt-master")[0].titleZh, "PPT Skills");
});

test("the static line shows the page's language and escapes titles", () => {
  const guides = [{ slug: "a", title: "A & B", titleZh: "甲" }];
  assert.match(guidesHtml(guides, "en", "Featured in:"), /Featured in: <a href="\/best\/a\/"[^>]*>A &amp; B<\/a>/);
  assert.match(guidesHtml(guides, "zh", "入选精选页："), />甲<\/a>/);
  assert.equal(guidesHtml([], "en", "Featured in:"), "");
});

test("the meta round-trips the guides as JSON and is empty without guides", () => {
  const guides = [{ slug: "a", title: "A \"quoted\" <b>", titleZh: "甲" }];
  const content = guidesMeta(guides).match(/content="([^"]*)"/)[1]
    .replace(/&quot;/g, "\"").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
  assert.deepEqual(JSON.parse(content), guides);
  assert.equal(guidesMeta([]), "");
});

test("the live data: heydamir/unslop links to the anti-slop guide, banana-claude to image generation", () => {
  const read = (name) => JSON.parse(readFileSync(new URL(name, import.meta.url), "utf-8"));
  const live = guidesIndex(read("./scenario-keywords.json"), read("./scenario-kinds.json"), read("./scenario-zh.json"));
  assert.ok(live.get("heydamir/unslop").some((g) => g.slug === "anti-slop"));
  assert.ok(live.get("agricidaniel/banana-claude").some((g) => g.slug === "image-generation"));
});
