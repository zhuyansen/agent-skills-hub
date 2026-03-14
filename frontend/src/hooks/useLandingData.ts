import { useCachedQuery } from "./useCachedQuery";
import { fetchLandingData } from "../api/client";
import type { LandingData } from "../types/skill";

/**
 * Fetches all overview/landing page data in a single request.
 * Uses useCachedQuery for instant cache-first loading + background revalidation.
 */
export function useLandingData() {
  return useCachedQuery<LandingData>("landing_data", fetchLandingData);
}
