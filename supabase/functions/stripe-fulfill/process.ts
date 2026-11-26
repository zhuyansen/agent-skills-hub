/** One completed checkout, start to finish. Outside calls come in as `deps`, so tests stub them. */
import { classify, EARLY_BIRD_LIMIT, keyNote, type Session, type Sku } from "./fulfil.ts";
import { buyerEmail, operatorAlert, orderIssue } from "./messages.ts";

export type KeyResult = { status?: string; key?: string } | null;

export interface Deps {
  /** True when a GitHub issue labelled `order` already names this session (either path did it). */
  orderRecorded(sessionId: string): Promise<boolean>;
  issueKey(email: string, note: string, orderId: string): Promise<KeyResult>;
  /** Keep the key, encrypted, for the buyer's success page (order_key_claims). False on failure. */
  storeClaim(orderId: string, key: string, note: string): Promise<boolean>;
  sendEmail(to: string, subject: string, html: string): Promise<boolean>;
  alertEmail: string;
  earlyBirdSold(): Promise<number | null>;
  createIssue(title: string, body: string): Promise<string>;
  capturePurchase(session: Session, sku: Sku): Promise<boolean>;
}

export type Outcome =
  | { done: false; reason: "not_ours" | "not_paid" | "test_mode" | "already_recorded" }
  | { done: true; sku: Sku; keyStatus: string; issueUrl: string };

/** The same steps, in the same order, as poll_stripe.process_session. Throws when the alert or
 *  the issue fails: Stripe then retries, and the key step is idempotent per order. */
export async function processSession(s: Session, deps: Deps): Promise<Outcome> {
  const classified = classify(s);
  if (!classified) return { done: false, reason: "not_ours" };
  if (s.payment_status !== "paid") return { done: false, reason: "not_paid" };
  if (s.livemode !== true) return { done: false, reason: "test_mode" };
  if (await deps.orderRecorded(s.id)) return { done: false, reason: "already_recorded" };
  const [sku, target] = classified;
  const keyStatus = await deliverKey(s, sku, deps);
  const alert = operatorAlert(s, sku, target, keyStatus, await deps.earlyBirdSold(), EARLY_BIRD_LIMIT);
  if (!(await deps.sendEmail(deps.alertEmail, alert.subject, alert.html))) throw new Error("operator alert failed");
  const issue = orderIssue(s, sku, target, keyStatus);
  const issueUrl = await deps.createIssue(issue.title, issue.body);
  // After the issue, as in the poll: the issue marks the order done, so a retry never reports it twice.
  await deps.capturePurchase(s, sku);
  return { done: true, sku, keyStatus, issueUrl };
}

/** "issued_and_emailed", "already_issued", "pending_manual_issue", … as the poll reports it. */
async function deliverKey(s: Session, sku: Sku, deps: Deps): Promise<string> {
  if (sku !== "pro" && sku !== "cigate") return "n/a";
  const email = s.customer_details?.email || "";
  if (!email.includes("@")) return "pending_manual_issue";
  const res = await deps.issueKey(email, keyNote(s, sku), s.id);
  if (!res) return "pending_manual_issue";
  if (res.status !== "issued" || !res.key) return String(res.status || "unknown");
  // Before the email: the key is returned only once, and an email can fail to arrive (11-26).
  const kept = await deps.storeClaim(s.id, res.key, keyNote(s, sku));
  const mail = buyerEmail(sku, res.key);
  const status = (await deps.sendEmail(email, mail.subject, mail.html)) ? "issued_and_emailed" : "issued_manual_email_needed";
  // Shown in the operator alert and the issue: with both failed, the key exists nowhere.
  return kept ? status : `${status}+success_page_failed`;
}
