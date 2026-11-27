import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  auditDescription, auditTitle, auditTitleVariant, loadTitleTest, scanMonth, sharedRepoNames, titleBucket, titleTestGroup,
} from "./audit-meta.mjs";
import { DESCRIPTION_LIMIT, TITLE_MAX_WIDTH, displayWidth } from "../src/lib/skillMeta.mjs";

const skill = (full, quality = 70) => ({ repo_full_name: full, repo_name: full.split("/")[1], quality_score: quality });

test("a short repo keeps the question, the audit and the owner", () => {
  assert.equal(auditTitle(skill("0xJacky/nginx-ui")), "Is nginx-ui Safe? Security Audit of 0xJacky/nginx-ui");
});

test("the site name is not in the title", () => {
  assert.ok(!auditTitle(skill("0x4m4/hexstrike-ai")).includes("Agent Skills Hub"));
});

test("a longer name is said once, with its owner", () => {
  const t = auditTitle(skill("anthropics/claude-plugins-official"));
  assert.equal(t, "Is anthropics/claude-plugins-official Safe? Security Audit");
  assert.ok(displayWidth(t) <= TITLE_MAX_WIDTH, t);
});

test("a very long owner/repo drops the owner when no other audited repo has the name", () => {
  const s = skill("decodingai-magazine/building-a-coding-agent-course");
  assert.equal(auditTitle(s, sharedRepoNames([s])), "Is building-a-coding-agent-course Safe? Security Audit");
});

test("a repo name two audited repos share keeps its owner", () => {
  const a = skill("some-long-organisation-name/agent-skills-collection-x");
  const b = skill("another-organisation/agent-skills-collection-x");
  const shared = sharedRepoNames([a, b]);
  assert.ok(shared.has("agent-skills-collection-x"));
  const ta = auditTitle(a, shared);
  const tb = auditTitle(b, shared);
  assert.ok(ta.startsWith("Is some-long-organisation-name/"), ta);
  assert.ok(displayWidth(ta) <= TITLE_MAX_WIDTH, `${displayWidth(ta)}: ${ta}`);
  assert.notEqual(ta, tb);
});

test("every title of a set is its own", () => {
  const set = ["a/skills", "b/skills", "anthropics/skills", "0xJacky/nginx-ui", "x/nginx-ui"].map((n) => skill(n));
  const shared = sharedRepoNames(set);
  const titles = set.map((s) => auditTitle(s, shared));
  assert.equal(new Set(titles).size, titles.length);
});

test("the description keeps its full sentence when it fits", () => {
  assert.equal(
    auditDescription(skill("0xJacky/nginx-ui", 69), "SAFE", 0),
    "0xJacky/nginx-ui security audit: graded SAFE by AgentSkillsHub's rule-based security scan. No dangerous patterns found. Quality score 69/100.",
  );
});

test("a long owner/repo shortens the description and keeps the result", () => {
  const d = auditDescription(skill("decodingai-magazine/building-a-coding-agent-from-scratch-course", 81), "CAUTION", 2);
  assert.ok(d.length <= DESCRIPTION_LIMIT, `${d.length}: ${d}`);
  assert.match(d, /graded CAUTION by AgentSkillsHub/);
  assert.match(d, /2 flags found\. Quality score 81\/100\.$/);
});

test("one flag is singular", () => {
  assert.match(auditDescription(skill("0x4m4/hexstrike-ai", 72), "SAFE", 1), /1 flag found\./);
});

test("a long owner/repo falls back to the repo's own name as the question", () => {
  const s = skill("EpicGames/unreal-engine-skills-for-claude-code-plugin");
  const t = auditTitle(s, sharedRepoNames([s]));
  assert.equal(t, "Is unreal-engine-skills-for-claude-code-plugin Safe?");
  assert.ok(displayWidth(t) <= TITLE_MAX_WIDTH, t);
});

test("a name nothing can fit keeps its owner and caps at TITLE_MAX_WIDTH", () => {
  const s = skill("NAalytics/Assemblies-of-putative-SARS-CoV2-spike-encoding-mRNA-sequences-for-vaccines-BNT-162b2-and-mRNA-1273");
  const t = auditTitle(s, sharedRepoNames([s]));
  assert.ok(t.startsWith("Is NAalytics/"), t);
  assert.ok(t.endsWith("… Safe?"), t);
  assert.ok(displayWidth(t) <= TITLE_MAX_WIDTH, `${displayWidth(t)}: ${t}`);
});

test("an ultra-long owner/repo caps the description and keeps the verdict", () => {
  const s = skill("NAalytics/Assemblies-of-putative-SARS-CoV2-spike-encoding-mRNA-sequences-for-vaccines-BNT-162b2-and-mRNA-1273", 68);
  const d = auditDescription(s, "SAFE", 0);
  assert.ok(d.length <= DESCRIPTION_LIMIT, `${d.length}: ${d}`);
  assert.ok(d.startsWith("NAalytics/"), d);
  assert.match(d, /…: graded SAFE by AgentSkillsHub\. No dangerous patterns found\. Quality score 68\/100\.$/);
});

test("the audit sitemap lists every page once, most-starred first, with no dates", async () => {
  const { auditSitemap } = await import("./audit-meta.mjs");
  const xml = auditSitemap([
    { repo_full_name: "a/small", stars: 60 },
    { repo_full_name: "b/big", stars: 9000 },
  ], "https://agentskillshub.top");
  const locs = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
  assert.deepEqual(locs, ["https://agentskillshub.top/audit/b/big/", "https://agentskillshub.top/audit/a/small/"]);
  assert.ok(!xml.includes("<lastmod>"));
  assert.match(xml, /^<\?xml version="1.0" encoding="UTF-8"\?>\n<urlset xmlns="http:\/\/www.sitemaps.org\/schemas\/sitemap\/0.9">/);
});

// ── title test (audit-title-test.json) ────────────────────────────────────────

const TEST_ID = "audit-title-grade-date";
const scanned = (full, at = "2026-11-25T08:00:00Z") => ({ ...skill(full), security_scanned_at: at });

test("the bucket of a page is pinned (ops/gsc/test_audit_title_test.py checks the same numbers)", () => {
  assert.equal(titleBucket("0xJacky/nginx-ui", TEST_ID), 17);
  assert.equal(titleBucket("anthropics/skills", TEST_ID), 80);
  assert.equal(titleBucket("langgenius/dify", TEST_ID), 33);
  assert.equal(titleBucket("MorDavid/BruteForceAI", TEST_ID), 20);
  assert.equal(titleBucket("mordavid/bruteforceai", TEST_ID), 20, "case does not move a page");
});

test("about one page in ten is treated", () => {
  const test10 = loadTitleTest({ id: TEST_ID, share_percent: 10, excluded: [] });
  const n = 20000;
  const treated = Array.from({ length: n }, (_, i) => titleTestGroup(scanned(`owner${i}/repo${i}`), test10)).filter((g) => g === "treated").length;
  assert.ok(treated / n > 0.09 && treated / n < 0.11, `${treated} of ${n}`);
});

test("a listed or never-scanned page is in neither group", () => {
  const t = loadTitleTest({ id: TEST_ID, share_percent: 100, excluded: ["Langgenius/Dify"] });
  assert.equal(titleTestGroup(scanned("langgenius/dify"), t), "excluded");
  assert.equal(titleTestGroup(scanned("x/y", null), t), "excluded");
  assert.equal(titleTestGroup(scanned("x/y"), t), "treated");
});

test("the test file names its start, share and exclusions", () => {
  const file = JSON.parse(readFileSync(new URL("./audit-title-test.json", import.meta.url), "utf-8"));
  assert.equal(file.id, TEST_ID);
  assert.match(file.start, /^\d{4}-\d{2}-\d{2}$/);
  assert.equal(file.share_percent, 10);
  assert.ok(file.excluded.length > 100 && file.excluded.every((n) => n === n.toLowerCase() && n.includes("/")));
});

test("the variant names the grade and the month of the scan, within the title width", () => {
  assert.equal(scanMonth("2026-11-25T08:00:00Z"), "Nov 2026");
  assert.equal(scanMonth(null), null);
  assert.equal(auditTitleVariant(scanned("0xJacky/nginx-ui"), "SAFE"), "Is nginx-ui Safe? Graded SAFE, Scanned Nov 2026");
  const shared = sharedRepoNames([scanned("a/skills"), scanned("anthropics/skills")]);
  assert.equal(auditTitleVariant(scanned("anthropics/skills"), "CAUTION", shared), "Is Anthropic Skills Safe? Graded CAUTION, Scanned Nov 2026");
  const long = auditTitleVariant(scanned("decodingai-magazine/building-a-coding-agent-from-scratch-course"), "UNSAFE", new Set(["building-a-coding-agent-from-scratch-course"]));
  assert.ok(displayWidth(long) <= TITLE_MAX_WIDTH, long);
  assert.match(long, /UNSAFE, Nov 2026$/);
  assert.equal(auditTitleVariant(scanned("x/y", null), "SAFE"), null);
});
