import { Link } from "react-router-dom";
import { VERIFIED_ORGANIZATIONS } from "../data/verifiedOrgs";

/**
 * Verified Organizations showcase.
 *
 * Deliberately SEPARATE from the data-driven "Organization Builders" list:
 * this is the certified / official-partner layer (✓ audited). Renders nothing
 * when there are no verified orgs, so it never shows an empty shell.
 *
 * Showcase ≠ ranking — certification never touches the objective Trending /
 * score / Organization Builders surfaces.
 */
export function VerifiedOrganizations() {
  if (VERIFIED_ORGANIZATIONS.length === 0) return null;

  return (
    <section className="mb-12">
      <div className="flex items-center gap-2 mb-1">
        <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500 text-white text-xs font-bold">
          ✓
        </span>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white tracking-tight">
          Verified Organizations
        </h2>
      </div>
      <p className="text-sm text-[var(--text-2)] mb-5">
        经 Hub 审计的官方机构 · 认证 ≠ 排名,客观榜单始终纯数据驱动
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {VERIFIED_ORGANIZATIONS.map((org) => (
          <div key={org.github} className="surface surface-hover p-5">
            <div className="flex items-start gap-4">
              <Link to={`/organization/${org.github}/`} className="shrink-0">
                <img
                  src={org.logo}
                  alt={org.name}
                  width={48}
                  height={48}
                  className="w-12 h-12 rounded-xl border border-[var(--border)] hover:border-indigo-400 transition-colors"
                  loading="lazy"
                />
              </Link>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5">
                  <h3 className="font-bold text-gray-900 dark:text-white truncate">
                    <Link
                      to={`/organization/${org.github}/`}
                      className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
                    >
                      {org.name}
                    </Link>
                  </h3>
                  <span
                    className="inline-flex items-center justify-center w-4 h-4 rounded-full bg-emerald-500 text-white text-[10px] font-bold shrink-0"
                    title="Verified Organization"
                  >
                    ✓
                  </span>
                </div>
                <p className="text-sm text-[var(--text-2)] leading-relaxed mt-1">
                  {org.tagline}
                </p>

                <div className="flex flex-wrap gap-2 mt-3">
                  {org.skills.map((s) => (
                    <Link
                      key={s.repo}
                      to={`/skill/${s.repo}/`}
                      className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-[var(--bg-elev)] text-[var(--text-1)] border border-[var(--border)] hover:border-indigo-400 transition-colors"
                    >
                      {s.label}
                    </Link>
                  ))}
                </div>

                {org.website && (
                  <a
                    href={org.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 mt-3 text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:underline"
                  >
                    官方 Skill 市场 →
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
