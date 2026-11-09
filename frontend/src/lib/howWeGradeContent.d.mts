// Types for howWeGradeContent.mjs, a plain module so the Node page generators can import it too.
import type { ProsePageText, TableBlock, Text } from "./proseContent.mjs";

export type HowWeGradePage = ProsePageText;

export declare const CODE_BLOCKS: { notCounted: Text; limit: Text };
export declare const QUALITY_WEIGHTS: TableBlock;
export declare const HOW_WE_GRADE: HowWeGradePage;
