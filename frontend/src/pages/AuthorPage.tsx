import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { fetchSkills } from "../api/client";
import { SkillCard } from "../components/SkillCard";
import { SkeletonCards } from "../components/SkeletonCards";
import { Pagination } from "../components/Pagination";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import type { PaginatedSkills, Skill } from "../types/skill";

const PAGE_SIZE = 30;

export function AuthorPage() {
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<PaginatedSkills | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  const load = useCallback(() => {
    if (!username) return;
    setLoading(true);
    fetchSkills({
      author: username,
      sort_by: "stars",
      sort_order: "desc",
      page,
      page_size: PAGE_SIZE,
    })
      .then(setData)
      .catch(console.error)
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

  // Derive author profile data from the first skill (all skills share the same author).
  const profile = useMemo(() => {
    const first = data?.items?.[0];
    if (!first) return null;
    const totalStars = (data?.items ?? []).reduce(
      (sum, s) => sum + (s.stars || 0),
      0,
    );
    const avgScore =
      (data?.items ?? []).reduce((sum, s) => sum + (s.score || 0), 0) /
      Math.max(1, data?.items?.length ?? 0);
    return {
      name: first.author_name,
      avatar: first.author_avatar_url,
      followers: first.author_followers,
      totalStars,
      avgScore,
    };
  }, [data]);

  const displayName = profile?.name || username || "Author";
  const total = data?.total ?? 0;
  const title = `${displayName} — ${total || ""} Claude Skills & Agent Tools · AgentSkillsHub`;
  const description = `Browse all ${total} open-source AI agent skills, MCP servers, and Claude skills by ${displayName}. Ranked by stars and quality score.`;

  return (
    <>
      <Helmet>
        <title>{title}</title>
        <meta name="description" content={description} />
        <link
          rel="canonical"
          href={`https://agentskillshub.top/author/${username}/`}
        />
        <meta property="og:title" content={title} />
        <meta property="og:description" content={description} />
        <meta property="og:type" content="profile" />
        {profile?.avatar && (
          <meta property="og:image" content={profile.avatar} />
        )}
        <meta name="twitter:card" content="summary" />
        <meta name="twitter:title" content={title} />
      </Helmet>

      <SiteHeader />

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <nav className="text-sm text-gray-400 dark:text-gray-500 mb-4">
          <Link to="/" className="text-indigo-500 hover:text-indigo-600">
            Home
          </Link>
          <span className="mx-2">&gt;</span>
          <span className="text-gray-600 dark:text-gray-300">Authors</span>
          <span className="mx-2">&gt;</span>
          <span className="text-gray-600 dark:text-gray-300">
            {displayName}
          </span>
        </nav>

        {/* Author header */}
        <div className="flex items-center gap-5 mb-8">
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
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white truncate">
              {displayName}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {total > 0
                ? `${total} open-source skills · ${profile?.totalStars.toLocaleString() || 0}+ stars across visible repos`
                : loading
                  ? "Loading author profile..."
                  : "No skills found for this author yet."}
            </p>
            <a
              href={`https://github.com/${displayName}`}
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
              github.com/{displayName}
            </a>
          </div>
        </div>

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
        ) : (
          <p className="text-center text-gray-400 py-16">
            No public skills found for <b>{displayName}</b>.
          </p>
        )}

        {/* Back to home */}
        <div className="text-center mt-12">
          <Link
            to="/"
            className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Explore All Skills
          </Link>
        </div>
      </main>

      <SiteFooter />
    </>
  );
}
