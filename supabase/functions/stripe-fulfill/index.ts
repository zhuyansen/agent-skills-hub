/**
 * Stripe webhook: checkout.session.completed and checkout.session.async_payment_succeeded.
 * Deployed with --no-verify-jwt (Stripe signs with STRIPE_WEBHOOK_SECRET, not a Supabase JWT).
 * Answers 200 for anything it does not need to act on, so Stripe does not retry it; 500 when
 * fulfilment failed part-way, so Stripe retries and the idempotent steps pick up from there.
 */
import { verifySignature, type Session } from "./fulfil.ts";
import { processSession } from "./process.ts";
import { liveDeps } from "./deps.ts";

const HANDLED = new Set(["checkout.session.completed", "checkout.session.async_payment_succeeded"]);

const reply = (status: number, body: Record<string, unknown>) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

Deno.serve(async (req) => {
  if (req.method !== "POST") return reply(405, { error: "POST only" });
  const body = await req.text();
  const ok = await verifySignature(Deno.env.get("STRIPE_WEBHOOK_SECRET") ?? "", req.headers.get("stripe-signature"), body, Math.floor(Date.now() / 1000));
  if (!ok) return reply(400, { error: "bad signature" });
  const event = JSON.parse(body) as { id?: string; type?: string; data?: { object?: Session } };
  if (!HANDLED.has(event.type || "") || !event.data?.object) return reply(200, { ignored: event.type });
  try {
    const outcome = await processSession(event.data.object, liveDeps);
    console.log(JSON.stringify({ event: event.id, session: event.data.object.id, ...outcome }));
    return reply(200, outcome);
  } catch (err) {
    console.error(`fulfilment failed for ${event.data.object.id}: ${(err as Error).message}`);
    return reply(500, { error: "fulfilment failed; Stripe will retry" });
  }
});
