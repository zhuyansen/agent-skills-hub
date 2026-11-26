/**
 * The success page's way to the key it just paid for: POST {"session_id": "cs_live_..."}.
 *
 * Stripe redirects a buyer to /pro/success/?session_id={CHECKOUT_SESSION_ID}; that id is long,
 * random and known only to the buyer's browser, so it is the claim. stripe-fulfill has usually
 * stored the key (order_key_claims, migration 046) within seconds of payment; until then this
 * answers "pending" and the page asks again. Rows live 24 hours. Deployed with --no-verify-jwt
 * (the page has no Supabase session); CORS is limited to the site.
 *
 * Answers: {status: "ready", key, note} | {status: "pending"} | {status: "invalid"}.
 */
import { openKey, SESSION_ID } from "../_shared/claim.ts";

const ORIGINS = new Set(["https://agentskillshub.top", "http://localhost:5173"]);
const env = (name: string) => Deno.env.get(name) ?? "";

function cors(req: Request): Record<string, string> {
  const origin = req.headers.get("origin") ?? "";
  return {
    "Access-Control-Allow-Origin": ORIGINS.has(origin) ? origin : "https://agentskillshub.top",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type",
    "Cache-Control": "no-store",
    Vary: "Origin",
  };
}

type Row = { iv: string; ciphertext: string; note: string; expires_at: string };

async function findClaim(sessionId: string): Promise<Row | null> {
  const service = env("SUPABASE_SERVICE_ROLE_KEY");
  const url = `${env("SUPABASE_URL")}/rest/v1/order_key_claims?select=iv,ciphertext,note,expires_at`
    + `&order_id=eq.${encodeURIComponent(sessionId)}&expires_at=gt.${new Date().toISOString()}`;
  const res = await fetch(url, { headers: { apikey: service, Authorization: `Bearer ${service}` } });
  if (!res.ok) throw new Error(`claims lookup answered ${res.status}`);
  const rows = await res.json() as Row[];
  return rows[0] ?? null;
}

Deno.serve(async (req) => {
  const headers = { ...cors(req), "Content-Type": "application/json" };
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers });
  if (req.method !== "POST") return new Response(JSON.stringify({ error: "POST only" }), { status: 405, headers });
  const { session_id: sessionId } = await req.json().catch(() => ({})) as { session_id?: string };
  if (!sessionId || !SESSION_ID.test(sessionId)) return new Response(JSON.stringify({ status: "invalid" }), { status: 400, headers });
  try {
    const row = await findClaim(sessionId);
    if (!row) return new Response(JSON.stringify({ status: "pending" }), { headers });
    const key = await openKey(row, env("CLAIM_KEY"));
    return new Response(JSON.stringify({ status: "ready", key, note: row.note }), { headers });
  } catch (err) {
    console.error(`claim failed: ${(err as Error).message}`);
    return new Response(JSON.stringify({ status: "pending" }), { status: 503, headers });
  }
});
