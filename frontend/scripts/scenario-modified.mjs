/**
 * When each /best/ page's content last changed: the lastmod its sitemap entries carry.
 *
 * Scenario pages used to be dated by lastReviewed, the day someone last reviewed one by
 * hand. Neither the daily review's new cards nor title or FAQ edits moved it:
 * /best/anti-slop/ still said 2026-10-07 after its 10-31 retitle (found 11-01), and
 * Google uses lastmod only while it stays accurate. Now each build fingerprints what a
 * reader sees on a page and compares it with the fingerprints the live site published
 * at /best/modified.json. A page whose fingerprint changed is dated that day; the
 * others keep their date.
 */
import { createHash } from "crypto";

export const MODIFIED_PATH = "/best/modified.json";
const FETCH_TRIES = 3;
const FETCH_TIMEOUT_MS = 10_000;
const RETRY_DELAY_MS = 2_000;
const DECLARED_DATE = /"(?:dateModified|lastReviewed)"\s*:\s*"(\d{4}-\d{2}-\d{2})/g;

/** JSON with object keys sorted at every level, so equal content always hashes equal. */
function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  if (value && typeof value === "object") {
    const keys = Object.keys(value).filter((k) => value[k] !== undefined).sort();
    return `{${keys.map((k) => `${JSON.stringify(k)}:${stableJson(value[k])}`).join(",")}}`;
  }
  return JSON.stringify(value ?? null);
}

/** A short hash of a page's reader-visible parts. */
export function fingerprint(parts) {
  return createHash("sha256").update(stableJson(parts)).digest("hex").slice(0, 16);
}

/**
 * The latest dateModified or lastReviewed a built page declares in its JSON-LD, or
 * null. The build date is dropped: the SPA shell stamps it on every page, and a date
 * that is always today tells Google our lastmod is noise (2026-10-14).
 */
export function declaredDateIn(html, today) {
  const dates = [...html.matchAll(DECLARED_DATE)].map((m) => m[1]).filter((d) => d !== today);
  return dates.sort().at(-1) || null;
}

/**
 * The next {slug: {fp, date}}. A page keeps its date while its fingerprint holds, and
 * is dated `today` when the fingerprint changes or the page first appears. With no
 * live file at all (the first build, or the site unreadable) every page starts from
 * `seed(slug)`, the date it declared before, so this moves no lastmod on its own.
 */
export function nextModified(live, fps, today, seed) {
  const pages = {};
  for (const [slug, fp] of Object.entries(fps)) {
    const was = live?.[slug];
    pages[slug] = was?.fp === fp ? was : { fp, date: live ? today : seed(slug) };
  }
  return pages;
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/** The pages the live site last published, or null when it has none or can't be read. */
export async function loadLiveModified(site, fetchImpl = fetch, wait = sleep) {
  const url = `${site}${MODIFIED_PATH}?t=${Date.now()}`; // past the Pages CDN cache
  for (let attempt = 1; attempt <= FETCH_TRIES; attempt++) {
    try {
      const res = await fetchImpl(url, { signal: AbortSignal.timeout(FETCH_TIMEOUT_MS) });
      if (res.status === 404) return null;
      if (res.ok) return (await res.json()).pages ?? null;
    } catch {
      // network error or timeout: try again below
    }
    if (attempt < FETCH_TRIES) await wait(RETRY_DELAY_MS);
  }
  console.warn(`${MODIFIED_PATH}: live copy unreadable, /best/ pages keep their declared dates`);
  return null;
}
