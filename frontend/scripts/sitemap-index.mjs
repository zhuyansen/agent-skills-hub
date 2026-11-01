/**
 * The sitemap index, dist/sitemap.xml. Each sub-sitemap's <lastmod> is the newest <lastmod> of
 * the URLs in it, so it moves only when one of them changed; a sub-sitemap whose URLs carry no
 * date gets none. Until 2026-11-01 every line carried the build date on every build, the same
 * noise the URL-level dates stopped making on 2026-10-14, and the kind that teaches Google to
 * ignore our lastmod (Search Central, "Build and submit a sitemap").
 */

const LASTMOD = /<lastmod>(\d{4}-\d{2}-\d{2})/g;

/** The newest date in a sub-sitemap's <lastmod> tags, or null when it has none. */
export function newestLastmod(xml) {
  const dates = [...xml.matchAll(LASTMOD)].map((m) => m[1]);
  return dates.sort().at(-1) ?? null;
}

/** The index for `files` (sub-sitemap names under `site`); `read(file)` returns one's XML. */
export function buildSitemapIndex(site, files, read) {
  const entries = files.map((file) => {
    const date = newestLastmod(read(file));
    const lastmod = date ? `\n    <lastmod>${date}</lastmod>` : "";
    return `  <sitemap>\n    <loc>${site}/${file}</loc>${lastmod}\n  </sitemap>`;
  });
  return `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${entries.join("\n")}
</sitemapindex>`;
}
