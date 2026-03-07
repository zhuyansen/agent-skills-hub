import { useState } from "react";
import { useI18n } from "../i18n/I18nContext";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export function NewsletterSubscribe() {
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || status === "loading") return;

    setStatus("loading");
    setMessage("");
    try {
      const res = await fetch(`${API_BASE}/api/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Subscription failed");
      setStatus("success");
      setMessage(data.message || t("newsletter.success"));
      setEmail("");
    } catch (err: any) {
      setStatus("error");
      setMessage(err.message || t("newsletter.error"));
    }
  };

  return (
    <section className="mt-10 mb-4">
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl border border-indigo-100 p-5 sm:p-6">
        <div className="flex items-start gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center shrink-0">
            <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{t("newsletter.title")}</h3>
            <p className="text-sm text-gray-500 mt-0.5">{t("newsletter.subtitle")}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="email"
            value={email}
            onChange={(e) => { setEmail(e.target.value); if (status !== "idle") setStatus("idle"); }}
            placeholder={t("newsletter.placeholder")}
            required
            className="flex-1 px-4 py-2.5 border border-gray-200 rounded-lg bg-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            aria-label="Email address"
          />
          <button
            type="submit"
            disabled={!email.trim() || status === "loading"}
            className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shrink-0 flex items-center gap-2"
          >
            {status === "loading" && (
              <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            )}
            {t("newsletter.button")}
          </button>
        </form>

        {/* Status feedback */}
        {status === "success" && (
          <div className="mt-3 px-3 py-2 rounded-lg text-sm bg-green-50 text-green-700 border border-green-100">
            <svg className="w-4 h-4 inline -mt-0.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            {message}
          </div>
        )}
        {status === "error" && (
          <div className="mt-3 px-3 py-2 rounded-lg text-sm bg-red-50 text-red-700 border border-red-100">
            {message}
          </div>
        )}
      </div>
    </section>
  );
}
