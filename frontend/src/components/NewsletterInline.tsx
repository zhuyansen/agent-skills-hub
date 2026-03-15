import { useState } from "react";
import { subscribe } from "../api/client";
import { useI18n } from "../i18n/I18nContext";

export function NewsletterInline() {
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setStatus("loading");
    try {
      await subscribe(email);
      setStatus("success");
    } catch {
      setStatus("error");
    }
  };

  if (status === "success") {
    return (
      <div className="my-6 px-4 py-3 bg-green-50 border border-green-200 rounded-xl text-center text-sm text-green-700">
        <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        {t("newsletter.checkEmail")}
      </div>
    );
  }

  return (
    <div className="my-6 bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-100 rounded-xl px-4 py-3 flex flex-col sm:flex-row items-center gap-3">
      <div className="flex items-center gap-2 shrink-0">
        <svg className="w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        <span className="text-sm font-medium text-indigo-700">{t("newsletter.inlineTitle")}</span>
      </div>
      <form onSubmit={handleSubmit} className="flex items-center gap-2 flex-1 w-full sm:w-auto">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder={t("newsletter.placeholder")}
          className="flex-1 px-3 py-2 text-sm rounded-lg border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 min-w-0"
          required
        />
        <button
          type="submit"
          disabled={status === "loading"}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50 shrink-0 cursor-pointer"
        >
          {status === "loading" ? "..." : t("newsletter.button")}
        </button>
      </form>
      {status === "error" && (
        <span className="text-xs text-red-500">{t("newsletter.error")}</span>
      )}
    </div>
  );
}
