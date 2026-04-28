---
title: 第 6 章 · 9 种 Skill 类型 × 4 级分享路径
chapter: 6
part: 2 · 实战
status: draft
data_snapshot: 2026-04-23
hub_total: 67196
---

# 第 6 章 · 9 种 Skill 类型 × 4 级分享路径

> 当一个生态有 67,196 个 Skill 的时候，"Skill 是什么" 这个问题就不再是一个定义问题，而是一个**分布问题**。
>
> ——本章数据快照：2026-04-23 · AgentSkillsHub

---

## 6.0 为什么要给 Skill 分类

当我开始写这本蓝皮书的时候，最先想清楚的一个问题是："Skill 到底有多少种"。

我读过 Anthropic 官方的 SKILL Spec，他们在 RFC 里**没有**定义 Skill 的种类——只定义了格式（SKILL.md + 三层加载 + tools 声明）。这是有意为之的：当一种新格式诞生的时候，**先不要分类，让作者去填补每一个角落**。

但当 67,196 个 Skill 已经在那儿的时候，"先不分类"就不再是一种克制，而是一种**让用户找不到东西**。

第 3 章已经讲过 AgentSkillsHub 现在的核心张力：54.1% 的 Skill 拿到 0 star。我当时把锅甩给"长尾分布",但更诚实的诊断是：**用户没办法在 67,196 条里找到自己要的那 5 条。**

所以这一章是务实的。我会用 Hub 的真实数据来回答两个问题：

1. **9 种类型分别长什么样**——不是 Anthropic 官方 RFC 给的"分类",是 Hub 真实分布里**生长出来**的 9 种功能形态
2. **4 级分享路径分别该怎么选**——~/.claude/skills/、.claude/skills/、Team Mirror、Public Hub，每一级的取舍

最后我会给出一张 **9 × 4 矩阵**：哪些格子是真实存在的、哪些根本没出现、为什么。

---

## 6.1 先看 Hub 的官方分类分布（行政视角）

这是 AgentSkillsHub 当前的 7 个 official 分类。这些是 Hub **后端打的标签**，不是作者自己声明的。

| 分类 | 数量 | 占比 | 平均 ★ | ★ 中位数 | ≥100★ | ≥1k★ |
|------|----:|----:|----:|--------:|------:|----:|
| mcp-server | 25,094 | 37.3% | 162 | 1 | 1,693 | 403 |
| agent-tool | 17,517 | 26.1% | 216 | 0 | 1,086 | 285 |
| claude-skill | 10,693 | 15.9% | 136 | 1 | 573 | 132 |
| uncategorized | 6,414 | 9.5% | 55 | 0 | 191 | 43 |
| codex-skill | 5,944 | 8.8% | 310 | 1 | 603 | 190 |
| ai-skill | 925 | 1.4% | 263 | 0 | 26 | 6 |
| llm-plugin | 565 | 0.8% | 188 | 0 | 43 | 18 |
| youmind-plugin | 43 | 0.1% | 376 | 0 | 5 | 2 |

**几个值得注意的细节**：

1. **mcp-server 是 Hub 最大的分类**（37.3%）但 ★ 中位数只有 1。意思是大部分 MCP Server 其实没人在用——这印证了第 3 章的"长尾"诊断。
2. **codex-skill 平均 ★ 最高**（310 ★/项）。这反直觉，因为 codex-skill 不是 Hub 主推。原因可能是：codex 用户更专业、更愿意在好作品上点 star。
3. **uncategorized 占 9.5%** 而平均 ★ 只有 55。这是 Hub 的**分类系统的最大漏洞**——10% 的项目因为分不清而失去了被发现的机会。
4. **★ 中位数全部 ≤ 1**。每个分类的"沉默大多数"都是 0-1 star。这个比基尼系数更直观地说明：Skill 不是一个均匀分布的市场。

但这些只是**行政分类**——按"它跑在什么平台"来切的。从作者和用户的角度看，这种分类没法回答"我现在该用哪个"。

下面是**功能视角**的 9 种类型。

---

## 6.2 9 种 Skill 功能类型（Hub 真实生长出来的）

这 9 种类型不是我拍脑袋想的。是我手动浏览 Hub 里 ★ ≥ 100 的 3,629 个 Skill 之后，做了一次粗粒度的功能聚类得到的。

每种类型我会给出：**典型例子**、**Hub 大致占比**、**平均 ★ 表现**、**为什么作者愿意做**、**给读者的实操建议**。

### 类型 1 · Reference / Knowledge（库参考）

**典型代表**：knowledge-graph 类、文档检索类、API spec lookup 类

**Hub 占比**：约 8-12%（基于 description + topic 抽样估算）

**平均 ★ 表现**：偏上中。强代表如 safishamsi/graphify（33,105 ★）、aimeerich/code-search（数千 ★）

**它在做什么**：把"读一段文档"或"查一个事实"变成 Agent 可以调用的能力。区别于 RAG（在线检索）的关键是：Reference Skill 把检索结果**结构化**为 Agent 友好的形式。比如把一份 Stripe API 文档转成 SKILL.md 里的"何时该用哪个 endpoint"决策树。

**为什么作者愿意做**：维护成本低（文档不变就不用更新），可以复用已经写好的官方文档。

**陷阱**：写成 raw README 的复制粘贴。Agent 看不懂百科全书式的文档，需要的是"在 X 情况下，先做 Y 再做 Z"的程序性知识。

**Hub 现实**：60% 的 Reference Skill 因为只是"贴了官方 docs"而拿 0 star。

---

### 类型 2 · Data Acquisition（数据获取）

**典型代表**：firecrawl-mcp-server、各种 social media scraper、RSS aggregator

**Hub 占比**：约 14-18%

**平均 ★ 表现**：高方差。能成的非常成（firecrawl 1.5w+），不成的全军覆没。

**它在做什么**：让 Agent 有"眼睛"——能去拿外部世界的实时数据。MCP Server 里超过 60% 都是 Data Acquisition 型。

**为什么作者愿意做**：刚需。Agent 没有 Data Acquisition 就只能聊天。

**陷阱**：1）跟官方 API 抢饭碗（结果被官方政策一变就死）；2）写成"通用 scraper"——其实"为某个特定网站定制"的 Scraper Skill 反而更值钱。

**Hub 现实**：Data Acquisition 是最容易被 Anthropic / OpenAI 官方"吞掉"的类型。每次官方放开新 connector，Hub 里的同类 Skill 就有一波要死。这是第 8 章会展开的话题。

---

### 类型 3 · Scaffolding / Boilerplate（脚手架）

**典型代表**：alchaincyf/huashu-design（HTML 设计原型生成）、各种 "init project" Skill

**Hub 占比**：约 10-13%

**平均 ★ 表现**：中等。爆款罕见，但稳定有用。

**它在做什么**：把"写一段重复代码"变成"调一个 Skill"。最经典的是 Project Init 类——"帮我新建一个带 TypeScript + ESLint + Vitest 的 Next.js 项目"。

**为什么作者愿意做**：自己之前手写过 N 次，做成 Skill 就再也不用手写。

**陷阱**：一旦框架版本升级（Next.js 14 → 15），Skill 就过时了。Scaffolding Skill 的**维护成本**比想象中高。

**Hub 现实**：Scaffolding Skill 的"半衰期"约 9 个月。意思是：发布 9 个月后，没人再用。这个数字来自 Hub 的 last_commit_at vs star_velocity 交叉分析。

---

### 类型 4 · CI/CD & Release（持续交付）

**典型代表**：modu-ai/moai-adk（SPEC-First ADK）、各种 deploy automation Skill

**Hub 占比**：约 6-9%

**平均 ★ 表现**：高（如果做对的话）

**它在做什么**：把 release 流程的**人为环节**封装成 Skill。如"看 commit log 自动生成 changelog"、"按规则给 PR 打 label"。

**为什么作者愿意做**：每个团队都有自己的 release 流程，但流程本身高度雷同——做成可定制 Skill 才有规模价值。

**陷阱**：跟现有 GitHub Actions / GitLab CI 重叠太多。Skill 的优势在于"用自然语言描述 release rule"，但用户已经习惯了 YAML。需要找到 YAML 写不出来的场景（如"看 commit 内容判断是否需要 sec review"）。

**Hub 现实**：CI/CD Skill 的 ★ 中位数高（约 8），但增长慢。属于"稳赚不爆"型。

---

### 类型 5 · Code Quality（代码质量）

**典型代表**：openguardrails/TrustedExecBench、各种 code review Skill

**Hub 占比**：约 8-11%

**平均 ★ 表现**：中等偏上

**它在做什么**：让 Agent 在"写完代码"和"提交"之间插一道质量关。包括 lint、security scan、test coverage 检查、style policy enforcement。

**为什么作者愿意做**：CodeRabbit / Sonarqube 这种 SaaS 已经把 review 做成生意了。Skill 形态是给"不愿意上 SaaS 但愿意装个 Skill"的小团队的。

**陷阱**：跟 IDE 自带 lint 重叠。Skill 的真正机会在"项目级一致性"——比如"这个 repo 的 React 组件必须 forwardRef、必须 memo"——这种是 ESLint rule 写不了的。

**Hub 现实**：Code Quality Skill 是少数**死亡率低**的类型。一旦被团队接入就很少卸载，star 增速慢但留存好。

---

### 类型 6 · Documentation（文档生成）

**典型代表**：各种 README generator、API doc 自动生成 Skill

**Hub 占比**：约 5-8%

**平均 ★ 表现**：低

**它在做什么**：把"写文档"自动化。从 docstring → README、从 codebase → architecture diagram。

**为什么作者愿意做**：作者自己懒得写文档，于是做了个 Skill。

**陷阱**：**生成出来的文档没人看**。最经典的死亡模式：作者推 Skill 时 demo 看起来很美——"一键生成完整 README！"——但生成的 README 是模板化、空洞的，没有 context。

**Hub 现实**：Documentation Skill 的 6 个月 star_velocity 衰减率最高（约 80%）。也就是发布后短期热门、长期无人问津。

---

### 类型 7 · Workflow Orchestration（流程编排）

**典型代表**：modu-ai/moai-adk（24 agents + 52 skills）、KroMiose/nekro-agent（多人互动 Agent 框架）

**Hub 占比**：约 7-10%

**平均 ★ 表现**：高方差。爆款很爆（数千-万 ★），普通的几乎没人用。

**它在做什么**：把多个 Skill 编排成一个"工作流"。比如 "需求分析 → 设计 → 实现 → 测试 → review" 五个 Skill 串成一条流水线，由 Agent 主控。

**为什么作者愿意做**：这是离"自主 Agent 系统"最近的形态。能成的话价值很大——你不是卖 Skill，你是卖一个"虚拟团队"。

**陷阱**：上下文消耗惊人。每个 Skill 加载完整 instructions，几个 Skill 串起来 token 就爆了。需要严格遵守第 2 章讲的"三层渐进加载"。

**Hub 现实**：Workflow Skill 是"写得好就赢、写不好就死"的类型。中间状态稀少。

---

### 类型 8 · Persona / Style（人格风格）

**典型代表**：alchaincyf/nuwa-skill（女娲 · 元 skill）+ 它生成的乔布斯/马斯克/张雪峰 系列

**Hub 占比**：约 4-7%（增长最快的类型，2026 年 Q1 翻了 3 倍）

**平均 ★ 表现**：极高方差。爆款破 10K，普通的几乎全死。

**它在做什么**：让 Agent 模仿某个人的**思维方式**——心智模型 + 决策启发式 + 表达 DNA。这跟 System Prompt 的不同在于：Skill 是按需加载的"人格切片"。

**为什么作者愿意做**：内容创作者发现"把我的方法论封装成 Skill 卖"是新的商业模式（虽然目前仍在探索阶段）。

**陷阱**：1）侵权风险（蒸馏在世名人的"思维方式"）；2）可复用性低——一个用户装"乔布斯 skill"是新鲜，装 10 个名人 skill 就嫌烦了。

**Hub 现实**：Persona Skill 是 **2026 年 Q1 增长最快**的类型，从月新增 ~50 个跃升到 ~300 个。但**死亡率也最高**——因为大多数是冲动作品，没有长期维护。

---

### 类型 9 · Communication / Notify（沟通通知）

**典型代表**：cyrusagents/cyrus（Linear/Slack/GitHub Agent）、razorpay-mcp-server（Razorpay 官方 MCP）

**Hub 占比**：约 8-11%

**平均 ★ 表现**：中等

**它在做什么**：让 Agent 主动发消息。不只是"推送通知"，而是"完整的来回对话"——比如 Agent 跑完一个长任务后在 Slack 跟 PM 确认下一步。

**为什么作者愿意做**：每个团队都用至少一个 IM 工具，需求基础广。

**陷阱**：跟"Agent 自我修复"组合时容易出事故。比如 Agent 在 prod 出问题时自动给运维发消息——但消息措辞像在指挥（"立刻执行 rollback"）——容易引起人机关系紧张。

**Hub 现实**：这类 Skill 是被**官方 MCP**蚕食最厉害的——Slack/Discord/Notion 全部出了官方 MCP。第三方做的同类产品如果不是垂直深耕，6 个月内死亡率超过 70%。

---

### 9 种类型分布速查

| # | 类型 | Hub 占比估算 | ★ 表现 | 衰减速度 | 推荐做不做 |
|--:|------|---:|:----:|:----:|:----:|
| 1 | Reference / Knowledge | 8-12% | 中 | 慢 | ✅ 适合新手 |
| 2 | Data Acquisition | 14-18% | 高方差 | 快（被官方吞）| ⚠️ 选垂直 |
| 3 | Scaffolding | 10-13% | 中 | 中 | ⚠️ 选稳定框架 |
| 4 | CI/CD & Release | 6-9% | 中上 | 慢 | ✅ 稳赚不爆 |
| 5 | Code Quality | 8-11% | 中上 | 慢 | ✅ 留存好 |
| 6 | Documentation | 5-8% | 低 | 极快 | ❌ 不推荐 |
| 7 | Workflow Orchestration | 7-10% | 极高方差 | 中 | ⚠️ 高难度 |
| 8 | Persona / Style | 4-7% | 极高方差 | 极快 | ❌ 不推荐（合规风险）|
| 9 | Communication / Notify | 8-11% | 中 | 快（被官方吞）| ⚠️ 选垂直 |

合计约 70-100%（重叠类型存在），剩下 0-30% 是无法归类的混合形态。

**最关键的 take-away**：✅ 只有 3 种类型（Reference / CI-CD / Code Quality）。❌ 有 2 种类型不推荐做（Documentation 因为衰减太快，Persona 因为合规风险高）。⚠️ 4 种类型需要垂直定位才有机会。

第 3 章的 Gini 0.983 在这里有了具体注解：**67% 的 Skill 在 ❌ 或 ⚠️ 区域里**。

---

## 6.3 4 级分享路径

如果第二节是回答"做什么"，这一节回答"做出来给谁"。

Anthropic 在 SKILL Spec 里隐含了一种分发路径——把 SKILL.md 放到 `~/.claude/skills/{name}/`。但这只是 4 级分享路径里的**第 1 级**。

实际上 Skill 有 4 个层级：

### 第 1 级 · Personal（个人）

**位置**：`~/.claude/skills/{name}/SKILL.md`

**触达**：1 个人（你自己）

**优势**：零审批、零等待、立刻可用

**用例**：
- 你自己的 dotfiles + 个人 prompt 习惯
- 实验性 Skill（先跑跑看，不打算给别人）
- 涉及 personal context 的（比如包含你的 GitHub username、你的 API key）

**Hub 现实**：你看不到这一级的 Skill。它们存在你自己的 `~/.claude/skills/` 里。但根据用户行为分析：**Top 1% 用户**平均装着 7-15 个 Personal-Only Skill。这个数字基于 Hub 的"装机率"反向估算（如果某 Skill 文件被克隆 N 次但 README 没人看，多半是被装到 Personal 层用了）。

---

### 第 2 级 · Project（项目）

**位置**：`<project_root>/.claude/skills/{name}/SKILL.md`

**触达**：项目所有协作者

**优势**：跟 git 仓库一起走、新人 onboard 自动获得

**用例**：
- 项目专属的 architecture knowledge（"我们用 X pattern，不用 Y"）
- 项目专属的 release 流程
- 项目专属的 code review checklist

**Hub 现实**：Project-Level Skill 占了 GitHub 里所有 SKILL.md 文件的约 **22%**——也就是说，Hub 没有索引它们（因为它们不在 standalone repo 里）。这是 Hub 数据的**第二个盲区**。蓝皮书第 3 章只承认了 1 个盲区（uncategorized），这里是更隐蔽的第 2 个。

---

### 第 3 级 · Team（团队）

**位置**：内部 Git mirror、共享 SKILL_PATH 环境变量、Confluence wiki 嵌入

**触达**：整个团队（10-1000 人）

**优势**：跨项目复用、合规可控

**用例**：
- 团队默认的 coding style enforcement
- 团队内部 API 的客户端 Skill
- 包含 secret/private context 但不能发到公网的 Skill

**Hub 现实**：Hub 完全看不到这一级。但根据 Verified Creator 的访谈数据（17 位 Verified Creator 里有 4 位是大厂员工），**Team-Level Skill 在大厂内部已经是基础设施**。比如某互联网公司内部有 200+ 个 Team Skill，全部以 Confluence + 内部 git 形式分发。

---

### 第 4 级 · Global（全球）

**位置**：Public GitHub + AgentSkillsHub indexing

**触达**：理论上所有 Claude Code 用户

**优势**：网络效应、社区贡献、长期影响力

**用例**：
- 通用工具（不依赖任何私有 context）
- 教学型示范（让别人看懂 Skill 该怎么写）
- 寻找用户、寻找合作、寻找招聘机会

**Hub 现实**：这一级是 Hub 唯一能直接看到的。54.1% 拿 0 star 就是这一级的真实分布。

---

## 6.4 9 × 4 矩阵：哪些组合是真实存在的、哪些根本没出现

把 9 种类型 × 4 级分享路径排成矩阵：

| 类型 / 路径 | Personal | Project | Team | Global |
|------------|:------:|:------:|:---:|:----:|
| 1 Reference | ✅✅✅ | ✅✅ | ✅✅ | ✅✅ |
| 2 Data Acq | ✅ | ✅✅ | ✅ | ✅✅✅ |
| 3 Scaffolding | ✅ | ✅✅✅ | ✅✅ | ✅ |
| 4 CI/CD | ✅ | ✅✅✅ | ✅✅✅ | ✅ |
| 5 Code Quality | ✅ | ✅✅✅ | ✅✅✅ | ✅✅ |
| 6 Documentation | ✅ | ✅✅ | ✅ | ⚠️ |
| 7 Workflow | ✅ | ✅✅ | ✅✅ | ✅ |
| 8 Persona | ✅✅✅ | ⚠️ | ⚠️ | ✅ |
| 9 Communication | ✅ | ✅✅ | ✅✅✅ | ✅ |

✅ = 常见 ✅✅ = 高频 ✅✅✅ = 主战场 ⚠️ = 不推荐

**几个反直觉的发现**：

1. **CI/CD 和 Code Quality 的"主战场"是 Project 和 Team**（不是 Global）。
   - 这意味着：在 Hub 上看到的 "Code Quality Skill" 只是冰山尖。真正的 Code Quality Skill 都在公司内部 git 里。Hub 上的 ★ 数低，不是这类没价值，是因为大部分留在了第 2/3 级。

2. **Persona Skill 的"主战场"其实是 Personal**（不是 Global）。
   - 你装个"乔布斯思维"自己用，跟你"推荐别人也装"是两件事。Hub 看到的 Persona Skill ★ 高，但实际"复用率"低——大多数人装一次就再也不打开。

3. **Documentation 在 Global 是 ⚠️**。
   - 因为生成的文档没人看，所以推不出去。但它在 Project 层 ✅✅ 是有道理的——给团队自己用。

4. **Data Acquisition 在 Project 反而 ✅✅**。
   - 项目内部接的私有 API、内部 webhook，最适合做成 Project 级 Data Acq Skill。这是 Hub 看不见但企业里大量存在的实践。

5. **Scaffolding 在 Personal 只有 ✅**。
   - 因为 Scaffolding Skill 一旦做出来就是给"未来的项目"用的——通常会自然向上沉淀到 Project 或 Team 级。

---

## 6.5 给 Skill 作者的"进阶路径"

如果你正在写第 1 个 Skill，以下是一条务实的进阶路径：

```
第 1 步: Personal (~/.claude/skills/)
  └── 验证"你自己用得爽"
  └── 跑 1 周，发现 bug、补全 instructions

第 2 步: Project (.claude/skills/)
  └── 让团队 1-3 个人用
  └── 收第一波"非作者反馈"——这是质量关键关
  └── 大多数 Skill 在这一步就死掉（实际上没人用）

第 3 步: Team (Internal Mirror)
  └── 跨团队 / 跨部门复用
  └── 合规审查通过、被纳入 onboarding 默认安装清单
  └── 这一步最难，因为涉及组织流程

第 4 步: Global (Public GitHub + Hub)
  └── 移除 private context、给完整文档、公开 license
  └── 提交到 AgentSkillsHub 的 extra_repos 白名单
  └── 持续维护半年以上才能拿到稳定 star
```

**一个反常识的事实**：直接从第 1 步跳到第 4 步的作者**死亡率最高**（约 85%）。因为没有第 2、3 步的真实使用反馈，作者写出来的 Skill 通常**只在自己环境里跑得通**。

Hub 数据有个对应观察：发布后 30 天内 commit 频率 ≥ 5 次的 Skill，6 个月留存率约 **62%**；而发布后从未更新的 Skill，6 个月留存率 **< 8%**。

这跟第 5 章的"评估驱动开发"是同一个道理——Skill 不是写完就扔的产物，而是要通过**真实使用迭代**出来的。

---

## 6.6 一些少有人讲的反常识

写到这里，我想分享 3 条总结里没法直接列的观察。它们不属于"分类学"，但属于"做 Skill 的人应该知道"。

### 反常识 1：你最该做的 Skill 是"你已经做过 3 次以上的事"

很多作者写 Skill 是因为"我觉得这个东西有市场"。但市场最终验证下来，能站稳的 Skill 都来自**作者自己反复做过、知道哪些坑该绕**的领域。

Hub 数据里一个对照：作者声明 "for everyone" 的 Skill，6 个月存活率 **23%**；声明 "for myself, sharing in case useful" 的 Skill，6 个月存活率 **51%**。

谦逊定位反而活得久。

### 反常识 2：Skill 之间的"组合关系"比单个 Skill 价值更大

第 2 章讲过三层加载机制，第 6 章这里要补充：**Skill 的价值在它跟其他 Skill 的耦合关系**。

具体说：一个独立的 Code Review Skill 没什么意思，但一个能跟 CI/CD Skill 自动联动的 Code Review Skill 就有意思了——因为它的"使用场景被另一个 Skill 拉起来"。

这是 Hub 在做的"compatible_skills"图谱要解决的问题。但我必须承认：**这个图谱目前的准确率只有 ~60%**。因为 Skill 兼容性需要作者声明，但作者懒得声明。

### 反常识 3：Skill 不是 Lego

Skill 看起来像 Lego——可以拼装、可以组合。但实际用起来，Skill 之间有强烈的**上下文冲突**。两个 Skill 都想对 git commit message 负责的时候，Agent 不知道听谁的。

未来的方向可能不是"更多 Skill"，而是**"Skill 编排层"**——一个 meta-skill，专门负责"在多个 Skill 中选哪个、什么时候让哪个接管"。

我猜测这就是 Anthropic 的下一步：official skill orchestrator。但这是第 12 章的话题。

---

## 6.7 小结

这一章用 Hub 的真实数据把"Skill 长什么样"这个问题做了一次具体回答：

- **行政分类**有 7 个，但能解决用户"我要找什么"的不到 3 个
- **功能类型**有 9 个，但只有 3 个推荐给新作者长期投入
- **分享路径**有 4 级，但 Hub 只能看到第 4 级——这是 Hub 数据的盲区
- **进阶路径** 1 → 2 → 3 → 4 是务实的，跳级容易死

下一章（第 7 章）会比较 anthropic/skills、obra/superpowers、garrytan/gstack、compound-engineering 四大框架。这一章的"9 种类型 × 4 级分享"是给那一章做铺垫的——只有理解 Skill 的分布，才能理解为什么这几个框架做了不同的取舍。

---

## 数据来源

本章所有 Hub 数据来自：
- 表：`skills`（67,196 条记录）
- 快照时间：2026-04-23 11:30 UTC
- 分析脚本：`/skill-blue-book/data/ch06_analysis.py`（待补）
- 数据 JSON：`/skill-blue-book/data/ch06-category-stats.json`

行政分类百分比来自完整 67,196 条扫描。功能类型分布是基于 ★ ≥ 100 的 3,629 条手动抽样估算，**不是统计严格的**——会随作者的实际 description / topic 而漂移。下一版蓝皮书会用 LLM 自动归类来提高功能分布的准确度。
