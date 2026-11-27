/**
 * The founder as our pages name him in JSON-LD: a reference to the one Person node, which lives on
 * jasonzhu.ai. Until 2026-11-27 the scenario and Blue Book templates wrote an anonymous Person
 * ("Jason Zhu", url /about/, his X and GitHub) on 36 pages, a second Jason Zhu next to the real one.
 * ops/geo/entity_edges.py (rule 8) checks every template for it.
 */
export const FOUNDER = Object.freeze({
  "@type": "Person",
  "@id": "https://jasonzhu.ai/#person",
  name: "Jason Zhu",
  url: "https://jasonzhu.ai/en",
});

/** True for the founder's own name, so a guest author keeps a Person of their own. */
export const isFounder = (name) => /^\s*(jason\s*zhu|祝彦森)\s*$/i.test(name || "");
