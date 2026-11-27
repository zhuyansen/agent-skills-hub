import { test } from "node:test";
import assert from "node:assert/strict";
import { FOUNDER, isFounder } from "./founder-ld.mjs";

const PERSON = "https://jasonzhu.ai/#person";

// The scenario pages (/best/) use FOUNDER from 2027-01-02: they are frozen for the GIGALinks readouts
// until 2027-01-01, and their tests come with branch entity/gigalinks-frozen-fixes.
test("the founder is a reference to his one Person node", () => {
  assert.deepEqual(FOUNDER, { "@type": "Person", "@id": PERSON, name: "Jason Zhu", url: "https://jasonzhu.ai/en" });
  assert.ok(Object.isFrozen(FOUNDER));
});

test("the founder's name, either script, any spacing", () => {
  for (const n of ["Jason Zhu", "jason zhu", " Jason  Zhu ", "祝彦森"]) assert.ok(isFounder(n), n);
  for (const n of ["Jason Zhuang", "Zhu", "", undefined]) assert.ok(!isFounder(n), String(n));
});
