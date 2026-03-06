import { useI18n } from "../i18n/I18nContext";
import { workflows } from "../data/workflows";

const iconPaths: Record<string, string> = {
  share: "M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z",
  book: "M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25",
  wrench: "M11.42 15.17l-5.384 5.384a1.522 1.522 0 01-2.153-2.153l5.384-5.384m2.153 2.153l5.384-5.384a1.522 1.522 0 00-2.153-2.153L9.267 12.95m2.153 2.22a3.015 3.015 0 004.276 0 3.015 3.015 0 000-4.276",
};

export function SkillWorkflows() {
  const { t, lang } = useI18n();

  return (
    <section className="mt-10">
      <div className="mb-6">
        <h2 className="text-lg font-bold text-gray-900">{t("workflows.title")}</h2>
        <p className="text-sm text-gray-500 mt-1">{t("workflows.subtitle")}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {workflows.map((wf) => (
          <div
            key={wf.id}
            className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-3 mb-4">
              <svg className="w-6 h-6 text-blue-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d={iconPaths[wf.icon] || iconPaths.wrench}/></svg>
              <div>
                <h3 className="font-semibold text-gray-900">
                  {lang === "zh" ? wf.title_zh : wf.title_en}
                </h3>
                <p className="text-xs text-gray-500">
                  {lang === "zh" ? wf.description_zh : wf.description_en}
                </p>
              </div>
            </div>

            <div className="space-y-2">
              {wf.steps.map((step, idx) => (
                <a
                  key={step.name}
                  href={step.repo}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-blue-50 transition-colors group"
                >
                  <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold shrink-0">
                    {idx + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium text-gray-800 group-hover:text-blue-600 transition-colors block truncate">
                      {step.name}
                    </span>
                    <span className="text-xs text-gray-400 block truncate">
                      {lang === "zh" ? step.description_zh : step.description_en}
                    </span>
                  </div>
                  <svg
                    className="w-4 h-4 text-gray-300 group-hover:text-blue-500 transition-colors shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                </a>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
