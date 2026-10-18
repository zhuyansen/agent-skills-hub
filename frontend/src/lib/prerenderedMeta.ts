// The <meta name="description"> a pre-rendered page shipped with. main.tsx removes it so
// Helmet owns the tag, but on a direct load of a /skill/ page it is the exact description
// the static generator wrote, including the install command it found in the README, which
// the React page never sees. Googlebot loads every URL fresh, so reusing it gives Google one
// description per page instead of two.

let description: string | null = null;
let path: string | null = null;

/** Called once in main.tsx, before the static tag is removed. */
export function rememberPrerenderedPage(content: string | null, canonical: string | null): void {
  description = content;
  // Only a page that names itself as canonical is pre-rendered for that URL. The 404.html
  // fallback boots index.html, whose description belongs to the homepage.
  path = canonical ? new URL(canonical, window.location.origin).pathname : null;
}

/** The pre-rendered description while the browser is still on that page, else null. */
export function prerenderedDescription(): string | null {
  return path !== null && path === window.location.pathname ? description : null;
}
