import { test } from "node:test";
import assert from "node:assert/strict";
import { featuredRepos } from "./featured-repos.mjs";

const SCENARIOS = [
  {
    slug: "anti-slop",
    match: { featured: ["Org/Featured"], exclude_repos: ["Bad/Lure"] },
    explainer: { top: { items: [{ repo: "Org/Top" }] } },
  },
  { slug: "old", retired: true, match: { featured: ["Org/Retired"] } },
];

const RUNS = {
  "anti-slop": {
    runs: { "Org/Ran": { ran: true }, "Org/NotRun": { ran: false }, "Org/Sub": { ran: true, sub: "x" }, "Bad/Lure": { ran: true } },
    verdict: { picks: [{ repo: "Org/Pick" }] },
  },
  "anti-slop-ui": { page: "anti-slop", runs: { "Org/Ui": { ran: true } } },
  old: { runs: { "Org/OldRun": { ran: true } } },
};

test("a live guide's tested, picked, top and featured repos count, lowercased", () => {
  const set = featuredRepos(RUNS, SCENARIOS);
  assert.deepEqual([...set].sort(), ["org/featured", "org/pick", "org/ran", "org/top", "org/ui"]);
});

test("not run, one skill inside, excluded by its page and retired pages do not count", () => {
  const set = featuredRepos(RUNS, SCENARIOS);
  for (const name of ["org/notrun", "org/sub", "bad/lure", "org/retired", "org/oldrun"]) {
    assert.equal(set.has(name), false, name);
  }
});
