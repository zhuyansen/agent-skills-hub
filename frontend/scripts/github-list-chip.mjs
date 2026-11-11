/**
 * The chip on a /best/ guide that opens its open-source list on GitHub (scenario.github_list).
 * It leads the row and asks for a star, with the list's star count, once the list has enough
 * stars for the number to help: on 2026-11-12 the video guide took about 1,890 engaged
 * sessions a month from GitHub while its list (1,907 stars) was the fourth chip, without a count.
 */
import { esc, starsK } from "./shared-utils.mjs";

/** Below this a count would not persuade anyone; the chip then just names the list. */
export const MIN_STARS_SHOWN = 100;
const STYLE = "text-decoration:none;color:var(--bp-link);border-color:var(--bp-border-accent)";

/** The list's stars as the catalog has them; 0 when the list is not in the catalog. */
export function listStars(url, allSkills) {
  const name = url.replace(/^https:\/\/github\.com\//, "").replace(/\/$/, "").toLowerCase();
  return allSkills.find((s) => (s.repo_full_name || "").toLowerCase() === name)?.stars || 0;
}

/** [English, Chinese] label for a list with that many stars. */
export function chipLabel(stars) {
  if (stars < MIN_STARS_SHOWN) return ["⭐ Open-source list on GitHub ↗", "⭐ GitHub 上的开源合集 ↗"];
  return [`⭐ Star the list on GitHub · ${starsK(stars)} ↗`, `⭐ 去 GitHub 给合集点星 · ${starsK(stars)} ↗`];
}

/** The chip's HTML; "" for a guide without a list. */
export function githubListChip(scenario, allSkills) {
  if (!scenario.github_list) return "";
  const [en, zh] = chipLabel(listStars(scenario.github_list, allSkills));
  return `<a class="bp-stat-chip" href="${esc(scenario.github_list)}" target="_blank" rel="noopener" style="${STYLE}" data-zh="${esc(zh)}" data-en="${esc(en)}">${esc(en)}</a>`;
}
