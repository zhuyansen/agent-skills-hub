// The catalog's exact counts as of the last build, which scripts/home-counts.mjs writes into
// index.html's <script id="catalog-counts">: every row, and the rows in each category. The hero
// paints these until the stats arrive, so its first paint has as many digits as the live
// numbers and nothing moves when they land. The page has none on the dev server, or when that
// build step failed; the slot then holds "{}".

export interface CatalogCounts {
  total: number;
  categories: Record<string, number>;
}

const SLOT_ID = "catalog-counts";

const isRecord = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);

function isCatalogCounts(v: unknown): v is CatalogCounts {
  if (!isRecord(v) || typeof v.total !== "number" || !isRecord(v.categories)) return false;
  return Object.values(v.categories).every((n) => typeof n === "number");
}

/** The counts the page carries, or null when it has none. */
export function readCatalogCounts(): CatalogCounts | null {
  const json = typeof document === "undefined" ? null : document.getElementById(SLOT_ID)?.textContent;
  if (!json) return null;
  try {
    const value: unknown = JSON.parse(json);
    return isCatalogCounts(value) ? value : null;
  } catch {
    return null;
  }
}
