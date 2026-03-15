/**
 * Shared time & formatting utilities.
 * Replaces 8+ duplicate timeAgo implementations across components.
 */

export function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "Unknown";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days === 1) return "Yesterday";
  if (days < 30) return `${days}d ago`;
  if (days < 365) return `${Math.floor(days / 30)}mo ago`;
  return `${Math.floor(days / 365)}y ago`;
}

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return "N/A";
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function parseTags(topics: string): string[] {
  try {
    return JSON.parse(topics);
  } catch {
    return [];
  }
}

export function formatStars(stars: number): string {
  if (stars >= 1000) return `${(stars / 1000).toFixed(1)}k`;
  return stars.toLocaleString();
}

/** Check if a skill was first indexed within `days` days */
export function isNew(firstSeen: string | null, days = 7): boolean {
  if (!firstSeen) return false;
  return Date.now() - new Date(firstSeen).getTime() < days * 24 * 60 * 60 * 1000;
}

/** Check if a date is within `days` days from now */
export function isRecentlyUpdated(dateStr: string | null, days = 3): boolean {
  if (!dateStr) return false;
  return Date.now() - new Date(dateStr).getTime() < days * 24 * 60 * 60 * 1000;
}
