import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { fetchSkills } from "../api/client";
import { SkillCard } from "../components/SkillCard";
import { SkeletonCards } from "../components/SkeletonCards";
import { Pagination } from "../components/Pagination";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import type { PaginatedSkills, Skill } from "../types/skill";

const CATEGORY_LABELS: Record<string, string> = {
  "mcp-server": "MCP Server",
  "claude-skill": "Claude Skill",
  "codex-skill": "Codex Skill",
  "agent-tool": "Agent Tool",
  "prompt-library": "Prompt Library",
  "ai-coding-assistant": "AI Coding Assistant",
  uncategorized: "AI Tool",
};

const ALL_CATEGORIES = Object.keys(CATEGORY_LABELS);

export function CategoryPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<PaginatedSkills | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  const catLabel = CATEGORY_LABELS[slug || ""] || slug || "AI Tool";

  const load = useCallback(() => {
    if (!slug) return;
    setLoading(true);
    fetchSkills({
      category: slug,
      sort_by: "stars",
      sort_order: "desc",
      page,
      page_size: 30,
    })
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [slug, page]);

  useEffect(() => {
    load();
    window.scrollTo(0, 0);
  }, [load]);

  const handleShowDetail = useCallback(
    (skill: Skill) => {
      navigate(`/skill/${skill.repo_full_name}`);
    },
    [navigate],
  );

  const title = `Best ${catLabel} Tools - Open Source Agent Skills | Agent Skills Hub`;
  const description = `Discover the top open-source ${catLabel} tools. Browse by stars, quality, and compatibility on Agent Skills Hub.`;

  return (
    <>
      <Helmet>
        <title>{title}</title>
        <meta name="description" content={description} />
        <link rel="canonical" href={`https://agentskillshub.top/category/${slug}/`} />
      </Helmet>

      <SiteHeader />

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <nav className="text-sm text-gray-400 mb-4">
          <Link to="/" className="text-indigo-500 hover:text-indigo-600">
            Home
          </Link>
          <span className="mx-2">&gt;</span>
          <span className="text-gray-600">{catLabel}</span>
        </nav>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          {catLabel} Tools
        </h1>
        <p className="text-gray-500 mb-6">
          {data?.total
            ? `${data.total}+ open-source ${catLabel.toLowerCase()} tools ranked by stars`
            : `Loading ${catLabel.toLowerCase()} tools...`}
        </p>

        {/* Other category links */}
        <div className="flex flex-wrap gap-2 mb-8">
          {ALL_CATEGORIES.filter((c) => c !== slug).map((c) => (
            <Link
              key={c}
              to={`/category/${c}`}
              className="px-3 py-1 text-sm rounded-full border border-gray-200 text-gray-600 hover:border-indigo-300 hover:text-indigo-600 transition-colors"
            >
              {CATEGORY_LABELS[c]}
            </Link>
          ))}
        </div>

        {/* Skills grid */}
        {loading ? (
          <SkeletonCards count={12} />
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
            No skills found in this category.
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
