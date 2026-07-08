import { useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { supabase } from "../lib/supabase";
import { trackEvent } from "../lib/analytics";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { useI18n } from "../i18n/I18nContext";
import { EN, ZH, ENTERPRISE_ORGS } from "../data/enterpriseCopy";

/**
 * /enterprise/ — the single B2B inbound surface (bilingual).
 *
 * Consolidates the former /enterprise/ (audit), /business/ (license/SBOM/mirror),
 * and /verified-creator/ (creator certification) into one page. /business/ and
 * /verified-creator/ now redirect here; the creator APPLY flow stays at
 * /verified-creator/apply/. All copy lives in ../data/enterpriseCopy.ts.
 *
 * HONESTY RULE (load-bearing): zero paying customers, zero testimonials, SOC 2
 * in progress (not certified). Frameworks are what Hub AUDITS AGAINST. The vuln
 * stat is the cited 26.1% (Liu et al. 2026), never the old unsourced "43%".
 *
 * Form submits go to enterprise_leads via the submit_enterprise_lead RPC.
 */

interface FormState {
  full_name: string;
  email: string;
  company: string;
  role_title: string;
  team_size: string;
  industry: string;
  use_case: string;
  current_stack: string;
  compliance_requirements: string;
  timeline: string;
  estimated_budget: string;
  message: string;
}

const EMPTY_FORM: FormState = {
  full_name: "",
  email: "",
  company: "",
  role_title: "",
  team_size: "",
  industry: "",
  use_case: "",
  current_stack: "",
  compliance_requirements: "",
  timeline: "",
  estimated_budget: "",
  message: "",
};

export function EnterprisePage() {
  const { lang } = useI18n();
  const c = lang === "zh" ? ZH : EN;
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onChange = <K extends keyof FormState>(key: K, value: string) =>
    setForm((f) => ({ ...f, [key]: value }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!supabase) {
      setError("Supabase not configured.");
      return;
    }
    if (!form.full_name || !form.email || !form.company || !form.use_case) {
      setError(c.form.errMissing);
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const { error: rpcErr } = await supabase.rpc("submit_enterprise_lead", {
        p_full_name: form.full_name,
        p_email: form.email,
        p_company: form.company,
        p_use_case: form.use_case,
        p_role_title: form.role_title || null,
        p_team_size: form.team_size || null,
        p_industry: form.industry || null,
        p_current_stack: form.current_stack || null,
        p_compliance_requirements: form.compliance_requirements || null,
        p_message: form.message || null,
        p_timeline: form.timeline || null,
        p_estimated_budget: form.estimated_budget || null,
        p_source: "enterprise_page",
      });
      if (rpcErr) throw rpcErr;
      setSubmitted(true);
      setForm(EMPTY_FORM);
    } catch (e) {
      setError(e instanceof Error ? e.message : c.form.errGeneric);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Helmet>
        <title>{c.meta.title}</title>
        <meta name="description" content={c.meta.description} />
        <meta
          name="keywords"
          content="MCP server security audit, AI agent compliance, EU AI Act, SOC 2 AI, ISO 42001, enterprise AI skills, agent deployment audit, prompt injection scanning, agent supply chain security, SBOM, license compliance"
        />
        <link rel="canonical" href="https://agentskillshub.top/enterprise/" />
      </Helmet>

      <div className="min-h-screen bg-white dark:bg-[var(--bg-base)]">
        <SiteHeader />

        <main>
          {/* ── HERO ─────────────────────────────────────────── */}
          <section className="relative overflow-hidden border-b border-gray-200 dark:border-[var(--border)]">
            <div
              className="pointer-events-none absolute inset-0 opacity-60"
              style={{
                background:
                  "radial-gradient(60% 50% at 50% 0%, rgba(91,95,233,0.12), transparent 70%)",
              }}
            />
            <div className="relative max-w-5xl mx-auto px-4 text-center pt-20 pb-16">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-[11px] font-bold tracking-wide uppercase bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 mb-6">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
                {c.hero.badge}
              </div>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-gray-900 dark:text-white leading-[1.05] mb-6">
                {c.hero.h1a}
                <br />
                <span className="text-indigo-600 dark:text-indigo-400">
                  {c.hero.h1b}
                </span>
              </h1>
              <p className="text-lg sm:text-xl text-gray-600 dark:text-gray-400 leading-relaxed max-w-2xl mx-auto mb-8">
                {c.hero.sub}
              </p>
              <div className="flex flex-wrap justify-center gap-3">
                <a
                  href="#demo-form"
                  onClick={() =>
                    trackEvent("enterprise_cta_click", { cta: "hero" })
                  }
                  className="inline-flex items-center px-7 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition-colors shadow-sm"
                >
                  {c.hero.ctaPrimary}
                </a>
                <a
                  href="/"
                  className="inline-flex items-center px-7 py-3.5 bg-white dark:bg-[var(--bg-card)] border border-gray-300 dark:border-[var(--border)] hover:border-indigo-400 text-gray-900 dark:text-white font-semibold rounded-lg transition-colors"
                >
                  {c.hero.ctaSecondary}
                </a>
              </div>
              <div className="mt-6 text-xs text-gray-500 dark:text-gray-500">
                {c.hero.note}
              </div>
            </div>
          </section>

          {/* ── COMPLIANCE FRAMEWORK BAND ─────────────────────── */}
          <section className="border-b border-gray-200 dark:border-[var(--border)] bg-gray-50 dark:bg-[var(--bg-card)]/40">
            <div className="max-w-5xl mx-auto px-4 py-10">
              <p className="text-center text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-6">
                {c.band.label}
              </p>
              <div className="flex flex-wrap items-stretch justify-center gap-3">
                {c.bandFrameworks.map((f) => (
                  <div
                    key={f.name}
                    className="flex flex-col items-center justify-center px-5 py-3 rounded-xl border border-gray-200 dark:border-[var(--border)] bg-white dark:bg-[var(--bg-card)] min-w-[140px]"
                  >
                    <span className="text-sm font-bold text-gray-900 dark:text-white">
                      {f.name}
                    </span>
                    <span className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">
                      {f.sub}
                    </span>
                  </div>
                ))}
              </div>
              <p className="text-center text-[11px] text-gray-400 dark:text-gray-500 mt-5 max-w-xl mx-auto">
                {c.band.footnote}
              </p>
            </div>
          </section>

          <div className="max-w-6xl mx-auto px-4">
            {/* ── TRUST SIGNALS ─────────────────────────────────── */}
            <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 mb-20">
              {c.signals.map((item) => (
                <div
                  key={item.stat}
                  className="text-center p-6 rounded-2xl border border-gray-200 dark:border-[var(--border)] bg-white dark:bg-[var(--bg-card)]"
                >
                  <div className="text-4xl font-bold text-indigo-600 dark:text-indigo-400 mb-2">
                    {item.stat}
                  </div>
                  <div className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                    {item.label}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                    {item.sub}
                  </div>
                </div>
              ))}
            </section>

            {/* ── PROBLEM ───────────────────────────────────────── */}
            <section className="mb-20">
              <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-3">
                {c.problem.h2}
              </h2>
              <p className="text-center text-xl text-gray-500 dark:text-gray-400 mb-12">
                {c.problem.sub}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {c.problem.items.map((item) => (
                  <div
                    key={item.title}
                    className="p-6 rounded-xl bg-red-50 dark:bg-red-950/20 border border-red-100 dark:border-red-900/50"
                  >
                    <div className="text-3xl mb-3">{item.emoji}</div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                      {item.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                      {item.body}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            {/* ── SOLUTION ──────────────────────────────────────── */}
            <section className="mb-20">
              <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-3">
                {c.solution.h2}
              </h2>
              <p className="text-center text-gray-600 dark:text-gray-400 mb-12 max-w-2xl mx-auto">
                {c.solution.sub}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {c.solution.items.map((item) => (
                  <div
                    key={item.title}
                    className="p-6 rounded-xl bg-white dark:bg-[var(--bg-card)] border border-gray-200 dark:border-[var(--border)]"
                  >
                    <div className="text-2xl mb-3">{item.icon}</div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                      {item.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                      {item.body}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            {/* ── HOW IT WORKS ──────────────────────────────────── */}
            <section id="how-it-works" className="mb-20">
              <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">
                {c.how.h2}
              </h2>
              <div className="space-y-4">
                {c.how.steps.map((step) => (
                  <div
                    key={step.num}
                    className="flex gap-6 p-6 rounded-xl border border-gray-200 dark:border-[var(--border)] bg-white dark:bg-[var(--bg-card)]"
                  >
                    <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-indigo-600 dark:bg-indigo-500 text-white font-bold text-xl flex items-center justify-center">
                      {step.num}
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-1">
                        {step.title}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                        {step.body}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* ── SOLUTIONS BY ROLE ─────────────────────────────── */}
            <section className="mb-20">
              <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-3">
                {c.roles.h2}
              </h2>
              <p className="text-center text-gray-600 dark:text-gray-400 mb-12 max-w-2xl mx-auto">
                {c.roles.sub}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {c.roles.items.map((item) => (
                  <div
                    key={item.role}
                    className="p-6 rounded-xl border border-gray-200 dark:border-[var(--border)] bg-white dark:bg-[var(--bg-card)]"
                  >
                    <div className="text-sm font-bold text-indigo-600 dark:text-indigo-400 mb-3">
                      {item.role}
                    </div>
                    <p className="text-xs uppercase tracking-wide text-gray-400 dark:text-gray-500 mb-1">
                      {c.roles.blocker}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 leading-relaxed">
                      {item.pain}
                    </p>
                    <p className="text-xs uppercase tracking-wide text-gray-400 dark:text-gray-500 mb-1">
                      {c.roles.gives}
                    </p>
                    <p className="text-sm text-gray-900 dark:text-white leading-relaxed">
                      {item.win}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            {/* ── COMPLIANCE / SBOM / MIRROR (folded from /business/) ── */}
            <section className="mb-20">
              <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-3">
                {c.compliance.h2}
              </h2>
              <p className="text-center text-gray-600 dark:text-gray-400 mb-12 max-w-2xl mx-auto">
                {c.compliance.sub}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {c.compliance.items.map((item) => (
                  <div
                    key={item.title}
                    className="p-6 rounded-xl border border-gray-200 dark:border-[var(--border)] bg-white dark:bg-[var(--bg-card)]"
                  >
                    <div className="text-2xl mb-3">{item.icon}</div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                      {item.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                      {item.body}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            {/* ── PRICING ───────────────────────────────────────── */}
            <section className="mb-20">
              <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-3">
                {c.pricing.h2}
              </h2>
              <p className="text-center text-gray-600 dark:text-gray-400 mb-12">
                {c.pricing.sub}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
                {c.pricing.tiers.map((tier) => {
                  const ctaHref = tier.highlight
                    ? "#demo-form"
                    : tier.name === "Pro"
                      ? "mailto:m17551076169@gmail.com?subject=Hub%20Pro%20-%20Early%20Access"
                      : "/";
                  return (
                  <div
                    key={tier.name}
                    onClick={(e) => {
                      // Whole card → its CTA. Clarity: pricing feature bullets
                      // were the top /enterprise/ dead-click cluster (35%);
                      // clicking a feature = "I want this tier". Inner <a>
                      // (the CTA button) wins via the guard.
                      if ((e.target as HTMLElement).closest("a")) return;
                      trackEvent("enterprise_cta_click", {
                        cta: "pricing-card",
                        tier: tier.name,
                      });
                      window.location.href = ctaHref;
                    }}
                    className={
                      tier.highlight
                        ? "p-6 rounded-2xl border-2 border-indigo-500 dark:border-indigo-400 bg-gradient-to-b from-indigo-50/50 to-white dark:from-indigo-950/20 dark:to-[var(--bg-card)] relative cursor-pointer"
                        : "p-6 rounded-2xl border border-gray-200 dark:border-[var(--border)] bg-white dark:bg-[var(--bg-card)] cursor-pointer"
                    }
                  >
                    {tier.highlight && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-indigo-600 text-white text-xs font-bold">
                        {lang === "zh" ? "联系销售" : "TALK TO SALES"}
                      </div>
                    )}
                    <div
                      className={
                        tier.highlight
                          ? "text-sm font-semibold text-indigo-600 dark:text-indigo-400 mb-2"
                          : "text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2"
                      }
                    >
                      {tier.name}
                    </div>
                    <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                      {tier.price}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-6">
                      {tier.unit}
                    </div>
                    <ul className="space-y-3 text-sm text-gray-700 dark:text-gray-300 mb-8">
                      {tier.features.map((f) => (
                        <li key={f}>✓ {f}</li>
                      ))}
                    </ul>
                    <a
                      href={ctaHref}
                      onClick={() =>
                        trackEvent("enterprise_cta_click", {
                          cta: "pricing",
                          tier: tier.name,
                        })
                      }
                      className={
                        tier.highlight
                          ? "block w-full text-center py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition-colors"
                          : "block w-full text-center py-2.5 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:border-indigo-400 transition-colors"
                      }
                    >
                      {tier.cta}
                    </a>
                  </div>
                  );
                })}
              </div>
              <p className="text-center text-xs text-gray-500 dark:text-gray-500 mt-6">
                {c.pricing.footnote}
              </p>
            </section>

            {/* ── VERIFIED CREATOR (folded from /verified-creator/) ── */}
            <section className="mb-20">
              <div className="rounded-2xl border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/40 dark:bg-emerald-950/20 p-8 sm:p-10">
                <div className="max-w-3xl mx-auto text-center">
                  <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-3">
                    {c.creator.h2}
                  </h2>
                  <p className="text-gray-600 dark:text-gray-300 mb-7 max-w-2xl mx-auto leading-relaxed">
                    {c.creator.sub}
                  </p>
                  <ul className="grid sm:grid-cols-2 gap-3 text-left max-w-2xl mx-auto mb-8">
                    {c.creator.benefits.map((b) => (
                      <li
                        key={b}
                        className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300"
                      >
                        <span className="text-emerald-500 flex-none mt-0.5">
                          ✓
                        </span>
                        <span>{b}</span>
                      </li>
                    ))}
                  </ul>
                  <Link
                    to="/verified-creator/apply/"
                    className="inline-block px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-lg transition-colors shadow-sm"
                  >
                    {c.creator.cta}
                  </Link>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-3">
                    {c.creator.note}
                  </p>
                </div>
              </div>
            </section>

            {/* ── WHY TRUST US ──────────────────────────────────── */}
            <section className="mb-20">
              <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-3">
                {c.trust.h2}
              </h2>
              <p className="text-center text-gray-600 dark:text-gray-400 mb-12 max-w-2xl mx-auto">
                {c.trust.sub}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
                {c.trust.items.map((item) => (
                  <div
                    key={item.title}
                    className="p-6 rounded-xl border border-gray-200 dark:border-[var(--border)] bg-white dark:bg-[var(--bg-card)]"
                  >
                    <h3 className="text-base font-bold text-gray-900 dark:text-white mb-2">
                      {item.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                      {item.body}
                    </p>
                  </div>
                ))}
              </div>
              <div className="text-center">
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-4">
                  {c.trust.orgsLabel}
                </p>
                <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm font-medium text-gray-400 dark:text-gray-500">
                  {ENTERPRISE_ORGS.map((org) => (
                    <span key={org}>{org}</span>
                  ))}
                </div>
                <p className="text-[11px] text-gray-400 dark:text-gray-500 mt-3">
                  {c.trust.orgsNote}
                </p>
              </div>
            </section>

            {/* ── FAQ ───────────────────────────────────────────── */}
            <section className="mb-20">
              <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">
                {c.faq.h2}
              </h2>
              <div className="max-w-3xl mx-auto space-y-3">
                {c.faq.items.map((item, i) => (
                  <details
                    key={i}
                    className="group p-4 rounded-lg border border-gray-200 dark:border-[var(--border)] bg-white dark:bg-[var(--bg-card)]"
                  >
                    <summary className="cursor-pointer font-semibold text-gray-900 dark:text-white list-none flex justify-between items-center">
                      <span>{item.q}</span>
                      <span className="text-indigo-600 group-open:rotate-45 transition-transform text-xl">
                        +
                      </span>
                    </summary>
                    <p className="mt-3 text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                      {item.a}
                    </p>
                  </details>
                ))}
              </div>
            </section>

            {/* ── DEMO FORM ─────────────────────────────────────── */}
            <section
              id="demo-form"
              className="max-w-3xl mx-auto mb-20 p-8 rounded-2xl border border-gray-200 dark:border-[var(--border)] bg-white dark:bg-[var(--bg-card)]"
            >
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                {c.form.h2}
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-8">
                {c.form.sub}
              </p>

              {submitted ? (
                <div className="p-6 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900">
                  <h3 className="text-lg font-bold text-emerald-700 dark:text-emerald-400 mb-2">
                    {c.form.okTitle}
                  </h3>
                  <p className="text-sm text-emerald-700 dark:text-emerald-400">
                    {c.form.okBody}
                  </p>
                </div>
              ) : (
                <form onSubmit={submit} className="space-y-5">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormField
                      label={c.form.fields.full_name}
                      value={form.full_name}
                      onChange={(v) => onChange("full_name", v)}
                      required
                      maxLength={100}
                    />
                    <FormField
                      label={c.form.fields.email}
                      value={form.email}
                      onChange={(v) => onChange("email", v)}
                      required
                      type="email"
                      maxLength={200}
                    />
                    <FormField
                      label={c.form.fields.company}
                      value={form.company}
                      onChange={(v) => onChange("company", v)}
                      required
                      maxLength={200}
                    />
                    <FormField
                      label={c.form.fields.role}
                      placeholder={c.form.fields.rolePlaceholder}
                      value={form.role_title}
                      onChange={(v) => onChange("role_title", v)}
                      maxLength={100}
                    />
                    <FormSelect
                      label={c.form.fields.teamSize}
                      value={form.team_size}
                      onChange={(v) => onChange("team_size", v)}
                      options={c.form.teamSizes}
                      lang={lang}
                    />
                    <FormField
                      label={c.form.fields.industry}
                      placeholder={c.form.fields.industryPlaceholder}
                      value={form.industry}
                      onChange={(v) => onChange("industry", v)}
                      maxLength={100}
                    />
                  </div>

                  <FormTextarea
                    label={c.form.fields.useCase}
                    placeholder={c.form.fields.useCasePlaceholder}
                    value={form.use_case}
                    onChange={(v) => onChange("use_case", v)}
                    required
                    maxLength={2000}
                  />

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <FormField
                      label={c.form.fields.stack}
                      placeholder={c.form.fields.stackPlaceholder}
                      value={form.current_stack}
                      onChange={(v) => onChange("current_stack", v)}
                      maxLength={500}
                    />
                    <FormField
                      label={c.form.fields.compliance}
                      placeholder={c.form.fields.compliancePlaceholder}
                      value={form.compliance_requirements}
                      onChange={(v) => onChange("compliance_requirements", v)}
                      maxLength={500}
                    />
                    <FormSelect
                      label={c.form.fields.timeline}
                      value={form.timeline}
                      onChange={(v) => onChange("timeline", v)}
                      options={c.form.timelines}
                      lang={lang}
                    />
                    <FormSelect
                      label={c.form.fields.budget}
                      value={form.estimated_budget}
                      onChange={(v) => onChange("estimated_budget", v)}
                      options={c.form.budgets}
                      lang={lang}
                    />
                  </div>

                  <FormTextarea
                    label={c.form.fields.message}
                    placeholder={c.form.fields.messagePlaceholder}
                    value={form.message}
                    onChange={(v) => onChange("message", v)}
                    maxLength={2000}
                    rows={3}
                  />

                  {error && (
                    <div className="p-3 rounded-md bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 text-sm text-red-700 dark:text-red-400">
                      {error}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={submitting}
                    className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
                  >
                    {submitting ? c.form.submitting : c.form.submit}
                  </button>

                  <p className="text-xs text-gray-500 dark:text-gray-500 text-center">
                    {c.form.privacy}
                  </p>
                </form>
              )}
            </section>
          </div>
        </main>

        <SiteFooter />
      </div>
    </div>
  );
}

// ── Tiny form primitives ─────────────────────────────────────────────

interface FormFieldProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  required?: boolean;
  type?: string;
  placeholder?: string;
  maxLength?: number;
}

function FormField({
  label,
  value,
  onChange,
  required,
  type = "text",
  placeholder,
  maxLength,
}: FormFieldProps) {
  return (
    <label className="block">
      <span className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
        {label}
      </span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        placeholder={placeholder}
        maxLength={maxLength}
        className="w-full px-3 py-2 rounded-md bg-white dark:bg-[var(--bg-elev)] border border-gray-300 dark:border-[var(--border)] text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
      />
    </label>
  );
}

interface FormSelectProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
  lang: string;
}

function FormSelect({
  label,
  value,
  onChange,
  options,
  lang,
}: FormSelectProps) {
  const placeholder = lang === "zh" ? "— 请选择 —" : "— select —";
  return (
    <label className="block">
      <span className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
        {label}
      </span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 rounded-md bg-white dark:bg-[var(--bg-elev)] border border-gray-300 dark:border-[var(--border)] text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt || placeholder}
          </option>
        ))}
      </select>
    </label>
  );
}

interface FormTextareaProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  required?: boolean;
  placeholder?: string;
  maxLength?: number;
  rows?: number;
}

function FormTextarea({
  label,
  value,
  onChange,
  required,
  placeholder,
  maxLength,
  rows = 4,
}: FormTextareaProps) {
  return (
    <label className="block">
      <span className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
        {label}
      </span>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        placeholder={placeholder}
        maxLength={maxLength}
        rows={rows}
        className="w-full px-3 py-2 rounded-md bg-white dark:bg-[var(--bg-elev)] border border-gray-300 dark:border-[var(--border)] text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-y"
      />
    </label>
  );
}
