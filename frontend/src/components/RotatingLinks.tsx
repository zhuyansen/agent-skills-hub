import { Link } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";
import { prerenderedRelated, type RelatedLink } from "../lib/prerenderedMeta";

// The static page's wording (scripts/skill-page-copy.mjs: recentTitle, randomTitle).
const TITLES = {
  en: { recent: "Recently added", random: "More from the catalog" },
  zh: { recent: "最近收录", random: "从目录里再看看" },
} as const;

const formatStars = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n));

function LinkList({ title, links }: { title: string; links: RelatedLink[] }) {
  if (!links.length) return null;
  return (
    <div>
      <h3 className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-3">{title}</h3>
      <ul className="space-y-1.5">
        {links.map(([slug, name, stars]) => (
          <li key={slug} className="text-sm">
            <Link to={`/skill/${slug}/`} className="text-indigo-600 dark:text-indigo-400 hover:underline">
              {name}
            </Link>
            <span className="text-xs text-gray-400 dark:text-gray-500"> ⭐ {formatStars(stars)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** The recently added and random skill pages of the static page, so the React page (the one Google
 *  indexes) links them too. They come with a direct load of the page; after an in-app navigation
 *  there are none, and the block is not shown. */
export function RotatingLinks() {
  const { lang } = useI18n();
  const { recent, random } = prerenderedRelated();
  if (!recent.length && !random.length) return null;
  const t = lang === "zh" ? TITLES.zh : TITLES.en;
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-5 mb-6 grid grid-cols-1 sm:grid-cols-2 gap-6">
      <LinkList title={t.recent} links={recent} />
      <LinkList title={t.random} links={random} />
    </div>
  );
}
