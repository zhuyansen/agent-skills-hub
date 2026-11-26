import { useEffect, useState } from "react";
import { Helmet } from "react-helmet-async";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { useI18n } from "../i18n/I18nContext";
import { trackEvent } from "../lib/analytics";
import { CLAIM_SESSION_STORAGE, isSessionId, KEY_STORAGE, NOTE_STORAGE, pollClaim } from "../lib/keyClaim";

// Where Stripe sends a Pro or CI Gate buyer after paying (payment link "after payment"
// redirect: /pro/success/?session_id={CHECKOUT_SESSION_ID}). Shows the key at once, saves it
// on this device, and drops the session id from the address bar once used.

type View = { state: "waiting" | "timeout" | "invalid" | "none" } | { state: "ready"; key: string; cigate: boolean };

declare global {
  interface Window { __ashClaimSession?: string }
}

function readStored(name: string): string {
  try {
    return localStorage.getItem(name) ?? "";
  } catch {
    return "";
  }
}

/** The id index.html moved out of the address bar (it never reaches analytics); the URL in dev. */
function claimSessionId(): string | null {
  let id: string | null = window.__ashClaimSession ?? null;
  try {
    id = id ?? sessionStorage.getItem(CLAIM_SESSION_STORAGE);
  } catch { /* storage blocked: the window copy above still has it */ }
  id = id ?? new URLSearchParams(window.location.search).get("session_id");
  return isSessionId(id) ? id : null;
}

/** Without a session id (a reload after the key was shown): the key this device saved, if any. */
function initialView(): View {
  if (claimSessionId()) return { state: "waiting" };
  const stored = readStored(KEY_STORAGE);
  return stored ? { state: "ready", key: stored, cigate: readStored(NOTE_STORAGE).startsWith("cigate") } : { state: "none" };
}

function useClaimedKey(): View {
  const [view, setView] = useState<View>(initialView);
  useEffect(() => {
    const sessionId = claimSessionId();
    if (!sessionId) return;
    let cancelled = false;
    pollClaim(sessionId, () => cancelled)
      .then((r) => { if (!cancelled) setView(viewOf(r)); })
      .catch(() => { if (!cancelled) setView({ state: "timeout" }); });
    return () => { cancelled = true; };
  }, []);
  return view;
}

function viewOf(r: Awaited<ReturnType<typeof pollClaim>>): View {
  if (r.status !== "ready") return { state: r.status === "invalid" ? "invalid" : "timeout" };
  saveKey(r.key, r.note);
  trackEvent("pro_key_claimed", { note: r.note });
  return { state: "ready", key: r.key, cigate: r.note.startsWith("cigate") };
}

function saveKey(key: string, note: string): void {
  try {
    localStorage.setItem(KEY_STORAGE, key);
    localStorage.setItem(NOTE_STORAGE, note);
    sessionStorage.removeItem(CLAIM_SESSION_STORAGE);
  } catch { /* private mode: the key is still on screen and in the email */ }
  delete window.__ashClaimSession;
}

function KeyBox({ k, zh }: { k: string; zh: boolean }) {
  const [copied, setCopied] = useState(false);
  const copy = () => navigator.clipboard?.writeText(k).then(() => setCopied(true)).catch(() => setCopied(false));
  return (
    <div className="flex flex-col sm:flex-row gap-2 items-stretch">
      <code className="ph-no-capture flex-1 break-all rounded-lg bg-gray-100 dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100">{k}</code>
      <button type="button" onClick={copy} className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-500">
        {copied ? (zh ? "已复制" : "Copied") : (zh ? "复制" : "Copy")}
      </button>
    </div>
  );
}

function Ready({ k, cigate, zh }: { k: string; cigate: boolean; zh: boolean }) {
  return (
    <>
      <p className="text-gray-700 dark:text-gray-300 mb-4">
        {zh ? "这是你的访问密钥，已保存在这台设备上，同时也发到了你的邮箱。" : "Here is your access key. It is saved on this device and also sent to your email."}
      </p>
      <KeyBox k={k} zh={zh} />
      <p className="mt-6 text-sm">
        <a href={cigate ? "/ci-gate/" : "/pro/"} className="text-indigo-600 dark:text-indigo-400 font-semibold hover:underline">
          {cigate ? (zh ? "设置 CI Skill Gate →" : "Set up the CI Skill Gate →") : (zh ? "开始 Pro 深度搜索 →" : "Start a Pro deep search →")}
        </a>
      </p>
    </>
  );
}

function Message({ state, zh }: { state: "waiting" | "timeout" | "invalid" | "none"; zh: boolean }) {
  const text = {
    waiting: zh ? "付款已收到，正在生成你的密钥……" : "Payment received. Preparing your key…",
    timeout: zh ? "密钥还在路上：它也会发到你的邮箱。几分钟内没收到，请通过联系页告诉我们。" : "Your key is on its way and will also arrive by email. If it has not come in a few minutes, tell us on the contact page.",
    invalid: zh ? "这个链接已失效或不对应任何订单。密钥也发到了你付款时填写的邮箱。" : "This link has expired or matches no order. Your key was also sent to the email you paid with.",
    none: zh ? "这台设备上没有保存的密钥。如果你刚付款，密钥在你付款时填写的邮箱里。" : "No key is saved on this device. If you just paid, your key is in the email you paid with.",
  }[state];
  return (
    <p className="text-gray-700 dark:text-gray-300">
      {text}{" "}
      {state !== "waiting" && <a href="/contact/" className="text-indigo-600 dark:text-indigo-400 hover:underline">{zh ? "联系我们" : "Contact"}</a>}
    </p>
  );
}

export default function ProSuccessPage() {
  const { lang } = useI18n();
  const zh = lang === "zh";
  const view = useClaimedKey();
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Helmet>
        <title>Your Pro key — Agent Skills Hub</title>
        <meta name="robots" content="noindex" />
        <meta name="referrer" content="no-referrer" />
      </Helmet>
      <SiteHeader />
      <main className="max-w-2xl mx-auto px-4 py-12">
        <h1 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">{zh ? "感谢支持 Agent Skills Hub" : "Thank you for supporting Agent Skills Hub"}</h1>
        {view.state === "ready" ? <Ready k={view.key} cigate={view.cigate} zh={zh} /> : <Message state={view.state} zh={zh} />}
      </main>
      <SiteFooter />
    </div>
  );
}
