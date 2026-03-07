import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { submitSkill } from "../api/client";
import { useI18n } from "../i18n/I18nContext";

export function SubmitSkill() {
  const { t } = useI18n();
  const navigate = useNavigate();
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
    <section className="mt-10 mb-4">
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-100 p-5 sm:p-6">
        <div className="flex items-start gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center shrink-0">
            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{t("submit.title")}</h3>
            <p className="text-sm text-gray-500 mt-0.5">{t("submit.subtitle")}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={url}
            onChange={(e) => { setUrl(e.target.value); setResult(null); }}
            placeholder="https://github.com/owner/repo"
            className="flex-1 px-4 py-2.5 border border-gray-200 rounded-lg bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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

        {/* Result feedback */}
        {result && (
          <div className={`mt-3 px-3 py-2 rounded-lg text-sm ${
            result.status === "submitted"
              ? "bg-green-50 text-green-700 border border-green-100"
              : result.status === "already_tracked"
              ? "bg-blue-50 text-blue-700 border border-blue-100"
              : result.status === "already_submitted"
              ? "bg-yellow-50 text-yellow-700 border border-yellow-100"
              : "bg-red-50 text-red-700 border border-red-100"
          }`}>
            {result.status === "submitted" && (
              <svg className="w-4 h-4 inline -mt-0.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            )}
            {result.message}
          </div>
        )}
      </div>
    </section>
  );
}
