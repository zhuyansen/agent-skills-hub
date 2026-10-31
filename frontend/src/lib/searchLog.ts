/**
 * Shadow record of what visitors search for (supabase migration 043). Each
 * settled search a visitor typed is sent once to log_site_search(); nothing on
 * the site reads the table back. It is reviewed offline to find terms that
 * return nothing, and is not shown or mailed anywhere until that review.
 */
import { supabase } from "./supabase";

export type SearchSurface = "list" | "suggest";

const RECORD_HOSTS = new Set(["agentskillshub.top", "www.agentskillshub.top"]);
const SETTLE_MS = 2000; // no newer search for this long = the visitor stopped typing
const MAX_TERM_LENGTH = 100; // log_site_search drops longer terms too
const MAX_SENDS_PER_PAGE = 30; // the RPC also caps each IP per day
const EMAIL_SHAPE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const latest: Record<SearchSurface, number> = { list: 0, suggest: 0 };
const pending: Partial<Record<SearchSurface, ReturnType<typeof setTimeout>>> = {};
const sent = new Set<string>();
// Searches loaded from a URL (crawlers, old indexed links) are not typed ones.
let typed = false;

if (typeof window !== "undefined") {
  window.addEventListener(
    "input",
    () => {
      typed = true;
    },
    { capture: true, once: true },
  );
}

function normalize(raw: string): string | null {
  const term = raw.trim().replace(/\s+/g, " ").toLowerCase();
  if (!term || term.length > MAX_TERM_LENGTH || EMAIL_SHAPE.test(term)) return null;
  return term;
}

function canRecord(): boolean {
  return (
    typed &&
    !navigator.webdriver &&
    RECORD_HOSTS.has(window.location.hostname) &&
    sent.size < MAX_SENDS_PER_PAGE
  );
}

function send(surface: SearchSurface, term: string, results: number): void {
  const key = `${surface}:${term}`;
  if (!supabase || sent.has(key)) return;
  sent.add(key);
  // Fire and forget: a failed shadow write must never reach the visitor.
  supabase
    .rpc("log_site_search", { p_term: term, p_results: results, p_surface: surface })
    .then(
      () => undefined,
      () => undefined,
    );
}

/**
 * Note a search that has just started; `results` resolves to how many it
 * found. Only the newest search on each surface counts, and only after
 * SETTLE_MS without another one, so the keystrokes of one word make one row.
 */
export function trackSearch(
  surface: SearchSurface,
  raw: string,
  results: Promise<number>,
): void {
  const seq = ++latest[surface];
  clearTimeout(pending[surface]);
  results.then(
    (count) => {
      const term = normalize(raw);
      if (seq !== latest[surface] || !term || !canRecord()) return;
      pending[surface] = setTimeout(() => send(surface, term, count), SETTLE_MS);
    },
    () => undefined,
  );
}
