import { useI18n } from "../i18n/I18nContext";

const steps = [
  {
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
      </svg>
    ),
    color: "text-blue-500 bg-blue-50 dark:bg-blue-900/30",
    titleKey: "guide.step1.title" as const,
    descKey: "guide.step1.desc" as const,
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
      </svg>
    ),
    color: "text-indigo-500 bg-indigo-50 dark:bg-indigo-900/30",
    titleKey: "guide.step2.title" as const,
    descKey: "guide.step2.desc" as const,
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6.75 7.5l3 2.25-3 2.25m4.5 0h3m-9 8.25h13.5A2.25 2.25 0 0021 18V6a2.25 2.25 0 00-2.25-2.25H5.25A2.25 2.25 0 003 6v12a2.25 2.25 0 002.25 2.25z" />
      </svg>
    ),
    color: "text-emerald-500 bg-emerald-50 dark:bg-emerald-900/30",
    titleKey: "guide.step3.title" as const,
    descKey: "guide.step3.desc" as const,
  },
];

export function InstallGuide() {
  const { t } = useI18n();

  return (
    <section className="mb-10">
      <div className="mb-6">
        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
          {t("guide.title")}
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t("guide.subtitle")}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {steps.map((step, idx) => (
          <div
            key={idx}
            className="relative bg-white dark:bg-gray-800/80 rounded-xl border border-gray-200 dark:border-gray-700 p-5 flex items-start gap-4"
          >
            {/* Step number */}
            <div className="absolute -top-2.5 -left-1 w-6 h-6 rounded-full bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 flex items-center justify-center text-xs font-bold">
              {idx + 1}
            </div>
            {/* Icon */}
            <div className={`w-11 h-11 rounded-lg ${step.color} flex items-center justify-center shrink-0`}>
              {step.icon}
            </div>
            {/* Text */}
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">
                {t(step.titleKey)}
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                {t(step.descKey)}
              </p>
            </div>
            {/* Arrow connector (not on last) */}
            {idx < steps.length - 1 && (
              <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-700 items-center justify-center">
                <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
