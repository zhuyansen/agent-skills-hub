/**
 * Which other pages a /skill/ or /audit/ page links to, beyond the most-starred repos of its
 * category. Until 2026-11 every page of a category linked the same top-10 (/skill/) or top-6
 * (/audit/) repos, so most pages had no internal link from anywhere but their category list,
 * and that list stops at 100. Eli Schwartz, Product-Led SEO (pp. 129–132): keep some popular
 * links, and spread the rest over the whole set with a random block and a recently-added block.
 *
 * Random picks are seeded by the build day and the page, so builds on the same day write the
 * same links (the site rebuilds three or more times a day) and the set changes every day. They
 * come off a hash ring: each candidate sits at hash(day, name), and a pick takes the next
 * candidate clockwise from a point drawn for the page. A page added or dropped between two builds
 * of the same day only moves the picks that landed next to it, where an index into a sorted list
 * would shift every pick after it.
 *
 * Test: node --test scripts/related-links.test.mjs
 */

/** How many links each block shows on a /skill/ page and on an /audit/ page. */
export const SKILL_LINKS = { popular: 5, language: 3, random: 8, recent: 5 };
export const AUDIT_LINKS = { popular: 3, random: 6, recent: 4 };

/** How many recently added pages each category keeps, so a page can skip itself and repeats. */
const RECENT_POOL = 20;

/** The build day (UTC, YYYY-MM-DD). ASH_BUILD_DATE pins it for a reproducible rebuild. */
export function buildDay(env = process.env, now = new Date()) {
  const pinned = env.ASH_BUILD_DATE;
  if (pinned && /^\d{4}-\d{2}-\d{2}$/.test(pinned)) return pinned;
  return now.toISOString().slice(0, 10);
}

/** FNV-1a, 32 bits: a stable hash of a string. */
export function hash32(text) {
  let h = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h >>> 0;
}

/** mulberry32: a small seeded generator of 32-bit integers. */
export function seeded(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return (t ^ (t >>> 14)) >>> 0;
  };
}

/** The day's ring of candidates: [{ key, item }] sorted by key. `nameOf(item)` names each one. */
export function linkRing(items, day, nameOf) {
  return items
    .map((item) => ({ key: hash32(`${day}|${nameOf(item)}`), item }))
    .sort((a, b) => a.key - b.key);
}

/** Index of the first ring entry whose key is >= point (wraps to 0). */
function successor(ring, point) {
  let lo = 0;
  let hi = ring.length;
  while (lo < hi) {
    const mid = (lo + hi) >>> 1;
    if (ring[mid].key < point) lo = mid + 1;
    else hi = mid;
  }
  return lo % ring.length;
}

/**
 * `n` items off the ring for one page. `skip(item)` rejects an item (the page itself, a link the
 * page already has); a rejected or repeated pick moves on clockwise.
 */
export function randomPicks(ring, day, pageName, n, skip = () => false) {
  const picks = [];
  if (!ring.length || n <= 0) return picks;
  const next = seeded(hash32(`${day}#${pageName}`));
  const taken = new Set();
  for (let draw = 0; picks.length < n && draw < n * 4; draw++) {
    let at = successor(ring, next());
    for (let step = 0; step < ring.length; step++, at = (at + 1) % ring.length) {
      const { item } = ring[at];
      if (taken.has(item) || skip(item)) continue;
      taken.add(item);
      picks.push(item);
      break;
    }
  }
  return picks;
}

/**
 * Category -> its most recently added items, newest first. `id` is the catalog's primary key,
 * given on first insert, so a higher id is a repo the catalog took in later.
 */
export function recentByCategory(items, poolSize = RECENT_POOL) {
  const byCat = new Map();
  for (const item of [...items].sort((a, b) => (b.id || 0) - (a.id || 0))) {
    const key = item.category || "other";
    const list = byCat.get(key) || [];
    if (list.length < poolSize) list.push(item);
    byCat.set(key, list);
  }
  return byCat;
}

/** The first `n` of `pool` that `skip` does not reject. */
export function firstPicks(pool, n, skip = () => false) {
  const out = [];
  for (const item of pool || []) {
    if (out.length >= n) break;
    if (!skip(item)) out.push(item);
  }
  return out;
}
