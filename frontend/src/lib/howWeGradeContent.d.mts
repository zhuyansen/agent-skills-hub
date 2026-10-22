// Types for howWeGradeContent.mjs, a plain module so the Node page generators can import it too.
import type { HowWeGradeLang } from "./howWeGradeMeta.mjs";

/** `[english, chinese]`, or one string that reads the same in both languages. */
export type Text = string | readonly [en: string, zh: string];

export type InlineToken =
  | { kind: "text" | "strong" | "em" | "code" | "br"; text: string }
  | { kind: "link"; text: string; href: string };

export interface TableBlock {
  type: "table";
  /** Names the scrollable box around the table for screen readers. */
  label: Text;
  /** Narrower than this, the table scrolls inside its box instead of squeezing its columns. */
  minRem?: number;
  head: readonly Text[];
  rows: readonly (readonly Text[])[];
}

export type Block =
  | { type: "p"; text: Text }
  | { type: "h3"; text: Text }
  | { type: "ul"; items: readonly Text[] }
  | TableBlock;

export interface Section {
  id: string;
  title: Text;
  blocks: readonly Block[];
}

export interface HowWeGradePage {
  h1: Text;
  updated: Text;
  crumbs: { home: Text; here: Text };
  lead: readonly Block[];
  sections: readonly Section[];
}

export declare const CODE_BLOCKS: { notCounted: Text; limit: Text };
export declare const CLASSES: Readonly<
  Record<
    | "page"
    | "main"
    | "crumbs"
    | "crumbLink"
    | "crumbSep"
    | "crumbHere"
    | "header"
    | "h1"
    | "updated"
    | "article"
    | "section"
    | "list"
    | "tableWrap",
    string
  >
>;
export declare const HOW_WE_GRADE: HowWeGradePage;
export declare function pick(text: Text, lang: HowWeGradeLang): string;
export declare function inlineTokens(text: string): InlineToken[];
