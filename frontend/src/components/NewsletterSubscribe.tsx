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
      <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-indigo-700 dark:from-indigo-800 dark:via-purple-800 dark:to-indigo-900 rounded-2xl p-6 sm:p-8 shadow-lg relative overflow-hidden">
        {/* Decorative background elements */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/3" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/4" />

        <div className="relative grid grid-cols-1 lg:grid-cols-5 gap-6 lg:gap-8 items-center">
          {/* Left: copy + benefits */}
          <div className="lg:col-span-3">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">{t("newsletter.title")}</h3>
                <p className="text-sm text-indigo-200">{t("newsletter.subtitle")}</p>
              </div>
            </div>

            {/* Benefits */}
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-5 mt-4">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-amber-300 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                <span className="text-xs text-indigo-100">{t("newsletter.benefits1")}</span>
              </div>
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-green-300 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                <span className="text-xs text-indigo-100">{t("newsletter.benefits2")}</span>
              </div>
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-blue-300 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span className="text-xs text-indigo-100">{t("newsletter.benefits3")}</span>
              </div>
            </div>
          </div>

          {/* Right: form or success */}
          <div className="lg:col-span-2">
            {status === "success" ? (
              /* Success state */
              <div className="text-center py-4 animate-fade-in-up">
                <div className="w-14 h-14 bg-green-400/20 rounded-full flex items-center justify-center mx-auto mb-3">
                  <svg className="w-7 h-7 text-green-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-white font-semibold text-base mb-1">{t("newsletter.successTitle")}</p>
                <p className="text-indigo-200 text-xs">{t("newsletter.checkEmail")}</p>
              </div>
            ) : (
              /* Form */
              <div>
                <form onSubmit={handleSubmit} className="space-y-3">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => { setEmail(e.target.value); if (status !== "idle") setStatus("idle"); }}
                    placeholder={t("newsletter.placeholder")}
                    required
                    className="w-full px-4 py-3 border border-white/20 rounded-xl bg-white/10 text-white text-sm placeholder-indigo-200 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent"
                    aria-label="Email address"
                  />
                  <button
                    type="submit"
                    disabled={!email.trim() || status === "loading"}
                    className="w-full px-5 py-3 bg-white text-indigo-600 rounded-xl text-sm font-semibold hover:bg-indigo-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer flex items-center justify-center gap-2"
                  >
                    {status === "loading" && (
                      <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
                    )}
                    {t("newsletter.button")}
                  </button>
                </form>

                {/* Error feedback */}
                {status === "error" && (
                  <div className="mt-2 px-3 py-2 rounded-lg text-xs bg-white/15 text-red-200 border border-white/20">
                    {message}
                  </div>
                )}

                {/* Social proof */}
                <p className="text-center text-xs text-indigo-300 mt-3">
                  {t("newsletter.socialProof").replace("{count}", "500")}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
