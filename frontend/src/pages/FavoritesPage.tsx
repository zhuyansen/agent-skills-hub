import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { fetchSkillsByIds } from "../api/client";
import { useFavorites } from "../hooks/useFavorites";
import { useI18n } from "../i18n/I18nContext";
import { SkillCard } from "../components/SkillCard";
import { SkeletonCards } from "../components/SkeletonCards";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import type { Skill } from "../types/skill";

export function FavoritesPage() {
  const navigate = useNavigate();
  const { lang } = useI18n();
  const isZh = lang === "zh";
  const { favorites, clearFavorites } = useFavorites();
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchSkillsByIds(favorites)
      .then((items) => {
        if (cancelled) return;
        // Preserve the order the user favorited them in.
        const order = new Map(favorites.map((id, i) => [id, i]));
        items.sort((a, b) => (order.get(a.id) ?? 0) - (order.get(b.id) ?? 0));
        setSkills(items);
      })
      .catch(console.error)
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [favorites]);

  const handleShowDetail = useCallback(
    (skill: Skill) => navigate(`/skill/${skill.repo_full_name}/`),
    [navigate],
  );

  const totalStars = useMemo(
    () => skills.reduce((sum, s) => sum + (s.stars || 0), 0),
    [skills],
  );

  const title = isZh
    ? "我的收藏 — AgentSkillsHub"
    : "My Favorites — AgentSkillsHub";

  return (
    // Wrap in a div: a bare fragment makes <header>/<main>/<footer> direct
    // children of #root, which index.html hides via `#root > header { display:none }`
    // (the SEO-fallback hiding rule). The wrapper keeps them one level deeper.
    <div className="min-h-screen flex flex-col">
      <Helmet>
        <title>{title}</title>
        <meta name="robots" content="noindex" />
      </Helmet>

      <SiteHeader />

      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-1 flex items-center gap-2">
              <svg
                className="w-6 h-6 text-rose-500"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
              </svg>
              {isZh ? "我的收藏" : "My Favorites"}
            </h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              {favorites.length > 0
                ? isZh
                  ? `${favorites.length} 个收藏 · 共 ${totalStars.toLocaleString()} ★ · 仅存于本设备`
                  : `${favorites.length} saved · ${totalStars.toLocaleString()} ★ total · stored on this device only`
                : isZh
                  ? "还没有收藏 · 在任意 skill 卡片上点 🔖 即可加入"
                  : "Nothing saved yet · tap 🔖 on any skill card to add it"}
            </p>
          </div>
          {favorites.length > 0 && (
            <button
              onClick={() => {
                if (
                  window.confirm(
                    isZh ? "清空全部收藏?" : "Clear all favorites?",
                  )
                )
                  clearFavorites();
              }}
              className="shrink-0 px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-rose-600 dark:hover:text-rose-400 border border-gray-200 dark:border-gray-700 rounded-lg transition-colors cursor-pointer"
            >
              {isZh ? "清空" : "Clear all"}
            </button>
          )}
        </div>

        {loading ? (
          <SkeletonCards count={6} />
        ) : skills.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {skills.map((skill) => (
              <SkillCard
                key={skill.id}
                skill={skill}
                onShowDetail={handleShowDetail}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-20">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-rose-50 dark:bg-rose-900/20 flex items-center justify-center">
              <svg
                className="w-8 h-8 text-rose-300 dark:text-rose-700"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                />
              </svg>
            </div>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              {isZh
                ? "把感兴趣的 skill 收藏起来,方便随时回看、对比、安装。"
                : "Save skills you're interested in to revisit, compare, and install later."}
            </p>
            <Link
              to="/"
              className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              {isZh ? "去发现 Skills →" : "Discover Skills →"}
            </Link>
          </div>
        )}
      </main>

      <SiteFooter />
    </div>
  );
}
