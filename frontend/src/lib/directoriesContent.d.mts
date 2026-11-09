// Types for directoriesContent.mjs, a plain module so the Node page generators can import it too.
import type { DirectoryEntry } from "./directoryEntries.mjs";
import type { ProsePageText, Text } from "./proseContent.mjs";

export declare const TOTAL: string;
export declare const UNKNOWN_TOTAL: string;
export declare const ABOUT_HALF: Readonly<{ min: number; max: number }>;
export declare const FIELD_KEYS: readonly string[];
export declare const ORDERED_ENTRIES: readonly DirectoryEntry[];
export declare const SIZE_QUESTION: Text;
/** The whole page, with TOTAL where our catalog count goes. */
export declare const DIRECTORIES_TEXT: ProsePageText;
export declare function countText(n: number): string;
export declare function directoriesText(total: string): ProsePageText;
