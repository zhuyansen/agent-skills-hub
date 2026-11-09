// Types for directoryEntries.mjs, a plain module so the Node page generators can import it too.
import type { Text } from "./proseContent.mjs";

/** One fact: `brief` goes in the comparison table, `more` follows it in the directory's section. */
export interface DirectoryFact {
  brief: Text;
  more?: Text;
}

export type DirectoryKind = "skills" | "mcp" | "official";

export interface DirectoryEntry {
  id: string;
  kind: DirectoryKind;
  domain: string;
  /** Where the table row links: an address on that site, or a path of this one. */
  home: string;
  heading: Text;
  /** The name under the address in the table, when the address is not the name. */
  tag?: Text;
  runBy: DirectoryFact;
  lists: DirectoryFact;
  size: DirectoryFact;
  security: DirectoryFact;
  ranking: DirectoryFact;
  listing: DirectoryFact;
  agents: DirectoryFact;
  openness: DirectoryFact;
  updates: DirectoryFact;
  languages: DirectoryFact;
  goodFor: Text;
  /** The pages read, as full addresses. */
  sources: readonly string[];
}

export declare const DIRECTORY_ENTRIES: readonly DirectoryEntry[];
