// The <meta name="description"> a pre-rendered page shipped with. main.tsx removes it so
// Helmet owns the tag, but on a direct load of a /skill/ page it is the exact description
// the static generator wrote, including the install command it found in the README, which
// the React page never sees. Googlebot loads every URL fresh, so reusing it gives Google one
// description per page instead of two.
//
// The same page also carries the README's install lines (<meta name="ash:install">, a JSON
// list). The React page does not load the README, so on a direct load this is the only way
// it can show a real command instead of a generic one (2026-10-21: a maintainer reported the
// guessed `mcp-remote` command, which pointed at the GitHub page and could never run).

//
// And the end-to-end tests the skill was in (<meta name="ash:tested">, scripts/skill-tested.mjs),
// which the React page has no other way to know.
//
// And the /best/ guides that list the skill (<meta name="ash:best">, scripts/skill-guides.mjs).

import type { Pair, TestedEntry } from "./testedCopy.mjs";

/** A /best/ guide the skill is listed on. */
export interface GuideLink {
  slug: string;
  title: string;
  titleZh: string;
}

let description: string | null = null;
let installs: string[] = [];
let tested: TestedEntry[] = [];
let guides: GuideLink[] = [];
let path: string | null = null;
let shell: string | null = null;

function parseList(json: string | null): unknown[] {
  if (!json) return [];
  try {
    const value: unknown = JSON.parse(json);
    return Array.isArray(value) ? value : [];
  } catch {
    return [];
  }
}

const isRecord = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null;
const isPair = (v: unknown): v is Pair => Array.isArray(v) && v.length === 2 && v.every((x) => typeof x === "string");
const isPick = (v: unknown) => v === null || (isRecord(v) && isPair(v.role) && isPair(v.why));
const isTop = (v: unknown) => v === null || (isRecord(v) && typeof v.place === "number" && isPair(v.title));
const isEvidence = (v: unknown) =>
  isRecord(v) && typeof v.href === "string" && typeof v.image === "boolean" && isPair(v.label);

function isTestedEntry(v: unknown): v is TestedEntry {
  return isRecord(v) && typeof v.page === "string" && isPair(v.pageTitle) && typeof v.date === "string"
    && typeof v.tested === "number" && Array.isArray(v.bits) && v.bits.every(isPair)
    && isPick(v.pick) && isTop(v.top) && isEvidence(v.evidence);
}

// A slug that is safe to put in a /best/<slug>/ link.
const SLUG = /^[a-z0-9][a-z0-9-]*$/;

function isGuideLink(v: unknown): v is GuideLink {
  return isRecord(v) && typeof v.slug === "string" && SLUG.test(v.slug)
    && typeof v.title === "string" && typeof v.titleZh === "string";
}

/** Called once in main.tsx, before the static tags are removed. */
export function rememberPrerenderedPage(
  content: string | null,
  canonical: string | null,
  installJson: string | null = null,
  testedJson: string | null = null,
  shellHtml: string | null = null,
  guidesJson: string | null = null,
): void {
  description = content;
  shell = shellHtml;
  installs = parseList(installJson).filter((v): v is string => typeof v === "string");
  tested = parseList(testedJson).filter(isTestedEntry);
  guides = parseList(guidesJson).filter(isGuideLink);
  // Only a page that names itself as canonical is pre-rendered for that URL. The 404.html
  // fallback boots index.html, whose description belongs to the homepage.
  path = canonical ? new URL(canonical, window.location.origin).pathname : null;
}

const onPrerenderedPage = () => path !== null && path === window.location.pathname;

/** The pre-rendered description while the browser is still on that page, else null. */
export function prerenderedDescription(): string | null {
  return onPrerenderedPage() ? description : null;
}

/** The README install lines of the pre-rendered page while the browser is on it, else []. */
export function prerenderedInstalls(): string[] {
  return onPrerenderedPage() ? installs : [];
}

/** The tests the pre-rendered page's skill was in while the browser is on it, else []. */
export function prerenderedTested(): TestedEntry[] {
  return onPrerenderedPage() ? tested : [];
}

/** The /best/ guides that list the pre-rendered page's skill while the browser is on it, else []. */
export function prerenderedGuides(): GuideLink[] {
  return onPrerenderedPage() ? guides : [];
}

/** The pre-rendered page body (#root before React mounted) while the browser is on that
 *  page, else null. A skill page whose data request fails shows this instead of an error,
 *  so a crawler that hits the failure still gets the full static page. */
export function prerenderedShell(): string | null {
  return onPrerenderedPage() ? shell : null;
}
