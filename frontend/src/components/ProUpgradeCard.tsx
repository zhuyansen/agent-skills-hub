import { useEffect, useRef, useState } from "react";
import { USD_PRICING, buildStripeCheckoutUrl } from "../lib/checkout";
import { isCompleteEmail, submitEnterpriseLead } from "../lib/enterpriseLead";
import { trackEvent } from "../lib/analytics";
import type { useProOffer } from "../hooks/useProOffer";

/** The Pro price + Stripe checkout card (pages/ProPage.tsx), or an email form when no Payment Link is configured. */
export function UpgradeCard({
  zh,
  trialLimit,
  exhausted = false,
  offer,
}: {
  zh: boolean;
  trialLimit: number;
  exhausted?: boolean;
  offer: ReturnType<typeof useProOffer>;
}) {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "sent" | "error">("idle");
  const [errMsg, setErrMsg] = useState("");
  const hasStripe = offer.link.length > 0;
  const root = useRef<HTMLDivElement>(null);
  const seen = useRef(false);

  // "Viewed" means the card entered the viewport, as for audit_lead_viewed. 2026-11-18..25:
  // 47 people opened /pro/ and none clicked checkout, with no way to tell if they saw the price.
  useEffect(() => {
    const el = root.current;
    if (!el || seen.current) return;
    const io = new IntersectionObserver((entries) => {
      if (seen.current || !entries.some((e) => e.isIntersecting)) return;
      seen.current = true;
      trackEvent("pro_upgrade_viewed", { exhausted, stripe: hasStripe, price: offer.price });
      io.disconnect();
    });
    io.observe(el);
    return () => io.disconnect();
  }, [exhausted, hasStripe, offer.price]);

  const checkoutHref = hasStripe
    ? buildStripeCheckoutUrl(offer.link, {
        clientReferenceId: "pro--web",
        prefilledEmail: email,
      })
    : "";

  async function handleOrderRequest(e: React.FormEvent) {
    e.preventDefault();
    const clean = email.trim();
    if (!isCompleteEmail(clean)) {
      setErrMsg(zh ? "请输入完整的邮箱地址。" : "Please enter a complete email address.");
      setStatus("error");
      return;
    }
    setStatus("submitting");
    setErrMsg("");
    try {
      await submitEnterpriseLead(
        {
          email: clean,
          use_case: `Pro Search (${offer.price})`,
          estimated_budget: offer.price,
          timeline: "Immediate self-serve",
        },
        "pro_checkout",
        {
          attempt: "pro_checkout_attempt",
          submitted: "pro_checkout_submitted",
          failed: "pro_checkout_failed",
        },
        { price: offer.price },
      );
      setStatus("sent");
    } catch (err) {
      setStatus("error");
      setErrMsg(
        err instanceof Error
          ? err.message
          : zh
            ? "提交失败,请稍后重试。"
            : "Request failed — please retry.",
      );
    }
  }

  return (
    <div
      ref={root}
      id="pro-checkout"
      className="max-w-xl mx-auto mt-10 p-8 rounded-2xl border border-indigo-200 dark:border-indigo-900 bg-indigo-50 dark:bg-indigo-950/40 text-center"
    >
      <h2 className="text-xl font-bold mb-2 text-gray-900 dark:text-white">
        {exhausted
          ? zh
            ? `${trialLimit} 次免费试用已用完`
            : `You've used all ${trialLimit} free trial searches`
          : zh
            ? "Pro 深度搜索 · 英文/全球 USD 会员"
            : "Unlock Pro Deep Search"}
      </h2>
      <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">
        {zh
          ? "README 全文检索 · 200 条/页 · CSV/JSON 导出 · CLI/MCP API 调用"
          : "Full README search · 200 results/page · CSV/JSON export · CLI & MCP API key"}
      </p>
      <p className="text-lg font-semibold my-3 text-indigo-700 dark:text-indigo-300">
        {offer.soldOut ? `Pro ${offer.price}` : zh
          ? `早鸟特惠 ${offer.price}（限前 100 单）`
          : `Early supporter: ${offer.price} (first 100 orders)`}
        {!offer.soldOut && <span className="ml-2 text-sm font-normal">
          {zh
            ? `之后 ${USD_PRICING.proStandard}`
            : `then ${USD_PRICING.proStandard}`}
        </span>}
      </p>
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
        {zh
          ? "续费同价 —— 以哪个价加入,续费永远锁定哪个价。支持全球信用卡 USD 结账。"
          : "Renewals locked at your joining price, forever. Billed in USD via Stripe."}
      </p>

      {hasStripe ? (
        <div className="space-y-3 max-w-sm mx-auto">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={zh ? "接收激活码的邮箱(可选)" : "Email for your ash_pro_ key (optional)"}
            className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white"
          />
          <a
            href={checkoutHref}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => {
              const liveHref = buildStripeCheckoutUrl(offer.link, {
                clientReferenceId: "pro--web",
                prefilledEmail: email,
              });
              if (liveHref) e.currentTarget.href = liveHref;
              trackEvent("pro_checkout_click", { sku: "pro", price: offer.price });
            }}
            className="inline-block w-full px-6 py-2.5 rounded-lg bg-indigo-600 text-white font-semibold hover:bg-indigo-500 transition-colors"
          >
            {zh
              ? `开通 Pro (${offer.price}) · Stripe 结账 →`
              : `Get Pro Key (${offer.price}) via Stripe →`}
          </a>
          <p className="text-[11px] text-gray-500 dark:text-gray-400">
            {zh
              ? "付款后系统自动向你的邮箱发送 ash_pro_ 激活码。"
              : "Your ash_pro_ key is emailed automatically after checkout."}
          </p>
        </div>
      ) : status === "sent" ? (
        <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-sm text-emerald-700 dark:text-emerald-300">
          {zh
            ? "✓ 已收到!我们会尽快把 USD Stripe 结账链接与 ash_pro_ 激活码发到你的邮箱。"
            : "✓ Request received! We'll email your USD Stripe checkout link and ash_pro_ activation key shortly."}
        </div>
      ) : (
        <form onSubmit={handleOrderRequest} className="space-y-2.5 max-w-sm mx-auto">
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={zh ? "输入邮箱获取结账链接与 Key" : "you@company.com"}
              className="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white"
            />
            <button
              type="submit"
              disabled={status === "submitting"}
              className="px-5 py-2 rounded-lg bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-500 disabled:opacity-50 whitespace-nowrap cursor-pointer"
            >
              {status === "submitting"
                ? "…"
                : zh
                  ? `开通 (${offer.price})`
                  : `Get Pro (${offer.price}) →`}
            </button>
          </div>
          {status === "error" && (
            <p className="text-xs text-red-500">{errMsg}</p>
          )}
          <p className="text-[11px] text-gray-500 dark:text-gray-400">
            {zh
              ? "填写邮箱后直接发送 USD Stripe 付款链接,付款后即发 ash_pro_ Key。"
              : "Instant USD Stripe checkout link sent to your inbox; ash_pro_ key issued on payment."}
          </p>
        </form>
      )}
    </div>
  );
}
