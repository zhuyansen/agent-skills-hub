import { useState } from "react";
import { Helmet } from "react-helmet-async";
import { supabase } from "../lib/supabase";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";

/**
 * /enterprise/ — the B-path landing page.
 *
 * Positioning: Hub is repositioned from "directory" → "Trust Layer for Agent
 * & MCP Deployment". This page is the single inbound surface for enterprise
 * leads ($10K-$30K/yr). The Chinese /business/ page coexists, serving
 * ¥ buyers; /enterprise/ is the USD/English-speaking surface.
 *
 * Form submits go to enterprise_leads table (migration 012). Anon RLS
 * enforces length bounds and status='new'.
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
      setError("Please fill in name, email, company, and your use case.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      // RPC, not direct table insert. The SECURITY DEFINER function on the
      // server side wraps the INSERT — see supabase/migrations/012_enterprise_leads.sql
      // for why (PostgREST + this specific table's column shape had an RLS
      // quirk that nuked direct inserts; RPC sidesteps it cleanly).
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
      setError(e instanceof Error ? e.message : "Submission failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Helmet>
        <title>
          Enterprise · Trust Layer for AI Agent & MCP Deployment | Agent Skills
          Hub
        </title>
        <meta
          name="description"
          content="Audit 78,000+ open-source agent skills before they touch your production. SSO/SCIM ready · Compliance evidence packs · Sandbox verification. Built for VP Engineering, CTOs, and platform teams deploying AI agents at scale."
        />
        <meta
          name="keywords"
          content="MCP server security audit, AI agent compliance, EU AI Act, SOC 2 AI, ISO 42001, enterprise AI skills, agent deployment audit"
        />
        <link rel="canonical" href="https://agentskillshub.top/enterprise/" />
      </Helmet>

      <div className="min-h-screen bg-white dark:bg-[var(--bg-base)]">
        <SiteHeader />

        <main className="max-w-6xl mx-auto px-4 py-12">
          {/* ── HERO ─────────────────────────────────────────── */}
          <section className="text-center max-w-3xl mx-auto pt-8 pb-16">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
              FOR ENTERPRISE TEAMS
            </div>
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-gray-900 dark:text-white leading-tight mb-6">
              Deploy AI Agents to Production.
              <br />
              <span className="text-indigo-600 dark:text-indigo-400">
                Without the Audit Panic.
              </span>
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-400 leading-relaxed mb-8">
              Hub audits MCP servers and Agent Skills against{" "}
              <strong className="text-gray-900 dark:text-white">
                EU AI Act 2026
              </strong>
              , <strong className="text-gray-900 dark:text-white">SOC 2</strong>
              , and{" "}
              <strong className="text-gray-900 dark:text-white">
                ISO/IEC 42001
              </strong>{" "}
              — before they ship to your prod.
            </p>
            <div className="flex flex-wrap justify-center gap-3">
              <a
                href="#demo-form"
                className="inline-flex items-center px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition-colors"
              >
                Book a 30-min demo →
              </a>
              <a
                href="#how-it-works"
                className="inline-flex items-center px-6 py-3 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-900 dark:text-white font-semibold rounded-lg transition-colors"
              >
                How it works
              </a>
            </div>
            <div className="mt-6 text-xs text-gray-500 dark:text-gray-500">
              Compliance-ready · SSO/SCIM · Audit-ready · No credit card to demo
            </div>
          </section>

          {/* ── TRUST SIGNALS ─────────────────────────────────── */}
          <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-20">
            {[
              {
                stat: "43%",
                label: "Critical vulnerabilities",
                sub: "in open-source MCP servers we've audited",
              },
              {
                stat: "78,000+",
                label: "Skills audited",
                sub: "every 8 hours across the open-source ecosystem",
              },
              {
                stat: "$10K-$30K",
                label: "Saved per incident",
                sub: "by pre-deployment audit vs. breach response",
              },
            ].map((item) => (
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
              Your MCP server worked in dev.
            </h2>
            <p className="text-center text-xl text-gray-500 dark:text-gray-400 mb-12">
              Then it shipped.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                {
                  emoji: "💉",
                  title: "Prompt Injection Disaster",
                  body: "43% of open-source MCP servers we've scanned have critical prompt injection or credential leak vulnerabilities. One bad request can exfiltrate your entire database.",
                },
                {
                  emoji: "🚧",
                  title: "Compliance Blockade",
                  body: "EU AI Act 2026 (full enforcement August 2026) and SOC 2 audits require provenance, audit logs, and risk classification. Your platform team blocks the launch.",
                },
                {
                  emoji: "🕳",
                  title: "Zero Incident Forensics",
                  body: "Agent breaks at 2am. No audit logs. No way to replay the failing tool call. No way to roll back to a known-good skill version. You're flying blind.",
                },
              ].map((item) => (
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
              The Trust Layer for Agent Deployment
            </h2>
            <p className="text-center text-gray-600 dark:text-gray-400 mb-12 max-w-2xl mx-auto">
              Hub sits between your developers and your production. Every skill
              gets audited, sandboxed, logged, and gated — before it touches a
              real user.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                {
                  icon: "🔐",
                  title: "Pre-deployment Sandbox",
                  body: "Clone your production data (de-identified) into an isolated environment. Run the skill against real-shaped data. Kill switch on first anomaly.",
                },
                {
                  icon: "📋",
                  title: "Compliance Evidence Pack",
                  body: "Auto-generated PDF: SOC 2 control mapping, ISO/IEC 42001 alignment, EU AI Act risk classification, model training data isolation proof. Hand it to your auditor.",
                },
                {
                  icon: "📊",
                  title: "Full-chain Audit Logs",
                  body: "Every tool call, every data flow, every error replay — captured in 1 click. JSON export to your SIEM (Splunk, Datadog, Elastic). 90-day retention default.",
                },
                {
                  icon: "👤",
                  title: "SSO/SCIM + Fine-grained RBAC",
                  body: "Okta, Auth0, Azure AD ready. Skill-level permissions (which agent can call which tool with which scope). Engineering manager approvals before prod.",
                },
              ].map((item) => (
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
              How it works
            </h2>
            <div className="space-y-4">
              {[
                {
                  num: "01",
                  title: "Connect your existing MCP setup",
                  body: "Point Hub at your registry of MCP servers and agent skills (GitHub, internal mirror, or direct upload). ≤ 30 min onboarding.",
                },
                {
                  num: "02",
                  title: "Hub runs 27-rule security scan + sandbox test",
                  body: "Each skill is statically scanned for prompt injection, credential exposure, sandbox escape risks, plus runtime sandbox testing with red-team probes.",
                },
                {
                  num: "03",
                  title: "Get a compliance evidence package",
                  body: "PDF report ready for auditors: control mapping, risk classification, audit log samples, training-data isolation proof. Ship to procurement, pass review.",
                },
              ].map((step) => (
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

          {/* ── PRICING ───────────────────────────────────────── */}
          <section className="mb-20">
            <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-3">
              Pricing
            </h2>
            <p className="text-center text-gray-600 dark:text-gray-400 mb-12">
              Three tiers, calibrated to where you are in your AI agent journey.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Free */}
              <div className="p-6 rounded-2xl border border-gray-200 dark:border-[var(--border)] bg-white dark:bg-[var(--bg-card)]">
                <div className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2">
                  Free
                </div>
                <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                  $0
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-6">
                  Forever
                </div>
                <ul className="space-y-3 text-sm text-gray-700 dark:text-gray-300 mb-8">
                  <li>✓ Browse 78K+ skill catalog</li>
                  <li>✓ Basic scan reports per skill</li>
                  <li>✓ Arena community voting access</li>
                  <li>✓ Blue Book free edition</li>
                  <li>✓ Newsletter (weekly trending)</li>
                </ul>
                <a
                  href="/"
                  className="block w-full text-center py-2.5 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:border-indigo-400 transition-colors"
                >
                  Explore Free
                </a>
              </div>

              {/* Pro */}
              <div className="p-6 rounded-2xl border border-gray-200 dark:border-[var(--border)] bg-white dark:bg-[var(--bg-card)]">
                <div className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2">
                  Pro
                </div>
                <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                  $49<span className="text-base font-normal">/mo</span>
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-6">
                  Per developer
                </div>
                <ul className="space-y-3 text-sm text-gray-700 dark:text-gray-300 mb-8">
                  <li>✓ Everything in Free</li>
                  <li>✓ VS Code / Cursor plugin (skill discovery + sandbox)</li>
                  <li>✓ Skill version lock + auto-rollback</li>
                  <li>✓ Audit log export (per-developer scope)</li>
                  <li>✓ Blue Book Pro (failure case studies)</li>
                  <li>✓ Email support</li>
                </ul>
                <a
                  href="mailto:m17551076169@gmail.com?subject=Hub%20Pro%20-%20Early%20Access"
                  className="block w-full text-center py-2.5 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:border-indigo-400 transition-colors"
                >
                  Request early access
                </a>
              </div>

              {/* Enterprise — highlight */}
              <div className="p-6 rounded-2xl border-2 border-indigo-500 dark:border-indigo-400 bg-gradient-to-b from-indigo-50/50 to-white dark:from-indigo-950/20 dark:to-[var(--bg-card)] relative">
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-indigo-600 text-white text-xs font-bold">
                  CORE
                </div>
                <div className="text-sm font-semibold text-indigo-600 dark:text-indigo-400 mb-2">
                  Enterprise
                </div>
                <div className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                  $10K–$30K
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-6">
                  /year / department
                </div>
                <ul className="space-y-3 text-sm text-gray-700 dark:text-gray-300 mb-8">
                  <li>✓ Everything in Pro</li>
                  <li>✓ SSO/SCIM (Okta, Auth0, Azure AD)</li>
                  <li>✓ Pre-deployment sandbox with de-identified data</li>
                  <li>
                    ✓ Compliance evidence pack (SOC 2 / ISO 42001 / EU AI Act)
                  </li>
                  <li>✓ Full-chain audit logs + SIEM export</li>
                  <li>✓ Red team report (quarterly)</li>
                  <li>✓ Dedicated account manager + 4h SLA</li>
                  <li>
                    ✓ Regulated industry add-ons (healthtech / fintech /
                    automotive)
                  </li>
                </ul>
                <a
                  href="#demo-form"
                  className="block w-full text-center py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition-colors"
                >
                  Book a demo →
                </a>
              </div>
            </div>
            <p className="text-center text-xs text-gray-500 dark:text-gray-500 mt-6">
              Pricing reflects engineering team sizes 10–200. For 200+ or
              regulated industries (healthtech / automotive), enterprise plans
              start at $50K/yr.{" "}
              <a
                href="#demo-form"
                className="text-indigo-600 dark:text-indigo-400 hover:underline"
              >
                Talk to sales
              </a>
              .
            </p>
          </section>

          {/* ── FAQ ───────────────────────────────────────────── */}
          <section className="mb-20">
            <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">
              Procurement FAQ
            </h2>
            <div className="max-w-3xl mx-auto space-y-3">
              {[
                {
                  q: "How is this different from Snyk or SonarQube?",
                  a: "Snyk and SonarQube scan your code. Hub scans the agent skills and MCP servers your code calls into — the supply-chain layer they don't cover. We focus on AI-specific risks: prompt injection, sandbox escape, credential leakage in tool definitions, model training data isolation.",
                },
                {
                  q: "Do you train models on our data?",
                  a: "No. Hub does not train, fine-tune, or send your data to any model provider. All analysis runs in our infrastructure or on-prem (Enterprise plan). Data isolation is a contractual term.",
                },
                {
                  q: "EU AI Act 2026 — do you cover the full checklist?",
                  a: "Yes. Hub's compliance evidence pack maps directly to Article 9 (risk management), Article 10 (data governance), Article 11 (technical documentation), and Article 12 (record-keeping). Updated for the August 2026 full enforcement.",
                },
                {
                  q: "Is Hub itself SOC 2 audited?",
                  a: "We are in active SOC 2 Type II observation period (target: Q3 2026). For customers requiring SOC 2 today, we provide our security control mapping under NDA and can complete a custom security questionnaire.",
                },
                {
                  q: "Can we deploy on-prem or private cloud?",
                  a: "Yes, for Enterprise. We support deployment on AWS (us-east-1, eu-west-1), GCP, Azure, and on-prem Kubernetes. Air-gapped deployments available for healthtech/defense customers.",
                },
                {
                  q: "What happens if a skill is updated upstream?",
                  a: "Hub re-scans on every commit to the upstream repo. Updated skills enter the pre-deployment sandbox automatically. Your engineering team gets notified before any auto-pull to production.",
                },
                {
                  q: "How long does a POC take?",
                  a: "Standard POC: 4 weeks. Week 1 onboarding + connector setup. Weeks 2-3 audit your current skill inventory + deliver findings. Week 4 review with your platform team. POC fee: $5,000, fully credited toward annual plan.",
                },
                {
                  q: "What's actually included in the $10K-$30K range?",
                  a: "Pricing scales with team size and number of skills audited. Starter: 10 engineers, 50 skills audited ($10K/yr). Standard: 50 engineers, 200 skills ($20K/yr). Business: 200 engineers, unlimited skills ($30K/yr). Beyond that, custom enterprise.",
                },
              ].map((item, i) => (
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
              Book a 30-min demo
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-8">
              We'll walk through your current MCP/agent setup and show you 3
              immediate risks before the call ends. No slides, no sales theater.
            </p>

            {submitted ? (
              <div className="p-6 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900">
                <h3 className="text-lg font-bold text-emerald-700 dark:text-emerald-400 mb-2">
                  Thanks — we'll be in touch within 24h.
                </h3>
                <p className="text-sm text-emerald-700 dark:text-emerald-400">
                  Jason or someone from the Hub team will reach out via email to
                  schedule the call. If urgent, ping{" "}
                  <a
                    href="https://x.com/GoSailGlobal"
                    target="_blank"
                    rel="noreferrer"
                    className="underline"
                  >
                    @GoSailGlobal
                  </a>{" "}
                  on X.
                </p>
              </div>
            ) : (
              <form onSubmit={submit} className="space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FormField
                    label="Full name *"
                    value={form.full_name}
                    onChange={(v) => onChange("full_name", v)}
                    required
                    maxLength={100}
                  />
                  <FormField
                    label="Work email *"
                    value={form.email}
                    onChange={(v) => onChange("email", v)}
                    required
                    type="email"
                    maxLength={200}
                  />
                  <FormField
                    label="Company *"
                    value={form.company}
                    onChange={(v) => onChange("company", v)}
                    required
                    maxLength={200}
                  />
                  <FormField
                    label="Role"
                    placeholder="VP Engineering, CTO, Platform Lead…"
                    value={form.role_title}
                    onChange={(v) => onChange("role_title", v)}
                    maxLength={100}
                  />
                  <FormSelect
                    label="Team size"
                    value={form.team_size}
                    onChange={(v) => onChange("team_size", v)}
                    options={[
                      "",
                      "1–10",
                      "10–50",
                      "50–200",
                      "200–1,000",
                      "1,000+",
                    ]}
                  />
                  <FormField
                    label="Industry"
                    placeholder="fintech, healthtech, automotive…"
                    value={form.industry}
                    onChange={(v) => onChange("industry", v)}
                    maxLength={100}
                  />
                </div>

                <FormTextarea
                  label="What's your use case? *"
                  placeholder="Briefly: how are you deploying AI agents today, and what's the biggest pain point?"
                  value={form.use_case}
                  onChange={(v) => onChange("use_case", v)}
                  required
                  maxLength={2000}
                />

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FormField
                    label="Current AI/agent stack"
                    placeholder="Claude Code + LangGraph + 12 MCP servers…"
                    value={form.current_stack}
                    onChange={(v) => onChange("current_stack", v)}
                    maxLength={500}
                  />
                  <FormField
                    label="Compliance requirements"
                    placeholder="SOC 2, ISO 42001, EU AI Act, HIPAA…"
                    value={form.compliance_requirements}
                    onChange={(v) => onChange("compliance_requirements", v)}
                    maxLength={500}
                  />
                  <FormSelect
                    label="Timeline"
                    value={form.timeline}
                    onChange={(v) => onChange("timeline", v)}
                    options={[
                      "",
                      "Immediate (this quarter)",
                      "1–3 months",
                      "3–6 months",
                      "Just exploring",
                    ]}
                  />
                  <FormSelect
                    label="Estimated budget"
                    value={form.estimated_budget}
                    onChange={(v) => onChange("estimated_budget", v)}
                    options={[
                      "",
                      "<$5K/yr",
                      "$5K–$10K/yr",
                      "$10K–$30K/yr",
                      "$30K–$100K/yr",
                      ">$100K/yr",
                    ]}
                  />
                </div>

                <FormTextarea
                  label="Anything else?"
                  placeholder="Context, urgency, specific risks you're worried about…"
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
                  {submitting ? "Submitting…" : "Request demo →"}
                </button>

                <p className="text-xs text-gray-500 dark:text-gray-500 text-center">
                  We'll never share your data. Form submissions stored encrypted
                  in our database. Manual review by Jason within 24h.
                </p>
              </form>
            )}
          </section>
        </main>

        <SiteFooter />
      </div>
    </>
  );
}

// ── Tiny form primitives (kept local; not worth extracting) ──────────

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
}

function FormSelect({ label, value, onChange, options }: FormSelectProps) {
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
            {opt || "— select —"}
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
