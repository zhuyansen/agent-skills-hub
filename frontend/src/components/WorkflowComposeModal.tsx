import { useEffect, useState } from "react";
import { submitWorkflow } from "../api/client";

interface WorkflowStep {
  name: string;
  slug: string;
  description: string;
}

interface Props {
  onClose: () => void;
}

export function WorkflowComposeModal({ onClose }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [steps, setSteps] = useState<WorkflowStep[]>([
    { name: "", slug: "", description: "" },
    { name: "", slug: "", description: "" },
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{
    status: string;
    message: string;
  } | null>(null);

  // Close on Esc
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const updateStep = (
    idx: number,
    field: keyof WorkflowStep,
    value: string,
  ) => {
    setSteps((prev) =>
      prev.map((s, i) => (i === idx ? { ...s, [field]: value } : s)),
    );
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

  const validStepCount = steps.filter(
    (s) => s.name.trim() && s.slug.trim(),
  ).length;
  const canSubmit =
    name.trim().length > 0 && validStepCount >= 2 && !submitting;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    const validSteps = steps.filter((s) => s.name.trim() && s.slug.trim());
    setSubmitting(true);
    setResult(null);
    try {
      const res = await submitWorkflow(
        name.trim(),
        description.trim(),
        validSteps,
      );
      setResult(res);
      if (res.status === "submitted") {
        setName("");
        setDescription("");
        setSteps([
          { name: "", slug: "", description: "" },
          { name: "", slug: "", description: "" },
        ]);
      }
    } catch (err: unknown) {
      setResult({
        status: "error",
        message: err instanceof Error ? err.message : "Submission failed",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-sm overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="relative bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl shadow-xl max-w-2xl w-full my-8 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-6 py-4 flex items-center justify-between rounded-t-xl">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Compose a Workflow
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Document a multi-step agent workflow. 2-5 steps, ~5 minutes.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                Workflow Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  setResult(null);
                }}
                placeholder="e.g. Research → Draft → Publish"
                required
                className="w-full px-3 py-2 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                Short Description
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What problem does it solve?"
                className="w-full px-3 py-2 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition-all"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-gray-700 dark:text-gray-300">
                Steps <span className="text-red-500">*</span>{" "}
                <span className="font-normal text-gray-400">
                  (2-5 steps, each pointing at an indexed Skill or repo)
                </span>
              </label>
              <span className="text-xs text-gray-400">
                {validStepCount}/{steps.length} valid
              </span>
            </div>
            <div className="space-y-2">
              {steps.map((step, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="w-6 h-6 mt-2 rounded-full bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-xs font-bold flex-none">
                    {idx + 1}
                  </span>
                  <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <input
                      type="text"
                      value={step.name}
                      onChange={(e) => updateStep(idx, "name", e.target.value)}
                      placeholder="Step name"
                      className="px-3 py-2 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition-all"
                    />
                    <input
                      type="text"
                      value={step.slug}
                      onChange={(e) => updateStep(idx, "slug", e.target.value)}
                      placeholder="owner/repo"
                      className="px-3 py-2 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition-all"
                    />
                    <input
                      type="text"
                      value={step.description}
                      onChange={(e) =>
                        updateStep(idx, "description", e.target.value)
                      }
                      placeholder="What it does"
                      className="px-3 py-2 bg-white dark:bg-gray-950 border border-gray-200 dark:border-gray-800 rounded-lg text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 outline-none transition-all"
                    />
                  </div>
                  {steps.length > 2 && (
                    <button
                      type="button"
                      onClick={() => removeStep(idx)}
                      aria-label="Remove step"
                      className="mt-2 text-gray-400 hover:text-red-500 transition-colors"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M6 18L18 6M6 6l12 12"
                        />
                      </svg>
                    </button>
                  )}
                </div>
              ))}
              {steps.length < 5 && (
                <button
                  type="button"
                  onClick={addStep}
                  className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
                >
                  + Add step
                </button>
              )}
            </div>
          </div>

          {result && (
            <div
              className={`px-3 py-2 rounded-lg text-sm ${
                result.status === "submitted"
                  ? "bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-900"
                  : "bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400 border border-red-100 dark:border-red-900"
              }`}
            >
              {result.message}
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2 border-t border-gray-200 dark:border-gray-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!canSubmit}
              className={`px-5 py-2 text-sm font-semibold rounded-lg transition-colors flex items-center gap-2 ${
                canSubmit
                  ? "bg-indigo-600 hover:bg-indigo-700 text-white"
                  : "bg-gray-200 dark:bg-gray-800 text-gray-400 dark:text-gray-600 cursor-not-allowed"
              }`}
            >
              {submitting && (
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              )}
              {submitting ? "Submitting…" : "Submit Workflow"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
