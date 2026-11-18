import { useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { useI18n } from "../i18n/I18nContext";
import {
  CHECKOUT_LINKS,
  USD_PRICING,
  buildStripeCheckoutUrl,
  sanitizeStripeRef,
} from "../lib/checkout";
import { isCompleteEmail, submitEnterpriseLead } from "../lib/enterpriseLead";
import { trackEvent } from "../lib/analytics";

const WORKFLOW_YAML = `name: Agent Skill Security Gate
on:
  pull_request:
    paths:
      - "**/SKILL.md"
      - "AGENTS.md"
      - "CLAUDE.md"
      - ".cursorrules"
      - "**/.mcp.json"
      - "**/mcp.json"

jobs:
  skill-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ZhuYansen/agent-skills-hub/tools/ci-skill-gate@main
        with:
          fail-on: unsafe
          allowlist: .agentskillshub-allowlist.json
          sarif-out: skill-gate.sarif`;

const ALLOWLIST_JSON = `{
  "expires_at": "2027-03-01",
  "ignore_paths": ["docs/threat-models/**"],
  "entries": [
    {
      "flag": "fenced_download_exec",
      "reason": "Reviewed internal bootstrap doc with Security on 2026-11-16",
      "expires_at": "2027-01-15"
    }
  ]
}`;

export function CiGatePage() {
  const { lang } = useI18n();
  const isZh = lang === "zh";

  const [email, setEmail] = useState("");
  const [githubOrg, setGithubOrg] = useState("");
  const [failPolicy, setFailPolicy] = useState<"unsafe" | "caution">("unsafe");
  const [copiedYaml, setCopiedYaml] = useState(false);
  const [copiedAllowlist, setCopiedAllowlist] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasStripeLink = CHECKOUT_LINKS.cigate.length > 0;

  const copyText = (text: string, which: "yaml" | "allowlist") => {
    navigator.clipboard.writeText(text).then(() => {
      if (which === "yaml") {
        setCopiedYaml(true);
        setTimeout(() => setCopiedYaml(false), 2000);
      } else {
        setCopiedAllowlist(true);
        setTimeout(() => setCopiedAllowlist(false), 2000);
      }
      trackEvent("ci_gate_copy_snippet", { which });
    });
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isCompleteEmail(email.trim())) {
      setError(
        isZh
          ? "请输入完整的团队工作邮箱（如 name@company.com）。"
          : "Please enter a complete work email (e.g. name@company.com).",
      );
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await submitEnterpriseLead(
        {
          email: email.trim(),
          company: githubOrg.trim() || undefined,
          use_case: `Team CI Skill Gate (${USD_PRICING.ciGate}) · fail-on=${failPolicy}`,
          estimated_budget: USD_PRICING.ciGate,
          team_size: "3-20 developers",
          current_stack: "GitHub Actions",
          message: githubOrg.trim()
            ? `GitHub org/repo: ${githubOrg.trim()}, policy: fail-on=${failPolicy}`
            : `Policy: fail-on=${failPolicy}`,
        },
        "ci_gate_page",
        {
          attempt: "ci_gate_lead_attempt",
          submitted: "ci_gate_lead_submitted",
          failed: "ci_gate_lead_failed",
        },
        { policy: failPolicy },
      );
      if (hasStripeLink) {
        const liveUrl = buildStripeCheckoutUrl(CHECKOUT_LINKS.cigate, {
          clientReferenceId: sanitizeStripeRef(
            githubOrg.trim() || "team",
            "cigate",
          ),
          prefilledEmail: email,
        });
        if (liveUrl) {
          trackEvent("cigate_checkout_click", { sku: "cigate", price: USD_PRICING.ciGate });
          window.open(liveUrl, "_blank", "noopener,noreferrer");
        }
      }
      setSubmitted(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : isZh
            ? "提交失败，请稍后重试。"
            : "Failed to submit. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100">
      <Helmet>
        <title>
          {isZh
            ? "Team CI Skill Gate — PR 合并前自动拦截危险 AI Skill 与 MCP 配置 · Agent Skills Hub"
            : "Team CI Skill Gate — Block Risky AI Skills & MCP Configs in PRs · Agent Skills Hub"}
        </title>
        <meta
          name="description"
          content="GitHub Action + SARIF security gate for SKILL.md, AGENTS.md, CLAUDE.md, .cursorrules, and .mcp.json. Built on 43 SlowMist & agent-era rules. Open-source runner + $49/mo Team Gate."
        />
        <link rel="canonical" href="https://agentskillshub.top/ci-gate/" />
      </Helmet>

      <SiteHeader
        breadcrumb={[
          { label: isZh ? "Team CI Skill Gate" : "CI Skill Gate" },
        ]}
      />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-10 space-y-10">
        {/* Hero */}
        <section className="rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white p-6 sm:p-10 shadow-xl border border-indigo-500/20">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-200 text-xs font-semibold mb-4">
            <span>🛡️</span>
            <span>
              {isZh
                ? "GitHub Actions · 零外部依赖 · SARIF 2.1"
                : "GitHub Actions · Zero Dependencies · SARIF 2.1"}
            </span>
          </div>
          <h1 className="text-2xl sm:text-4xl font-bold tracking-tight mb-3">
            {isZh
              ? "在 PR 合并前拦截高危 SKILL.md、.cursorrules 与 MCP 配置"
              : "Block risky SKILL.md, .cursorrules & MCP configs before PR merge"}
          </h1>
          <p className="text-sm sm:text-base text-slate-300 max-w-3xl leading-relaxed mb-6">
            {isZh
              ? "开发者把第三方 skill、提示词规则或 .mcp.json 提进仓库时，普通代码扫描器根本看不懂「隐蔽外传凭证」「不信任脚本 curl|sh」或「提示词覆盖」。Agent Skills Hub CI Gate 把 43 条开源规则打包进一条 GitHub Action。"
              : "Traditional SAST ignores Markdown and MCP JSON. When a PR adds a third-party SKILL.md, CLAUDE.md, .cursorrules, or .mcp.json with covert credential theft, untrusted pipe-to-shell, or prompt injection, CI Gate catches it before merge."}
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href="#team-checkout"
              onClick={() => trackEvent("ci_gate_hero_cta", { cta: "team" })}
              className="px-5 py-2.5 rounded-xl bg-indigo-500 hover:bg-indigo-400 text-white text-sm font-semibold transition-colors shadow-lg shadow-indigo-500/25"
            >
              {isZh
                ? `开通 Team Gate（${USD_PRICING.ciGate}）`
                : `Start Team Gate (${USD_PRICING.ciGate})`}
            </a>
            <a
              href="https://github.com/ZhuYansen/agent-skills-hub/tree/main/tools/ci-skill-gate"
              target="_blank"
              rel="noopener noreferrer"
              className="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-sm font-medium border border-white/15 transition-colors"
            >
              {isZh ? "查看 MIT 开源扫描器代码 →" : "Inspect MIT Runner Source →"}
            </a>
            <Link
              to="/org-audit/"
              className="px-4 py-2.5 rounded-xl text-slate-300 hover:text-white text-sm font-medium transition-colors"
            >
              {isZh ? "或先批量审计整个 GitHub 组织" : "Or batch-audit a GitHub org first"}
            </Link>
          </div>
        </section>

        {/* What it catches */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              badge: "REJECT / UNSAFE",
              tone: "text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40",
              title: isZh ? "外传、后门与未授权下载执行" : "Exfil, backdoors & untrusted pipe-to-shell",
              body: isZh
                ? "识别 SSH/AWS/Agent 凭证外传组合、启动脚本持久化、以及指向陌生域名/GitHub Pages 诱饵按钮的 curl|sh。"
                : "Detects SSH/AWS/agent config theft, startup persistence, GitHub Pages download lures, and curl|sh from non-official hosts.",
            },
            {
              badge: "CAUTION",
              tone: "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40",
              title: isZh ? "提示词劫持与明文硬编码 Key" : "Agent prompt risks & leaked secrets",
              body: isZh
                ? "抓出越狱人设劫持、工具优先级抢占、要求用户在对话贴密码，以及误提交的 OpenAI / Anthropic / AWS / GitHub Token。"
                : "Flags jailbreak overrides, tool-priority manipulation, chat credential harvesting, and real leaked API keys (skipping docs dummies).",
            },
            {
              badge: "ALLOWLIST",
              tone: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40",
              title: isZh ? "带过期时间的团队白名单" : "Expiring repo allowlists + SARIF",
              body: isZh
                ? "通过 .agentskillshub-allowlist.json 为已人工复核的条目设置有效期，并输出 SARIF 2.1 直接接入 GitHub Code Scanning。"
                : "Suppress reviewed findings with time-bounded .agentskillshub-allowlist.json rules and upload SARIF 2.1 straight to GitHub Security.",
            },
          ].map((card) => (
            <div
              key={card.title}
              className="rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 p-5"
            >
              <span
                className={`inline-block text-[11px] font-bold px-2 py-0.5 rounded ${card.tone} mb-2`}
              >
                {card.badge}
              </span>
              <h2 className="text-base font-semibold mb-1.5">{card.title}</h2>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                {card.body}
              </p>
            </div>
          ))}
        </section>

        {/* Copyable GitHub Action + Allowlist */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/80">
              <code className="text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                .github/workflows/skill-gate.yml
              </code>
              <button
                type="button"
                onClick={() => copyText(WORKFLOW_YAML, "yaml")}
                className="px-2.5 py-1 text-xs rounded-md bg-indigo-600 text-white hover:bg-indigo-700 cursor-pointer transition-colors"
              >
                {copiedYaml ? (isZh ? "已复制" : "Copied") : isZh ? "复制 YAML" : "Copy YAML"}
              </button>
            </div>
            <pre className="p-4 text-xs overflow-x-auto text-gray-800 dark:text-gray-200 leading-relaxed">
              <code>{WORKFLOW_YAML}</code>
            </pre>
          </div>

          <div className="rounded-xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/80">
              <code className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                .agentskillshub-allowlist.json
              </code>
              <button
                type="button"
                onClick={() => copyText(ALLOWLIST_JSON, "allowlist")}
                className="px-2.5 py-1 text-xs rounded-md bg-gray-800 dark:bg-gray-700 text-white hover:bg-gray-700 cursor-pointer transition-colors"
              >
                {copiedAllowlist ? (isZh ? "已复制" : "Copied") : isZh ? "复制示例" : "Copy JSON"}
              </button>
            </div>
            <pre className="p-4 text-xs overflow-x-auto text-gray-800 dark:text-gray-200 leading-relaxed">
              <code>{ALLOWLIST_JSON}</code>
            </pre>
          </div>
        </section>

        {/* Pricing comparison + Checkout */}
        <section
          id="team-checkout"
          className="rounded-2xl bg-white dark:bg-gray-900 border border-indigo-200 dark:border-indigo-900/60 p-6 sm:p-8 shadow-sm"
        >
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-6 space-y-4">
              <div className="inline-flex items-center gap-2 text-xs font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">
                {isZh ? "自助团队方案" : "Self-serve team plan"}
              </div>
              <h2 className="text-2xl font-bold">
                Team CI Skill Gate — {USD_PRICING.ciGate}
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {isZh
                  ? "适合 3–20 人的研发/安全团队：静态扫描脚本开源可自查，订阅包含全员 Pro Deep Search + CI 规则同步、白名单策略模板及 48 小时人工误报/例外复核。"
                  : "Built for 3–20 developer teams. The core static runner is MIT open source so your security team can inspect every line; the Team subscription bundles Pro Deep Search/API keys, org onboarding, policy templates, and 48h human triage for tricky PR flags."}
              </p>
              <ul className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
                {(isZh
                  ? [
                      "包含全部 43 条 SlowMist + Agent 时代规则与 SARIF 输出",
                      "附带 Team `ash_pro_` Key，用于 Pro 深度检索、CSV/JSON 导出与 API",
                      "每月最多 3 次高风险/疑难 Skill PR 人工复核（48h 内邮件回执）",
                      "随时取消，不绑定长期合同；仅在需要私有部署/SSO/SOC 2 证据包时升级 Enterprise",
                    ]
                  : [
                      "All 43 SlowMist + agent-era rules with GitHub annotations & SARIF 2.1",
                      "Includes Team `ash_pro_` key for Pro Deep Search, CSV/JSON export & API",
                      "Up to 3 human PR security second-opinions/month within 48h",
                      "Cancel anytime — upgrade to Enterprise only if you need on-prem mirror, SSO, or SOC 2 evidence",
                    ]
                ).map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <span className="text-emerald-500 font-bold mt-0.5">✓</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
              <div className="pt-2 text-xs text-gray-500 dark:text-gray-400">
                {isZh ? "需要私有镜像 / SSO / 合规证据包？" : "Need on-prem mirror, SSO, or compliance evidence?"}{" "}
                <Link
                  to="/enterprise/"
                  className="text-indigo-600 dark:text-indigo-400 hover:underline font-medium"
                >
                  {isZh ? "查看 Enterprise 方案 →" : "See Enterprise →"}
                </Link>
              </div>
            </div>

            <div className="lg:col-span-6 rounded-xl bg-gray-50 dark:bg-gray-950 border border-gray-200 dark:border-gray-800 p-5">
              {submitted ? (
                <div className="py-6 text-center space-y-2">
                  <div className="text-2xl">✓</div>
                  <h3 className="text-base font-semibold">
                    {hasStripeLink
                      ? isZh
                        ? "已打开 Stripe 结账页"
                        : "Stripe Checkout Opened"
                      : isZh
                        ? "已记录 Team CI Gate 开通申请"
                        : "Team CI Gate Request Recorded"}
                  </h3>
                  <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                    {hasStripeLink
                      ? isZh
                        ? "完成付款后，系统会自动发送你的 `ash_pro_` 密钥和团队接入清单到上述邮箱。"
                        : "Once payment clears, we email your `ash_pro_` key and onboarding checklist automatically."
                      : isZh
                        ? "已收到你的邮箱与组织信息，我们将尽快发送 $49/mo Stripe 订阅链接及配置协助。"
                        : "We received your work email and org info, and will send your $49/mo Stripe checkout link and setup guide shortly."}
                  </p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label
                      htmlFor="cigate-email"
                      className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
                    >
                      {isZh ? "工作邮箱（用于接收密钥与告警）*" : "Work email (key & triage delivery) *"}
                    </label>
                    <input
                      id="cigate-email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="security@company.com"
                      className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor="cigate-org"
                      className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
                    >
                      {isZh ? "GitHub 组织或仓库（选填）" : "GitHub org or repository (optional)"}
                    </label>
                    <input
                      id="cigate-org"
                      type="text"
                      value={githubOrg}
                      onChange={(e) => setGithubOrg(e.target.value)}
                      placeholder="acme-ai/agent-skills"
                      className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor="cigate-policy"
                      className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
                    >
                      {isZh ? "默认拦截阈值" : "Default PR block threshold"}
                    </label>
                    <select
                      id="cigate-policy"
                      value={failPolicy}
                      onChange={(e) =>
                        setFailPolicy(
                          e.target.value === "caution" ? "caution" : "unsafe",
                        )
                      }
                      className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="unsafe">
                        {isZh
                          ? "unsafe / reject（推荐：高危与恶意必拦，中危告警）"
                          : "unsafe / reject (recommended: block high-risk, warn on caution)"}
                      </option>
                      <option value="caution">
                        {isZh
                          ? "caution 及以上（严格：含提示词注入/硬编码 Key 也拦截）"
                          : "caution & above (strict: also block prompt-risk / secret cautions)"}
                      </option>
                    </select>
                  </div>

                  {error && (
                    <p className="text-xs text-rose-600 dark:text-rose-400">
                      {error}
                    </p>
                  )}

                  <button
                    type="submit"
                    disabled={submitting}
                    className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-semibold transition-colors cursor-pointer"
                  >
                    {submitting
                      ? isZh
                        ? "提交中…"
                        : "Submitting…"
                      : hasStripeLink
                        ? isZh
                          ? `继续去 Stripe 订阅（${USD_PRICING.ciGate}）`
                          : `Continue to Stripe (${USD_PRICING.ciGate})`
                        : isZh
                          ? `申请开通 Team Gate（${USD_PRICING.ciGate}）`
                          : `Request Team Gate (${USD_PRICING.ciGate})`}
                  </button>
                  <p className="text-[11px] text-gray-500 dark:text-gray-400 leading-relaxed">
                    {isZh
                      ? "透明度承诺：付费不改变任何公开仓库在 Hub 上的安全评级或排名。"
                      : "Neutrality pledge: paying for Team CI Gate never alters public Hub security grades or rankings."}
                  </p>
                </form>
              )}
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}

export default CiGatePage;
