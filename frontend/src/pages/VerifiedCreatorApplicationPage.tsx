import { useMemo, useState } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { submitVerifiedCreatorApplication } from "../api/client";

const SKILL_CATEGORIES = [
  "MCP Server",
  "Claude Skill",
  "Codex Skill",
  "Agent Tool",
  "Reference/Knowledge",
  "Communication",
  "Workflow Orchestration",
  "Code Quality",
  "CI/CD",
] as const;

const TIMEZONES = [
  { value: "UTC", label: "UTC (Default)" },
  { value: "Asia/Shanghai", label: "Asia/Shanghai (UTC +8)" },
  { value: "Asia/Tokyo", label: "Asia/Tokyo (UTC +9)" },
  { value: "Europe/London", label: "Europe/London (UTC 0)" },
  { value: "Europe/Berlin", label: "Europe/Berlin (UTC +1)" },
  { value: "America/New_York", label: "America/New_York (UTC -5)" },
  { value: "America/Los_Angeles", label: "America/Los_Angeles (UTC -8)" },
  { value: "Asia/Kolkata", label: "Asia/Kolkata (UTC +5:30)" },
];

const BIO_MAX = 140;
const MAX_CATEGORIES = 3;

type SubmitState = "idle" | "submitting" | "success" | "error";

export function VerifiedCreatorApplicationPage() {
  const [displayName, setDisplayName] = useState("");
  const [githubUsername, setGithubUsername] = useState("");
  const [categories, setCategories] = useState<string[]>([]);
  const [timezone, setTimezone] = useState("UTC");
  const [forHire, setForHire] = useState(false);
  const [rateMin, setRateMin] = useState("");
  const [rateMax, setRateMax] = useState("");
  const [bio, setBio] = useState("");
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const canSubmit = useMemo(() => {
    const baseValid =
      displayName.trim().length > 0 &&
      githubUsername.trim().length > 0 &&
      categories.length > 0 &&
      categories.length <= MAX_CATEGORIES;
    if (!forHire) return baseValid;
    return baseValid && bio.trim().length > 0;
  }, [displayName, githubUsername, categories, forHire, bio]);

  function toggleCategory(cat: string) {
    setCategories((prev) => {
      if (prev.includes(cat)) return prev.filter((c) => c !== cat);
      if (prev.length >= MAX_CATEGORIES) return prev;
      return [...prev, cat];
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit || submitState === "submitting") return;
    setSubmitState("submitting");
    setErrorMessage("");
    try {
      const result = await submitVerifiedCreatorApplication({
        display_name: displayName.trim(),
        github_username: githubUsername.trim().replace(/^@/, ""),
        skill_categories: categories,
        timezone,
        available_for_hire: forHire,
        rate_min: forHire && rateMin ? Number(rateMin) : null,
        rate_max: forHire && rateMax ? Number(rateMax) : null,
        bio: forHire ? bio.trim() : "",
      });
      if (result.status === "submitted") {
        setSubmitState("success");
      } else {
        setSubmitState("error");
        setErrorMessage(result.message || "Submission failed.");
      }
    } catch (err) {
      setSubmitState("error");
      setErrorMessage(
        err instanceof Error ? err.message : "Submission failed.",
      );
    }
  }

  if (submitState === "success") {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
        <Helmet>
          <title>Application Submitted — AgentSkillsHub</title>
        </Helmet>
        <SiteHeader />
        <main className="max-w-xl mx-auto px-4 py-16">
          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <svg
                width="32"
                height="32"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Application submitted
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-6">
              We'll review within 5 business days. If approved, you'll get an
              email with next steps.
            </p>
            <Link
              to="/verified-creator/"
              className="inline-block px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              Back to Verified Creator
            </Link>
          </div>
        </main>
        <SiteFooter />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Helmet>
        <title>Apply for Verified Creator — AgentSkillsHub</title>
        <meta
          name="description"
          content="Apply for the AgentSkillsHub Verified Creator badge. For serious Skill authors who want recognition, trending boost, and consulting matchmaking."
        />
        <link
          rel="canonical"
          href="https://agentskillshub.top/verified-creator/apply/"
        />
      </Helmet>
      <SiteHeader />

      <main className="max-w-3xl mx-auto px-4 py-10 sm:py-14 pb-32">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-3">
            Apply for Verified Creator
          </h1>
          <p className="text-base text-gray-600 dark:text-gray-300 max-w-xl mx-auto">
            Tell us who you are, what you build, and how to reach you. Manual
            review within 5 business days.
          </p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-between mb-12 max-w-md mx-auto">
          {[
            { n: 1, label: "Identity" },
            { n: 2, label: "Skills" },
            { n: 3, label: "Review" },
          ].map((step, i) => (
            <div
              key={step.n}
              className="flex items-center flex-1 last:flex-none"
            >
              <div className="flex flex-col items-center gap-2">
                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center font-semibold text-sm ${
                    step.n === 1
                      ? "bg-indigo-600 text-white"
                      : "border-2 border-gray-300 dark:border-gray-700 text-gray-400 dark:text-gray-600"
                  }`}
                >
                  {step.n}
                </div>
                <span
                  className={`text-xs font-semibold tracking-wide uppercase ${
                    step.n === 1
                      ? "text-indigo-600 dark:text-indigo-400"
                      : "text-gray-400 dark:text-gray-600"
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {i < 2 && (
                <div className="h-px bg-gray-200 dark:bg-gray-800 flex-1 -mt-6 mx-2" />
              )}
            </div>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-10">
          {/* SECTION 1 */}
          <section>
            <h2 className="text-xs font-semibold tracking-widest uppercase text-gray-500 dark:text-gray-400 mb-4">
              Section 1 · Identity
            </h2>
            <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6 space-y-5">
              <div>
                <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                  Display Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="How should we credit you?"
                  className="w-full px-4 py-2.5 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                  GitHub Username <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
                    @
                  </span>
                  <input
                    type="text"
                    value={githubUsername}
                    onChange={(e) => setGithubUsername(e.target.value)}
                    placeholder="your-handle"
                    className="w-full pl-9 pr-4 py-2.5 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition-all"
                  />
                </div>
              </div>
            </div>
          </section>

          {/* SECTION 2 */}
          <section>
            <h2 className="text-xs font-semibold tracking-widest uppercase text-gray-500 dark:text-gray-400 mb-4">
              Section 2 · Skills & Availability
            </h2>
            <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6 space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-1">
                  Primary Skill Categories{" "}
                  <span className="text-red-500">*</span>
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                  Choose 1-3 categories that best represent your work. (
                  {categories.length}/{MAX_CATEGORIES})
                </p>
                <div className="flex flex-wrap gap-2">
                  {SKILL_CATEGORIES.map((cat) => {
                    const selected = categories.includes(cat);
                    const disabled =
                      !selected && categories.length >= MAX_CATEGORIES;
                    return (
                      <button
                        key={cat}
                        type="button"
                        onClick={() => toggleCategory(cat)}
                        disabled={disabled}
                        className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
                          selected
                            ? "border-indigo-600 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300"
                            : disabled
                              ? "border-gray-200 dark:border-gray-800 text-gray-300 dark:text-gray-700 cursor-not-allowed"
                              : "border-gray-200 dark:border-gray-800 text-gray-600 dark:text-gray-300 hover:border-indigo-600 hover:text-indigo-600 dark:hover:text-indigo-400"
                        }`}
                      >
                        {cat}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="grid sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Time Zone <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="w-full px-4 py-2.5 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition-all"
                  >
                    {TIMEZONES.map((tz) => (
                      <option key={tz.value} value={tz.value}>
                        {tz.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="flex items-center justify-between text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    <span>Available for Hire</span>
                    <button
                      type="button"
                      role="switch"
                      aria-checked={forHire}
                      onClick={() => setForHire(!forHire)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        forHire
                          ? "bg-indigo-600"
                          : "bg-gray-300 dark:bg-gray-700"
                      }`}
                    >
                      <span
                        className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition-transform ${
                          forHire ? "translate-x-[22px]" : "translate-x-0.5"
                        }`}
                      />
                    </button>
                  </label>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Allow teams to contact you for custom skill development.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* SECTION 3 — only when forHire */}
          {forHire && (
            <section>
              <h2 className="text-xs font-semibold tracking-widest uppercase text-gray-500 dark:text-gray-400 mb-4">
                Section 3 · Consulting
              </h2>
              <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6 space-y-5">
                <div>
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-2">
                    Hourly Rate Range{" "}
                    <span className="text-gray-400 text-xs font-normal">
                      (optional)
                    </span>
                  </label>
                  <div className="flex items-center gap-3">
                    <div className="relative flex-1">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 text-sm">
                        $
                      </span>
                      <input
                        type="number"
                        min="0"
                        value={rateMin}
                        onChange={(e) => setRateMin(e.target.value)}
                        placeholder="Min"
                        className="w-full pl-8 pr-4 py-2.5 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition-all"
                      />
                    </div>
                    <span className="text-gray-400">—</span>
                    <div className="relative flex-1">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 text-sm">
                        $
                      </span>
                      <input
                        type="number"
                        min="0"
                        value={rateMax}
                        onChange={(e) => setRateMax(e.target.value)}
                        placeholder="Max"
                        className="w-full pl-8 pr-4 py-2.5 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition-all"
                      />
                    </div>
                    <span className="text-sm text-gray-500 dark:text-gray-400 font-medium whitespace-nowrap">
                      USD / hr
                    </span>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <label className="block text-sm font-semibold text-gray-900 dark:text-white">
                      One-line Bio <span className="text-red-500">*</span>
                    </label>
                    <span
                      className={`text-xs font-medium ${
                        bio.length > BIO_MAX * 0.9
                          ? "text-orange-500"
                          : "text-gray-400"
                      }`}
                    >
                      {bio.length}/{BIO_MAX}
                    </span>
                  </div>
                  <textarea
                    value={bio}
                    onChange={(e) => setBio(e.target.value.slice(0, BIO_MAX))}
                    rows={3}
                    placeholder="What problem do you solve best?"
                    className="w-full px-4 py-2.5 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition-all resize-none"
                  />
                </div>
              </div>
            </section>
          )}

          {/* Verification info card */}
          <div className="bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900 rounded-xl p-5 flex gap-4">
            <div className="flex-none w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12 2L4 6v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V6l-8-4zm-1.4 14.6L6 12l1.4-1.4 3.2 3.2 6.2-6.2L18.2 9l-7.6 7.6z" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                Verification Process
              </h3>
              <p className="text-xs text-gray-600 dark:text-gray-300 leading-relaxed">
                Our review team analyzes your GitHub contributions and indexed
                Skills on Hub. Verified badges are awarded to authors with
                sustained quality and clear documentation.
              </p>
            </div>
          </div>

          {errorMessage && (
            <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900 rounded-lg p-4 text-sm text-red-700 dark:text-red-400">
              {errorMessage}
            </div>
          )}
        </form>
      </main>

      {/* Sticky bottom action bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 z-40">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <div className="text-xs text-gray-500 dark:text-gray-400 hidden sm:block">
            Manual review within 5 business days
          </div>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit || submitState === "submitting"}
            className={`px-6 py-2.5 text-sm font-semibold rounded-lg transition-colors ${
              canSubmit && submitState !== "submitting"
                ? "bg-indigo-600 hover:bg-indigo-700 text-white"
                : "bg-gray-200 dark:bg-gray-800 text-gray-400 dark:text-gray-600 cursor-not-allowed"
            }`}
          >
            {submitState === "submitting" ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Submitting…
              </span>
            ) : (
              "Submit Application"
            )}
          </button>
        </div>
      </div>

      <SiteFooter />
    </div>
  );
}
