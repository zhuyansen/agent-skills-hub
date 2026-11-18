// node --test scripts/search-assist.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { githubRepoFromInput, correctTerm, scenarioForTerm } from "../src/lib/searchAssist.mjs";
import { buildSearchAssist } from "./generate-search-assist-data.mjs";

const data = JSON.parse(readFileSync(new URL("../src/data/search-assist.json", import.meta.url), "utf-8"));

test("search-assist.json is up to date with the scenario config", () => {
  assert.deepEqual(data, buildSearchAssist(), "run: node scripts/generate-search-assist-data.mjs");
});

test("GitHub URLs become owner/repo", () => {
  assert.equal(githubRepoFromInput("https://github.com/panniantong/agent-reach"), "panniantong/agent-reach");
  assert.equal(githubRepoFromInput("github.com/greensock/gsap-skills/tree/main/skills"), "greensock/gsap-skills");
  assert.equal(githubRepoFromInput("https://github.com/o/r.git"), "o/r");
  assert.equal(githubRepoFromInput("git@github.com:o/my.repo.git"), "o/my.repo");
  assert.equal(githubRepoFromInput("https://amir-fx.com/bots"), null);
  assert.equal(githubRepoFromInput("motion graphics"), null);
});

test("typos from the search log are corrected", () => {
  const v = data.vocab;
  assert.equal(correctTerm("viideo", v), "video");
  assert.equal(correctTerm("yutube", v), "youtube");
  assert.equal(correctTerm("motion gra[hics", v), "motion graphics");
  assert.equal(correctTerm("website dvelopement", v), "website development");
  assert.equal(correctTerm("animationn", v), "animation");
});

test("known, short, numeric and CJK words are left alone", () => {
  const v = data.vocab;
  assert.equal(correctTerm("video", v), null);
  assert.equal(correctTerm("ppt", v), null);
  assert.equal(correctTerm("gpt5", v), null);
  assert.equal(correctTerm("视频剪辑", v), null);
});

test("search terms find their scenario page", () => {
  const t = data.scenarios;
  assert.equal(scenarioForTerm("video", t)?.slug, "claude-video-skills");
  assert.equal(scenarioForTerm("Video Editing", t)?.slug, "claude-video-skills");
  assert.equal(scenarioForTerm("motion", t)?.slug, "animation-skills");
  assert.equal(scenarioForTerm("gsap", t)?.slug, "animation-skills");
  assert.equal(scenarioForTerm("动画", t)?.slug, "animation-skills");
  assert.equal(scenarioForTerm("ppt", t)?.slug, "ppt-presentation");
  assert.equal(scenarioForTerm("claude", t), null);
  assert.equal(scenarioForTerm("agent reach", t), null);
});
