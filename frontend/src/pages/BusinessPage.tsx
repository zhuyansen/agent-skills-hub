import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { SiteHeader } from "../components/SiteHeader";
import { SiteFooter } from "../components/SiteFooter";

interface Tier {
  name: string;
  price: string;
  priceUnit: string;
  tagline: string;
  features: string[];
  cta: string;
  ctaHref: string;
  highlight?: boolean;
}

const TIERS: Tier[] = [
  {
    name: "Starter",
    price: "¥9,999",
    priceUnit: "/年",
    tagline: "中小团队快速接入",
    features: [
      "5 个团队账号",
      "每月依赖 CVE 扫描报告（PDF）",
      "Skill 许可证合规标签（MIT / Apache / GPL 矩阵）",
      "秘钥泄露自动检测",
      "邮件工单支持（48h 响应）",
    ],
    cta: "申请 Starter",
    ctaHref:
      "mailto:m17551076169@gmail.com?subject=Business%20Inquiry%20-%20Starter&body=Company%3A%0D%0ATeam%20size%3A%0D%0AUse%20case%3A%0D%0ATimeline%3A",
  },
  {
    name: "Business",
    price: "¥29,999",
    priceUnit: "/年",
    tagline: "严肃合规 + 私有化部署",
    features: [
      "无限团队账号 + SSO 集成",
      "Starter 全部功能",
      "SBOM（软件物料清单）自动导出",
      "供应链风险持续监控 + Webhook 告警",
      "企业内网 Skill 镜像源（每 8 小时同步）",
      "私有 Skill 提交审核队列",
      "专属 Slack 频道支持（4h 响应）",
    ],
    cta: "申请 Business",
    ctaHref:
      "mailto:m17551076169@gmail.com?subject=Business%20Inquiry%20-%20Business&body=Company%3A%0D%0ATeam%20size%3A%0D%0AUse%20case%3A%0D%0ATimeline%3A",
    highlight: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    priceUnit: "",
    tagline: "定制化 + 合规审计",
    features: [
      "Business 全部功能",
      "定制合规标签（等保 / HIPAA / SOC 2 / GDPR）",
      "季度安全审计 + 现场报告",
      "定制 Skill 白名单 / 黑名单规则",
      "SLA 99.9% 可用性保证",
      "技术顾问日（每季度 1 天）",
      "专属客户经理",
    ],
    cta: "联系销售",
    ctaHref:
      "mailto:m17551076169@gmail.com?subject=Business%20Inquiry%20-%20Enterprise&body=Company%3A%0D%0ATeam%20size%3A%0D%0AUse%20case%3A%0D%0ATimeline%3A",
  },
];

export function BusinessPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Helmet>
        <title>For Business — AgentSkillsHub Enterprise Skill Directory</title>
        <meta
          name="description"
          content="Enterprise-grade AI Agent Skill directory with security audits, SBOM export, license compliance, and on-prem mirroring. Trusted source for Fortune 500 legal + security teams."
        />
        <link rel="canonical" href="https://agentskillshub.top/business/" />
      </Helmet>
      <SiteHeader />
      <main className="max-w-6xl mx-auto px-4 py-10 sm:py-16">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 mb-4 px-3 py-1 bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-400 rounded-full text-sm font-medium">
            🏢 For Business
          </div>
          <h1 className="text-3xl sm:text-5xl font-bold text-gray-900 dark:text-white mb-4">
            Enterprise-Grade Skill Directory
          </h1>
          <p className="text-base sm:text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto leading-relaxed">
            给法务和技术决策者的 Skill
            目录——不是"最全的列表"，是"筛选过、可审计、能部署"的清单。
          </p>
        </div>

        <section className="grid sm:grid-cols-3 gap-6 mb-12">
          {[
            {
              icon: "🔒",
              title: "安全审计",
              body: "每个 Skill 自动扫描秘钥泄露、CVE、恶意依赖、可疑网络调用。输出审计级 PDF 报告。",
            },
            {
              icon: "📋",
              title: "合规标签",
              body: "许可证矩阵（MIT / Apache / GPL / 商用限制）+ 等保 / GDPR / HIPAA 适用性标注。",
            },
            {
              icon: "🏠",
              title: "私有化部署",
              body: "企业内网 Skill 镜像，每 8 小时从 Hub 同步认证通过的子集，不依赖公网。",
            },
          ].map((f) => (
            <div
              key={f.title}
              className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6"
            >
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                {f.title}
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                {f.body}
              </p>
            </div>
          ))}
        </section>

        <section className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white text-center mb-8">
            定价
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {TIERS.map((tier) => (
              <div
                key={tier.name}
                className={`bg-white dark:bg-gray-900 rounded-xl p-6 flex flex-col ${
                  tier.highlight
                    ? "border-2 border-blue-500 shadow-lg"
                    : "border border-gray-200 dark:border-gray-800"
                }`}
              >
                {tier.highlight && (
                  <div className="text-xs font-semibold text-blue-600 dark:text-blue-400 mb-2">
                    RECOMMENDED
                  </div>
                )}
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                  {tier.name}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                  {tier.tagline}
                </p>
                <div className="mb-5">
                  <span className="text-3xl font-bold text-gray-900 dark:text-white">
                    {tier.price}
                  </span>
                  <span className="text-gray-500 dark:text-gray-400">
                    {tier.priceUnit}
                  </span>
                </div>
                <ul className="space-y-2.5 mb-6 flex-1">
                  {tier.features.map((f) => (
                    <li
                      key={f}
                      className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300"
                    >
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        className="text-blue-500 flex-none mt-0.5"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        />
                      </svg>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
                <a
                  href={tier.ctaHref}
                  className={`block w-full text-center py-2.5 px-4 rounded-lg text-sm font-medium transition ${
                    tier.highlight
                      ? "bg-blue-600 hover:bg-blue-700 text-white"
                      : "border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800"
                  }`}
                >
                  {tier.cta}
                </a>
              </div>
            ))}
          </div>
        </section>

        <section className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 sm:p-8 mb-12">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-5">
            常见问题
          </h2>
          <div className="space-y-5">
            {[
              {
                q: "和直接在 GitHub 上搜 Skill 有什么区别？",
                a: "GitHub 给你 55,000 个结果，没有质量过滤、没有合规标注、没有持续监控。Business 版相当于你的法务和安全团队有一个 7×24 的 AI 助手筛选 Skill。",
              },
              {
                q: "私有化部署支持哪些环境？",
                a: "当前支持 Docker / Kubernetes。Enterprise 版支持离线环境（通过定期镜像包人工同步）。",
              },
              {
                q: "能否定制合规规则？",
                a: "可以。Business 支持基础规则配置，Enterprise 支持完全定制（如：只允许某些 License、禁止某些作者 / 组织）。",
              },
              {
                q: "如何开始试用？",
                a: "发邮件给 m17551076169@gmail.com 描述你的场景，我们会给出 2 周免费试用期 + 你所在行业的典型合规清单样本。",
              },
            ].map((f) => (
              <div key={f.q}>
                <h3 className="font-medium text-gray-900 dark:text-white mb-1.5">
                  {f.q}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                  {f.a}
                </p>
              </div>
            ))}
          </div>
        </section>

        <div className="text-center">
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
