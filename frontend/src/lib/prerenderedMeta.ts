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

let description: string | null = null;
let installs: string[] = [];
let path: string | null = null;

function parseInstalls(json: string | null): string[] {
  if (!json) return [];
  try {
    const value: unknown = JSON.parse(json);
    return Array.isArray(value) ? value.filter((v): v is string => typeof v === "string") : [];
  } catch {
    return [];
  }
}

/** Called once in main.tsx, before the static tags are removed. */
export function rememberPrerenderedPage(
  content: string | null,
  canonical: string | null,
  installJson: string | null = null,
): void {
  description = content;
  installs = parseInstalls(installJson);
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
