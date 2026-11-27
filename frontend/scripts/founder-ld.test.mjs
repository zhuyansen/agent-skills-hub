import { test } from "node:test";
import assert from "node:assert/strict";
import { FOUNDER, isFounder } from "./founder-ld.mjs";
import { methodLd } from "./scenario-method.mjs";

const PERSON = "https://jasonzhu.ai/#person";
// Branch entity/gigalinks-frozen-fixes: the scenario pages (/best/) were frozen for the GIGALinks readouts until
// 2027-01-01, so their part of the 2026-11-27 fix lands with this branch.
const AUTHOR = { name: "Jason Zhu", about: "/about/", x: "https://x.com/GoSailGlobal", github: "https://github.com/zhuyansen", reviewed: "2026-10-08" };

/** The JSON-LD object inside methodLd's <script> tag. */
function ld(author) {
  const html = methodLd({ method: { author } }, "https://agentskillshub.top/best/ai-design/");
  return JSON.parse(html.slice(html.indexOf("{"), html.lastIndexOf("}") + 1));
}

test("the founder is a reference to his one Person node", () => {
  assert.deepEqual(FOUNDER, { "@type": "Person", "@id": PERSON, name: "Jason Zhu", url: "https://jasonzhu.ai/en" });
  assert.ok(Object.isFrozen(FOUNDER));
});

test("a scenario method by the founder names him by @id, with none of his accounts", () => {
  const data = ld(AUTHOR);
  assert.equal(data.author["@id"], PERSON);
  assert.equal(data.reviewedBy["@id"], PERSON);
  assert.equal(data.author.sameAs, undefined);
});

test("a guest author keeps a Person of their own", () => {
  const data = ld({ ...AUTHOR, name: "Ada Guest", x: "https://x.com/ada", github: "https://github.com/ada" });
  assert.equal(data.author["@id"], undefined);
  assert.deepEqual(data.author.sameAs, ["https://x.com/ada", "https://github.com/ada"]);
});

test("the founder's name, either script, any spacing", () => {
  for (const n of ["Jason Zhu", "jason zhu", " Jason  Zhu ", "祝彦森"]) assert.ok(isFounder(n), n);
  for (const n of ["Jason Zhuang", "Zhu", "", undefined]) assert.ok(!isFounder(n), String(n));
});
