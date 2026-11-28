import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";

/**
 * Homepage conversion hook: paste a GitHub URL → security grade.
 * Routes to /analyzer?repo=… which auto-scans on mount. The tool itself
 * already existed (AnalyzerPage) — this box makes it discoverable.
 */
export function AuditBox() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const [value, setValue] = useState("");

  const submit = () => {
    const v = value.trim();
    if (!v) return;
    navigate(`/analyzer/?repo=${encodeURIComponent(v)}`, {
      state: { autorun: true },
    });
  };

  return (
    <section className="mb-8">
      <div className="rounded-2xl border border-indigo-200/80 dark:border-indigo-500/25 bg-gradient-to-r from-indigo-50/90 via-white to-violet-50/80 dark:from-[#121933]/90 dark:via-[#0f162b]/90 dark:to-[#1b1433]/90 px-5 py-5 sm:px-7 sm:py-6 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center gap-4 lg:gap-6">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="w-6 h-6 rounded-lg bg-indigo-500/15 dark:bg-indigo-400/20 flex items-center justify-center text-sm" aria-hidden>
                🛡️
              </span>
              <h2 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white tracking-tight">
                {t("audit.title")}
              </h2>
            </div>
            <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
              {t("audit.subtitle")}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-2 lg:w-[460px] shrink-0">
            <input
              type="text"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
              placeholder="https://github.com/owner/repo"
              aria-label={t("audit.title")}
              className="flex-1 px-3.5 py-2.5 rounded-xl border border-gray-300 dark:border-white/15 bg-white dark:bg-[#0b1020]/80 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
            />
            <button
              onClick={submit}
              className="shrink-0 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-colors cursor-pointer shadow-sm"
            >
              {t("audit.cta")}
            </button>
          </div>
        </div>
        <p className="mt-2.5 text-[11px] text-gray-500 dark:text-gray-500">{t("audit.hint")}</p>
      </div>
    </section>
  );
}
