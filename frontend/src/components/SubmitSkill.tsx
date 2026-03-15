import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { submitSkill, submitMasterApplication, submitWorkflow } from "../api/client";
import { useI18n } from "../i18n/I18nContext";
import type { TransKey } from "../i18n/translations";

type SubmitTab = "skill" | "master" | "workflow";

export function SubmitSkill() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<SubmitTab>("skill");

  return (
    <section className="mt-10 mb-4">
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800/80 dark:to-gray-800/80 rounded-xl border border-blue-100 dark:border-gray-700 p-5 sm:p-6">
        {/* Tab selector */}
        <div className="flex items-center gap-1 mb-4 bg-white/60 dark:bg-gray-900/60 rounded-lg p-1 border border-blue-100 dark:border-gray-700">
          <button
            onClick={() => setActiveTab("skill")}
            className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors cursor-pointer ${
              activeTab === "skill"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
            }`}
          >
            <svg className="w-4 h-4 inline -mt-0.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {t("submit.tabSkill")}
          </button>
          <button
            onClick={() => setActiveTab("master")}
            className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors cursor-pointer ${
              activeTab === "master"
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
            }`}
          >
            <svg className="w-4 h-4 inline -mt-0.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            {t("submit.tabMaster")}
          </button>
          <button
            onClick={() => setActiveTab("workflow")}
            className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors cursor-pointer ${
              activeTab === "workflow"
                ? "bg-purple-600 text-white shadow-sm"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
            }`}
          >
            <svg className="w-4 h-4 inline -mt-0.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {t("submit.tabWorkflow")}
          </button>
        </div>

        {activeTab === "skill" ? (
          <SkillForm t={t} navigate={navigate} />
        ) : activeTab === "master" ? (
          <MasterForm t={t} />
        ) : (
          <WorkflowForm t={t} />
        )}
      </div>
    </section>
  );
}

/* ── Skill Submission Form ── */
function SkillForm({ t, navigate }: { t: (key: TransKey) => string; navigate: ReturnType<typeof useNavigate> }) {
  const [url, setUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ status: string; message: string; skill_id?: number } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim() || submitting) return;
    setSubmitting(true);
    setResult(null);
    try {
      const res = await submitSkill(url.trim());
      setResult(res);
      if (res.status === "already_tracked" && res.skill_id) {
        setTimeout(() => navigate(`/skill/${res.skill_id}`), 1500);
      }
      if (res.status === "submitted") {
        setUrl("");
      }
    } catch (err: any) {
      setResult({ status: "error", message: err.message || "Submission failed" });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <div className="flex items-start gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
          <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </div>
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">{t("submit.title")}</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{t("submit.subtitle")}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={url}
          onChange={(e) => { setUrl(e.target.value); setResult(null); }}
          placeholder="https://github.com/owner/repo"
          className="flex-1 px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          aria-label="GitHub repository URL"
        />
        <button
          type="submit"
          disabled={!url.trim() || submitting}
          className="px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shrink-0 flex items-center gap-2"
        >
          {submitting && (
            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          )}
          {t("submit.button")}
        </button>
      </form>

      {result && (
        <div className={`mt-3 px-3 py-2 rounded-lg text-sm ${
          result.status === "submitted"
            ? "bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 border border-green-100 dark:border-green-800"
            : result.status === "already_tracked"
            ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 border border-blue-100 dark:border-blue-800"
            : result.status === "already_submitted"
            ? "bg-yellow-50 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 border border-yellow-100 dark:border-yellow-800"
            : "bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-100 dark:border-red-800"
        }`}>
          {result.status === "submitted" && (
            <svg className="w-4 h-4 inline -mt-0.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          )}
          {result.message}
        </div>
      )}
    </>
  );
}

/* ── Master Application Form ── */
function MasterForm({ t }: { t: (key: TransKey) => string }) {
  const [github, setGithub] = useState("");
  const [name, setName] = useState("");
  const [bio, setBio] = useState("");
  const [repoUrls, setRepoUrls] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ status: string; message: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!github.trim() || !name.trim() || submitting) return;
    setSubmitting(true);
    setResult(null);
    try {
      const urls = repoUrls
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
      const res = await submitMasterApplication(github.trim(), name.trim(), bio.trim(), urls);
      setResult(res);
      if (res.status === "submitted") {
        setGithub("");
        setName("");
        setBio("");
        setRepoUrls("");
      }
    } catch (err: any) {
      setResult({ status: "error", message: err.message || "Submission failed" });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <div className="flex items-start gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center shrink-0">
          <svg className="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">{t("submit.masterTitle")}</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{t("submit.masterSubtitle")}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <input
            type="text"
            value={github}
            onChange={(e) => { setGithub(e.target.value); setResult(null); }}
            placeholder={t("submit.masterGithub")}
            required
            className="px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            aria-label="GitHub username"
          />
          <input
            type="text"
            value={name}
            onChange={(e) => { setName(e.target.value); setResult(null); }}
            placeholder={t("submit.masterName")}
            required
            className="px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            aria-label="Display name"
          />
        </div>
        <input
          type="text"
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          placeholder={t("submit.masterBio")}
          className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          aria-label="Bio"
        />
        <textarea
          value={repoUrls}
          onChange={(e) => setRepoUrls(e.target.value)}
          placeholder={t("submit.masterRepos")}
          rows={3}
          className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
          aria-label="Repository URLs"
        />
        <button
          type="submit"
          disabled={!github.trim() || !name.trim() || submitting}
          className="w-full sm:w-auto px-5 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer flex items-center justify-center gap-2"
        >
          {submitting && (
            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          )}
          {t("submit.masterButton")}
        </button>
      </form>

      {result && (
        <div className={`mt-3 px-3 py-2 rounded-lg text-sm ${
          result.status === "submitted"
            ? "bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 border border-green-100 dark:border-green-800"
            : "bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-100 dark:border-red-800"
        }`}>
          {result.status === "submitted" && (
            <svg className="w-4 h-4 inline -mt-0.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          )}
          {result.message}
        </div>
      )}
    </>
  );
}

/* ── Workflow Submission Form ── */
interface WorkflowStep {
  name: string;
  slug: string;
  description: string;
}

function WorkflowForm({ t }: { t: (key: TransKey) => string }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [steps, setSteps] = useState<WorkflowStep[]>([
    { name: "", slug: "", description: "" },
    { name: "", slug: "", description: "" },
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ status: string; message: string } | null>(null);

  const updateStep = (idx: number, field: keyof WorkflowStep, value: string) => {
    setSteps((prev) => prev.map((s, i) => (i === idx ? { ...s, [field]: value } : s)));
  };

  const addStep = () => {
    if (steps.length < 5) {
      setSteps((prev) => [...prev, { name: "", slug: "", description: "" }]);
    }
  };

  const removeStep = (idx: number) => {
    if (steps.length > 2) {
      setSteps((prev) => prev.filter((_, i) => i !== idx));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || submitting) return;
    const validSteps = steps.filter((s) => s.name.trim() && s.slug.trim());
    if (validSteps.length < 2) return;
    setSubmitting(true);
    setResult(null);
    try {
      const res = await submitWorkflow(name.trim(), description.trim(), validSteps);
      setResult(res);
      if (res.status === "submitted") {
        setName("");
        setDescription("");
        setSteps([
          { name: "", slug: "", description: "" },
          { name: "", slug: "", description: "" },
        ]);
      }
    } catch (err: any) {
      setResult({ status: "error", message: err.message || "Submission failed" });
    } finally {
      setSubmitting(false);
    }
  };

  const validStepCount = steps.filter((s) => s.name.trim() && s.slug.trim()).length;

  return (
    <>
      <div className="flex items-start gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center shrink-0">
          <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">{t("submit.workflowTitle")}</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{t("submit.workflowSubtitle")}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <input
            type="text"
            value={name}
            onChange={(e) => { setName(e.target.value); setResult(null); }}
            placeholder={t("submit.workflowName")}
            required
            className="px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={t("submit.workflowDesc")}
            className="px-4 py-2.5 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>

        {/* Workflow steps */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-500 dark:text-gray-400">{t("submit.workflowSteps")}</label>
          {steps.map((step, idx) => (
            <div key={idx} className="flex items-start gap-2">
              <span className="w-5 h-5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 flex items-center justify-center text-[10px] font-bold shrink-0 mt-2.5">
                {idx + 1}
              </span>
              <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-2">
                <input
                  type="text"
                  value={step.name}
                  onChange={(e) => updateStep(idx, "name", e.target.value)}
                  placeholder={t("submit.workflowStepName")}
                  className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <input
                  type="text"
                  value={step.slug}
                  onChange={(e) => updateStep(idx, "slug", e.target.value)}
                  placeholder="owner/repo"
                  className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <input
                  type="text"
                  value={step.description}
                  onChange={(e) => updateStep(idx, "description", e.target.value)}
                  placeholder={t("submit.workflowStepDesc")}
                  className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              {steps.length > 2 && (
                <button
                  type="button"
                  onClick={() => removeStep(idx)}
                  className="mt-2 text-gray-400 dark:text-gray-500 hover:text-red-500 transition-colors cursor-pointer"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          ))}
          {steps.length < 5 && (
            <button
              type="button"
              onClick={addStep}
              className="text-xs text-purple-500 hover:text-purple-700 font-medium cursor-pointer"
            >
              + {t("submit.workflowAddStep")}
            </button>
          )}
        </div>

        <button
          type="submit"
          disabled={!name.trim() || validStepCount < 2 || submitting}
          className="w-full sm:w-auto px-5 py-2.5 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer flex items-center justify-center gap-2"
        >
          {submitting && (
            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          )}
          {t("submit.workflowButton")}
        </button>
      </form>

      {result && (
        <div className={`mt-3 px-3 py-2 rounded-lg text-sm ${
          result.status === "submitted"
            ? "bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 border border-green-100 dark:border-green-800"
            : "bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-100 dark:border-red-800"
        }`}>
          {result.status === "submitted" && (
            <svg className="w-4 h-4 inline -mt-0.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          )}
          {result.message}
        </div>
      )}
    </>
  );
}
