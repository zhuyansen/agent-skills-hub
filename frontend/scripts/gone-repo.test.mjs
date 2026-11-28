/**
 * Tests for gone-repository mirror classification, command rewriting, and
 * archived-repo guide linking (without mutating frozen /best/ pages).
 *
 * Run: node --test scripts/gone-repo.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  goneCopy,
  retargetKind,
  retargetedSlug,
  rewriteMirrorCommand,
} from "../src/lib/goneRepo.mjs";
import { guidesIndex } from "./skill-guides.mjs";

test("same repo name under a different owner is classified as a mirror", () => {
  assert.equal(
    retargetedSlug("Bodila51/gtavi-claudecode", "https://github.com/zhuyansen/gtavi-claudecode"),
    "zhuyansen/gtavi-claudecode",
  );
  assert.equal(
    retargetKind("Bodila51/gtavi-claudecode", "https://github.com/zhuyansen/gtavi-claudecode"),
    "mirror",
  );
  const copy = goneCopy("Bodila51/gtavi-claudecode", "https://github.com/zhuyansen/gtavi-claudecode");
  assert.equal(copy.kind, "mirror");
  assert.match(copy.headingEn, /Mirror/i);
  assert.match(copy.bodyEn, /zhuyansen\/gtavi-claudecode/);
  assert.match(copy.bodyZh, /镜像/);
});

test("different repo name under another owner is classified as a substitute", () => {
  assert.equal(
    retargetKind("Manavarya09/design-extract", "https://github.com/arvindrk/extract-design-system"),
    "substitute",
  );
  const copy = goneCopy("Manavarya09/design-extract", "https://github.com/arvindrk/extract-design-system");
  assert.equal(copy.kind, "substitute");
  assert.match(copy.bodyEn, /SEPARATE project/);
});

test("un-retargeted gone repo returns null kind", () => {
  assert.equal(
    retargetKind("Bodila51/gtavi-claudecode", "https://github.com/Bodila51/gtavi-claudecode"),
    null,
  );
});

test("rewriteMirrorCommand replaces deleted original owner/repo case-insensitively", () => {
  assert.equal(
    rewriteMirrorCommand(
      "/plugin marketplace add Bodila51/gtavi-claudecode",
      "Bodila51/gtavi-claudecode",
      "zhuyansen/gtavi-claudecode",
    ),
    "/plugin marketplace add zhuyansen/gtavi-claudecode",
  );
  assert.equal(
    rewriteMirrorCommand(
      "/plugin install gtavi-claudecode@gtavi-claudecode",
      "Bodila51/gtavi-claudecode",
      "zhuyansen/gtavi-claudecode",
    ),
    "/plugin install gtavi-claudecode@gtavi-claudecode",
  );
});

test("Bodila51/gtavi-claudecode links to /best/claude-video-skills/ via guidesIndex", () => {
  const read = (name) => JSON.parse(readFileSync(new URL(name, import.meta.url), "utf-8"));
  const live = guidesIndex(read("./scenario-keywords.json"), read("./scenario-kinds.json"), read("./scenario-zh.json"));
  const guides = live.get("bodila51/gtavi-claudecode") || [];
  assert.ok(guides.some((g) => g.slug === "claude-video-skills"));
});
