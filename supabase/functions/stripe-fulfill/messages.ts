/** The emails and the GitHub issue, worded as ops/stripe/poll_stripe.py words them. */
import { escapeHtml, maskEmail, type Session, type Sku } from "./fulfil.ts";

const amountOf = (s: Session) => ((s.amount_total || 0) / 100).toFixed(2);
const currencyOf = (s: Session) => (s.currency || "usd").toUpperCase();

export function buyerEmail(sku: Sku, key: string): { subject: string; html: string } {
  const cigate = sku === "cigate";
  const subject = cigate ? "Your Agent Skills Hub Team CI Gate + Pro Key (`ash_pro_...`)" : "Your Agent Skills Hub Pro Access Key";
  const setup = cigate
    ? '<p><b>CI Skill Gate workflow</b>: copy the GitHub Action from <a href="https://agentskillshub.top/ci-gate/">https://agentskillshub.top/ci-gate/</a> and store this key as <code>ASH_GATE_KEY</code> in your repo secrets.</p>'
    : '<p><b>Activate Pro Deep Search</b>: open <a href="https://agentskillshub.top/pro/">https://agentskillshub.top/pro/</a> and paste the key above (also works via <code>npx @agentskillshub/cli</code>).</p>';
  const html = "<div><h2>Thank you for supporting Agent Skills Hub</h2><p>Your access key is ready:</p>"
    + `<pre style='padding:12px;background:#f1f5f9;border-radius:8px;font-size:14px'>${escapeHtml(key)}</pre>`
    + `${setup}<p style='color:#64748b;font-size:12px'>Need help or a team invoice? Reply directly to this email.</p></div>`;
  return { subject, html };
}

const TITLES: Record<Sku, string> = {
  pro: "⚡ Pro Membership — ", cigate: "🛡️ Team CI Skill Gate — ",
  fasttrack: "🚀 48h Fast-Track Review — ", sponsor: "⭐ Homepage Rail Sponsor — ",
  deep_audit: "💰 Deep Audit order — ",
};

function checklist(sku: Sku, target: string): string {
  const lines: Record<Sku, string[]> = {
    pro: ["Confirm `ash_pro_` key delivered to buyer email"],
    cigate: ["Confirm Team `ash_pro_` key delivered", "Send CI Gate onboarding / allowlist review check-in"],
    fasttrack: [`Run full manual + static review on \`${target}\` within 48h`, "Update catalog grade/notes if verified safe/fixed",
      "Email 48h Fast-Track report to submitter"],
    sponsor: [`Confirm logo, 1-line pitch, target URL & left/right slot for \`${target}\``,
      "Add sponsor entry to `frontend/src/data/sponsors.ts` (`rel=\"sponsored\"`) and deploy",
      "Email live homepage screenshot + complimentary Fast-Track audit offer to sponsor"],
    deep_audit: [`Run deep audit on \`${target}\``, "Write report", "Send report to customer"],
  };
  return [...lines[sku], "Close this issue"].map((l) => `- [ ] ${l}\n`).join("");
}

/** The public issue: masked email only (the repository is public), plaintext key never. */
export function orderIssue(s: Session, sku: Sku, target: string, keyStatus: string): { title: string; body: string } {
  const email = s.customer_details?.email || "";
  const body = `New paid \`${sku}\` order.\n\n- **SKU**: \`${sku}\`\n- **Target**: \`${target}\`\n`
    + `- **Amount**: ${amountOf(s)} ${currencyOf(s)}\n- **Customer**: ${maskEmail(email)} (full details in the alert email / Stripe dashboard)\n`
    + `- **Auto key fulfillment**: \`${keyStatus}\`\n- **Fulfilled by**: \`stripe-webhook\`\n- **Session**: \`${s.id}\`\n\n`
    + `Delivery checklist:\n${checklist(sku, target)}`;
  return { title: TITLES[sku] + target, body };
}

export function operatorAlert(s: Session, sku: Sku, target: string, keyStatus: string, earlySold: number | null, limit: number): { subject: string; html: string } {
  const email = escapeHtml(s.customer_details?.email || "(none)");
  const sold = earlySold === null ? "（未能统计）" : `${earlySold}/${limit}`;
  const html = `<div lang="zh"><h2>💰 有人付款了!${amountOf(s)} ${currencyOf(s)}（${sku}）</h2>`
    + `<p><b>目标/团队</b>:${escapeHtml(target)}<br><b>客户邮箱</b>:${email}<br><b>自动发码状态</b>:${escapeHtml(keyStatus)}<br>`
    + `<b>Session</b>:${escapeHtml(s.id)}<br><b>发货</b>:Stripe webhook（即时）</p>`
    + `<p>订单详情:<a href="https://dashboard.stripe.com/payments">https://dashboard.stripe.com/payments</a></p>`
    + `<p>美元早鸟已售：${sold}。</p><p>按工单 checklist 交付即可。</p></div>`;
  return { subject: `💰 ${amountOf(s)} ${currencyOf(s)} [${sku}] 成交:${target}`, html };
}
