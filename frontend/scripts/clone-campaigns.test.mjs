import { test } from "node:test";
import assert from "node:assert/strict";
import { cloneCampaignRepos, withoutCloneCampaigns } from "./clone-campaigns.mjs";

const MANUS = "AI Manus is a general-purpose AI Agent system that supports running various tools";
const row = (repo_full_name, stars, created_at, description = MANUS) =>
  ({ repo_full_name, author_name: repo_full_name.split("/")[0], stars, created_at, description });

const copies = (n, stars = 80, day = "2026-11-07") =>
  Array.from({ length: n }, (_, i) => row(`Bot${i}/ai--manus`, stars, `${day}T06:34:${String(i).padStart(2, "0")}Z`));

test("five starred copies of one description on five accounts are a campaign", () => {
  assert.equal(cloneCampaignRepos(copies(5)).size, 5);
});

test("four accounts are not enough", () => {
  assert.equal(cloneCampaignRepos(copies(4)).size, 0);
});

test("forks of a real project sit at 0–1 stars and are left alone (anthropics/claude-code)", () => {
  const group = [row("anthropics/claude-code", 156083, "2025-02-22T00:00:00Z"),
    ...copies(8, 1).map((s) => ({ ...s, description: MANUS }))];
  assert.equal(cloneCampaignRepos(group).size, 0);
});

test("the original that predates its copies by a month is kept (Simpleyyt/ai-manus)", () => {
  const group = [row("Simpleyyt/ai-manus", 1648, "2025-04-26T00:00:00Z"), ...copies(6)];
  const drop = cloneCampaignRepos(group);
  assert.equal(drop.size, 6);
  assert.ok(!drop.has("simpleyyt/ai-manus"));
});

test("independent projects with the same name but their own descriptions are left alone (open-jev)", () => {
  const group = ["JoshuaSP", "daseinlabs", "Zefan-Cai", "nico-martin", "kyegomez"].map((o, i) =>
    row(`${o}/open-jev`, 100, "2026-09-16T00:00:00Z", `Open Jev implementation number ${i} with its own description`));
  assert.equal(cloneCampaignRepos(group).size, 0);
});

test("short descriptions are not compared", () => {
  assert.equal(cloneCampaignRepos(copies(6).map((s) => ({ ...s, description: "AI agent" }))).size, 0);
});

test("case and spacing do not hide a copy", () => {
  const group = copies(5).map((s, i) => ({ ...s, description: i % 2 ? MANUS.toUpperCase() : `  ${MANUS}  ` }));
  assert.equal(cloneCampaignRepos(group).size, 5);
});

test("withoutCloneCampaigns keeps everything else in order", () => {
  const keep = [row("a/one", 10, "2026-01-01T00:00:00Z", "something else entirely, long enough to compare"), row("b/two", 3, null, "")];
  const out = withoutCloneCampaigns([keep[0], ...copies(5), keep[1]]);
  assert.deepEqual(out, keep);
});
