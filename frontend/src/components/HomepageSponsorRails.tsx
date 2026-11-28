import { Link } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";
import { trackEvent } from "../lib/analytics";
import { USD_PRICING } from "../lib/checkout";
import {
  LEFT_SPONSORS,
  RIGHT_SPONSORS,
  SLOTS_PER_SIDE,
  type SponsorSlot,
} from "../data/sponsors";

interface RailProps {
  side: "left" | "right";
}

function FilledSponsorCard({ slot, side }: { slot: SponsorSlot; side: "left" | "right" }) {
  const { lang } = useI18n();
  const isZh = lang === "zh";
  const tagline = isZh && slot.taglineZh ? slot.taglineZh : slot.tagline;

  return (
    <a
      href={slot.url}
      target="_blank"
      rel="sponsored noopener noreferrer"
      onClick={() => trackEvent("sponsor_slot_click", { slot_id: slot.id, side })}
      className="group block rounded-xl border border-gray-200 dark:border-gray-800 bg-white/95 dark:bg-gray-900/95 p-3 hover:border-indigo-400 dark:hover:border-indigo-500 hover:shadow-sm transition-all no-underline"
    >
      <div className="flex items-center gap-2 mb-1.5">
        {slot.logoUrl ? (
          <img
            src={slot.logoUrl}
            alt={slot.name}
            width={24}
            height={24}
            loading="lazy"
            className="w-6 h-6 rounded-md object-cover shrink-0"
          />
        ) : (
          <span
            className={`w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold shrink-0 ${
              slot.accent || "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300"
            }`}
          >
            {slot.badge}
          </span>
        )}
        <span className="text-xs font-semibold text-gray-900 dark:text-gray-100 truncate group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
          {slot.name}
        </span>
      </div>
      <p className="text-[11px] leading-snug text-gray-500 dark:text-gray-400 line-clamp-2">
        {tagline}
      </p>
      <span className="mt-2 inline-block text-[10px] uppercase tracking-wider text-gray-400 dark:text-gray-500">
        {isZh ? "赞助" : "Sponsored"}
      </span>
    </a>
  );
}

function OpenSponsorCard({ side, index }: { side: "left" | "right"; index: number }) {
  const { lang } = useI18n();
  const isZh = lang === "zh";
  const isFirst = index === 0;

  return (
    <Link
      to={`/submit/#sponsor`}
      onClick={() => trackEvent("sponsor_rail_advertise_click", { side, slot_index: index + 1 })}
      className={`group block rounded-xl border border-dashed p-3 transition-all no-underline ${
        isFirst
          ? "border-indigo-300/80 dark:border-indigo-700/70 bg-indigo-50/40 dark:bg-indigo-950/20 hover:border-indigo-500 hover:bg-indigo-50/80 dark:hover:bg-indigo-950/40"
          : "border-gray-200 dark:border-gray-800 bg-white/60 dark:bg-gray-900/40 hover:border-indigo-400 dark:hover:border-indigo-600"
      }`}
    >
      <div className="flex items-center justify-between gap-1 mb-1">
        <span className="text-[11px] font-semibold text-gray-700 dark:text-gray-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
          {isZh ? "首页赞助位" : "Advertise here"}
        </span>
        <span className="text-[10px] font-semibold text-indigo-600 dark:text-indigo-400">
          {USD_PRICING.sponsorMonthly}
        </span>
      </div>
      <p className="text-[11px] leading-snug text-gray-500 dark:text-gray-400">
        {isFirst
          ? isZh
            ? "面向 2 万+ AI Agent 开发者 · 独立标注赞助位"
            : "Reach 20K+ AI agent developers · rel=sponsored"
          : isZh
            ? "点击查看权益与排期 →"
            : "Claim an open desktop rail slot →"}
      </p>
    </Link>
  );
}

/**
 * Sticky desktop sponsor rail (TrustMRR-style) placed on the left or right flank of
 * the homepage. Hidden below `xl` (<1280px) so mobile & narrow screens stay clutter-free.
 */
export function HomepageSponsorRail({ side }: RailProps) {
  const { lang } = useI18n();
  const isZh = lang === "zh";
  const slots = side === "left" ? LEFT_SPONSORS : RIGHT_SPONSORS;
  const openCount = Math.max(0, SLOTS_PER_SIDE - slots.length);
  // Keep unfilled rail clean: show all filled sponsors plus at most 2 open CTA cards per side.
  const visibleOpen = Math.min(openCount, 2);

  return (
    <aside
      aria-label={side === "left" ? "Sponsored tools (left)" : "Sponsored tools (right)"}
      className="hidden xl:flex flex-col gap-2.5 w-[176px] 2xl:w-[196px] shrink-0 sticky top-32 self-start pt-8 z-30"
    >
      <div className="flex items-center justify-between px-1">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
          {isZh ? "赞助位" : "Sponsors"}
        </span>
        <Link
          to="/submit/#sponsor"
          onClick={() => trackEvent("sponsor_rail_advertise_click", { side, slot_index: 0 })}
          className="text-[10px] text-indigo-600 dark:text-indigo-400 hover:underline no-underline"
        >
          {isZh ? "投放" : "Book"}
        </Link>
      </div>
      {slots.slice(0, SLOTS_PER_SIDE).map((slot) => (
        <FilledSponsorCard key={slot.id} slot={slot} side={side} />
      ))}
      {Array.from({ length: visibleOpen }, (_, i) => (
        <OpenSponsorCard key={`open-${side}-${i}`} side={side} index={i} />
      ))}
    </aside>
  );
}
