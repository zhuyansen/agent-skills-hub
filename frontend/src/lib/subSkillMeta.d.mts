// Types for subSkillMeta.mjs, a plain module so the Node page generators can import it too.
export declare function subSkillTitle(repoFullName: string, name: string, description: string | null | undefined): string;
export declare function subSkillDescription(repoFullName: string, name: string, description: string | null | undefined): string;
export declare function subSkillPath(repoFullName: string, slug: string): string;
export declare function subSkillUrl(repoFullName: string, slug: string): string;
export declare function subSkillsJsonPath(repoFullName: string): string;
export declare function skillMdUrl(repoFullName: string, path: string): string;
export declare function githubFolderUrl(repoFullName: string, path: string): string;
export declare function subSkillInstall(repoFullName: string, name: string): string;
