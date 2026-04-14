import { useState, useRef, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useI18n } from "../i18n/I18nContext";
import { supabase } from "../lib/supabase";

export function AuthButton() {
  const {
    user,
    loading,
    signInWithGoogle,
    signInWithEmail,
    signUpWithEmail,
    signOut,
  } = useAuth();
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"signin" | "signup" | "forgot">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // If Supabase is not configured, don't render
  if (!supabase) return null;
  if (loading) return null;

  const resetForm = () => {
    setError("");
    setMessage("");
    setEmail("");
    setPassword("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setSubmitting(true);
    try {
      if (mode === "forgot") {
        await supabase!.auth.resetPasswordForEmail(email, {
          redirectTo: window.location.origin,
        });
        setMessage(t("auth.resetSent"));
      } else if (mode === "signup") {
        await signUpWithEmail(email, password);
        setMessage(t("auth.confirmEmail"));
      } else {
        await signInWithEmail(email, password);
        setOpen(false);
        resetForm();
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t("auth.authFailed"));
    } finally {
      setSubmitting(false);
    }
  };

  const switchMode = (newMode: "signin" | "signup" | "forgot") => {
    setMode(newMode);
    setError("");
    setMessage("");
  };

  if (user) {
    return (
      <div className="relative" ref={ref}>
        <button
          onClick={() => setOpen(!open)}
          className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
        >
          {user.user_metadata?.avatar_url ? (
            <img
              src={user.user_metadata.avatar_url}
              alt="User avatar"
              className="w-7 h-7 rounded-full"
            />
          ) : (
            <div className="w-7 h-7 rounded-full bg-blue-500 text-white flex items-center justify-center text-xs font-bold">
              {(user.email?.[0] || "U").toUpperCase()}
            </div>
          )}
        </button>
        {open && (
          <div className="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-xl shadow-lg py-2 z-50">
            <div className="px-4 py-2 text-xs text-gray-500 truncate border-b border-gray-100">
              {user.email}
            </div>
            <button
              onClick={() => {
                signOut();
                setOpen(false);
              }}
              className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
            >
              {t("auth.signOut")}
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="px-3 py-1.5 text-xs bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition-colors font-medium cursor-pointer"
      >
        {t("auth.signIn")}
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-xl shadow-xl p-5 z-50">
          <h3 className="text-base font-semibold text-gray-900 mb-4 text-center">
            {mode === "forgot"
              ? t("auth.resetPassword")
              : mode === "signup"
                ? t("auth.createAccount")
                : t("auth.welcome")}
          </h3>

          {/* Google */}
          {mode !== "forgot" && (
            <>
              <button
                onClick={signInWithGoogle}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors cursor-pointer"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                {t("auth.google")}
              </button>

              <div className="flex items-center gap-3 my-4">
                <div className="flex-1 h-px bg-gray-200" />
                <span className="text-xs text-gray-400">{t("auth.or")}</span>
                <div className="flex-1 h-px bg-gray-200" />
              </div>
            </>
          )}

          {/* Email form */}
          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t("auth.email")}
              required
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {mode !== "forgot" && (
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t("auth.password")}
                required
                minLength={6}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            )}

            {error && (
              <div className="px-3 py-2 bg-red-50 border border-red-100 rounded-lg">
                <p className="text-xs text-red-600">{error}</p>
              </div>
            )}
            {message && (
              <div className="px-3 py-2 bg-green-50 border border-green-100 rounded-lg">
                <p className="text-xs text-green-700">{message}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full px-4 py-2.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-60 flex items-center justify-center gap-2 cursor-pointer"
            >
              {submitting && (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              )}
              {mode === "forgot"
                ? t("auth.sendReset")
                : mode === "signup"
                  ? t("auth.createAccount")
                  : t("auth.signIn")}
            </button>
          </form>

          {/* Footer links */}
          <div className="mt-3 space-y-1 text-center">
            {mode === "signin" && (
              <>
                <button
                  onClick={() => switchMode("forgot")}
                  className="block w-full text-xs text-gray-400 hover:text-blue-500 transition-colors cursor-pointer"
                >
                  {t("auth.forgotPassword")}
                </button>
                <button
                  onClick={() => switchMode("signup")}
                  className="block w-full text-xs text-blue-500 hover:text-blue-700 transition-colors cursor-pointer"
                >
                  {t("auth.noAccount")}
                </button>
              </>
            )}
            {mode === "signup" && (
              <button
                onClick={() => switchMode("signin")}
                className="block w-full text-xs text-blue-500 hover:text-blue-700 transition-colors cursor-pointer"
              >
                {t("auth.hasAccount")}
              </button>
            )}
            {mode === "forgot" && (
              <button
                onClick={() => switchMode("signin")}
                className="block w-full text-xs text-blue-500 hover:text-blue-700 transition-colors cursor-pointer"
              >
                {t("auth.backToSignIn")}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
