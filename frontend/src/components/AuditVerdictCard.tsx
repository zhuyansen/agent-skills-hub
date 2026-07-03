import { Link } from "react-router-dom";
import { useI18n } from "../i18n/I18nContext";
import type { SkillDetail } from "../types/skill";

/**
 * Grade-first audit verdict for the skill detail page — the Trust Layer's
 * answer to "is this safe to install?", shown before README/stats instead of
 * burying the grade in a metadata chip. Mirrors the CLI/MCP verdict copy.
 */

const GRADE_STYLE: Record<
  string,
  { icon: string; label: string; card: string; badge: string }
> = {
  safe: {
    icon: "✓",
    label: "SAFE",
    card: "border-green-200 dark:border-green-800 bg-green-50/60 dark:bg-green-900/15",
    badge: "bg-green-600 text-white",
  },
  caution: {
    icon: "⚠",
    label: "CAUTION",
    card: "border-amber-200 dark:border-amber-800 bg-amber-50/60 dark:bg-amber-900/15",
    badge: "bg-amber-500 text-white",
  },
  unsafe: {
    icon: "✕",
    label: "UNSAFE",
    card: "border-red-200 dark:border-red-800 bg-red-50/60 dark:bg-red-900/15",
    badge: "bg-red-600 text-white",
  },
  reject: {
    icon: "⛔",
    label: "REJECT",
    card: "border-red-300 dark:border-red-700 bg-red-100/60 dark:bg-red-900/25",
    badge: "bg-red-700 text-white",
  },
  unknown: {
    icon: "?",
    label: "UNAUDITED",
    card: "border-gray-200 dark:border-gray-700 bg-gray-50/60 dark:bg-gray-800/40",
    badge: "bg-gray-500 text-white",
  },
};

const VERDICT_KEY = {
  safe: "auditCard.verdict.safe",
  caution: "auditCard.verdict.caution",
  unsafe: "auditCard.verdict.unsafe",
  reject: "auditCard.verdict.reject",
  unknown: "auditCard.verdict.unknown",
} as const;

function parseFlags(raw: SkillDetail["security_flags"]): string[] {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  try {
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch {
    return [];
  }
}

export function AuditVerdictCard({ skill }: { skill: SkillDetail }) {
  const { t } = useI18n();
  const grade: keyof typeof VERDICT_KEY =
    skill.security_grade && skill.security_grade in VERDICT_KEY
      ? (skill.security_grade as keyof typeof VERDICT_KEY)
      : "unknown";
  const s = GRADE_STYLE[grade];
  const flags = parseFlags(skill.security_flags);

  return (
    <section
      aria-label="Security audit verdict"
      className={`rounded-xl border p-5 mb-6 ${s.card}`}
    >
      <div className="flex flex-wrap items-center gap-3 mb-2">
        <span
          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-bold tracking-wide ${s.badge}`}
        >
          <span aria-hidden>{s.icon}</span>
          {s.label}
        </span>
        <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          {t("auditCard.title")}
        </h2>
        <span className="ml-auto text-xs text-gray-400 dark:text-gray-500">
          {t("auditCard.method")}
        </span>
      </div>

      <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
        {t(VERDICT_KEY[grade])}
      </p>

      {flags.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-1.5">
          {flags.map((f) => (
            <li
              key={f}
              className="px-2 py-0.5 rounded text-xs font-mono bg-white/70 dark:bg-black/30 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400"
            >
              🚩 {f}
            </li>
          ))}
        </ul>
      )}

      {grade === "unknown" && (
        <ul className="mt-3 space-y-1 text-xs text-gray-500 dark:text-gray-400 list-disc list-inside">
          <li>{t("auditCard.check.credentials")}</li>
          <li>{t("auditCard.check.maintainer")}</li>
          <li>{t("auditCard.check.code")}</li>
        </ul>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
        <Link
          to={`/analyzer?repo=${encodeURIComponent(`https://github.com/${skill.repo_full_name}`)}`}
          className="font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
        >
          {t("auditCard.rescan")} →
        </Link>
        <Link
          to="/enterprise/"
          className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
        >
          {t("auditCard.deepAudit")}
        </Link>
      </div>
    </section>
  );
}
