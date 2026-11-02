/**
 * scripts/skill-page-copy.mjs and the blocks that take its language: which /skill/ pages are
 * written in Chinese, and that the shared blocks keep their English text unchanged.
 *
 * Run: node --test scripts/skill-page-copy.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { skillPageLang, skillCopy, flagName, findingText } from "./skill-page-copy.mjs";
import { installSectionHtml } from "./skill-install.mjs";
import { trustBlock } from "./shared-utils.mjs";
import { parentSectionHtml } from "./sub-skills.mjs";

test("a description written in Chinese makes a Chinese page", () => {
  assert.equal(skillPageLang("艺术动画skill：35种艺术风格、9种解说语法，用代码让画动起来。"), "zh");
  assert.equal(skillPageLang("面向数学建模竞赛的 Claude Code / Codex Skills ，支持分阶段建模流程"), "zh");
});

test("English with a Chinese brand name, Japanese, or nothing stays English", () => {
  assert.equal(skillPageLang("A CLI for Xiaohongshu (小红书) — search, read, interact via reverse-engineered API"), "en");
  assert.equal(skillPageLang("AIにまじなPPTXを作らせる Claude Code / Codex スキル"), "en");
  assert.equal(skillPageLang("日本語の説明文です"), "en");
  assert.equal(skillPageLang(""), "en");
  assert.equal(skillPageLang(null), "en");
});

test("flag names come in both languages, unknown flags fall back to their key", () => {
  assert.equal(flagName("reverse_shell", "en"), "reverse shell");
  assert.equal(flagName("reverse_shell", "zh"), "反弹 shell");
  assert.equal(flagName("some_new_rule", "zh"), "some new rule");
});

test("the finding names four flags and counts the rest", () => {
  const names = ["a", "b", "c", "d", "e", "f"];
  assert.equal(findingText(skillCopy("en"), names, 42), "Flagged: a, b, c, d and 2 more.");
  assert.equal(findingText(skillCopy("zh"), names, 42), "命中：a、b、c、d，另有 2 项。");
  assert.equal(findingText(skillCopy("en"), [], 42),
    "None of the 42 rules matched — no credential harvesting, no data exfiltration, no curl-pipe-shell installer.");
  assert.match(findingText(skillCopy("zh"), [], 42), /^42 条规则都没有命中/);
});

test("Chinese category names get a space only next to a Latin word", () => {
  const zh = skillCopy("zh");
  assert.equal(zh.moreCat("Claude Skill"), "更多 Claude Skill");
  assert.equal(zh.moreCat("教育"), "更多教育");
  assert.match(zh.altIntro("x", "MCP 服务器", 3), /收录的 MCP 服务器里/);
});

test("the install section keeps its English text and has a Chinese one", () => {
  const en = installSectionHtml("tool", ["npx skills add a/tool"], "/audit/a/tool/");
  assert.match(en, /<h2 [^>]*>How to install tool<\/h2>/);
  assert.match(en, /Taken from the project's README on GitHub\. Check <a href="\/audit\/a\/tool\/" style="color:#4f46e5">the security audit<\/a> before running it\./);
  const zh = installSectionHtml("tool", ["npx skills add a/tool"], "/audit/a/tool/", "zh");
  assert.match(zh, /<h2 [^>]*>怎么安装 tool<\/h2>/);
  assert.match(zh, /命令取自这个项目在 GitHub 上的 README。运行前先看看<a [^>]*>安全审计<\/a>。/);
  assert.equal(installSectionHtml("tool", [], null, "zh"), "");
});

test("the repository's skill list follows the page's language", () => {
  const list = Array.from({ length: 52 }, (_, i) => ({ slug: `s${i}`, name: `skill-${i}`, path: `skills/s${i}`, description: "", page: i < 3 }));
  const en = parentSectionHtml("owner/repo", list);
  assert.match(en, />Skills in this repository \(52\)<\/h2>/);
  assert.match(en, /2 more in <a [^>]*>the repository on GitHub<\/a>\./);
  const zh = parentSectionHtml("owner/repo", list, "zh");
  assert.match(zh, />本仓库里的 Skills（52）<\/h2>/);
  assert.match(zh, /另有 2 个，见 <a [^>]*>GitHub 仓库<\/a>。/);
});

test("the trust block shows Chinese text on a Chinese page and English elsewhere", () => {
  assert.match(trustBlock(), />How this security grade is produced<\/h2>/);
  assert.match(trustBlock("zh"), />这个安全评级是怎么来的<\/h2>/);
  assert.doesNotMatch(trustBlock("zh"), />Grades come from/);
});
