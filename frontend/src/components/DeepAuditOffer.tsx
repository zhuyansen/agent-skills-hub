import { useI18n } from "../i18n/I18nContext";
import { trackEvent } from "../lib/analytics";

/**
 * The first paid offer: $49 concierge deep audit, surfaced right after a free
 * scan result (hottest intent moment). Fulfillment is manual per
 * ops/deep-audit-sop.md — sell it, deliver by hand, automate after 3 orders.
 *
 * PAYMENT_URL: paste your LemonSqueezy (or Stripe Payment Link) checkout URL to
 * flip the CTA from mailto to a real one-click checkout. Empty = mailto
 * fallback, so no broken button ever ships. LemonSqueezy is a merchant of
 * record (handles VAT + non-US payouts); create a $49 product, copy its
 * `/buy/<uuid>` link, paste it below. The repo is attached to the order via
 * custom data so fulfillment knows what to audit.
 */
const PAYMENT_URL = "";
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

  const paid = PAYMENT_URL.length > 0;
  const checkoutHref = paid
    ? `${PAYMENT_URL}${PAYMENT_URL.includes("?") ? "&" : "?"}checkout[custom][repo]=${encodeURIComponent(repo || "")}`
    : `mailto:${CONTACT}?subject=${subject}&body=${body}`;

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
          href={checkoutHref}
          {...(paid ? { target: "_blank", rel: "noopener noreferrer" } : {})}
          onClick={() =>
            trackEvent(paid ? "deep_audit_checkout" : "deep_audit_mailto", {
              repo: repo || undefined,
            })
          }
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
