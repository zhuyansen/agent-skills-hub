import { useI18n } from "../i18n/I18nContext";
import { trackEvent } from "../lib/analytics";

/**
 * The first paid offer: $49 concierge deep audit, surfaced right after a free
 * scan result (hottest intent moment). Fulfillment is manual per
 * ops/deep-audit-sop.md — sell it, deliver by hand, automate after 3 orders.
 *
 * PAYMENT_URL: paste a Stripe Payment Link (buy.stripe.com/...) or a
 * LemonSqueezy buy link to flip the CTA from mailto to a real one-click
 * checkout. Empty = mailto fallback, so no broken button ever ships.
 *
 * The repo under audit is attached to the order so fulfillment knows what to
 * audit — provider-specific param, auto-detected from the URL:
 *   - Stripe: client_reference_id (alphanumeric/dash/underscore only, so
 *     "owner/repo" is sanitized to "owner--repo"; invalid values would be
 *     silently dropped by Stripe)
 *   - LemonSqueezy: checkout[custom][repo]
 */
const PAYMENT_URL = "https://buy.stripe.com/00w3cu6arbkx27FdhW2VG05";
const CONTACT = "m17551076169@gmail.com";

function checkoutUrl(base: string, repo: string): string {
  const sep = base.includes("?") ? "&" : "?";
  if (base.includes("buy.stripe.com")) {
    const ref = repo.replace(/[^a-zA-Z0-9_-]/g, "--").slice(0, 200);
    return ref ? `${base}${sep}client_reference_id=${ref}` : base;
  }
  return `${base}${sep}checkout[custom][repo]=${encodeURIComponent(repo)}`;
}

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
    ? checkoutUrl(PAYMENT_URL, repo || "")
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
          {t(paid ? "deepAudit.ctaPay" : "deepAudit.cta")}
        </a>
        <span className="text-xs text-[var(--text-3)]">
          {t(paid ? "deepAudit.notePay" : "deepAudit.note")}
        </span>
      </div>
    </section>
  );
}
