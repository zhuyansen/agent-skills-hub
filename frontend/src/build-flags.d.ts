/** Build-time flags set by `define` in vite.config.ts. */

/** True once the first /stats/ issue exists; links to /stats/ render only then. */
declare const __STATS_LIVE__: boolean;

/** Guide slug -> how many tools its own test covers (scripts/scenario-runs.json), set by vite.config.ts. */
declare const __GUIDE_TESTED__: Record<string, number>;
