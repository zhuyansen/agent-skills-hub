import { useEffect, useState } from "react";
import { fetchLandingData } from "../api/client";
import type { LandingData } from "../types/skill";

/**
 * Fetches all overview/landing page data in a single request.
 * When the backend is available, this replaces 7+ individual API calls
 * with one bundled `/api/landing` call, eliminating waterfall latency.
 */
export function useLandingData() {
  const [data, setData] = useState<LandingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchLandingData()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { data, loading, error };
}
