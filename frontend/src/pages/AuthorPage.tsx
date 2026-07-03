import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { fetchSkills, fetchMasters, fetchOrgBuilders } from "../api/client";
import type { Master } from "../api/client";
import { SkillCard } from "../components/SkillCard";
import { SkeletonCards } from "../components/SkeletonCards";
import { Pagination } from "../components/Pagination";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { useI18n } from "../i18n/I18nContext";
import { isVerifiedOrgAuthor } from "../data/verifiedOrgs";
import type { PaginatedSkills, Skill } from "../types/skill";

const PAGE_SIZE = 30;

export function AuthorPage() {
  const { t } = useI18n();
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  // /organization/{name}/ is the canonical namespace for GitHub orgs;
  // /author/{name}/ stays canonical for individual creators.
  const isOrgRoute = location.pathname.startsWith("/organization/");
  const [data, setData] = useState<PaginatedSkills | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [copied, setCopied] = useState(false);
  // Curated master profile (skill_masters): real name, bio, X handle,
  // verified status — the LobeHub-style creator-page enrichment. isOrg flips
  // the JSON-LD entity to Organization (GitHub orgs like anthropics).
  const [master, setMaster] = useState<Master | null>(null);
  const [isOrg, setIsOrg] = useState(false);

  useEffect(() => {
    if (!username) return;
    let cancelled = false;
    const key = username.toLowerCase();
    fetchMasters()
      .then((all) => {
        if (cancelled) return;
        const hit = all.find(
          (m) =>
            m.github?.toLowerCase() === key ||
            (m.github_aliases ?? []).some((a) => a.toLowerCase() === key),
        );
        setMaster(hit ?? null);
      })
      .catch(() => {});
    fetchOrgBuilders()
      .then((orgs) => {
        if (cancelled) return;
        setIsOrg(orgs.some((o) => o.github?.toLowerCase() === key));
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [username]);

  // fetchError separates "the query returned zero rows" from "the query never
  // arrived" (slow/flaky Supabase closing connections). Without it a transient
  // network failure rendered as "No public skills found for {name}" — a lying
  // empty state, worst possible message on a creator's own vanity page.
  const [fetchError, setFetchError] = useState(false);

  const load = useCallback(() => {
    if (!username) return;
    setLoading(true);
    setFetchError(false);
    fetchSkills({
      author: username,
      sort_by: "stars",
      sort_order: "desc",
      page,
      page_size: PAGE_SIZE,
    })
      .then(setData)
      .catch((err) => {
        console.error(err);
        setFetchError(true);
      })
      .finally(() => setLoading(false));
  }, [username, page]);

  useEffect(() => {
    load();
    window.scrollTo(0, 0);
  }, [load]);

  const handleShowDetail = useCallback(
    (skill: Skill) => {
      navigate(`/skill/${skill.repo_full_name}/`);
    },
    [navigate],
  );

  // Derive author profile + trust stats from the loaded skills (the Trust Layer
  // signals — quality score + security grade — are what set a collection page
  // here apart from a generic marketplace listing).
  const profile = useMemo(() => {
    const items = data?.items ?? [];
    const first = items[0];
    if (!first) return null;
    const totalStars = items.reduce((sum, s) => sum + (s.stars || 0), 0);
    const scored = items.filter((s) => typeof s.quality_score === "number");
    const avgQuality = scored.length
      ? Math.round(
          scored.reduce((sum, s) => sum + (s.quality_score || 0), 0) /
            scored.length,
        )
      : 0;
    const safeCount = items.filter((s) => s.security_grade === "safe").length;
    const topRepos = items.slice(0, 5).map((s) => s.repo_full_name);
    const topCategory = first.category;
    return {
      name: first.author_name,
      avatar: first.author_avatar_url,
      totalStars,
      avgQuality,
      safeCount,
      topRepos,
      topCategory,
    };
  }, [data]);

  const displayName = master?.name || profile?.name || username || "Author";
  const githubName = profile?.name || username || "";
  const total = data?.total ?? 0;
  const verified = isVerifiedOrgAuthor(githubName) || !!master?.is_verified;
  const xHandle = master?.x_handle?.replace(/^@/, "") || null;
  // Entity type: org-builders RPC hit, curated verified-org list, or being on
  // the /organization/ route all mean "organization".
  const entityIsOrg = isOrg || isOrgRoute || isVerifiedOrgAuthor(githubName);
  const canonicalPath = entityIsOrg ? "organization" : "author";
  const canonicalUrl = `https://agentskillshub.top/${canonicalPath}/${username}/`;
  const installCmd = profile?.topRepos.length
    ? `npx @agentskillshub/cli install ${profile.topRepos.slice(0, 3).join(" ")}`
    : "";
  // Name-search intent (LobeHub pattern): lead with the creator's name + the
  // security angle only we can claim.
  const title = `${displayName} — Top ${total || ""} AI Agent Skills${profile?.safeCount ? " (Security-Graded)" : ""} · Agent Skills Hub`;
  const description = `${displayName}'s AI agent skills: ${total} open-source skills & MCP servers${profile?.safeCount ? `, ${profile.safeCount} security-verified safe` : ""}. Quality-scored on AgentSkillsHub.`;
  const personLd = JSON.stringify({
    "@context": "https://schema.org",
    "@type": entityIsOrg ? "Organization" : "Person",
    name: displayName,
    alternateName: githubName,
    url: canonicalUrl,
    ...(profile?.avatar ? { image: profile.avatar } : {}),
    ...(master?.bio ? { description: master.bio } : {}),
    sameAs: [
      `https://github.com/${githubName}`,
      ...(xHandle ? [`https://x.com/${xHandle}`] : []),
    ],
  });

  return (
    <div className="min-h-screen flex flex-col">
      <Helmet>
        <title>{title}</title>
        <meta name="description" content={description} />
        <link rel="canonical" href={canonicalUrl} />
        <meta property="og:title" content={title} />
        <meta property="og:description" content={description} />
        <meta property="og:type" content="profile" />
        {profile?.avatar && (
          <meta property="og:image" content={profile.avatar} />
        )}
        <meta name="twitter:card" content="summary" />
        <meta name="twitter:title" content={title} />
        <script type="application/ld+json">{personLd}</script>
      </Helmet>

      <SiteHeader />

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <nav className="text-sm text-gray-400 dark:text-gray-500 mb-4">
          <Link to="/" className="text-indigo-500 hover:text-indigo-600">
            {t("common.home")}
          </Link>
          <span className="mx-2">&gt;</span>
          <span className="text-gray-600 dark:text-gray-300">
            {t("author.breadcrumb")}
          </span>
          <span className="mx-2">&gt;</span>
          <span className="text-gray-600 dark:text-gray-300">
            {displayName}
          </span>
        </nav>

        {/* Author header */}
        <div className="flex items-start gap-5 mb-6">
          {profile?.avatar ? (
            <img
              src={profile.avatar}
              alt={displayName}
              width={72}
              height={72}
              className="w-18 h-18 rounded-full border-2 border-gray-200 dark:border-gray-700 shrink-0"
            />
          ) : (
            <div className="w-18 h-18 rounded-full bg-gray-200 dark:bg-gray-700 shrink-0" />
          )}
          <div className="min-w-0">
            <h1 className="flex items-center gap-2 text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
              <span className="truncate">{displayName}</span>
              {verified && (
                <span
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 shrink-0"
                  title={t("author.verifiedTitle")}
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <path d="M12 2L4 6v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V6l-8-4zm-1.4 14.6L6 12l1.4-1.4 3.2 3.2 6.2-6.2L18.2 9l-7.6 7.6z" />
                  </svg>
                  {t("author.verified")}
                </span>
              )}
            </h1>
            {/* SEO-friendly unique intro */}
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1.5 leading-relaxed max-w-2xl">
              {total > 0
                ? t("author.intro")
                    .replace("{name}", displayName)
                    .replace("{n}", String(total))
                    .replace(
                      "{focus}",
                      profile?.topCategory
                        ? t("author.focus").replace(
                            "{cat}",
                            profile.topCategory,
                          )
                        : "",
                    )
                : loading
                  ? t("author.loading")
                  : t("author.noSkillsYet")}
            </p>
            {master?.bio && (
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-2 leading-relaxed max-w-2xl">
                {master.bio}
              </p>
            )}
            {xHandle && (
              <a
                href={`https://x.com/${xHandle}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-sm text-indigo-600 dark:text-indigo-400 hover:underline mt-2 mr-4"
              >
                <svg
                  className="w-3.5 h-3.5"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
                @{xHandle}
              </a>
            )}
            <a
              href={`https://github.com/${githubName}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-indigo-600 dark:text-indigo-400 hover:underline mt-2"
            >
              <svg
                className="w-4 h-4"
                fill="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
              </svg>
              github.com/{githubName}
            </a>
          </div>
        </div>

        {/* Trust stats bar — our differentiator (LobeHub shows installs, not trust) */}
        {total > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
            {[
              { v: total.toLocaleString(), l: t("author.statSkills") },
              {
                v: `${(profile?.totalStars || 0).toLocaleString()}+`,
                l: t("author.statStars"),
              },
              {
                v: `${profile?.avgQuality || 0}/100`,
                l: t("author.statQuality"),
              },
              { v: `${profile?.safeCount || 0}`, l: t("author.statSafe") },
            ].map((s) => (
              <div
                key={s.l}
                className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 px-4 py-3 text-center"
              >
                <div className="text-lg font-bold text-gray-900 dark:text-white tabular-nums">
                  {s.v}
                </div>
                <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">
                  {s.l}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Install-all (agent-first) — feed the prompt to your agent */}
        {installCmd && (
          <div className="rounded-xl overflow-hidden border border-gray-800 bg-[#0d1117] shadow-sm mb-8">
            <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800">
              <span className="text-[11px] text-gray-400 font-medium">
                {t("author.installLabel").replace("{name}", displayName)}
              </span>
              <button
                onClick={() => {
                  navigator.clipboard?.writeText(installCmd).then(() => {
                    setCopied(true);
                    setTimeout(() => setCopied(false), 1600);
                  });
                }}
                className="text-xs px-2.5 py-1 rounded-md text-gray-300 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 transition-colors cursor-pointer"
              >
                {copied ? t("author.copied") : t("author.copy")}
              </button>
            </div>
            <code className="block px-4 py-3 font-mono text-sm text-gray-100 overflow-x-auto whitespace-nowrap">
              <span className="text-emerald-400 select-none">$ </span>
              {installCmd}
            </code>
          </div>
        )}

        {/* Skills grid */}
        {loading ? (
          <SkeletonCards count={9} />
        ) : data?.items?.length ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.items.map((skill: Skill) => (
                <SkillCard
                  key={skill.id}
                  skill={skill}
                  onShowDetail={handleShowDetail}
                />
              ))}
            </div>
            {data.total_pages > 1 && (
              <div className="mt-8">
                <Pagination
                  page={page}
                  totalPages={data.total_pages}
                  onPageChange={setPage}
                />
              </div>
            )}
          </>
        ) : fetchError ? (
          <div className="text-center py-16">
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              {t("author.loadError")}
            </p>
            <button
              onClick={load}
              className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-colors cursor-pointer"
            >
              {t("author.retry")}
            </button>
          </div>
        ) : (
          <p className="text-center text-gray-400 py-16">
            {(() => {
              const [before, after] = t("author.noPublicSkills").split(
                "{name}",
              );
              return (
                <>
                  {before}
                  <b>{displayName}</b>
                  {after}
                </>
              );
            })()}
          </p>
        )}

        {/* Back to home */}
        <div className="text-center mt-12">
          <Link
            to="/"
            className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            {t("common.exploreAll")}
          </Link>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
