// Types for howWeGradeMeta.mjs, a plain module so the Node page generators can import it too.
export type HowWeGradeLang = "en" | "zh";

export interface HowWeGradePageMeta {
  title: string;
  description: string;
}

export declare const HOW_WE_GRADE_PATH: string;
export declare const HOW_WE_GRADE_URL: string;
export declare const GRADES_ANCHOR: string;
export declare const HOW_WE_GRADE_PUBLISHED: string;
export declare const HOW_WE_GRADE_UPDATED: string;
export declare const HOW_WE_GRADE_META: Readonly<Record<HowWeGradeLang, HowWeGradePageMeta>>;
export declare const HOW_WE_GRADE_LINK: Readonly<Record<HowWeGradeLang, string>>;
