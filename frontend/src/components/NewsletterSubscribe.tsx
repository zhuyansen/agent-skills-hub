import { useState } from "react";
import { useI18n } from "../i18n/I18nContext";
import { subscribe } from "../api/client";

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
      const res = await subscribe(email.trim());
      if (res.status === "already") {
        setStatus("success");
        setMessage(res.message);
      } else if (res.status === "success") {
        setStatus("success");
        setMessage(res.message || t("newsletter.success"));
        setEmail("");
      } else {
        throw new Error(res.message);
      }
    } catch (err: any) {
      setStatus("error");
      setMessage(err.message || t("newsletter.error"));
    }
  };

  return (
    <section className="mt-8 mb-6">
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-5 sm:p-6 shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <div className="flex items-start gap-3 flex-1">
            <div className="w-10 h-10 rounded-lg bg-white/20 flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-white">{t("newsletter.title")}</h3>
              <p className="text-sm text-indigo-100 mt-0.5">{t("newsletter.subtitle")}</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="flex gap-2 sm:w-auto w-full">
            <input
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); if (status !== "idle") setStatus("idle"); }}
              placeholder={t("newsletter.placeholder")}
              required
              className="flex-1 sm:w-56 px-4 py-2.5 border border-white/20 rounded-lg bg-white/10 text-white text-sm placeholder-indigo-200 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent"
              aria-label="Email address"
            />
            <button
              type="submit"
              disabled={!email.trim() || status === "loading"}
              className="px-5 py-2.5 bg-white text-indigo-600 rounded-lg text-sm font-semibold hover:bg-indigo-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shrink-0 flex items-center gap-2"
            >
              {status === "loading" && (
                <div className="w-3.5 h-3.5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
              )}
              {t("newsletter.button")}
            </button>
          </form>
        </div>

        {/* Status feedback */}
        {status === "success" && (
          <div className="mt-3 px-3 py-2 rounded-lg text-sm bg-white/15 text-green-200 border border-white/20">
            <svg className="w-4 h-4 inline -mt-0.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            {message}
          </div>
        )}
        {status === "error" && (
          <div className="mt-3 px-3 py-2 rounded-lg text-sm bg-white/15 text-red-200 border border-white/20">
            {message}
          </div>
        )}
      </div>
    </section>
  );
}
