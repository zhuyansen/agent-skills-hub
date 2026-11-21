/**
 * The pages a /best/ page recommends: the "Related Categories" links and the page its
 * "what's the difference" question compares against (generate-scenario-pages.mjs), from the
 * `related` slugs in scenario-keywords.json.
 *
 * A live page recommends only live pages. A retired page is noindex, so a link to it earns
 * nothing, and ops/seo-watersystem-model.md takes a retired page out of the places that
 * recommend it. Until 2026-11-20 the list was shown as written: 25 of the 107 related links on
 * live pages led to a retired page (all three on /best/cli-tools/), while 14 live pages were
 * recommended by no other live page. A retired page keeps its list as written.
 */

/** The scenarios `scenario` recommends, in the order written; a slug with no page is skipped. */
export function relatedScenarios(scenario, allScenarios) {
  return (scenario.related || [])
    .map((slug) => allScenarios.find((s) => s.slug === slug))
    .filter((rel) => rel && rel.title && (scenario.retired || !rel.retired));
}
