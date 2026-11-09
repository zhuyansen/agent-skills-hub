// Types for proseContent.mjs, a plain module so the Node page generators can import it too.
export type Lang = "en" | "zh";

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
  /** On large screens the table's box widens into the page margins (CLASSES.tableWide). */
  wide?: boolean;
  head: readonly Text[];
  rows: readonly (readonly Text[])[];
}

/** A boxed note under a bold title, such as a disclosure. */
export interface NoteBlock {
  type: "note";
  title: Text;
  items: readonly Text[];
}

export type Block =
  | { type: "p"; text: Text }
  | { type: "h3"; text: Text; id?: string }
  | { type: "ul"; items: readonly Text[] }
  | NoteBlock
  | TableBlock;

export interface Section {
  id: string;
  title: Text;
  blocks: readonly Block[];
}

/** A page's whole text: the heading, the label before its date, the breadcrumbs, the opening blocks and the sections. */
export interface ProsePageText {
  h1: Text;
  updated: Text;
  crumbs: { home: Text; here: Text };
  lead: readonly Block[];
  sections: readonly Section[];
}

export type LinkKind = "route" | "page" | "external";

export declare const SITE_ORIGIN: string;
export declare const EXTERNAL_REL: string;
export declare const NOFOLLOW_REL: string;
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
    | "tableWrap"
    | "tableWide"
    | "anchor"
    | "note",
    string
  >
>;
export declare function pick(text: Text, lang: Lang): string;
export declare function inlineTokens(text: string): InlineToken[];
export declare function linkKind(href: string): LinkKind;
