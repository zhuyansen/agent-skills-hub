import { supabase } from "./supabase";
import { trackEvent } from "./analytics";

/**
 * The one write path for an enterprise lead, shared by every surface that
 * captures one. Until 2026-09-23 that was only /enterprise/ — a page the people
 * with demonstrated security intent never visit: 28 days of GA read 80 people
 * running an audit in /analyzer/ against 2 who started the enterprise form.
 * The capture now also lives at the audit result, so the RPC call, the
 * name/company synthesis and the funnel events must not be copy-pasted twice.
 *
 * Each surface keeps its own event family (enterprise_lead_* vs audit_lead_*)
 * so the daily digest can print two funnels without a GA custom dimension.
 */
export type LeadSource =
  | "enterprise_page"
  | "audit_result"
  | "pro_checkout"
  | "submit_fasttrack"
  | "ci_gate_page";

export const HOW_FOUND_OPTIONS = [
  "",
  "ChatGPT / AI Search (Perplexity, Claude, Gemini)",
  "Google / Bing Search",
  "GitHub",
  "X / Social",
  "Other",
] as const;

export interface LeadInput {
  email: string;
  use_case: string;
  full_name?: string;
  company?: string;
  role_title?: string;
  team_size?: string;
  industry?: string;
  current_stack?: string;
  compliance_requirements?: string;
  message?: string;
  timeline?: string;
  estimated_budget?: string;
  how_found?: string;
}

export interface LeadEvents {
  attempt: string;
  submitted: string;
  failed: string;
}

type EventParams = Record<string, string | number | boolean | undefined>;

const NAME_MAX = 100;
const COMPANY_MAX = 200;
const REASON_MAX = 100;

/**
 * Whether an address is complete enough to reply to. A browser's
 * <input type="email"> accepts name@host with no dot and the RPC only checks
 * for an "@", so a forgotten ".com" went straight through: the first
 * audit-result lead (2026-11-07) was stored as name@gmail, which bounces, and
 * synthesised() below named its company "gmail". Both forms call this before
 * submitting.
 *
 * Rule: one "@", a non-empty local part, no whitespace, and a domain made of
 * non-empty dot-separated labels whose last one is 2+ letters (any script, so
 * .com and .中国) or punycode (xn--…).
 */
const COMPLETE_EMAIL = /^[^\s@]+@(?:[^\s@.]+\.)+(?:\p{L}{2,}|xn--[a-z0-9-]+)$/iu;

export function isCompleteEmail(email: string): boolean {
  return COMPLETE_EMAIL.test(email);
}

/** enterprise_leads needs a non-empty name and company (enforced in the RPC).
 *  When the visitor didn't volunteer them, derive both from the email so the
 *  write succeeds without a schema change — sales enriches them on follow-up. */
function synthesised(email: string): { name: string; company: string } {
  const [local, domain] = email.split("@");
  return {
    name: (local || "there").slice(0, NAME_MAX),
    company: (domain || "unknown").slice(0, COMPANY_MAX),
  };
}

/** Writes the lead and fires attempt → submitted, or attempt → failed. Throws
 *  after firing `failed`, so a broken write can never look like no demand. */
export async function submitEnterpriseLead(
  input: LeadInput,
  source: LeadSource,
  events: LeadEvents,
  params: EventParams = {},
): Promise<void> {
  const howFound = input.how_found?.trim() || "";
  const eventParams: EventParams = {
    ...params,
    how_found: howFound || "unset",
  };
  trackEvent(events.attempt, eventParams);
  try {
    if (!supabase) throw new Error("Supabase not configured.");
    const fallback = synthesised(input.email);
    const combinedMessage = [
      howFound ? `[How found: ${howFound}]` : "",
      input.message?.trim() || "",
    ]
      .filter(Boolean)
      .join("\n");
    const { error } = await supabase.rpc("submit_enterprise_lead", {
      p_full_name: input.full_name || fallback.name,
      p_email: input.email,
      p_company: input.company || fallback.company,
      p_use_case: input.use_case,
      p_role_title: input.role_title || null,
      p_team_size: input.team_size || null,
      p_industry: input.industry || null,
      p_current_stack: input.current_stack || null,
      p_compliance_requirements: input.compliance_requirements || null,
      p_message: combinedMessage || null,
      p_timeline: input.timeline || null,
      p_estimated_budget: input.estimated_budget || null,
      p_source: howFound ? `${source}:${howFound}` : source,
    });
    if (error) throw error;
    trackEvent(events.submitted, eventParams);
  } catch (e) {
    trackEvent(events.failed, {
      ...eventParams,
      reason: e instanceof Error ? e.message.slice(0, REASON_MAX) : "unknown",
    });
    throw e;
  }
}
