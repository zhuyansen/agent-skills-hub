import { Link } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";
import { trackEvent } from "../lib/analytics";
import { USD_PRICING } from "../lib/checkout";
import {
  LEFT_HOUSE_CARDS,
  LEFT_SPONSORS,
  RIGHT_HOUSE_CARDS,
  RIGHT_SPONSORS,
  SLOTS_PER_SIDE,
  TOTAL_SPONSOR_SLOTS,
  type SponsorSlot,
  type SponsorTheme,
} from "../data/sponsors";

interface RailProps {
  side: "left" | "right";
}

const THEME_STYLES: Record<
  SponsorTheme,
  { card: string; badge: string }
> = {
  emerald: {
    card: "bg-emerald-50/90 border-emerald-200/80 hover:border-emerald-400 dark:bg-[#0d241b]/95 dark:border-emerald-500/20 dark:hover:border-emerald-400/45",
    badge: "bg-emerald-500/15 text-emerald-700 dark:bg-emerald-400/20 dark:text-emerald-300",
  },
  violet: {
    card: "bg-purple-50/90 border-purple-200/80 hover:border-purple-400 dark:bg-[#22122e]/95 dark:border-fuchsia-500/20 dark:hover:border-fuchsia-400/45",
    badge: "bg-purple-500/15 text-purple-700 dark:bg-fuchsia-400/20 dark:text-fuchsia-300",
  },
  blue: {
    card: "bg-blue-50/90 border-blue-200/80 hover:border-blue-400 dark:bg-[#111b36]/95 dark:border-blue-500/20 dark:hover:border-blue-400/45",
    badge: "bg-blue-500/15 text-blue-700 dark:bg-blue-400/20 dark:text-blue-300",
  },
  rose: {
    card: "bg-rose-50/90 border-rose-200/80 hover:border-rose-400 dark:bg-[#2a151b]/95 dark:border-rose-500/20 dark:hover:border-rose-400/45",
    badge: "bg-rose-500/15 text-rose-700 dark:bg-rose-400/20 dark:text-rose-300",
  },
  indigo: {
    card: "bg-indigo-50/90 border-indigo-200/80 hover:border-indigo-400 dark:bg-[#151836]/95 dark:border-indigo-500/25 dark:hover:border-indigo-400/50",
    badge: "bg-indigo-500/15 text-indigo-700 dark:bg-indigo-400/20 dark:text-indigo-300",
  },
  amber: {
    card: "bg-amber-50/90 border-amber-200/80 hover:border-amber-400 dark:bg-[#261c10]/95 dark:border-amber-500/20 dark:hover:border-amber-400/45",
    badge: "bg-amber-500/15 text-amber-700 dark:bg-amber-400/20 dark:text-amber-300",
  },
};

function RailCard({ slot, side }: { slot: SponsorSlot; side: "left" | "right" }) {
  const { lang } = useI18n();
  const isZh = lang === "zh";
  const name = isZh && slot.nameZh ? slot.nameZh : slot.name;
  const tagline = isZh && slot.taglineZh ? slot.taglineZh : slot.tagline;
  const palette = THEME_STYLES[slot.theme] ?? THEME_STYLES.indigo;
  const isExternal = /^https?:\/\//i.test(slot.url);

  const inner = (
    <div
      className={`group relative rounded-2xl border px-4 py-5 min-h-[126px] flex flex-col items-center justify-center text-center transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg ${palette.card}`}
    >
      {slot.sponsored && (
        <span className="absolute top-2.5 right-2.5 text-[9px] font-medium uppercase tracking-wider text-gray-400 dark:text-white/35">
          {isZh ? "赞助" : "Ad"}
        </span>
      )}
      {slot.logoUrl ? (
        <img
          src={slot.logoUrl}
          alt={name}
          width={32}
          height={32}
          loading="lazy"
          className="w-8 h-8 rounded-lg object-cover mb-2.5 shadow-sm"
        />
      ) : (
        <span
          className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold mb-2.5 ${palette.badge}`}
        >
          {slot.badge}
        </span>
      )}
      <span className="text-[13px] font-semibold text-gray-900 dark:text-white leading-tight mb-1.5">
        {name}
      </span>
      <p className="text-[11.5px] leading-snug text-gray-600 dark:text-white/60 line-clamp-2">
        {tagline}
      </p>
    </div>
  );

  if (isExternal) {
    return (
      <a
        href={slot.url}
        target="_blank"
        rel={slot.sponsored ? "sponsored noopener noreferrer" : "noopener noreferrer"}
        onClick={() => trackEvent("sponsor_slot_click", { slot_id: slot.id, side, sponsored: !!slot.sponsored })}
        className="block no-underline"
      >
        {inner}
      </a>
    );
  }

  return (
    <Link
      to={slot.url}
      onClick={() => trackEvent("sponsor_slot_click", { slot_id: slot.id, side, sponsored: false })}
      className="block no-underline"
    >
      {inner}
    </Link>
  );
}

function AdvertiseCard({ side, openTotal }: { side: "left" | "right"; openTotal: number }) {
  const { lang } = useI18n();
  const isZh = lang === "zh";

  return (
    <Link
      to="/submit/#sponsor"
      onClick={() => trackEvent("sponsor_rail_advertise_click", { side })}
      className="group rounded-2xl border border-dashed border-gray-300 dark:border-white/15 bg-white/70 dark:bg-white/[0.02] hover:border-indigo-400 dark:hover:border-indigo-400/60 hover:bg-indigo-50/50 dark:hover:bg-indigo-500/[0.07] px-4 py-5 min-h-[126px] flex flex-col items-center justify-center text-center transition-all duration-200 hover:-translate-y-0.5 no-underline"
    >
      <svg
        className="w-5 h-5 text-gray-400 dark:text-white/45 group-hover:text-indigo-500 dark:group-hover:text-indigo-400 mb-2 transition-colors"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"
        />
      </svg>
      <span className="text-[13px] font-semibold text-gray-700 dark:text-white/85 group-hover:text-indigo-600 dark:group-hover:text-indigo-300 transition-colors">
        {isZh ? "投放广告位" : "Advertise"}
      </span>
      <span className="text-[11px] text-gray-500 dark:text-white/45 mt-1">
        {isZh
          ? `余 ${openTotal}/${TOTAL_SPONSOR_SLOTS} 席 · ${USD_PRICING.sponsorMonthly}`
          : `${openTotal}/${TOTAL_SPONSOR_SLOTS} spots left · ${USD_PRICING.sponsorMonthly}`}
      </span>
    </Link>
  );
}

/**
 * TrustMRR-style sticky desktop sponsor rail placed on the left or right flank of
 * the homepage. Hidden below `xl` (<1280px) so mobile & narrow screens stay clean.
 */
export function HomepageSponsorRail({ side }: RailProps) {
  const paid = side === "left" ? LEFT_SPONSORS : RIGHT_SPONSORS;
  const house = side === "left" ? LEFT_HOUSE_CARDS : RIGHT_HOUSE_CARDS;
  const openTotal = Math.max(
    0,
    TOTAL_SPONSOR_SLOTS - LEFT_SPONSORS.length - RIGHT_SPONSORS.length,
  );

  // Fill up to SLOTS_PER_SIDE - 1 top cards (paid sponsors first, then house cards),
  // reserving the bottom slot for the clean dashed "Advertise" card whenever seats remain.
  const maxContentSlots = openTotal > 0 ? Math.max(1, SLOTS_PER_SIDE - 1) : SLOTS_PER_SIDE;
  const cards: SponsorSlot[] = [
    ...paid.slice(0, maxContentSlots).map((s) => ({ ...s, sponsored: true })),
    ...house.slice(0, Math.max(0, maxContentSlots - paid.length)),
  ];

  return (
    <aside
      aria-label={side === "left" ? "Sponsored tools (left)" : "Sponsored tools (right)"}
      className="hidden xl:flex flex-col gap-3.5 w-[196px] 2xl:w-[216px] shrink-0 sticky top-32 self-start pt-4 z-30"
    >
      {cards.map((slot) => (
        <RailCard key={slot.id} slot={slot} side={side} />
      ))}
      {openTotal > 0 && <AdvertiseCard side={side} openTotal={openTotal} />}
    </aside>
  );
}
