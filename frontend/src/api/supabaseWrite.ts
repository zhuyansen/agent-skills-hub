/**
 * Supabase write operations — submit, subscribe, verify, admin actions.
 * Extracted from supabaseClient.ts to keep file sizes under 800 lines.
 */
import { supabase } from "../lib/supabase";

function ensureSupabase() {
  if (!supabase) throw new Error("Supabase not configured");
  return supabase;
}

export async function sbSubmitSkill(
  repoUrl: string,
): Promise<{ status: string; message: string; skill_id?: number }> {
  const sb = ensureSupabase();

  const match = repoUrl.match(/github\.com\/([^/]+\/[^/]+)/);
  if (!match) {
    return { status: "error", message: "Invalid GitHub URL" };
  }
  const fullName = match[1].replace(/\.git$/, "");

  const { data: existing } = await sb
    .from("skills")
    .select("id")
    .eq("repo_full_name", fullName)
    .maybeSingle();

  if (existing) {
    return {
      status: "already_tracked",
      message: "This skill is already tracked!",
      skill_id: existing.id,
    };
  }

  try {
    const { data: submitted } = await sb
      .from("extra_repos")
      .select("id, status")
      .eq("full_name", fullName)
      .maybeSingle();

    if (submitted) {
      return {
        status: "already_submitted",
        message: `This repo has already been submitted (status: ${submitted.status || "pending"})`,
      };
    }
  } catch {
    // SELECT may be blocked by RLS — skip dedup check
  }

  const { error } = await sb.from("extra_repos").insert({
    full_name: fullName,
    is_active: false,
    status: "pending",
    submitted_by: "community",
  });

  if (error) {
    if (error.code === "23505") {
      return {
        status: "already_submitted",
        message: "This repo has already been submitted",
      };
    }
    return { status: "error", message: error.message };
  }

  return {
    status: "submitted",
    message: "Submitted successfully! It will be reviewed by our team.",
  };
}

export async function sbSubscribe(
  email: string,
): Promise<{ status: string; message: string }> {
  const sb = ensureSupabase();

  const { data, error } = await sb.rpc("subscribe", { p_email: email });
  if (error) {
    return { status: "error", message: error.message };
  }

  const result = data as { status?: string; token?: string; error?: string };

  if (result.error) {
    return {
      status: "error",
      message:
        result.error === "invalid_email"
          ? "Invalid email address."
          : result.error,
    };
  }

  switch (result.status) {
    case "already_subscribed":
      return {
        status: "already",
        message: "You are already subscribed and verified!",
      };
    case "reactivated":
      return {
        status: "success",
        message: "Welcome back! Your subscription has been reactivated.",
      };
    case "pending_verification":
    case "created": {
      try {
        await sb.rpc("send_verification_email", {
          p_email: email,
          p_token: result.token,
        });
      } catch {
        // Silent fail — email may be sent by cron job or admin
      }
      return {
        status: "success",
        message: "Please check your email and click the verification link.",
      };
    }
    default:
      return { status: "error", message: "Unexpected response." };
  }
}

export async function sbVerifyEmail(
  token: string,
): Promise<{ status: string; message: string }> {
  const sb = ensureSupabase();

  const { data, error } = await sb.rpc("verify_email", { p_token: token });
  if (error) {
    return { status: "error", message: error.message };
  }

  const result = data as { status?: string; email?: string; error?: string };

  if (result.error) {
    switch (result.error) {
      case "invalid_token":
        return { status: "error", message: "Invalid verification token." };
      case "token_not_found":
        return {
          status: "error",
          message: "Invalid or expired verification token.",
        };
      default:
        return { status: "error", message: result.error };
    }
  }

  switch (result.status) {
    case "already_verified":
      return { status: "already", message: "Email already verified!" };
    case "verified":
      return { status: "success", message: "Email verified successfully!" };
    default:
      return { status: "error", message: "Unexpected response." };
  }
}

export async function sbSubmitMasterApplication(
  github: string,
  name: string,
  bio: string,
  repoUrls: string[],
): Promise<{ status: string; message: string }> {
  const sb = ensureSupabase();

  const { error } = await sb.from("master_applications").insert({
    github,
    name,
    bio,
    repo_urls: JSON.stringify(repoUrls),
    status: "pending",
  });

  if (error) {
    return { status: "error", message: error.message };
  }

  return {
    status: "submitted",
    message: "Application submitted! We will review it soon.",
  };
}

export interface VerifiedCreatorApplicationPayload {
  display_name: string;
  github_username: string;
  skill_categories: string[];
  timezone: string;
  available_for_hire: boolean;
  rate_min: number | null;
  rate_max: number | null;
  bio: string;
}

export async function sbSubmitVerifiedCreatorApplication(
  payload: VerifiedCreatorApplicationPayload,
): Promise<{ status: string; message: string }> {
  const sb = ensureSupabase();

  const { error } = await sb.from("verified_creator_applications").insert({
    display_name: payload.display_name,
    github_username: payload.github_username,
    skill_categories: payload.skill_categories,
    timezone: payload.timezone,
    available_for_hire: payload.available_for_hire,
    rate_min: payload.rate_min,
    rate_max: payload.rate_max,
    bio: payload.bio,
    status: "pending",
  });

  if (error) {
    return { status: "error", message: error.message };
  }

  return {
    status: "submitted",
    message: "Application submitted. We'll review within 5 business days.",
  };
}

export async function sbSubmitWorkflow(
  name: string,
  description: string,
  steps: { name: string; slug: string; description: string }[],
): Promise<{ status: string; message: string }> {
  const sb = ensureSupabase();

  const { error } = await sb.from("submitted_workflows").insert({
    name,
    description,
    steps: JSON.stringify(steps),
    submitted_by: "community",
    status: "pending",
  });

  if (error) {
    return { status: "error", message: error.message };
  }

  return {
    status: "submitted",
    message: "Workflow submitted! It will be reviewed by our team.",
  };
}

export async function sbAdminAction<T = unknown>(
  token: string,
  action: string,
  payload: Record<string, unknown> = {},
): Promise<T> {
  const sb = ensureSupabase();
  const { data, error } = await sb.rpc("admin_action", {
    admin_token: token,
    action,
    payload,
  });
  if (error) throw new Error(error.message);
  return data as T;
}
