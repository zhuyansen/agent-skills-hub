import { useEffect, useState } from "react";
import { fetchMasters, fetchOrgBuilders, type Master, type OrgBuilder } from "../api/client";
import { useI18n } from "../i18n/I18nContext";

function formatCount(n: number): string {
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

export function SkillsMasters() {
  const { t } = useI18n();
  const [masters, setMasters] = useState<Master[]>([]);
  const [orgs, setOrgs] = useState<OrgBuilder[]>([]);
  const [expandedOrgIdx, setExpandedOrgIdx] = useState<number | null>(null);

  useEffect(() => {
    fetchMasters().then((data) => {
      const cleaned = data.map((m) => ({
        ...m,
        top_repos: (m.top_repos || []).filter((r) => r.stars > 0),
      })).filter((m) => m.total_stars > 0 || m.x_followers > 0 || !m.discovered);
      setMasters(cleaned);
    }).catch(console.error);

    fetchOrgBuilders().then((data) => {
      setOrgs(data.filter((o) => o.total_stars > 0));
    }).catch(console.error);
  }, []);

  const curated = masters.filter((m) => !m.discovered);

  if (curated.length === 0 && orgs.length === 0) return null;

  return (
    <section className="mb-10">
      {/* Skills Masters */}
      {curated.length > 0 && (
        <>
          <div className="mb-4">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128H9m6 0a5.972 5.972 0 00-.786-3.07M9 19.128v-.003c0-1.113.285-2.16.786-3.07M9 19.128H3.375a4.125 4.125 0 017.533-2.493M9 19.128a5.972 5.972 0 01.786-3.07m4.428 0a9.36 9.36 0 00-4.428 0M12 10.5a3.75 3.75 0 110-7.5 3.75 3.75 0 010 7.5z"/></svg>
              <h2 className="text-lg font-bold text-gray-900">{t("masters.title")}</h2>
              <span className="text-sm text-gray-400">{t("masters.subtitle")}</span>
            </div>
            <p className="text-xs text-gray-400 mt-1.5 ml-7">
              {t("masters.warning")}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            {curated.map((m) => (
              <div
                key={m.github}
                className="bg-gradient-to-br from-white to-indigo-50/30 border border-indigo-100 rounded-xl p-5 hover:shadow-lg transition-all"
              >
                {/* Header */}
                <div className="flex items-start gap-4 mb-4">
                  <img
                    src={m.avatar_url}
                    alt=""
                    className="w-14 h-14 rounded-full border-2 border-indigo-200 shadow-sm"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-gray-900">{m.name}</h3>
                      <span className="px-1.5 py-0.5 text-[10px] bg-emerald-100 text-emerald-700 rounded-full font-semibold">
                        {t("masters.verified")}
                      </span>
                    </div>
                    <a
                      href={`https://github.com/${m.github}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-gray-500 hover:text-indigo-600"
                    >
                      @{m.github}
                    </a>
                    {m.x_handle && (
                      <span className="text-xs text-gray-400 ml-2">
                        ·{" "}
                        <a
                          href={`https://x.com/${m.x_handle}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:text-blue-500"
                        >
                          @{m.x_handle}
                        </a>
                        {m.x_followers > 0 && (
                          <span className="ml-1 text-gray-400">
                            · {formatCount(m.x_followers)} {t("masters.followers")}
                          </span>
                        )}
                        {m.x_posts_count > 0 && (
                          <span className="ml-1 text-gray-400">
                            · {formatCount(m.x_posts_count)} {t("masters.posts")}
                          </span>
                        )}
                      </span>
                    )}
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">{m.bio}</p>
                  </div>
                </div>

                {/* Stats */}
                <div className="flex items-center gap-4 mb-3 text-sm">
                  <span className="flex items-center gap-1 text-gray-600">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                    </svg>
                    <strong>{m.repo_count}</strong> {t("masters.repos")}
                  </span>
                  <span className="flex items-center gap-1 text-gray-600">
                    <svg className="w-4 h-4 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                    </svg>
                    <strong>{m.total_stars >= 1000 ? `${(m.total_stars / 1000).toFixed(1)}k` : m.total_stars}</strong> {t("masters.totalStars")}
                  </span>
                </div>

                {/* Tags */}
                {m.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {m.tags.map((tag) => (
                      <span key={tag} className="px-2 py-0.5 text-[10px] rounded-full bg-indigo-50 text-indigo-500 border border-indigo-100">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                {/* Top repos */}
                <div className="space-y-1.5">
                  {m.top_repos.slice(0, 4).map((r) => (
                    <a
                      key={r.id}
                      href={r.repo_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/80 border border-gray-100 hover:border-indigo-200 hover:bg-indigo-50/30 transition-all text-sm"
                    >
                      <span className="font-medium text-gray-800 truncate flex-1">{r.repo_name}</span>
                      <span className="flex items-center gap-0.5 text-xs text-gray-500 shrink-0">
                        <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                        </svg>
                        {r.stars >= 1000 ? `${(r.stars / 1000).toFixed(1)}k` : r.stars}
                      </span>
                    </a>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Organization Builders */}
      {orgs.length > 0 && (
        <>
          <div className="flex items-center gap-2 mb-3 mt-6">
            <svg className="w-4 h-4 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 21c0-4-3-7-7-7 4 0 7-3 7-7 0 4 3 7 7 7-4 0-7 3-7 7z"/></svg>
            <h3 className="text-sm font-semibold text-gray-700">{t("emerging.title")}</h3>
            <span className="text-xs text-gray-400">{t("emerging.subtitle")}</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {orgs.map((o, i) => {
              const isExpanded = expandedOrgIdx === i;
              const visibleRepos = (o.top_repos || []).filter((r) => r.stars > 0);
              return (
                <div
                  key={o.github}
                  className="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-md hover:border-purple-200 transition-all"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <img
                      src={o.avatar_url}
                      alt=""
                      className="w-10 h-10 rounded-full border border-gray-100"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <a
                          href={`https://github.com/${o.github}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-semibold text-sm text-gray-900 hover:text-purple-600 transition-colors truncate block"
                        >
                          {o.github}
                        </a>
                        <span className="px-1.5 py-0.5 text-[10px] bg-purple-100 text-purple-600 rounded-full font-semibold shrink-0">
                          {t("emerging.rising")}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span>{o.repo_count} {t("masters.repos")}</span>
                        <span className="flex items-center gap-0.5">
                          <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                          </svg>
                          {formatCount(o.total_stars)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Mini repo list */}
                  <div className="space-y-1">
                    {visibleRepos.slice(0, isExpanded ? 5 : 2).map((r) => (
                      <a
                        key={r.id}
                        href={r.repo_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-between px-2 py-1.5 rounded-md hover:bg-gray-50 transition-colors text-xs"
                      >
                        <span className="font-medium text-gray-700 truncate">{r.repo_name}</span>
                        <span className="flex items-center gap-0.5 text-gray-400 shrink-0 ml-2">
                          <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                          {formatCount(r.stars)}
                        </span>
                      </a>
                    ))}
                  </div>

                  {visibleRepos.length > 2 && (
                    <button
                      onClick={() => setExpandedOrgIdx(isExpanded ? null : i)}
                      className="text-xs text-purple-500 hover:text-purple-700 mt-1 font-medium"
                    >
                      {isExpanded ? t("masters.showLess") : `+${visibleRepos.length - 2} ${t("masters.more")}`}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}
