/**
 * TrustMRR-style left & right homepage sponsor rail inventory.
 *
 * Editorial neutrality rule:
 *   - Every paid slot is explicitly labeled "Sponsored" and uses `rel="sponsored noopener noreferrer"`.
 *   - Sponsorship buys homepage visibility ONLY — never a SAFE grade, audit override,
 *     or organic ranking slot on /best/* guides.
 *
 * To activate a paid sponsor, add an entry to `LEFT_SPONSORS` or `RIGHT_SPONSORS`
 * (up to `SLOTS_PER_SIDE` each). Unfilled slots render a clean "Advertise here" CTA
 * pointing to `/submit/#sponsor`.
 */

export interface SponsorSlot {
  id: string;
  name: string;
  tagline: string;
  taglineZh?: string;
  url: string;
  /** Short 1–2 char monogram or emoji badge when no logo URL is provided. */
  badge: string;
  /** Optional square icon URL (32x32). */
  logoUrl?: string;
  /** Optional accent color classes for the badge background. */
  accent?: string;
}

export const SLOTS_PER_SIDE = 4;
export const TOTAL_SPONSOR_SLOTS = SLOTS_PER_SIDE * 2;

export const LEFT_SPONSORS: SponsorSlot[] = [];

export const RIGHT_SPONSORS: SponsorSlot[] = [];
