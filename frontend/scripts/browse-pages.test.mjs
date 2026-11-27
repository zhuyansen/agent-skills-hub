import { test } from "node:test";
import assert from "node:assert/strict";
import { BROWSE_PATH, hubHtml, letterOf, listHtml, pagePath, paginate } from "./browse-pages.mjs";

const links = (html, base) => [...html.matchAll(new RegExp(`href="${base}([^"]+)/"`, "g"))].map((m) => m[1]);

test("pages are filed under the first character of owner/repo", () => {
  assert.equal(letterOf("Anthropics/skills"), "a");
  assert.equal(letterOf("0xJacky/nginx-ui"), "0-9");
  assert.equal(letterOf("_x/y"), "other");
  assert.equal(pagePath("skills", "a", 1), "/browse/skills/a/");
  assert.equal(pagePath("audits", "0-9", 3), "/browse/audits/0-9/3/");
});

test("a letter is cut into pages of the given size, A–Z regardless of case", () => {
  const names = ["b/x", "a/z", "A/y", "a/b", "9/q", "c/1"];
  const pages = paginate("skills", names, 2);
  assert.deepEqual(pages.map((p) => [p.letter, p.n, p.of, p.start, p.names]), [
    ["0-9", 1, 1, 1, ["9/q"]],
    ["a", 1, 2, 1, ["a/b", "A/y"]],
    ["a", 2, 2, 3, ["a/z"]],
    ["b", 1, 1, 1, ["b/x"]],
    ["c", 1, 1, 1, ["c/1"]],
  ]);
  assert.deepEqual(pages.map((p) => p.path), ["/browse/skills/0-9/", "/browse/skills/a/", "/browse/skills/a/2/", "/browse/skills/b/", "/browse/skills/c/"]);
});

test("every name is linked exactly once across the pages", () => {
  const names = Array.from({ length: 1234 }, (_, i) => `${"abc"[i % 3]}owner${i}/repo-${i}`);
  const pages = paginate("audits", names);
  const linked = pages.flatMap((p) => links(listHtml(p, pages), "/audit/"));
  assert.equal(linked.length, names.length);
  assert.deepEqual([...linked].sort(), [...names].sort());
  assert.ok(pages.every((p) => p.names.length <= 500));
});

test("a listing page is indexable, canonical to itself and chained to its neighbours", () => {
  const pages = paginate("skills", Array.from({ length: 1001 }, (_, i) => `a${String(i).padStart(4, "0")}/r`));
  const html = listHtml(pages[1], pages);
  assert.ok(!/noindex/i.test(html));
  assert.match(html, /<link rel="canonical" href="https:\/\/agentskillshub\.top\/browse\/skills\/a\/2\/" \/>/);
  assert.match(html, /<link rel="prev" href="https:\/\/agentskillshub\.top\/browse\/skills\/a\/" \/>/);
  assert.match(html, /<link rel="next" href="https:\/\/agentskillshub\.top\/browse\/skills\/a\/3\/" \/>/);
  assert.match(html, /<ol start="501"/);
  assert.match(html, /<title>Skill pages A, page 2 of 3 \| Agent Skills Hub<\/title>/);
  assert.ok(!html.includes("/assets/"), "no SPA bundle");
});

test("the hub links the first page of every letter in both sections with its count", () => {
  const skills = paginate("skills", ["a/1", "a/2", "b/1"], 1);
  const audits = paginate("audits", ["z/1"]);
  const html = hubHtml({ skills, audits });
  assert.match(html, new RegExp(`<link rel="canonical" href="https://agentskillshub.top${BROWSE_PATH}" />`));
  assert.ok(html.includes('id="skills"') && html.includes('id="audits"'));
  assert.ok(html.includes('href="/browse/skills/a/"') && html.includes("(2)"));
  assert.ok(!html.includes('href="/browse/skills/a/2/"'), "later pages are reached from the letter page");
  assert.ok(html.includes('href="/browse/audits/z/"'));
});

test("names are escaped in links and text", () => {
  const pages = paginate("skills", ['a/"x<y'], 10);
  const html = listHtml(pages[0], pages);
  assert.ok(html.includes("a/&quot;x&lt;y"));
  assert.ok(!html.includes('a/"x<y'));
});
