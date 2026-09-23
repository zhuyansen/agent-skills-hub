import { useEffect, useRef, useState } from "react";
import { useI18n } from "../i18n/I18nContext";
import { trackEvent } from "../lib/analytics";
import { submitEnterpriseLead } from "../lib/enterpriseLead";

/**
 * Enterprise lead capture at the audit result — the only moment on the site
 * with demonstrated security intent.
 *
 * Two weeks after the low-friction /enterprise/ form shipped (2026-09-08), the
 * funnel read 146 sessions → 33 scrolled to the form → 2 started → 0 submitted.
 * Cutting required fields could not have moved that: 98.6% of visitors never
 * reached the form at all. Meanwhile 80 people ran a free audit in /analyzer/.
 * The capture belongs where the intent is, not on a page nobody with intent
 * visits. This is the smallest version: one email field, use_case prefilled
 * from the scan, the same 48h promise /enterprise/ makes and nothing more.
 *
 * Own event family (audit_lead_*) so the daily digest prints this funnel on
 * its own line and the /enterprise/ numbers stay comparable to their history.
 */
const RISKY_GRADES = new Set(["caution", "unsafe", "reject"]);
const EVENTS = {
  attempt: "audit_lead_attempt",
  submitted: "audit_lead_submitted",
  failed: "audit_lead_failed",
};

interface Copy {
  headline: string;
  pitch: string;
  placeholder: string;
  submit: string;
  submitting: string;
  okTitle: string;
  okBody: string;
  privacy: string;
  errMissing: string;
  errGeneric: string;
}

function copyFor(zh: boolean, risky: boolean, unknown: boolean, owner: string, flagCount: number): Copy {
  if (zh) {
    return {
      headline: unknown
        ? "这个仓库没有可评的 README —— 要我们看看你们整套栈吗?"
        : risky
          ? `这个仓库有 ${flagCount} 个标记 —— 你们整套 agent 栈呢?`
          : `这个是干净的 —— 你们跑的其他 MCP server 呢?`,
      pitch: `留下工作邮箱,48 小时内收到一份分级安全审计:${owner} 名下的仓库,加上你们自己的 MCP/agent 栈里的主要风险。不约电话,不做 PPT。`,
      placeholder: "工作邮箱",
      submit: "把审计发我 →",
      submitting: "提交中…",
      okTitle: "收到 —— 审计在路上。",
      okBody: "48 小时内发到你的邮箱。急的话在 X 上找 @GoSailGlobal。",
      privacy: "不会分享你的数据。Jason 在 48 小时内人工审核。",
      errMissing: "请填写工作邮箱。",
      errGeneric: "提交失败。",
    };
  }
  return {
    headline: unknown
      ? "No README here to grade — want us to audit your whole stack instead?"
      : risky
        ? `${flagCount} flag${flagCount === 1 ? "" : "s"} in this repo — what about your whole agent stack?`
        : "This one's clean — what about the other MCP servers you run?",
    pitch: `Leave a work email and get a graded security audit within 48h: the repos under ${owner}, plus the top risks in your own MCP/agent stack. No call, no slides.`,
    placeholder: "Work email",
    submit: "Email me the audit →",
    submitting: "Submitting…",
    okTitle: "Thanks — your audit is on its way.",
    okBody: "We'll email it within 48h. If urgent, ping @GoSailGlobal on X.",
    privacy: "We'll never share your data. Manual review by Jason within 48h.",
    errMissing: "Please add your work email.",
    errGeneric: "Submission failed.",
  };
}

export function AuditLeadCapture({
  repo,
  grade,
  flagCount = 0,
}: {
  repo: string;
  grade?: string | null;
  flagCount?: number;
}) {
  const { lang } = useI18n();
  const g = (grade || "unknown").toLowerCase();
  const owner = repo.split("/")[0];
  const c = copyFor(lang === "zh", RISKY_GRADES.has(g), g === "unknown", owner, flagCount);
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  // The kind, not the text: a resolved string would stay in the old language
  // when the visitor flips 中文/EN with a validation message on screen.
  const [error, setError] = useState<"missing" | { message: string } | null>(null);
  const errorText = error === "missing" ? c.errMissing : error?.message ?? null;
  const root = useRef<HTMLElement>(null);
  const started = useRef(false);

  // Same semantics as /enterprise/: "viewed" means entered the viewport, so
  // the two funnels' first stages measure the same thing.
  useEffect(() => {
    const el = root.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (!entries.some((e) => e.isIntersecting)) return;
        trackEvent("audit_lead_viewed", { grade: g });
        io.disconnect();
      },
      { threshold: 0 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [g]);

  const onChange = (value: string) => {
    if (!started.current && value) {
      started.current = true;
      trackEvent("audit_lead_started", { grade: g });
    }
    setEmail(value);
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
      // Tracked, not blocked by the browser: "tried and got pushed back" must
      // stay distinguishable from "never tried".
      trackEvent("audit_lead_invalid", { missing: "email", grade: g });
      setError("missing");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await submitEnterpriseLead(
        {
          email,
          use_case: `Org audit for ${owner} — requested after scanning ${repo} (grade ${g}, ${flagCount} flags)`,
        },
        "audit_result",
        EVENTS,
        { grade: g, owner },
      );
      setSubmitted(true);
    } catch (err) {
      setError({ message: err instanceof Error ? err.message : c.errGeneric });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section
      ref={root}
      className="mt-4 rounded-xl border border-indigo-200 dark:border-indigo-500/30 bg-white dark:bg-transparent p-5 sm:p-6"
    >
      {submitted ? (
        <>
          <h3 className="text-base font-bold text-gray-900 dark:text-white mb-1">{c.okTitle}</h3>
          <p className="text-sm text-[var(--text-2)]">{c.okBody}</p>
        </>
      ) : (
        <>
          <h3 className="text-base font-bold text-gray-900 dark:text-white mb-1.5">{c.headline}</h3>
          <p className="text-sm text-[var(--text-2)] leading-relaxed mb-4">{c.pitch}</p>
          <form onSubmit={submit} noValidate className="flex flex-col sm:flex-row gap-2">
            <input
              type="email"
              inputMode="email"
              autoComplete="email"
              value={email}
              onChange={(e) => onChange(e.target.value)}
              placeholder={c.placeholder}
              aria-label={c.placeholder}
              className="flex-1 min-w-0 px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white text-sm font-semibold transition-colors"
            >
              {submitting ? c.submitting : c.submit}
            </button>
          </form>
          {errorText && (
            <p role="alert" className="mt-2 text-sm text-red-600 dark:text-red-400">{errorText}</p>
          )}
          <p className="mt-2 text-xs text-[var(--text-3)]">{c.privacy}</p>
        </>
      )}
    </section>
  );
}
