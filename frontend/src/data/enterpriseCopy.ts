/**
 * Bilingual copy for the consolidated /enterprise/ page.
 *
 * This page is the SINGLE B2B inbound surface. It folds in what used to be
 * three pages:
 *   - /enterprise/        (audit · compliance · sandbox · SSO)        — the spine
 *   - /business/          (license matrix · SBOM · on-prem mirror)    — §compliance
 *   - /verified-creator/  (creator certification)                    — §creator
 * /business/ and /verified-creator/ now redirect here; the creator APPLY flow
 * still lives at /verified-creator/apply/.
 *
 * HONESTY RULE (load-bearing): zero paying customers, zero testimonials, SOC 2
 * in progress (not certified). Frameworks are what Hub AUDITS AGAINST, not what
 * Hub is certified for. The 26.1% vuln figure is cited (Liu et al. 2026,
 * arXiv:2601.10338, n=31,132) — never the old unsourced "43%".
 */

export interface RoleItem {
  role: string;
  pain: string;
  win: string;
}
export interface Tier {
  name: string;
  price: string;
  unit: string;
  features: string[];
  cta: string;
  highlight?: boolean;
}
export interface QA {
  q: string;
  a: string;
}

export interface EnterpriseCopy {
  meta: { title: string; description: string };
  hero: {
    badge: string;
    h1a: string;
    h1b: string;
    sub: string;
    ctaPrimary: string;
    ctaSecondary: string;
    note: string;
  };
  band: { label: string; footnote: string };
  bandFrameworks: { name: string; sub: string }[];
  signals: { stat: string; label: string; sub: string }[];
  problem: {
    h2: string;
    sub: string;
    items: { emoji: string; title: string; body: string }[];
  };
  solution: {
    h2: string;
    sub: string;
    items: { icon: string; title: string; body: string }[];
  };
  how: { h2: string; steps: { num: string; title: string; body: string }[] };
  roles: {
    h2: string;
    sub: string;
    blocker: string;
    gives: string;
    items: RoleItem[];
  };
  compliance: {
    h2: string;
    sub: string;
    items: { icon: string; title: string; body: string }[];
  };
  pricing: { h2: string; sub: string; tiers: Tier[]; footnote: string };
  creator: {
    h2: string;
    sub: string;
    benefits: string[];
    cta: string;
    note: string;
  };
  trust: {
    h2: string;
    sub: string;
    items: { title: string; body: string }[];
    orgsLabel: string;
    orgsNote: string;
  };
  faq: { h2: string; items: QA[] };
  form: {
    h2: string;
    sub: string;
    okTitle: string;
    okBody: string;
    fields: Record<string, string>;
    teamSizes: string[];
    timelines: string[];
    budgets: string[];
    submit: string;
    submitting: string;
    privacy: string;
    errMissing: string;
    errGeneric: string;
  };
}

const ORGS = [
  "Anthropic",
  "OpenAI",
  "Alibaba Cloud",
  "Tencent Cloud",
  "Google",
  "Frappe",
  "Lightning Labs",
  "Portainer",
];

export const EN: EnterpriseCopy = {
  meta: {
    title:
      "Enterprise · The Trust Layer for AI Agent & MCP Deployment | Agent Skills Hub",
    description:
      "Security-grade 130,000+ open-source agent skills and MCP servers, and deep-audit any of them before it touches production. Deploy-time security scanning, sandbox validation, license/SBOM compliance, on-prem mirroring, and audit-ready evidence — SOC 2, ISO 42001, EU AI Act.",
  },
  hero: {
    badge: "The Trust Layer for AI Agent & MCP Deployment",
    h1a: "Deploy AI Agents to Production.",
    h1b: "Without the Audit Panic.",
    sub: "Deploy-time security scanning, sandbox validation, and audit-ready compliance evidence for every MCP server and agent skill you ship — mapped to SOC 2, ISO/IEC 42001, and the EU AI Act.",
    ctaPrimary: "Book a 30-min demo →",
    ctaSecondary: "Browse 130,000+ security-graded skills free",
    note: "No slides, no sales theater · We surface 3 real risks in your stack before the call ends",
  },
  band: {
    label:
      "Audit findings mapped to the frameworks your procurement team asks about",
    footnote:
      "Hub generates evidence against these frameworks for the skills you deploy. Hub's own SOC 2 Type II is in progress (target Q3 2026) — control mapping available under NDA today.",
  },
  bandFrameworks: [
    { name: "SOC 2", sub: "Type II controls" },
    { name: "ISO/IEC 42001", sub: "AI management system" },
    { name: "EU AI Act", sub: "Art. 9–12, 2026" },
    { name: "GDPR", sub: "data governance" },
    { name: "HIPAA", sub: "healthtech add-on" },
  ],
  signals: [
    {
      stat: "26.1%",
      label: "Contain vulnerabilities",
      sub: "of agent skills, per Liu et al. 2026 (arXiv:2601.10338, n=31,132) — the risk your team inherits",
    },
    {
      stat: "130,000+",
      label: "Skills under continuous scanning",
      sub: "re-scanned every 8 hours across the open-source ecosystem",
    },
    {
      stat: "Open",
      label: "Methodology, MIT-licensed",
      sub: "every detection rule and score is public and reproducible",
    },
  ],
  problem: {
    h2: "Your MCP server worked in dev.",
    sub: "Then it shipped.",
    items: [
      {
        emoji: "💉",
        title: "Prompt Injection Disaster",
        body: "More than one in four open-source agent skills carry security vulnerabilities — prompt injection, credential leak, data exfiltration. One crafted request can drain your database.",
      },
      {
        emoji: "🚧",
        title: "Compliance Blockade",
        body: "EU AI Act (full enforcement August 2026) and SOC 2 require provenance, audit logs, and risk classification. Your platform team blocks the launch until you have them.",
      },
      {
        emoji: "🕳",
        title: "Zero Incident Forensics",
        body: "Agent breaks at 2am. No audit logs. No way to replay the failing tool call. No way to roll back to a known-good skill version. You're flying blind.",
      },
    ],
  },
  solution: {
    h2: "One layer between your developers and production",
    sub: "Every skill gets audited, sandboxed, logged, and gated — before it touches a real user. Free answers “is this skill any good?” Enterprise answers “can I prove to my auditor it's safe to run in production?”",
    items: [
      {
        icon: "🔐",
        title: "Pre-deployment Sandbox",
        body: "Run each skill against de-identified, production-shaped data in isolation. Red-team probes. Kill switch on first anomaly — before it ever reaches a customer.",
      },
      {
        icon: "📋",
        title: "Compliance Evidence Pack",
        body: "Auto-generated PDF: SOC 2 control mapping, ISO/IEC 42001 alignment, EU AI Act risk classification, training-data isolation proof. Hand it straight to your auditor.",
      },
      {
        icon: "📊",
        title: "Full-chain Audit Logs",
        body: "Every tool call, every data flow, every error — replayable in one click. JSON export to your SIEM (Splunk, Datadog, Elastic). 90-day retention by default.",
      },
      {
        icon: "👤",
        title: "SSO/SCIM + Fine-grained RBAC",
        body: "Okta, Auth0, Azure AD ready. Skill-level permissions (which agent calls which tool, with which scope). Engineering-manager approval gate before prod.",
      },
    ],
  },
  how: {
    h2: "How it works",
    steps: [
      {
        num: "01",
        title: "Connect your existing MCP setup",
        body: "Point Hub at your registry of MCP servers and agent skills — GitHub, internal mirror, or direct upload. Onboarding takes ≤ 30 minutes.",
      },
      {
        num: "02",
        title: "Hub runs a static scan + sandbox test",
        body: "Each skill is statically scanned for prompt injection, credential exposure, and sandbox-escape risk, then runtime-tested against red-team probes in isolation.",
      },
      {
        num: "03",
        title: "Get a compliance evidence package",
        body: "Auditor-ready PDF: control mapping, risk classification, audit-log samples, training-data isolation proof. Ship it to procurement, pass review, deploy.",
      },
    ],
  },
  roles: {
    h2: "Built for whoever owns the launch",
    sub: "Different seat at the table, same blocker: nobody can prove the agent is safe to ship.",
    blocker: "The blocker",
    gives: "What Hub gives you",
    items: [
      {
        role: "Platform / VP Engineering",
        pain: "Launches keep slipping because nobody can sign off on third-party MCP servers.",
        win: "A deploy-time gate that says ship / don't-ship per skill, with the evidence attached.",
      },
      {
        role: "Security / CISO",
        pain: "AI agents are a new supply chain your existing SCA tools don't reach.",
        win: "Continuous scanning of the skill + MCP layer, mapped to MITRE ATT&CK and your frameworks.",
      },
      {
        role: "Compliance / GRC",
        pain: "Auditors want provenance and risk classification you don't have for agent tools.",
        win: "A signed evidence pack per deployment — SOC 2, ISO 42001, EU AI Act — generated, not hand-assembled.",
      },
    ],
  },
  compliance: {
    h2: "License, SBOM & on-prem mirror",
    sub: "For legal and platform teams that need the skill supply chain governed, not just discovered.",
    items: [
      {
        icon: "📜",
        title: "License compliance matrix",
        body: "Every skill tagged MIT / Apache / GPL / commercial-restricted, with applicability flags for GDPR / HIPAA / regional regimes — so legal can clear it fast.",
      },
      {
        icon: "📦",
        title: "SBOM export",
        body: "Software bill of materials per skill, plus continuous supply-chain monitoring with webhook alerts when a dependency picks up a CVE.",
      },
      {
        icon: "🏠",
        title: "Private on-prem mirror",
        body: "An internal mirror of the audited subset, synced from Hub every 8 hours. Your agents pull skills without reaching the public internet.",
      },
    ],
  },
  pricing: {
    h2: "Pricing",
    sub: "Free to discover & assess. Paid to validate, govern & prove.",
    tiers: [
      {
        name: "Free",
        price: "$0",
        unit: "Forever · no card",
        features: [
          "Browse the full 100K skill catalog",
          "Quality score + 6-dimension breakdown",
          "Basic security scan per skill",
          "Scenario & comparison pages",
          "Newsletter (weekly trending)",
        ],
        cta: "Explore free",
      },
      {
        name: "Pro",
        price: "$49",
        unit: "/mo · per developer · no sales call",
        features: [
          "Everything in Free",
          "API access (catalog + scores)",
          "Skill version lock + auto-rollback",
          "Audit-log export (per-developer)",
          "Vulnerability alerts for your skills",
          "Email support",
        ],
        cta: "Request early access",
      },
      {
        name: "Enterprise",
        price: "$10K–$30K",
        unit: "/year / department",
        highlight: true,
        features: [
          "Everything in Pro",
          "SSO/SCIM (Okta, Auth0, Azure AD)",
          "Pre-deployment sandbox",
          "Compliance evidence pack",
          "Full-chain audit logs + SIEM export",
          "License matrix · SBOM · on-prem mirror",
          "Dedicated account manager + 4h SLA",
          "Regulated-industry add-ons",
        ],
        cta: "Book a demo →",
      },
    ],
    footnote:
      "Enterprise scales with team size and skills audited. Starter: 10 engineers / 50 skills ($10K/yr). Standard: 50 / 200 ($20K/yr). Business: 200 / unlimited ($30K/yr). 200+ engineers or regulated industries start at $50K/yr.",
  },
  creator: {
    h2: "Are you a skill creator, not a buyer?",
    sub: "The Verified Creator program certifies serious skill authors — audited, trusted, and surfaced above the 100K-skill noise.",
    benefits: [
      "Authenticated ✓ badge on your skill pages and cards",
      "Featured slot in Verified Organizations (rankings stay objective, never paid)",
      "Priority indexing + expedited security & quality audit",
      "“Contact author” channel so users can reach you directly",
    ],
    cta: "Apply for Verified Creator →",
    note: "Manual review within 5 business days. Certification is earned on iteration, quality, and community signal — not bought.",
  },
  trust: {
    h2: "Why teams trust the data",
    sub: "We're early on the enterprise product and we say so. What we're not early on: the largest open audit corpus in the ecosystem.",
    items: [
      {
        title: "Open methodology, nothing to take on faith",
        body: "Every scoring weight, detection rule, and decision boundary is published and MIT-licensed. You can reproduce any finding yourself — no black-box trust-us claims.",
      },
      {
        title: "Continuous, not point-in-time",
        body: "We re-scan the entire corpus every 8 hours. A new CVE in a skill you depend on surfaces within hours, not at your next quarterly review.",
      },
      {
        title: "We complement Snyk, we don't replace it",
        body: "Snyk and SonarQube scan your code. Hub scans the agent skills and MCP servers your code calls into — the AI-specific supply-chain layer they don't reach.",
      },
      {
        title: "Your data is never trained on",
        body: "Hub does not train, fine-tune, or forward your data to any model provider. Analysis runs in our infrastructure or on-prem. Data isolation is a contractual term.",
      },
    ],
    orgsLabel: "Already indexing official skills & MCP servers from",
    orgsNote:
      "These organizations' open-source skills are in our catalog. They are not customers — yet.",
  },
  faq: {
    h2: "Procurement FAQ",
    items: [
      {
        q: "How is this different from Snyk or SonarQube?",
        a: "Snyk and SonarQube scan your code. Hub scans the agent skills and MCP servers your code calls into — the supply-chain layer they don't cover. We focus on AI-specific risks: prompt injection, sandbox escape, credential leakage in tool definitions, and model training-data isolation.",
      },
      {
        q: "Do you train models on our data?",
        a: "No. Hub does not train, fine-tune, or send your data to any model provider. All analysis runs in our infrastructure or on-prem (Enterprise plan). Data isolation is a contractual term.",
      },
      {
        q: "EU AI Act — do you cover the full checklist?",
        a: "Yes. Hub's compliance evidence pack maps to Article 9 (risk management), Article 10 (data governance), Article 11 (technical documentation), and Article 12 (record-keeping). Updated for the August 2026 full enforcement.",
      },
      {
        q: "Is Hub itself SOC 2 audited?",
        a: "Not yet — we're honest about that. We are scoping SOC 2 Type II (target Q3 2026). For customers who require SOC 2 today, we provide our security control mapping under NDA, can complete a custom security questionnaire, and will commit to a timeline as part of contract negotiation.",
      },
      {
        q: "Can we deploy on-prem or private cloud?",
        a: "Yes, for Enterprise. We support AWS, GCP, Azure, and on-prem Kubernetes, plus a private skill mirror synced every 8 hours. Air-gapped deployments available for healthtech / defense customers.",
      },
      {
        q: "What happens if a skill is updated upstream?",
        a: "Hub re-scans on every commit to the upstream repo. Updated skills enter the pre-deployment sandbox automatically, and your engineering team is notified before any auto-pull to production.",
      },
      {
        q: "How long does a POC take?",
        a: "Standard POC: 4 weeks. Week 1 onboarding + connector setup. Weeks 2–3 audit your current skill inventory and deliver findings. Week 4 review with your platform team. POC fee: $5,000, fully credited toward an annual plan.",
      },
    ],
  },
  form: {
    h2: "Book a 30-min demo",
    sub: "We'll walk through your current MCP/agent setup and show you 3 immediate risks before the call ends. No slides, no sales theater.",
    okTitle: "Thanks — we'll be in touch within 24h.",
    okBody:
      "Jason or someone from the Hub team will reach out via email to schedule the call. If urgent, ping @GoSailGlobal on X.",
    fields: {
      full_name: "Full name *",
      email: "Work email *",
      company: "Company *",
      role: "Role",
      rolePlaceholder: "VP Engineering, CTO, Platform Lead…",
      teamSize: "Team size",
      industry: "Industry",
      industryPlaceholder: "fintech, healthtech, automotive…",
      useCase: "What's your use case? *",
      useCasePlaceholder:
        "Briefly: how are you deploying AI agents today, and what's the biggest pain point?",
      stack: "Current AI/agent stack",
      stackPlaceholder: "Claude Code + LangGraph + 12 MCP servers…",
      compliance: "Compliance requirements",
      compliancePlaceholder: "SOC 2, ISO 42001, EU AI Act, HIPAA…",
      timeline: "Timeline",
      budget: "Estimated budget",
      message: "Anything else?",
      messagePlaceholder:
        "Context, urgency, specific risks you're worried about…",
    },
    teamSizes: ["", "1–10", "10–50", "50–200", "200–1,000", "1,000+"],
    timelines: [
      "",
      "Immediate (this quarter)",
      "1–3 months",
      "3–6 months",
      "Just exploring",
    ],
    budgets: [
      "",
      "<$5K/yr",
      "$5K–$10K/yr",
      "$10K–$30K/yr",
      "$30K–$100K/yr",
      ">$100K/yr",
    ],
    submit: "Request demo →",
    submitting: "Submitting…",
    privacy:
      "We'll never share your data. Submissions are stored encrypted. Manual review by Jason within 24h.",
    errMissing: "Please fill in name, email, company, and your use case.",
    errGeneric: "Submission failed.",
  },
};

export const ZH: EnterpriseCopy = {
  meta: {
    title: "企业版 · AI Agent 与 MCP 部署的信任层 | Agent Skills Hub",
    description:
      "对 130,000+ 开源 agent skill 与 MCP server 做安全评级,并在进入生产前对任意一个做深度审计。部署前安全扫描、沙箱验证、许可证/SBOM 合规、企业内网镜像、审计级证据包 —— 对齐 SOC 2、ISO 42001、欧盟 AI 法案。",
  },
  hero: {
    badge: "AI Agent 与 MCP 部署的信任层",
    h1a: "把 AI Agent 部署到生产。",
    h1b: "不用再为审计提心吊胆。",
    sub: "为你上线的每个 MCP server 与 agent skill 提供部署前安全扫描、沙箱验证、审计级合规证据 —— 对齐 SOC 2、ISO/IEC 42001 与欧盟 AI 法案。",
    ctaPrimary: "预约 30 分钟演示 →",
    ctaSecondary: "免费浏览 10 万+ 已评级 skill",
    note: "没有 PPT,没有销售套路 · 通话结束前先给你指出技术栈里 3 个真实风险",
  },
  band: {
    label: "审计结论直接对齐采购团队会问到的合规框架",
    footnote:
      "Hub 为你部署的 skill 生成对齐这些框架的证据。Hub 自身的 SOC 2 Type II 正在推进(目标 2026 Q3)—— 控制项映射现可在 NDA 下提供。",
  },
  bandFrameworks: [
    { name: "SOC 2", sub: "Type II 控制项" },
    { name: "ISO/IEC 42001", sub: "AI 管理体系" },
    { name: "欧盟 AI 法案", sub: "第 9–12 条, 2026" },
    { name: "GDPR", sub: "数据治理" },
    { name: "HIPAA", sub: "医疗行业附加" },
  ],
  signals: [
    {
      stat: "26.1%",
      label: "含安全漏洞",
      sub: "开源 agent skill 的占比,据 Liu et al. 2026(arXiv:2601.10338,n=31,132)—— 这是你团队继承的风险",
    },
    {
      stat: "130,000+",
      label: "持续扫描中的 skill",
      sub: "覆盖整个开源生态,每 8 小时重扫一次",
    },
    {
      stat: "开放",
      label: "方法论, MIT 许可",
      sub: "每条检测规则与评分都公开、可复现",
    },
  ],
  problem: {
    h2: "你的 MCP server 在开发环境跑得好好的。",
    sub: "然后它上线了。",
    items: [
      {
        emoji: "💉",
        title: "Prompt 注入灾难",
        body: "每四个开源 agent skill 就有超过一个含安全漏洞 —— prompt 注入、凭证泄露、数据外泄。一个精心构造的请求就能掏空你的数据库。",
      },
      {
        emoji: "🚧",
        title: "合规卡关",
        body: "欧盟 AI 法案(2026 年 8 月全面执行)与 SOC 2 要求溯源、审计日志、风险分级。拿不出来,平台团队就卡住你的上线。",
      },
      {
        emoji: "🕳",
        title: "事故零取证",
        body: "凌晨两点 agent 崩了。没有审计日志,无法回放出错的工具调用,无法回滚到已知可用的 skill 版本。你在盲飞。",
      },
    ],
  },
  solution: {
    h2: "在你的开发者和生产环境之间,加一层",
    sub: "每个 skill 在触达真实用户前,都先被审计、沙箱、记录、把关。免费版回答「这 skill 好不好用?」企业版回答「我能不能向审计师证明它能安全上生产?」",
    items: [
      {
        icon: "🔐",
        title: "部署前沙箱",
        body: "在隔离环境里用脱敏的、贴近生产形态的数据跑每个 skill。红队探针。一有异常立刻熔断 —— 在它触达客户之前。",
      },
      {
        icon: "📋",
        title: "合规证据包",
        body: "自动生成 PDF:SOC 2 控制项映射、ISO/IEC 42001 对齐、欧盟 AI 法案风险分级、训练数据隔离证明。直接交给审计师。",
      },
      {
        icon: "📊",
        title: "全链路审计日志",
        body: "每次工具调用、每条数据流、每个报错 —— 一键回放。JSON 导出到你的 SIEM(Splunk、Datadog、Elastic)。默认保留 90 天。",
      },
      {
        icon: "👤",
        title: "SSO/SCIM + 细粒度 RBAC",
        body: "支持 Okta、Auth0、Azure AD。Skill 级权限(哪个 agent 调哪个工具、什么范围)。上生产前设工程经理审批闸口。",
      },
    ],
  },
  how: {
    h2: "如何运作",
    steps: [
      {
        num: "01",
        title: "接入你现有的 MCP 配置",
        body: "把 Hub 指向你的 MCP server 与 agent skill 清单 —— GitHub、内网镜像或直接上传。接入 ≤ 30 分钟。",
      },
      {
        num: "02",
        title: "Hub 跑静态扫描 + 沙箱测试",
        body: "对每个 skill 静态扫描 prompt 注入、凭证暴露、沙箱逃逸风险,再在隔离环境用红队探针做运行时测试。",
      },
      {
        num: "03",
        title: "拿到合规证据包",
        body: "审计级 PDF:控制项映射、风险分级、审计日志样本、训练数据隔离证明。交给采购、过审、部署。",
      },
    ],
  },
  roles: {
    h2: "为真正扛上线的人而做",
    sub: "位置不同,卡点相同:没人能证明这个 agent 能安全上线。",
    blocker: "卡点",
    gives: "Hub 给你什么",
    items: [
      {
        role: "平台 / 工程 VP",
        pain: "上线一再延期,因为没人敢为第三方 MCP server 签字背书。",
        win: "一个部署前闸口,逐个 skill 给出「能上 / 不能上」,并附证据。",
      },
      {
        role: "安全 / CISO",
        pain: "AI agent 是一条新供应链,你现有的 SCA 工具够不着。",
        win: "对 skill + MCP 层持续扫描,对齐 MITRE ATT&CK 和你的合规框架。",
      },
      {
        role: "合规 / GRC",
        pain: "审计师要 agent 工具的溯源与风险分级,你手上没有。",
        win: "每次部署一份签名证据包 —— SOC 2、ISO 42001、欧盟 AI 法案 —— 自动生成,不靠手工拼。",
      },
    ],
  },
  compliance: {
    h2: "许可证、SBOM 与企业内网镜像",
    sub: "给需要「治理」而不只是「发现」skill 供应链的法务和平台团队。",
    items: [
      {
        icon: "📜",
        title: "许可证合规矩阵",
        body: "每个 skill 标注 MIT / Apache / GPL / 商用受限,并标记 GDPR / HIPAA / 各地区适用性 —— 让法务快速放行。",
      },
      {
        icon: "📦",
        title: "SBOM 导出",
        body: "每个 skill 一份软件物料清单,加上供应链持续监控:依赖一旦出 CVE,Webhook 即时告警。",
      },
      {
        icon: "🏠",
        title: "企业内网镜像",
        body: "已审计子集的内网镜像源,每 8 小时从 Hub 同步。你的 agent 不必访问公网即可拉取 skill。",
      },
    ],
  },
  pricing: {
    h2: "定价",
    sub: "发现与评估免费。验证、治理、举证收费。",
    tiers: [
      {
        name: "免费",
        price: "$0",
        unit: "永久 · 无需信用卡",
        features: [
          "浏览完整 10 万 skill 目录",
          "质量分 + 6 维拆解",
          "每个 skill 基础安全扫描",
          "场景页与对比页",
          "周报订阅(每周热门)",
        ],
        cta: "免费探索",
      },
      {
        name: "Pro",
        price: "$49",
        unit: "/月 · 每开发者 · 无需销售对接",
        features: [
          "免费版全部功能",
          "API 访问(目录 + 评分)",
          "Skill 版本锁定 + 自动回滚",
          "审计日志导出(开发者级)",
          "你依赖的 skill 漏洞告警",
          "邮件支持",
        ],
        cta: "申请抢先体验",
      },
      {
        name: "企业版",
        price: "$10K–$30K",
        unit: "/年 / 部门",
        highlight: true,
        features: [
          "Pro 全部功能",
          "SSO/SCIM(Okta、Auth0、Azure AD)",
          "部署前沙箱",
          "合规证据包",
          "全链路审计日志 + SIEM 导出",
          "许可证矩阵 · SBOM · 内网镜像",
          "专属客户经理 + 4h SLA",
          "受监管行业附加包",
        ],
        cta: "预约演示 →",
      },
    ],
    footnote:
      "企业版按团队规模与审计 skill 数量定价。Starter:10 工程师 / 50 skill($10K/年)。Standard:50 / 200($20K/年)。Business:200 / 不限($30K/年)。200+ 工程师或受监管行业从 $50K/年起。",
  },
  creator: {
    h2: "你是 skill 作者,不是采购方?",
    sub: "Verified Creator 计划为严肃的 skill 作者做认证 —— 审计过、可信、在 10 万 skill 的噪音里被看见。",
    benefits: [
      "Skill 详情页与卡片带认证 ✓ 徽章",
      "进入 Verified Organizations 展示位(排名始终客观、不接受付费)",
      "优先收录 + 加急安全与质量审计",
      "「联系作者」入口,用户可直接触达你",
    ],
    cta: "申请 Verified Creator →",
    note: "5 个工作日内人工审核。认证靠迭代、质量、社区反馈赢得,而非付费购买。",
  },
  trust: {
    h2: "为什么团队信这份数据",
    sub: "企业产品我们还早期,这点我们直说。不早期的是:全生态最大的开放审计语料库。",
    items: [
      {
        title: "方法论开放,无需盲信",
        body: "每个评分权重、检测规则、判定边界都公开且 MIT 许可。任何结论你都能自己复现 —— 没有黑箱式的「相信我们」。",
      },
      {
        title: "持续扫描,而非一次性",
        body: "我们每 8 小时重扫整个语料库。你依赖的 skill 出新 CVE,几小时内浮现,而不是等下个季度复审。",
      },
      {
        title: "我们补足 Snyk,不替代它",
        body: "Snyk 和 SonarQube 扫你的代码。Hub 扫你代码调用的 agent skill 与 MCP server —— 它们够不着的、AI 特有的供应链层。",
      },
      {
        title: "绝不拿你的数据训练",
        body: "Hub 不训练、不微调、不把你的数据转发给任何模型厂商。分析在我们的基础设施或本地运行。数据隔离写进合同条款。",
      },
    ],
    orgsLabel: "已收录这些机构的官方 skill 与 MCP server",
    orgsNote: "这些机构的开源 skill 在我们目录中。他们还不是客户 —— 暂时。",
  },
  faq: {
    h2: "采购常见问题",
    items: [
      {
        q: "和 Snyk 或 SonarQube 有什么区别?",
        a: "Snyk 和 SonarQube 扫你的代码。Hub 扫你代码调用的 agent skill 与 MCP server —— 它们不覆盖的供应链层。我们聚焦 AI 特有风险:prompt 注入、沙箱逃逸、工具定义里的凭证泄露、模型训练数据隔离。",
      },
      {
        q: "你们会拿我们的数据训练模型吗?",
        a: "不会。Hub 不训练、不微调、不把你的数据发给任何模型厂商。所有分析在我们的基础设施或本地(企业版)运行。数据隔离写进合同条款。",
      },
      {
        q: "欧盟 AI 法案 —— 你们覆盖完整清单吗?",
        a: "覆盖。Hub 的合规证据包对齐第 9 条(风险管理)、第 10 条(数据治理)、第 11 条(技术文档)、第 12 条(记录留存),并按 2026 年 8 月全面执行更新。",
      },
      {
        q: "Hub 自己过 SOC 2 审计了吗?",
        a: "还没有 —— 这点我们如实相告。我们正在筹备 SOC 2 Type II(目标 2026 Q3)。对于现在就需要 SOC 2 的客户,我们在 NDA 下提供安全控制项映射、可填写定制安全问卷,并在合同谈判中承诺时间表。",
      },
      {
        q: "能私有化或私有云部署吗?",
        a: "企业版可以。支持 AWS、GCP、Azure 和本地 Kubernetes,外加每 8 小时同步的私有 skill 镜像源。医疗 / 国防客户可做气隙(air-gapped)部署。",
      },
      {
        q: "上游 skill 更新了怎么办?",
        a: "上游仓库每次提交,Hub 都会重扫。更新后的 skill 自动进入部署前沙箱,在自动拉取到生产前会先通知你的工程团队。",
      },
      {
        q: "POC 要多久?",
        a: "标准 POC:4 周。第 1 周接入 + 连接器配置。第 2–3 周审计你现有的 skill 清单并交付发现。第 4 周与你的平台团队复盘。POC 费用 $5,000,全额抵扣年度合同。",
      },
    ],
  },
  form: {
    h2: "预约 30 分钟演示",
    sub: "我们会过一遍你当前的 MCP/agent 配置,并在通话结束前指出 3 个即时风险。没有 PPT,没有销售套路。",
    okTitle: "收到 —— 我们会在 24 小时内联系你。",
    okBody:
      "Jason 或 Hub 团队成员会通过邮件联系你安排通话。急的话可以在 X 上 @GoSailGlobal。",
    fields: {
      full_name: "姓名 *",
      email: "工作邮箱 *",
      company: "公司 *",
      role: "职位",
      rolePlaceholder: "工程 VP、CTO、平台负责人…",
      teamSize: "团队规模",
      industry: "行业",
      industryPlaceholder: "金融科技、医疗、汽车…",
      useCase: "你的使用场景是? *",
      useCasePlaceholder: "简述:你现在怎么部署 AI agent,最大的痛点是什么?",
      stack: "当前 AI/agent 技术栈",
      stackPlaceholder: "Claude Code + LangGraph + 12 个 MCP server…",
      compliance: "合规要求",
      compliancePlaceholder: "SOC 2、ISO 42001、欧盟 AI 法案、HIPAA…",
      timeline: "时间线",
      budget: "预算区间",
      message: "还有什么?",
      messagePlaceholder: "背景、紧迫度、你担心的具体风险…",
    },
    teamSizes: ["", "1–10", "10–50", "50–200", "200–1,000", "1,000+"],
    timelines: ["", "立即(本季度)", "1–3 个月", "3–6 个月", "只是了解"],
    budgets: [
      "",
      "<$5K/年",
      "$5K–$10K/年",
      "$10K–$30K/年",
      "$30K–$100K/年",
      ">$100K/年",
    ],
    submit: "申请演示 →",
    submitting: "提交中…",
    privacy:
      "我们绝不分享你的数据。提交内容加密存储。Jason 会在 24 小时内人工审阅。",
    errMissing: "请填写姓名、邮箱、公司和使用场景。",
    errGeneric: "提交失败。",
  },
};

export const ENTERPRISE_ORGS = ORGS;
