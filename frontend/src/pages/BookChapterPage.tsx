import { useEffect, useMemo } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSlug from "rehype-slug";
import rehypeAutolinkHeadings from "rehype-autolink-headings";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import {
  findChapterBySlug,
  nextChapter,
  prevChapter,
  PUBLISHED_CHAPTERS,
} from "../data/bookChapters";

const CHAPTER_FILES = import.meta.glob("../../content/book/*.md", {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;

function loadChapterMarkdown(slug: string): string | null {
  const key = `../../content/book/${slug}.md`;
  return CHAPTER_FILES[key] ?? null;
}

function stripFrontmatter(md: string): string {
  if (md.startsWith("---")) {
    const end = md.indexOf("\n---", 3);
    if (end > 0) return md.slice(end + 4).trimStart();
  }
  return md;
}

export function BookChapterPage() {
  const { slug } = useParams<{ slug: string }>();
  const chapter = slug ? findChapterBySlug(slug) : undefined;
  const raw = slug ? loadChapterMarkdown(slug) : null;
  const markdown = useMemo(() => (raw ? stripFrontmatter(raw) : ""), [raw]);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [slug]);

  if (!chapter || !raw) {
    return <Navigate to="/book/" replace />;
  }

  const prev = prevChapter(chapter);
  const next = nextChapter(chapter);
  const canonical = `https://agentskillshub.top/book/${chapter.slug}/`;
  const title = `第 ${chapter.number} 章 · ${chapter.title} · Skill 蓝皮书 2026`;
  const description = chapter.summary;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Helmet>
        <title>{title}</title>
        <meta name="description" content={description} />
        <link rel="canonical" href={canonical} />
        <meta property="og:title" content={title} />
        <meta property="og:description" content={description} />
        <meta property="og:type" content="article" />
        <meta property="og:url" content={canonical} />
        <meta
          property="og:image"
          content="https://agentskillshub.top/book/assets/cover.png"
        />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={title} />
        <meta name="twitter:description" content={description} />
      </Helmet>

      <SiteHeader />

      <main className="max-w-3xl mx-auto px-4 py-8">
        <nav className="text-sm text-gray-400 dark:text-gray-500 mb-4">
          <Link to="/" className="text-indigo-500 hover:text-indigo-600">
            Home
          </Link>
          <span className="mx-2">&gt;</span>
          <Link to="/book/" className="text-indigo-500 hover:text-indigo-600">
            Skill 蓝皮书
          </Link>
          <span className="mx-2">&gt;</span>
          <span className="text-gray-600 dark:text-gray-300">
            第 {chapter.number} 章
          </span>
        </nav>

        <header className="mb-8 pb-6 border-b border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-400 dark:text-gray-500 mb-2">
            {chapter.part} · 第 {chapter.number} 章
          </p>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white tracking-tight">
            {chapter.title}
          </h1>
          <p className="mt-3 text-gray-500 dark:text-gray-400 text-base leading-relaxed">
            {chapter.summary}
          </p>
        </header>

        <article className="book-prose">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[
              rehypeSlug,
              [rehypeAutolinkHeadings, { behavior: "wrap" }],
            ]}
          >
            {markdown}
          </ReactMarkdown>
        </article>

        <hr className="my-10 border-gray-200 dark:border-gray-700" />

        <nav className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-12">
          {prev ? (
            <Link
              to={`/book/${prev.slug}/`}
              className="block rounded-xl border border-gray-200 dark:border-gray-700 px-4 py-3 hover:border-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors"
            >
              <div className="text-xs text-gray-400">← 上一章</div>
              <div className="text-sm font-medium text-gray-900 dark:text-white truncate mt-1">
                第 {prev.number} 章 · {prev.title}
              </div>
            </Link>
          ) : (
            <div />
          )}
          {next ? (
            <Link
              to={`/book/${next.slug}/`}
              className="block rounded-xl border border-gray-200 dark:border-gray-700 px-4 py-3 hover:border-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors text-right"
            >
              <div className="text-xs text-gray-400">下一章 →</div>
              <div className="text-sm font-medium text-gray-900 dark:text-white truncate mt-1">
                第 {next.number} 章 · {next.title}
              </div>
            </Link>
          ) : (
            <div />
          )}
        </nav>

        <div className="text-center text-xs text-gray-400 dark:text-gray-500 mb-12">
          已发布章节：{PUBLISHED_CHAPTERS.length}/12 ·{" "}
          <a
            href="https://github.com/zhuyansen/skill-blue-book"
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-500 hover:underline"
          >
            GitHub 全本
          </a>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
