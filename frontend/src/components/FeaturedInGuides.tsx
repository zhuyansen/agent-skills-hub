import { useI18n } from "../i18n/I18nContext";
import { prerenderedGuides } from "../lib/prerenderedMeta";

// The static page's wording (scripts/skill-page-copy.mjs, featuredIn).
const LABEL = { en: "Featured in:", zh: "入选精选页：" } as const;

/** "Featured in": the /best/ guides that list this skill, as on the static page
 *  (scripts/skill-guides.mjs). They come with the pre-rendered page, so a direct load (Google's)
 *  shows them. Plain links: /best/ pages are static, outside the app's router. */
export function FeaturedInGuides() {
  const { lang } = useI18n();
  const guides = prerenderedGuides();
  if (!guides.length) return null;
  const zh = lang === "zh";
  return (
    <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
      {zh ? LABEL.zh : `${LABEL.en} `}
      {guides.map((g, i) => (
        <span key={g.slug}>
          {i > 0 && " · "}
          <a href={`/best/${g.slug}/`} className="text-indigo-600 dark:text-indigo-400 hover:underline">
            {zh ? g.titleZh : g.title}
          </a>
        </span>
      ))}
    </p>
  );
}
