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
export type LeadSource = "enterprise_page" | "audit_result";

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
  trackEvent(events.attempt, params);
  try {
    if (!supabase) throw new Error("Supabase not configured.");
    const fallback = synthesised(input.email);
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
      p_message: input.message || null,
      p_timeline: input.timeline || null,
      p_estimated_budget: input.estimated_budget || null,
      p_source: source,
    });
    if (error) throw error;
    trackEvent(events.submitted, params);
  } catch (e) {
    trackEvent(events.failed, {
      reason: e instanceof Error ? e.message.slice(0, REASON_MAX) : "unknown",
    });
    throw e;
  }
}
