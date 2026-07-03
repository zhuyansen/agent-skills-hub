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
    navigate(`/analyzer?repo=${encodeURIComponent(v)}`);
  };

  return (
    <section className="mt-6 mb-10">
      <div className="max-w-3xl mx-auto rounded-2xl border border-indigo-200 dark:border-indigo-500/30 bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-indigo-950/40 dark:via-transparent dark:to-purple-950/30 p-6 sm:p-8">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xl" aria-hidden>
            🛡️
          </span>
          <h2 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white tracking-tight">
            {t("audit.title")}
          </h2>
        </div>
        <p className="text-sm text-[var(--text-2)] mb-4">
          {t("audit.subtitle")}
        </p>

        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="https://github.com/owner/repo"
            aria-label={t("audit.title")}
            className="flex-1 px-4 py-3 rounded-xl border border-gray-300 dark:border-white/15 bg-white dark:bg-white/5 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
          />
          <button
            onClick={submit}
            className="shrink-0 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-colors cursor-pointer"
          >
            {t("audit.cta")}
          </button>
        </div>

        <p className="mt-3 text-xs text-[var(--text-3)]">{t("audit.hint")}</p>
      </div>
    </section>
  );
}
