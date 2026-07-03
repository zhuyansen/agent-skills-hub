import { useI18n } from "../i18n/I18nContext";

/**
 * The first paid offer: $49 concierge deep audit, surfaced right after a free
 * scan result (hottest intent moment). Fulfillment is manual per
 * ops/deep-audit-sop.md — sell it, deliver by hand, automate after 3 orders.
 */
const CONTACT = "m17551076169@gmail.com";

export function DeepAuditOffer({ repo }: { repo?: string | null }) {
  const { t } = useI18n();
  const subject = encodeURIComponent(
    `Deep audit request${repo ? `: ${repo}` : ""}`,
  );
  const body = encodeURIComponent(
    `Repo: ${repo || "https://github.com/owner/repo"}\n` +
      `Use case (personal / brand / production): \n` +
      `Anything specific to look at: \n`,
  );

  return (
    <section className="mt-6 rounded-xl border border-indigo-200 dark:border-indigo-500/30 bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-indigo-950/40 dark:via-transparent dark:to-purple-950/30 p-5 sm:p-6">
      <div className="flex flex-wrap items-baseline gap-2 mb-1.5">
        <h3 className="text-base font-bold text-gray-900 dark:text-white">
          {t("deepAudit.title")}
        </h3>
        <span className="text-2xl font-extrabold text-indigo-600 dark:text-indigo-400">
          $49
        </span>
        <span className="text-xs text-[var(--text-3)]">
          {t("deepAudit.per")}
        </span>
      </div>
      <p className="text-sm text-[var(--text-2)] leading-relaxed mb-3">
        {t("deepAudit.pitch")}
      </p>
      <ul className="text-xs text-[var(--text-2)] space-y-1 mb-4 list-disc list-inside">
        <li>{t("deepAudit.item1")}</li>
        <li>{t("deepAudit.item2")}</li>
        <li>{t("deepAudit.item3")}</li>
      </ul>
      <div className="flex flex-wrap items-center gap-3">
        <a
          href={`mailto:${CONTACT}?subject=${subject}&body=${body}`}
          className="inline-flex items-center px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-colors"
        >
          {t("deepAudit.cta")}
        </a>
        <span className="text-xs text-[var(--text-3)]">
          {t("deepAudit.note")}
        </span>
      </div>
    </section>
  );
}
