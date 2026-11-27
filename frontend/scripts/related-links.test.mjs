import { test } from "node:test";
import assert from "node:assert/strict";
import { buildDay, firstPicks, hash32, linkRing, randomPicks, recentByCategory } from "./related-links.mjs";

const names = (n, prefix = "o") => Array.from({ length: n }, (_, i) => `${prefix}${i}/repo-${i}`);
const ringOf = (list, day) => linkRing(list, day, (x) => x);

test("the build day is the UTC date unless ASH_BUILD_DATE pins it", () => {
  assert.equal(buildDay({}, new Date("2026-11-26T23:30:00Z")), "2026-11-26");
  assert.equal(buildDay({ ASH_BUILD_DATE: "2026-12-01" }), "2026-12-01");
  assert.equal(buildDay({ ASH_BUILD_DATE: "tomorrow" }, new Date("2026-11-26T01:00:00Z")), "2026-11-26");
});

test("the hash is FNV-1a", () => {
  assert.equal(hash32(""), 0x811c9dc5);
  assert.equal(hash32("a"), 0xe40c292c);
});

test("two builds on the same day pick the same links", () => {
  const ring = ringOf(names(500), "2026-11-26");
  const a = randomPicks(ring, "2026-11-26", "x/y", 8);
  const b = randomPicks(ringOf(names(500), "2026-11-26"), "2026-11-26", "x/y", 8);
  assert.deepEqual(a, b);
  assert.equal(a.length, 8);
  assert.equal(new Set(a).size, 8);
});

test("the next day and another page get other links", () => {
  const pool = names(500);
  const today = randomPicks(ringOf(pool, "2026-11-26"), "2026-11-26", "x/y", 8);
  const tomorrow = randomPicks(ringOf(pool, "2026-11-27"), "2026-11-27", "x/y", 8);
  const other = randomPicks(ringOf(pool, "2026-11-26"), "2026-11-26", "z/w", 8);
  assert.notDeepEqual(today, tomorrow);
  assert.notDeepEqual(today, other);
});

test("a page never links to itself or to what skip rejects", () => {
  const pool = names(30);
  const self = pool[3];
  const already = new Set(pool.slice(10, 20));
  for (const page of pool) {
    const picks = randomPicks(ringOf(pool, "2026-11-26"), "2026-11-26", self, 8, (x) => x === self || already.has(x));
    assert.ok(!picks.includes(self), page);
    assert.ok(picks.every((x) => !already.has(x)));
    assert.equal(picks.length, 8);
  }
});

test("a small pool gives what it has", () => {
  const pool = names(3);
  const picks = randomPicks(ringOf(pool, "d"), "d", pool[0], 8, (x) => x === pool[0]);
  assert.deepEqual([...picks].sort(), pool.slice(1).sort());
  assert.deepEqual(randomPicks([], "d", "p", 8), []);
});

test("one page added between two builds of a day moves few picks", () => {
  const day = "2026-11-26";
  const before = ringOf(names(1000), day);
  const after = ringOf([...names(1000), "new/page"], day);
  let moved = 0;
  let total = 0;
  for (const page of names(200, "p")) {
    const a = randomPicks(before, day, page, 8);
    const b = new Set(randomPicks(after, day, page, 8));
    total += a.length;
    moved += a.filter((x) => !b.has(x)).length;
  }
  assert.ok(moved / total < 0.02, `${moved} of ${total} picks moved`);
});

test("over a month the random block reaches most of the catalog", () => {
  const pool = names(2000);
  const reached = new Set();
  for (let d = 1; d <= 30; d++) {
    const day = `2026-12-${String(d).padStart(2, "0")}`;
    const ring = ringOf(pool, day);
    for (const page of pool) for (const x of randomPicks(ring, day, page, 8, (y) => y === page)) reached.add(x);
  }
  assert.ok(reached.size / pool.length > 0.99, `${reached.size} of ${pool.length}`);
});

test("recently added means the highest ids of each category, newest first", () => {
  const items = [
    { id: 5, category: "mcp-server", name: "a" },
    { id: 9, category: "mcp-server", name: "b" },
    { id: 7, category: "claude-skill", name: "c" },
    { id: 1, category: "mcp-server", name: "d" },
    { id: 8, name: "e" },
  ];
  const recent = recentByCategory(items, 2);
  assert.deepEqual(recent.get("mcp-server").map((x) => x.name), ["b", "a"]);
  assert.deepEqual(recent.get("claude-skill").map((x) => x.name), ["c"]);
  assert.deepEqual(recent.get("other").map((x) => x.name), ["e"]);
});

test("firstPicks skips what the page already shows", () => {
  assert.deepEqual(firstPicks([1, 2, 3, 4, 5], 2, (x) => x < 3), [3, 4]);
  assert.deepEqual(firstPicks(undefined, 2), []);
});
