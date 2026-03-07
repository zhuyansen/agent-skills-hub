import { useI18n } from "../i18n/I18nContext";
import { platforms } from "../data/platforms";

const iconPaths: Record<string, string> = {
  globe: "M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418",
  search: "M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z",
  store: "M13.5 21v-7.5a.75.75 0 01.75-.75h3a.75.75 0 01.75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349m-16.5 11.65V9.35m0 0a3.001 3.001 0 003.75-.615A2.993 2.993 0 009.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 002.25 1.016c.896 0 1.7-.393 2.25-1.016A3.001 3.001 0 0021 9.349m-18 0a2.999 2.999 0 00.621-1.657L4.25 3.5h15.5l.629 4.192a3 3 0 00.621 1.657",
};

export function PlatformRecommendations() {
  const { t, lang } = useI18n();

  return (
    <section className="mb-10">
      <div className="mb-4">
        <h2 className="text-lg font-bold text-gray-900">{t("platforms.title")}</h2>
        <p className="text-sm text-gray-500 mt-1">{t("platforms.subtitle")}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        {platforms.map((p) => (
          <a
            key={p.name}
            href={p.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex flex-col items-center text-center p-5 bg-white rounded-xl border border-gray-200 hover:shadow-lg hover:border-blue-200 hover:-translate-y-0.5 transition-all group"
          >
            <svg className="w-8 h-8 mb-3 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d={iconPaths[p.icon] || iconPaths.globe}/></svg>
            <h3 className="font-semibold text-gray-900 text-sm group-hover:text-blue-600 transition-colors">
              {p.name}
            </h3>
            <p className="text-xs text-gray-500 mt-1">
              {lang === "zh" ? p.description_zh : p.description_en}
            </p>
            <span className="mt-3 text-xs text-blue-500 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
              {lang === "zh" ? "访问" : "Visit"}
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </span>
          </a>
        ))}
      </div>
    </section>
  );
}
