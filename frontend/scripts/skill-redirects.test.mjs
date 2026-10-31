/**
 * scripts/skill-redirects.mjs: which old names get a redirect page, what the page says, how the
 * curated files are renamed, and how skill_redirects is read. No network: fetch is stubbed.
 *
 * Run: node --test scripts/skill-redirects.test.mjs
 */
import { test, afterEach } from "node:test";
import assert from "node:assert/strict";
import {
  fetchSkillRedirects, stubsToWrite, redirectStubHtml, renameMap, renameNames, curatedJson,
} from "./skill-redirects.mjs";

const realFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = realFetch; });

const json = (body, status = 200) => new Response(JSON.stringify(body), { status });

test("an old name gets a page unless only its case changed or it has a page of its own", () => {
  const redirects = [["affaan-m/everything-claude-code", "affaan-m/ECC"], ["MiroMindAI/miroflow", "MiroMindAI/MiroFlow"],
    ["reused/name", "elsewhere/name"]];
  assert.deepEqual(stubsToWrite(redirects, (name) => name === "reused/name"),
    [["affaan-m/everything-claude-code", "affaan-m/ECC"]]);
});

test("the redirect page points at the new URL three ways and does not ask for noindex", () => {
  const html = redirectStubHtml("affaan-m/ECC");
  assert.match(html, /<link rel="canonical" href="https:\/\/agentskillshub\.top\/skill\/affaan-m\/ECC\/" \/>/);
  assert.match(html, /<meta http-equiv="refresh" content="0; url=\/skill\/affaan-m\/ECC\/" \/>/);
  assert.match(html, /location\.replace\("\/skill\/affaan-m\/ECC\/"\)/);
  assert.doesNotMatch(html, /noindex/);
});

test("curated names are renamed as values and keys, in any case, and nothing else changes", () => {
  const renames = renameMap([["feder-cr/AIHawk", "feder-cr/invisible_dots"], ["safishamsi/graphify", "Graphify-Labs/graphify"]]);
  const scenarios = [{
    slug: "job-search", keywords: ["AIHawk", "aihawk"],
    match: { featured: ["feder-cr/aihawk", "other/repo"], exclude_repos: ["safishamsi/graphify", "Graphify-Labs/graphify"] },
    extra_faq: [{ a: "Use feder-cr/AIHawk for this." }],
  }];
  const changes = [];
  const out = renameNames(scenarios, renames, changes);
  assert.deepEqual(out[0].match, { featured: ["feder-cr/invisible_dots", "other/repo"], exclude_repos: ["Graphify-Labs/graphify"] });
  assert.deepEqual(out[0].keywords, ["AIHawk", "aihawk"]);
  assert.equal(out[0].extra_faq[0].a, "Use feder-cr/AIHawk for this.");
  assert.deepEqual(changes, [["feder-cr/aihawk", "feder-cr/invisible_dots"], ["safishamsi/graphify", "Graphify-Labs/graphify"]]);
});

test("a renamed key keeps its place, and an entry already under the new name wins", () => {
  const renames = renameMap([["a/old", "a/new"], ["b/old", "b/new"]]);
  const desc = { "z/first": "1", "a/old": "old text", "b/old": "stale", "b/new": "curated" };
  const out = renameNames(desc, renames);
  assert.deepEqual(Object.entries(out), [["z/first", "1"], ["a/new", "old text"], ["b/new", "curated"]]);
});

test("a file with no old names comes back byte for byte", () => {
  const text = '[\n {\n  "slug": "x",\n  "match": {\n   "featured": [\n    "a/b"\n   ]\n  }\n }\n]\n';
  const changes = [];
  assert.equal(curatedJson(renameNames(JSON.parse(text), renameMap([["c/d", "e/f"]]), changes)), text);
  assert.deepEqual(changes, []);
});

test("redirects are read a page at a time", async () => {
  const offsets = [];
  globalThis.fetch = async (url) => {
    const offset = Number(new URL(url).searchParams.get("offset"));
    offsets.push(offset);
    const rows = Array.from({ length: offset === 0 ? 1000 : 1 }, (_, i) => ({ old_full_name: `o/${offset + i}`, new_full_name: "n/x" }));
    return json(rows);
  };
  const redirects = await fetchSkillRedirects();
  assert.equal(redirects.length, 1001);
  assert.deepEqual(offsets, [0, 1000]);
  assert.deepEqual(redirects[0], ["o/0", "n/x"]);
});

test("no table yet (before migration 041) means no redirects, not a failed build", async () => {
  globalThis.fetch = async () => json({ code: "PGRST205", message: "Could not find the table 'public.skill_redirects'" }, 404);
  assert.deepEqual(await fetchSkillRedirects(), []);
});

test("a failing read is retried, then fails the build", async () => {
  let calls = 0;
  globalThis.fetch = async () => { calls += 1; return json({ message: "boom" }, 503); };
  await assert.rejects(fetchSkillRedirects(), /skill_redirects: HTTP 503/);
  assert.equal(calls, 3);
});
