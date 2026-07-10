import { useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { submitSkill } from "../api/client";
import { WorkflowComposeModal } from "../components/WorkflowComposeModal";
import { useI18n } from "../i18n/I18nContext";

const GITHUB_URL_RE = /^https?:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/i;

type SubmitState =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "success"; message: string }
  | { kind: "error"; message: string };

export function SubmitPage() {
  const { lang } = useI18n();
  const isZh = lang === "zh";
  const [repoUrl, setRepoUrl] = useState("");
  const [urlTouched, setUrlTouched] = useState(false);
  const [submitState, setSubmitState] = useState<SubmitState>({ kind: "idle" });
  const [workflowOpen, setWorkflowOpen] = useState(false);

  const urlValid = GITHUB_URL_RE.test(repoUrl.trim());
  const showUrlError = urlTouched && repoUrl.length > 0 && !urlValid;

  async function handleSkillSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!urlValid || submitState.kind === "submitting") return;
    setSubmitState({ kind: "submitting" });
    const okMsg = isZh
      ? "已提交,我们会在 24 小时内审核。"
      : "Submitted. We'll review within 24 hours.";
    const failMsg = isZh ? "提交失败。" : "Submission failed.";
    try {
      const res = await submitSkill(repoUrl.trim());
      if (res.status === "submitted" || res.status === "success") {
        setSubmitState({ kind: "success", message: res.message || okMsg });
        setRepoUrl("");
        setUrlTouched(false);
      } else {
        setSubmitState({ kind: "error", message: res.message || failMsg });
      }
    } catch (err) {
      setSubmitState({
        kind: "error",
        message: err instanceof Error ? err.message : failMsg,
      });
    }
  }

  const perks = isZh
    ? ["认证徽章", "热门加权", "创作者数据", "咨询撮合"]
    : [
        "Authenticated badge",
        "Trending boost",
        "Creator analytics",
        "Consulting leads",
      ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex flex-col">
      <Helmet>
        <title>
          {isZh
            ? "提交到 Hub — AgentSkillsHub"
            : "Submit to the Hub — AgentSkillsHub"}
        </title>
        <meta
          name="description"
          content={
            isZh
              ? "提交 Skill、编排 Workflow,或申请 Verified Creator。向 AgentSkillsHub 目录贡献的三种方式。"
              : "Submit a Skill, compose a Workflow, or apply for Verified Creator. Three ways to contribute to the AgentSkillsHub directory."
          }
        />
        <link rel="canonical" href="https://agentskillshub.top/submit/" />
      </Helmet>
      <SiteHeader />

      <main className="flex-grow w-full max-w-3xl mx-auto px-4 py-10 sm:py-14">
        {/* Hero */}
        <header className="text-center mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-2">
            {isZh ? "提交到 Hub" : "Submit to the Hub"}
          </h1>
          <p className="text-base text-gray-600 dark:text-gray-300">
            {isZh
              ? "三种贡献方式,任选其一。"
              : "Three ways to contribute. Pick yours."}
          </p>
          <div className="mt-6 flex items-center justify-center gap-3 text-xs text-gray-500 dark:text-gray-500">
            <span>
              {isZh ? "已收录 130,000+ skill" : "130,000+ skills indexed"}
            </span>
            <span className="w-1 h-1 bg-gray-300 dark:bg-gray-700 rounded-full" />
            <span>{isZh ? "每 8 小时刷新" : "refreshed every 8h"}</span>
            <span className="w-1 h-1 bg-gray-300 dark:bg-gray-700 rounded-full" />
            <span>CC BY-NC-SA</span>
          </div>
        </header>

        {/* Cards */}
        <div className="space-y-5">
          {/* Card 1 — Submit a Skill */}
          <article className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 sm:p-8 hover:border-indigo-500 hover:shadow-md hover:-translate-y-0.5 transition-all">
            <div className="flex gap-5">
              <div className="flex-none w-12 h-12 bg-indigo-50 dark:bg-indigo-950/40 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-indigo-600 dark:text-indigo-400"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 4v16m8-8H4"
                  />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  {isZh ? "提交一个 Skill" : "Submit a Skill"}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-5 leading-relaxed">
                  {isZh
                    ? "发现或做了一个不错的 Claude Skill、MCP server 或 Codex Skill?贴上 GitHub 链接 —— 我们会在 24 小时内审核并收录。"
                    : "Found or built a great Claude Skill, MCP server, or Codex Skill? Paste the GitHub URL — we'll review and index it within 24 hours."}
                </p>
                <form
                  onSubmit={handleSkillSubmit}
                  className="flex flex-col sm:flex-row gap-2"
                >
                  <input
                    type="url"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    onBlur={() => setUrlTouched(true)}
                    placeholder="https://github.com/owner/repo"
                    className={`flex-1 px-4 py-2.5 bg-white dark:bg-gray-950 border rounded-lg text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-indigo-600/20 outline-none transition-all ${
                      showUrlError
                        ? "border-red-400 focus:border-red-500"
                        : "border-gray-200 dark:border-gray-800 focus:border-indigo-600"
                    }`}
                  />
                  <button
                    type="submit"
                    disabled={!urlValid || submitState.kind === "submitting"}
                    className={`px-6 py-2.5 text-sm font-semibold rounded-lg transition-colors whitespace-nowrap ${
                      urlValid && submitState.kind !== "submitting"
                        ? "bg-indigo-600 hover:bg-indigo-700 text-white"
                        : "bg-gray-200 dark:bg-gray-800 text-gray-400 dark:text-gray-600 cursor-not-allowed"
                    }`}
                  >
                    {submitState.kind === "submitting"
                      ? isZh
                        ? "提交中…"
                        : "Submitting…"
                      : isZh
                        ? "提交"
                        : "Submit"}
                  </button>
                </form>
                {showUrlError && (
                  <p className="text-xs text-red-500 mt-2">
                    {isZh
                      ? "请输入有效的 GitHub 仓库链接(https://github.com/owner/repo)"
                      : "Please enter a valid GitHub repo URL (https://github.com/owner/repo)"}
                  </p>
                )}
                {submitState.kind === "success" && (
                  <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-2">
                    ✓ {submitState.message}
                  </p>
                )}
                {submitState.kind === "error" && (
                  <p className="text-xs text-red-500 mt-2">
                    {submitState.message}
                  </p>
                )}
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-3">
                  {isZh
                    ? "收录要求:README、许可证、≥10 stars 或 有活跃提交"
                    : "Inclusion requires: README, license, ≥10 stars OR active commits"}
                </p>
              </div>
            </div>
          </article>

          {/* Card 2 — Submit a Workflow */}
          <article className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 sm:p-8 hover:border-indigo-500 hover:shadow-md hover:-translate-y-0.5 transition-all">
            <div className="flex gap-5">
              <div className="flex-none w-12 h-12 bg-indigo-50 dark:bg-indigo-950/40 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-indigo-600 dark:text-indigo-400"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4 6h16M4 12h16m-7 6h7"
                  />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  {isZh ? "提交一个 Workflow" : "Submit a Workflow"}
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-5 leading-relaxed">
                  {isZh
                    ? "做了一套多 skill 协作的 agent 工作流?写清步骤、用到的工具和场景。我们会在 "
                    : "Built a multi-skill agent workflow? Document the steps, the tools, and the use case. We feature curated workflows on "}
                  <Link
                    to="/category/workflow/"
                    className="text-indigo-600 dark:text-indigo-400 hover:underline"
                  >
                    /workflows/
                  </Link>
                  {isZh ? " 精选展示。" : "."}
                </p>
                <button
                  type="button"
                  onClick={() => setWorkflowOpen(true)}
                  className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg transition-colors"
                >
                  {isZh ? "编排 Workflow →" : "Compose Workflow →"}
                </button>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-3">
                  {isZh
                    ? "多步表单,约 5 分钟完成。"
                    : "Multi-step form. ~5 minutes to complete."}
                </p>
              </div>
            </div>
          </article>

          {/* Card 3 — Verified Creator */}
          <article className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 sm:p-8 hover:border-indigo-500 hover:shadow-md hover:-translate-y-0.5 transition-all">
            <div className="flex gap-5">
              <div className="flex-none w-12 h-12 bg-indigo-50 dark:bg-indigo-950/40 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-indigo-600 dark:text-indigo-400"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 2L4 6v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V6l-8-4zm-1.4 14.6L6 12l1.4-1.4 3.2 3.2 6.2-6.2L18.2 9l-7.6 7.6z" />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-start mb-2 gap-3">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    {isZh
                      ? "申请 Verified Creator"
                      : "Apply for Verified Creator"}
                  </h2>
                  <span className="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap pt-1">
                    {isZh ? "5 天内审核" : "Reviewed within 5 days"}
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-5 leading-relaxed">
                  {isZh
                    ? "为严肃的 Skill 作者而设。获得认证徽章、热门加权、创作者数据,以及咨询撮合。"
                    : "For serious Skill authors. Get a verified badge, trending boost, creator analytics, and consulting matchmaking."}
                </p>
                <div className="grid grid-cols-2 gap-y-2 gap-x-5 mb-5">
                  {perks.map((perk) => (
                    <div key={perk} className="flex items-center gap-2 text-sm">
                      <svg
                        className="w-4 h-4 text-emerald-500 flex-none"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                          clipRule="evenodd"
                        />
                      </svg>
                      <span className="text-gray-700 dark:text-gray-300">
                        {perk}
                      </span>
                    </div>
                  ))}
                </div>
                <Link
                  to="/verified-creator/apply/"
                  className="inline-block px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg transition-colors"
                >
                  {isZh ? "开始申请 →" : "Start Application →"}
                </Link>
              </div>
            </div>
          </article>
        </div>

        {/* Bottom — Enterprise banner */}
        <section className="mt-10 bg-gray-100 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-800 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="flex-none w-10 h-10 bg-gray-200 dark:bg-gray-800 rounded-lg flex items-center justify-center">
              <svg
                className="w-5 h-5 text-gray-600 dark:text-gray-400"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                {isZh ? "需要企业级视角?" : "Need an enterprise-grade view?"}
              </h3>
              <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                {isZh
                  ? "安全审计、SBOM、合规标签、私有镜像。为法务与技术决策者而建。"
                  : "Security audits, SBOM, compliance tags, private mirrors. Built for legal and tech decision-makers."}
              </p>
            </div>
          </div>
          <Link
            to="/enterprise/"
            className="flex-none px-4 py-2 border border-gray-300 dark:border-gray-700 hover:border-indigo-500 hover:text-indigo-600 dark:hover:text-indigo-400 text-sm font-medium text-gray-700 dark:text-gray-300 rounded-lg transition-colors text-center"
          >
            {isZh ? "查看企业版 →" : "See Enterprise →"}
          </Link>
        </section>
      </main>

      <SiteFooter />

      {workflowOpen && (
        <WorkflowComposeModal onClose={() => setWorkflowOpen(false)} />
      )}
    </div>
  );
}
