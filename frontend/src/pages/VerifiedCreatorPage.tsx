import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";
import { VERIFIED_CREATORS } from "../data/verifiedCreators";

export function VerifiedCreatorPage() {
  const foundingMembers = VERIFIED_CREATORS.filter(
    (c) => c.tier === "founding",
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Helmet>
        <title>Verified Creator Program — AgentSkillsHub</title>
        <meta
          name="description"
          content="AgentSkillsHub Verified Creator program. For serious Skill authors who commercialize via consulting, subscriptions, or community. Authenticated badge, trending boost, creator analytics, leads channel."
        />
        <link
          rel="canonical"
          href="https://agentskillshub.top/verified-creator/"
        />
      </Helmet>
      <SiteHeader />
      <main className="max-w-4xl mx-auto px-4 py-10 sm:py-16">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 mb-4 px-3 py-1 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 rounded-full text-sm font-medium">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L4 6v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V6l-8-4zm-1.4 14.6L6 12l1.4-1.4 3.2 3.2 6.2-6.2L18.2 9l-7.6 7.6z" />
            </svg>
            Verified Creator Program
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">
            为严肃做 Skill 商业化的作者而生
          </h1>
          <p className="text-base sm:text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto leading-relaxed">
            在 55,000+ 开源 Skill 的噪音里，让真正在持续迭代的作者被看见。
            不做最多，只做最可信。
          </p>
        </div>

        <section className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 sm:p-8 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-5">
            认证作者的 4 项权益
          </h2>
          <div className="grid sm:grid-cols-2 gap-5">
            {[
              {
                icon: "✓",
                title: "认证徽章",
                body: "每个 Skill 详情页、Trending 榜、分类页都带绿色 ✓ 标识，区别于普通开源作者。",
              },
              {
                icon: "🚀",
                title: "Trending 轻微加权",
                body: "在 Star Velocity 算法里获得可解释的小幅加权，让真实在迭代的作者更容易上榜。",
              },
              {
                icon: "📊",
                title: "作者数据面板",
                body: "访问量、来源、点击 GitHub/站外、搜索关键词——独家给到的用户行为数据。",
              },
              {
                icon: "💬",
                title: "咨询撮合入口",
                body: '详情页加"联系作者"按钮，用户可通过你挂出的渠道直接触达，Hub 不介入交易。',
              },
            ].map((f) => (
              <div key={f.title} className="flex gap-3">
                <div className="flex-none w-10 h-10 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-lg font-bold">
                  {f.icon}
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-white mb-1">
                    {f.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                    {f.body}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 sm:p-8 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-5">
            定价
          </h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="border-2 border-emerald-500 rounded-lg p-5 relative bg-emerald-50/30 dark:bg-emerald-950/20">
              <div className="absolute -top-3 left-4 bg-emerald-500 text-white text-xs font-semibold px-2 py-0.5 rounded">
                早鸟价（前 30 名）
              </div>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                ¥699
                <span className="text-sm font-normal text-gray-500">/年</span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">
                包含所有权益 · 建站用于筛选严肃作者，不图赚钱
              </p>
            </div>
            <div className="border border-gray-200 dark:border-gray-800 rounded-lg p-5">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                ¥999
                <span className="text-sm font-normal text-gray-500">/年</span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">
                常规价 · 早鸟席位满后生效
              </p>
            </div>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-4 leading-relaxed">
            认证不是付费就有。核心按迭代频率、质量分、社区反馈评估。
            年费只覆盖审核和运营成本。不续费 = 失去徽章，但 Skill
            本身继续免费收录。
          </p>
        </section>

        <section className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 sm:p-8 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">
            申请
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-5 leading-relaxed">
            目前处于<strong>首批邀请制</strong>阶段。请提供：GitHub username、 3
            个你最代表性的 Skill 仓库链接、商业化现状（订阅/咨询/社群）、
            为什么希望加入。
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <a
              href="mailto:m17551076169@gmail.com?subject=Verified%20Creator%20Application&body=GitHub%20username%3A%0D%0ARepresentative%20skills%20(3)%3A%0D%0ACurrent%20commercialization%3A%0D%0AWhy%20join%3A"
              className="flex-1 text-center py-3 px-5 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-lg hover:opacity-90 transition text-sm font-medium"
            >
              📧 Email Application
            </a>
            <a
              href="https://x.com/GoSailGlobal"
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 text-center py-3 px-5 border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition text-sm font-medium"
            >
              DM @GoSailGlobal on X
            </a>
          </div>
        </section>

        {foundingMembers.length === 0 ? (
          <section className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 sm:p-8 text-center">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">
              Founding Members
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed max-w-xl mx-auto">
              暂无 · 首批邀请制进行中。想成为首批认证作者，请发邮件申请。
              我们会在评估后公开每位获认证者的名字与联系渠道——只有在得到本人
              明确同意之后。
            </p>
          </section>
        ) : (
          <section className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 sm:p-8">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-5">
              Founding Members
            </h2>
            <div className="grid sm:grid-cols-2 gap-4">
              {foundingMembers.map((c) => (
                <div
                  key={c.github}
                  className="flex items-start gap-3 p-4 border border-gray-100 dark:border-gray-800 rounded-lg"
                >
                  <img
                    src={`https://github.com/${c.github}.png?size=80`}
                    alt={c.name}
                    className="w-12 h-12 rounded-full"
                    loading="lazy"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className="font-medium text-gray-900 dark:text-white truncate">
                        {c.name}
                      </span>
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="currentColor"
                        className="text-emerald-500 flex-none"
                      >
                        <path d="M12 2L4 6v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V6l-8-4zm-1.4 14.6L6 12l1.4-1.4 3.2 3.2 6.2-6.2L18.2 9l-7.6 7.6z" />
                      </svg>
                    </div>
                    <a
                      href={`https://github.com/${c.github}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 transition"
                    >
                      @{c.github}
                    </a>
                    {c.tagline && (
                      <p className="text-xs text-gray-600 dark:text-gray-300 mt-1.5 leading-relaxed line-clamp-2">
                        {c.tagline}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <div className="mt-10 text-center">
          <Link
            to="/"
            className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition"
          >
            ← Back to AgentSkillsHub
          </Link>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
