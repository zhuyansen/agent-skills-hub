/**
 * Three helpers for the site search, from the search shadow log (site_searches,
 * migration 043; 1,661 searches 10-31 → 11-17):
 *
 * - githubRepoFromInput: visitors paste a GitHub URL into the box. The URL found
 *   nothing ("https:* & github:* & com:* …" matches no row); the repo's own
 *   owner/repo does.
 * - correctTerm: 5.8% of searches found nothing, mostly typos (viideo, yutube,
 *   motion gra[hics, website dvelopement). When a search comes back empty, each
 *   unknown word is replaced by the closest known word, and the search reruns.
 * - scenarioForTerm: "video" was the most searched term (99), and the reviewed
 *   /best/claude-video-skills/ page was never offered to those visitors.
 */

const GITHUB_REPO =
  /^(?:https?:\/\/)?(?:www\.)?github\.com[/:]([A-Za-z0-9-]+)\/([A-Za-z0-9._-]+?)(?:\.git)?(?:[/?#].*)?$/i;
const GIT_SSH = /^git@github\.com:([A-Za-z0-9-]+)\/([A-Za-z0-9._-]+?)(?:\.git)?$/i;

/** "https://github.com/o/r/tree/main" → "o/r"; anything else → null. */
export function githubRepoFromInput(input) {
  const s = String(input ?? "").trim();
  const m = s.match(GITHUB_REPO) || s.match(GIT_SSH);
  return m ? `${m[1]}/${m[2]}` : null;
}

/** Lowercase, trimmed, single spaces: the form both lookup tables use. */
export function normalizeTerm(term) {
  return String(term ?? "").trim().toLowerCase().replace(/\s+/g, " ");
}

/** Optimal string alignment distance (Damerau–Levenshtein with adjacent swaps), capped. */
function distance(a, b, cap) {
  if (Math.abs(a.length - b.length) > cap) return cap + 1;
  const prev2 = new Array(b.length + 1).fill(0);
  let prev = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    let rowMin = i;
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      let v = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
        v = Math.min(v, prev2[j - 2] + 1);
      }
      cur[j] = v;
      rowMin = Math.min(rowMin, v);
    }
    if (rowMin > cap) return cap + 1;
    for (let j = 0; j <= b.length; j++) prev2[j] = prev[j];
    prev = cur;
  }
  return prev[b.length];
}

/** Edits a word may need: none under 4 letters (too many near neighbours), one up to 6, two after. */
function allowedEdits(word) {
  if (word.length < 4) return 0;
  return word.length <= 6 ? 1 : 2;
}

/**
 * The term with each unknown Latin word replaced by its closest known word, or
 * null when nothing changes. `vocab` is ordered most common first, which breaks ties.
 * Words with digits and non-Latin words are left as typed.
 */
export function correctTerm(term, vocab) {
  const words = normalizeTerm(term).split(" ").filter(Boolean);
  if (!words.length) return null;
  const known = new Set(vocab);
  let changed = false;
  const out = words.map((word) => {
    if (known.has(word) || /\d/.test(word) || !/^[a-z][\x21-\x7e]*$/.test(word)) return word;
    const cap = allowedEdits(word);
    if (!cap) return word;
    let best = null;
    let bestD = cap + 1;
    for (const cand of vocab) {
      const d = distance(word, cand, cap);
      if (d < bestD) {
        best = cand;
        bestD = d;
        if (d === 1) break;
      }
    }
    if (!best) return word;
    changed = true;
    return best;
  });
  return changed ? out.join(" ") : null;
}

/** The scenario page a search term asks for, from `{ term: scenario }`, or null. */
export function scenarioForTerm(term, table) {
  const t = normalizeTerm(term);
  if (!t) return null;
  if (table[t]) return table[t];
  // "video skills for claude" → "video skills"; a term's last word dropped one at a time.
  const words = t.split(" ");
  for (let n = words.length - 1; n >= 1; n--) {
    const head = words.slice(0, n).join(" ");
    if (table[head]) return table[head];
  }
  return null;
}
