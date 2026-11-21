// Types for authorMeta.mjs, a plain module so the Node page generators can import it too.
export declare function countNoun(count: number, one: string, many: string): string;
export declare const THIN_AUTHOR_MAX_SKILLS: number;
export declare function authorIndexable(
  skillCount: number,
  master?: { bio?: string | null; is_verified?: boolean | null } | null,
): boolean;
export declare function authorTitle(displayName: string, total: number, safeCount: number): string;
export declare function authorDescription(
  displayName: string,
  total: number,
  safeCount: number,
  totalStars?: number,
): string;
