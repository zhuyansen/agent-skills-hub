// Types for skillMeta.mjs, a plain module so the Node page generators can import it too.
export declare const TITLE_MAX_WIDTH: number;
export declare const HEADING_MAX_WIDTH: number;
export declare const TITLE_FALLBACK: string;
export declare const DESCRIPTION_LIMIT: number;
export declare const DESCRIPTION_MIN_WIDTH: number;
export declare function displayWidth(text: string): number;
export declare function cleanDescription(description: string | null | undefined, repoName: string | null | undefined): string;
export declare function fitClause(clause: string, budget: number): string;
export declare function fitName(name: string, budget: number): string;
export declare function skillTitle(
  repoFullName: string,
  repoName: string,
  description: string | null | undefined,
  fallback?: string,
): string;
export declare function fallbackTitle(head: string, fallback?: string): string;
export declare function headingClause(repoName: string, description: string | null | undefined): string;
export declare function brandedHeading(
  repoFullName: string,
  repoName: string,
  description: string | null | undefined,
): string | null;
export declare function skillDescription(
  repoName: string,
  description: string | null | undefined,
  installs?: string[],
  meta?: { grade?: string | null; quality?: number | null },
): string;
