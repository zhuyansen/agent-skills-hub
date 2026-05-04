import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { BOOK_CHAPTERS, PUBLISHED_CHAPTERS } from "../data/bookChapters";

const TITLE =
  "Skill 蓝皮书 2026 · 67,000+ Skill 数据的原生研究 — AgentSkillsHub";
const DESCRIPTION =
  "Skill 蓝皮书 2026：基于 AgentSkillsHub 67,000+ 真实 Skill 数据的原生研究。Mahesh vs Barry / Gini 0.983 / 9 种类型 × 4 级路径 / Verified Creator 设计。7/12 章已发布，持续更新。";

export function BookIndexPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Helmet>
        <title>{TITLE}</title>
        <meta name="description" content={DESCRIPTION} />
        <link rel="canonical" href="https://agentskillshub.top/book/" />
        <meta property="og:title" content={TITLE} />
        <meta property="og:description" content={DESCRIPTION} />
        <meta property="og:type" content="book" />
        <meta property="og:url" content="https://agentskillshub.top/book/" />
        <meta
          property="og:image"
          content="https://agentskillshub.top/book/assets/cover.png"
        />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={TITLE} />
        <meta name="twitter:description" content={DESCRIPTION} />
        <meta
          name="twitter:image"
          content="https://agentskillshub.top/book/assets/cover.png"
        />
      </Helmet>

      <SiteHeader />

      <main className="max-w-4xl mx-auto px-4 py-10">
        <nav className="text-sm text-gray-400 dark:text-gray-500 mb-4">
          <Link to="/" className="text-indigo-500 hover:text-indigo-600">
            Home
          </Link>
          <span className="mx-2">&gt;</span>
          <span className="text-gray-600 dark:text-gray-300">Skill 蓝皮书</span>
        </nav>

        <header className="mb-10">
          <p className="text-sm text-indigo-500 dark:text-indigo-400 font-medium mb-2">
            Blue Book of Agent Skills · 2026
          </p>
          <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 dark:text-white tracking-tight">
            Skill 蓝皮书 2026
          </h1>
          <p className="mt-4 text-lg text-gray-500 dark:text-gray-400 leading-relaxed">
            基于 AgentSkillsHub 67,000+ 真实 Skill 数据的原生研究——不是再写一遍
            Anthropic 已经讲过的 Skill Spec，是去回答没人答过的问题：现在的
            Skill 生态长什么样、谁活下来了、谁要饿死、还有 30% 的 Skill
            写不出来。
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3 text-sm">
            <span className="px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 font-medium">
              已发布 {PUBLISHED_CHAPTERS.length}/12 章
            </span>
            <a
              href="https://github.com/zhuyansen/skill-blue-book"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              GitHub 全本 →
            </a>
            <span className="text-gray-400">·</span>
            <span className="text-gray-400 dark:text-gray-500">
              CC BY-NC-SA 4.0
            </span>
          </div>
        </header>

        {/* Hero cover */}
        <div className="mb-12">
          <img
            src="/book/assets/cover.png"
            alt="Skill 蓝皮书 2026 封面"
            className="rounded-2xl border border-gray-200 dark:border-gray-700 w-full"
            width={1200}
            height={630}
            loading="lazy"
          />
        </div>

        {/* Chapter list */}
        <section className="space-y-3">
          {BOOK_CHAPTERS.map((c) => {
            const published = c.status === "published";
            return published ? (
              <Link
                key={c.slug}
                to={`/book/${c.slug}/`}
                className="block rounded-xl border border-gray-200 dark:border-gray-700 px-5 py-4 hover:border-indigo-300 hover:bg-indigo-50/50 dark:hover:bg-indigo-900/20 transition-colors"
              >
                <div className="flex items-start gap-4">
                  <div className="shrink-0 w-12 text-center">
                    <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                      {c.number}
                    </div>
                    <div className="text-[10px] text-gray-400 uppercase tracking-wider mt-0.5">
                      章
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-400 dark:text-gray-500 mb-1">
                      {c.part}
                    </p>
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {c.title}
                    </h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1.5 leading-relaxed">
                      {c.summary}
                    </p>
                  </div>
                </div>
              </Link>
            ) : null;
          })}

          {/* All 12 chapters complete — no pending list */}
          <div className="mt-8 pt-6 border-t border-dashed border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
              全 12 章完稿 · v1.1 · 2026-05-04 ·{" "}
              <a
                href="https://github.com/zhuyansen/skill-blue-book/releases"
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-500 hover:underline"
              >
                下载 PDF →
              </a>
            </p>
          </div>
        </section>

        {/* CTA */}
        <div className="mt-12 p-6 rounded-2xl bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            为什么有这本书
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
            一年内 Skill 从「prompt 片段」涨成「Agent
            系统的中枢」。但现有讨论几乎都是 Anthropic
            官方文档的二次复述——而真正能说明白「这个生态长什么样、有什么病、要往哪去」的，只能用
            Hub 自己的 67,000+ 数据来答。蓝皮书是这个工作的副产物——本来是 Hub
            的内部研究，索性公开。
          </p>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
