/**
 * Which /stats/ issues exist: the monthly snapshots committed under public/stats/data/
 * (ops/stats/monthly_snapshot.py). Generators that link to /stats/ ask this first, so no
 * page links to it before the first issue is built (2026-10-19). Paths are relative to
 * frontend/, where the build runs. vite.config.ts makes the same check for the app.
 */
import { existsSync, readdirSync } from "fs";
import { join } from "path";

export const STATS_DATA_DIR = join("public", "stats", "data");

/** Published periods (YYYY-MM), oldest first; empty until the first snapshot. */
export function statsPeriods() {
  if (!existsSync(STATS_DATA_DIR)) return [];
  return readdirSync(STATS_DATA_DIR)
    .filter((f) => /^\d{4}-\d{2}\.json$/.test(f))
    .map((f) => f.slice(0, 7))
    .sort();
}
