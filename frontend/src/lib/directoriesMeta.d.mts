// Types for directoriesMeta.mjs, a plain module so the Node page generators can import it too.
import type { Lang } from "./proseContent.mjs";

export interface DirectoriesPageMeta {
  title: string;
  description: string;
}

export declare const DIRECTORIES_PATH: string;
export declare const DIRECTORIES_URL: string;
export declare const COMPARED_COUNT: number;
export declare const FACTS_READ_ON: string;
export declare const DIRECTORIES_PUBLISHED: string;
export declare const DIRECTORIES_UPDATED: string;
export declare const DIRECTORIES_HEADLINE: Readonly<Record<Lang, string>>;
export declare const DIRECTORIES_META: Readonly<Record<Lang, DirectoriesPageMeta>>;
export declare const DIRECTORIES_LINK: Readonly<Record<Lang, string>>;
