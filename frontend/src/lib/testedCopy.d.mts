// Types for testedCopy.mjs, a plain module so the Node page generators can import it too.
export type Pair = [string, string];

/** One end-to-end test a skill was in (scripts/skill-tested.mjs writes these). */
export interface TestedEntry {
  page: string;
  pageTitle: Pair;
  date: string;
  tested: number;
  bits: Pair[];
  pick: { role: Pair; why: Pair } | null;
  top: { place: number; title: Pair; ranked?: boolean } | null;
  /** `shot` is what the tool made, at the size to show it; null when the test left no picture. */
  evidence: { href: string; image: boolean; shot?: { src: string; w: number; h: number } | null; label: Pair };
}

export declare const TESTED_TITLE: Pair;
export declare const TESTED_SEE_ALL: Pair;
export declare const TESTED_IMAGE_ALT: Pair;
export declare function testedIntro(e: TestedEntry): Pair;
export declare function testedTop(e: TestedEntry): Pair | null;
export declare function testedPick(e: TestedEntry): Pair | null;
export declare function testedResult(e: TestedEntry): Pair;
