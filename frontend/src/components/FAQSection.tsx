import { useState } from "react";
import { Helmet } from "react-helmet-async";
import { useI18n } from "../i18n/I18nContext";

const FAQ_KEYS = [
  { q: "faq.q1", a: "faq.a1" },
  { q: "faq.q2", a: "faq.a2" },
  { q: "faq.q3", a: "faq.a3" },
  { q: "faq.q4", a: "faq.a4" },
  { q: "faq.q5", a: "faq.a5" },
] as const;

export function FAQSection() {
  const { t } = useI18n();
  const [openIdx, setOpenIdx] = useState<number | null>(null);

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: FAQ_KEYS.map((item) => ({
      "@type": "Question",
      name: t(item.q as any),
      acceptedAnswer: {
        "@type": "Answer",
        text: t(item.a as any),
      },
    })),
  };

  return (
    <section className="mb-10">
      <Helmet>
        <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
      </Helmet>

      <div className="flex items-center gap-2 mb-4">
        <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h2 className="text-lg font-bold text-gray-900">{t("faq.title")}</h2>
      </div>

      <div className="space-y-2">
        {FAQ_KEYS.map((item, i) => (
          <div key={i} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <button
              onClick={() => setOpenIdx(openIdx === i ? null : i)}
              className="w-full px-4 py-3 text-left text-sm font-medium text-gray-800 flex items-center justify-between hover:bg-gray-50 transition-colors cursor-pointer"
            >
              <span>{t(item.q as any)}</span>
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform ${openIdx === i ? "rotate-180" : ""}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {openIdx === i && (
              <div className="px-4 pb-3 text-sm text-gray-600 leading-relaxed border-t border-gray-100 pt-2">
                {t(item.a as any)}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
