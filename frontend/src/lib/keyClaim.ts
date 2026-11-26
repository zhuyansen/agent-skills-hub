// The key a buyer just paid for, fetched on the success page Stripe redirects to.
// The claim-key function answers "pending" until the Stripe webhook has issued the key
// (usually seconds), so the page asks every POLL_MS for up to MAX_POLLS times.
// Until 2026-11-26 the email was the key's only copy; the first early-bird buyer's email
// domain stopped resolving and he never got it.

export type ClaimResult =
  | { status: "ready"; key: string; note: string }
  | { status: "pending" }
  | { status: "invalid" };

export const POLL_MS = 2000;
export const MAX_POLLS = 30;
export const KEY_STORAGE = "pro_key";
const SESSION_ID = /^cs_(live|test)_[A-Za-z0-9]{20,100}$/;

const claimUrl = () => `${import.meta.env?.VITE_SUPABASE_URL || ""}/functions/v1/claim-key`;

export function isSessionId(value: string | null): value is string {
  return Boolean(value && SESSION_ID.test(value));
}

export async function claimOnce(sessionId: string, fetcher: typeof fetch = fetch): Promise<ClaimResult> {
  try {
    const res = await fetcher(claimUrl(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    });
    const body = (await res.json()) as ClaimResult;
    return body.status === "ready" || body.status === "invalid" ? body : { status: "pending" };
  } catch {
    return { status: "pending" };
  }
}

/** Ask until the key is ready, the id is refused, or MAX_POLLS run out ("timeout"). */
export async function pollClaim(
  sessionId: string,
  cancelled: () => boolean,
  wait = (ms: number) => new Promise((r) => setTimeout(r, ms)),
  fetcher: typeof fetch = fetch,
): Promise<ClaimResult | { status: "timeout" }> {
  for (let i = 0; i < MAX_POLLS && !cancelled(); i++) {
    const result = await claimOnce(sessionId, fetcher);
    if (result.status !== "pending") return result;
    await wait(POLL_MS);
  }
  return { status: "timeout" };
}
