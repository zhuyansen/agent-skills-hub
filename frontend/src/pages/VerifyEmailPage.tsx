import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { verifyEmail } from "../api/client";
import { useI18n } from "../i18n/I18nContext";

export function VerifyEmailPage() {
  const { t } = useI18n();
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [status, setStatus] = useState<
    "loading" | "success" | "already" | "error"
  >("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("No verification token provided.");
      return;
    }

    verifyEmail(token)
      .then((res) => {
        setStatus(
          res.status === "success"
            ? "success"
            : res.status === "already"
              ? "already"
              : "error",
        );
        setMessage(res.message);
      })
      .catch((err) => {
        setStatus("error");
        setMessage(err.message || "Verification failed.");
      });
  }, [token]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <Helmet>
        <title>Verify Email - AgentSkillsHub</title>
      </Helmet>
      <div className="bg-white p-8 rounded-xl shadow-lg border border-gray-200 w-full max-w-md text-center">
        {status === "loading" && (
          <>
            <div className="w-12 h-12 border-3 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <h2 className="text-lg font-semibold text-gray-900">
              Verifying your email...
            </h2>
          </>
        )}
        {(status === "success" || status === "already") && (
          <>
            <div
              className={`w-16 h-16 ${status === "success" ? "bg-green-100" : "bg-blue-100"} rounded-full flex items-center justify-center mx-auto mb-4`}
            >
              <svg
                className={`w-8 h-8 ${status === "success" ? "text-green-600" : "text-blue-600"}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d={
                    status === "success"
                      ? "M5 13l4 4L19 7"
                      : "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  }
                />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              {status === "success" ? "Email Verified! 🎉" : "Already Verified"}
            </h2>
            <p className="text-sm text-gray-500">{message}</p>

            {/* PDF Lead Magnet — the reason they subscribed */}
            <div className="mt-6 p-5 bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 border border-indigo-200 dark:border-indigo-800 rounded-xl">
              <div className="flex items-start gap-3 mb-3">
                <span className="text-3xl">📚</span>
                <div className="text-left flex-1">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">
                    Skill 蓝皮书 2026 · v1.0
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    130+ pages · 12 chapters · ~75K words · 5.3 MB
                  </p>
                </div>
              </div>
              <a
                href="https://github.com/zhuyansen/skill-blue-book/releases/download/v1.0/skill-blue-book-2026-v1.0.pdf"
                target="_blank"
                rel="noopener noreferrer"
                className="block w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg text-center transition-colors"
              >
                ⬇ Download Free PDF
              </a>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-3 text-center">
                Or read online:{" "}
                <a
                  href="https://agentskillshub.top/book/"
                  className="text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  agentskillshub.top/book/
                </a>
              </p>
            </div>

            <p className="text-xs text-gray-400 dark:text-gray-500 mt-4">
              You'll also receive our weekly newsletter every Monday.
            </p>
          </>
        )}
        {status === "error" && (
          <>
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Verification Failed
            </h2>
            <p className="text-sm text-gray-500">{message}</p>
          </>
        )}
        <Link
          to="/"
          className="inline-block mt-6 px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          {t("detail.backToHome")}
        </Link>
      </div>
    </div>
  );
}
