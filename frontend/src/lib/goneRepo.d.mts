export type RetargetKind = "mirror" | "substitute" | null;

export interface GoneCopyResult {
  kind: RetargetKind;
  targetSlug: string | null;
  headingEn: string;
  headingZh: string;
  bodyEn: string;
  bodyZh: string;
}

export function retargetedSlug(repoFullName: string, repoUrl?: string | null): string | null;
export function retargetKind(repoFullName: string, repoUrl?: string | null): RetargetKind;
export function rewriteMirrorCommand(
  command: string,
  originalFullName: string,
  mirrorFullName: string,
): string;
export function goneCopy(repoFullName: string, repoUrl?: string | null): GoneCopyResult;
