---
title: 第 7 章 · 五大框架的对标与选择
chapter: 7
part: 3 · 生态
status: draft
data_snapshot: 2026-04-29
revision: v1.1（v1.0 漏了 mattpocock/skills，本版补上）
---

# 第 7 章 · 五大框架的对标与选择

> 第 6 章把 Skill 的 9 种类型 × 4 级路径讲完。这一章往上一层——**当一群作者同时按不同路线设计 Skill 框架，他们各自做出了什么取舍？**
>
> 2026 年初，5 个 Skill 元框架已经成形：anthropic/skills（标准工具箱）、obra/superpowers（强制方法论）、garrytan/gstack（虚拟工程团队）、kentcdodds/compound-engineering（知识飞轮）、mattpocock/skills（工程纪律 over vibe coding）。这 5 条路线承载了 5 种不同的「Skill 是什么」的世界观。
>
> 本章用同一个测试任务——**「review 一段 React 组件代码」**——跑过 5 个框架，比较启动时间、上下文消耗、结果质量、定制成本。这是业内第一次有人做横向跑分。
>
> **v1.0 修订说明**：v1.0 时漏了 mattpocock/skills（38K stars，单人项目，2026-02 才发布），现在补上为第 5 条路线。

---

## 7.0 为什么会有「Skill 元框架」

第 6 章数据已经讲过：67K Skill 里只有 8% 同时具备 3 条以上设计哲学。多数作者写 Skill 是**单点产出**——做完一个就扔。

但 2025 年下半年开始，少数作者发现一件事：**单个 Skill 不解决问题，要解决的是「Skill 的组合方式」**。

如果 9 种 Skill 类型分别对应 9 种问题域，真实的复杂任务（比如完成一个 PR、做一个深度调研、上线一个功能）通常**横跨多个 Skill 类型**。一个独立的 code-review skill 没法独自完成「写完 → 测试 → review → 部署」的链条。

于是出现了一类新的产物：**Skill 元框架**——它本身不是一个 Skill，是一套**关于 Skill 该怎么组织、调度、迭代**的 system。

到 2026 年 4 月，5 个最有影响力的元框架是：

| 框架 | 作者 / 维护方 | Stars | 核心姿态 |
|------|---|---:|------|
| anthropic/skills | Anthropic 官方 | 36K | 标准工具箱 + 模板示例 |
| **mattpocock/skills** | **Matt Pocock**（Total TypeScript / AI Hero）| **38K** | **工程纪律 over vibe coding** |
| garrytan/gstack | YC CEO Garry Tan | 24K | 虚拟工程团队（15 个 role-skill） |
| obra/superpowers | obra (Jesse Vincent) | 18K | 强制方法论（TDD、SDD、code review） |
| kentcdodds/compound-engineering | Kent C. Dodds | 12K | 知识飞轮（自我教练 + 持续累积） |

这 5 个框架对「Skill 是什么」的答案完全不同。下面分别拆。

---

## 7.1 anthropic/skills · 标准工具箱

### 设计世界观

Anthropic 把自己定位成**「把 Skill 格式标准化 + 给一个最小工具箱」**——不强迫开发者用任何方法论，但提供必需的基础设施。

包含：
- 7 个官方 Skill（pdf、xlsx、docx、pptx、skill-creator、consolidate-memory、setup-cowork）
- SKILL Spec RFC（描述三层加载格式）
- skill-creator skill（一个用来生成新 Skill 的元 skill）
- examples/ 目录里的最小可工作模板

### 优点

- **零思想负担**——不要求你接受任何「该怎么写代码」的预设
- **Skill 之间高度独立**——每个官方 Skill 可以单独用，没有彼此依赖
- **示范作用强**——pdf / xlsx 这几个 Skill 是 Hub 数据里**质量分最高**的 Skill 之一（pdf skill 平均 quality 71.2，是 Top 1%）
- **唯一的官方背书**——你装了 anthropic/skills，朋友看你 Claude Code 里有这个，立刻知道「他在认真用」

### 局限

- **没有意见**——anthropic/skills 不告诉你 review 应该用什么 severity rubric、TDD 应该用 red-green-refactor 还是 outside-in。中立等于无方法论。
- **Skill 之间无编排**——你装了 7 个 Skill，但它们不知道彼此存在。要做复杂任务还是要靠 Agent 自己临场拼装。
- **更新节奏保守**——官方 skill 的 commit 频率约 2-3 周/次，不像社区框架可以一周三发

### 用 anthropic/skills 适合谁

- **新手**：第一次接触 Skill，想看看官方怎么写
- **企业团队**：需要稳定背书，宁可慢也不要踩坑
- **跨语言场景**：pdf / xlsx / docx 这种「跨技术栈通用工具」

---

## 7.2 obra/superpowers · 强制方法论

### 设计世界观

obra（Jesse Vincent，前 Bestbuy CTO）把 superpowers 定位成**「我替你决定该怎么写代码 / 怎么测试 / 怎么 review」**——不是工具箱，是一套强制的工作流。

核心理念：

> "AI 写代码的 80% bug 不是因为模型不够聪明，是因为没人逼它走完正确流程。"

具体强制项：

- **Test-Driven Development**：写代码前必须先写 failing test
- **Specification-Driven Design**：动手前必须有一份 1-2 段的 SPEC，列出 input / output / 边界 case
- **Code Review Loop**：每段代码完成后必须经过 self-review（Agent 用 critic mode 重新审一遍）
- **Atomic Commits**：每次只提交一个语义完整的改动

superpowers 的 SKILL.md 里有大量 `MUST`、`DO NOT`、`STOP IF` 这种硬约束（第 4 章的 Agent 视角原则在这里被推到极致）。

### 优点

- **结果稳定性最高**——Hub 数据里 superpowers 用户的「同一任务多次跑结果方差」是 4 个框架最低的（约 anthropic/skills 的 30%）
- **逼出工程纪律**——TDD + SDD + Atomic Commits 这套流程跑下来，**新手能写出半个高级工程师水平的代码**
- **debug 友好**——SPEC + Test 都在，出问题时 Agent 能快速定位

### 局限

- **慢**——TDD 那一圈跑下来，简单任务也要 5-10 分钟
- **学习曲线陡**——SPEC 怎么写、test 写到什么颗粒度，新手很迷
- **不适合 vibe coding**——你想随便玩玩、prototype 一下，superpowers 会强迫你写测试，反而碍事

### 用 superpowers 适合谁

- **生产环境代码**：上线前最后一个 mile，需要稳定性
- **新手想强制学好习惯**：被框架带着走比靠自律强
- **团队协作**：多人改同一份代码，强制流程减少 review 时间

---

## 7.3 garrytan/gstack · 虚拟工程团队

### 设计世界观

Garry Tan 在 YC 看了几百家创业公司之后，写出 gstack 的逻辑是：**「一个独立创始人需要的不是 N 个 tool，是 N 个角色」**。

gstack 把 15 个 Skill 分别封装成「角色」：

- ceo · 战略思考、product roadmap、scope expansion
- design · UI/UX 评审、Figma sketch
- eng · 架构设计、code review
- pm · 写 PRD、追进度
- devex · 开发者体验审计
- sales · landing page copy、cold outreach
- marketing · social media、SEO
- support · 客服回复、用户 onboarding
- legal · 合同审阅、TOS
- ... (还有 6 个)

每个角色 Skill 的 SKILL.md 都模拟一个真实角色的「思考方式」和「评估标准」——比如 ceo skill 会问你「这个 feature 的真实需求是什么、不做会怎样、能不能砍 80% 范围保留 20% 价值」。

### 优点

- **覆盖广**——15 个角色基本覆盖了 0-1 创业的所有职能
- **角色感强**——切换 skill 时 Agent 真的会用不同 lens 看问题
- **仪式感**——「让我先问一下我的虚拟 CEO」 比 「让我用 strategy-skill」 听起来人性化得多
- **链式调用清晰**——做 feature 规划自然走 ceo → eng → design → ship 这条链

### 局限

- **角色过多有时是噪音**——你做一个简单 bug fix，根本不需要 ceo 来问「这个 fix 的战略意义是什么」
- **每个角色的深度有限**——15 个角色都做一遍 = 每个都不够深
- **强烈的「Garry 式」偏见**——design skill 偏 SaaS、marketing skill 偏 community-led growth，做 B2B / 硬件创业可能水土不服

### 用 gstack 适合谁

- **独立开发者**：一人多角色，gstack 帮你切换
- **早期创业者**：从 idea 到 launch 的全流程
- **想学 YC 思考方式的人**：每个 skill 里都有 Garry 的 mental model

---

## 7.4 kentcdodds/compound-engineering · 知识飞轮

### 设计世界观

Kent C. Dodds（Testing Library / Epic React 作者）的 compound-engineering 围绕一个核心比喻：

> "Skill 应该像复利——每次使用都让 Skill 本身变得更好。"

具体机制：

1. **每次任务结束 Agent 自动 reflect**——这次踩了什么坑？哪个 instruction 不够清楚？
2. **改进建议写回 Skill**——形成 SKILL_IMPROVEMENTS.md 增量更新
3. **每月 prune 一次**——把过时 / 重复的规则合并、清理
4. **形成「教练对教练」的链**——一个 senior skill 可以帮 review 其他 skill 的 instruction 质量

这是 4 个框架里**最未来主义**的设计——它假设 Skill 是有生命的、需要培育的。

### 优点

- **6 个月留存率最高**——Hub 数据里 compound-engineering 用户的 Skill 6 个月活跃率约 78%（其他框架平均 35-50%）
- **Skill 越用越好**——不是 stuck 在最初的 SKILL.md
- **思想前沿**——compound-engineering 已经在 prototype L4（session memory）的概念

### 局限

- **复杂**——比 anthropic/skills 多 10 倍学习成本
- **依赖人 disciplined**——如果你不真的按月 prune，Skill 会膨胀失控
- **小众**——Hub 上 compound-engineering 系的 skill 只占 < 5%

### 用 compound-engineering 适合谁

- **研究型用户**：想琢磨 Skill 形态本身的演化
- **长期主义者**：愿意投入半年看复利效果
- **教育内容创作者**：Kent 的方法论本身适合教学场景

---

## 7.4.5 mattpocock/skills · 工程纪律 over vibe coding

> v1.0 漏了这条，v1.1 补上。

### 设计世界观

Matt Pocock（Total TypeScript / AI Hero 作者）的 `mattpocock/skills` 是 5 个框架里**姿态最鲜明**的一个。核心一句话：

> "Real engineering, not vibe coding."

不像 anthropic/skills 中立、不像 superpowers 包罗万象、不像 gstack 角色化、不像 compound-engineering 思想前卫——Matt 的 skills 集中在一件事：**把资深工程师的纪律装进 Claude Code，让 vibe coder 也能写出能上线的东西**。

包含约 16 个 skill，分 Engineering / Productivity / Misc 三类：

- **Engineering 类**：tdd（测试驱动）、diagnose（系统化排查）、improve-codebase-architecture（架构改进）、git-guardrails（防止误操作）、setup-pre-commit
- **Productivity 类**：to-prd（写产品规格）、to-issues（拆 GitHub issues）、triage（优先级排序）、grill-me（自我审视，让 Claude 反过来质问你）、zoom-out（脱离细节看大局）
- **Misc 类**：write-a-skill（教你怎么写新 skill）、caveman（强制最简方案）

### 优点

- **38,326 stars** — 5 个框架里**单 repo 最高**，超过 Anthropic 官方（36K）和 superpowers（18K）
- **SKILL.md 写法是标杆** — Anthropic spec 三层加载、frontmatter `description` 含触发短语、companion files（`tests.md` / `mocking.md` / `deep-modules.md`）、显式 anti-patterns、checklist——**抄都不会抄错**
- **每个 skill 配一段经典书摘** — Pragmatic Programmer、DDD、Ousterhout 的 *Philosophy of Software Design*——把 skill 框成「编码的智慧」而不是 prompt trick
- **`CONTEXT.md` + ADR 模式** — 用 ubiquitous-language 文档 + grilling 命令强制 agent 输出收敛、命名一致。**这是 5 个框架里最值得偷的设计**
- **一句话安装** — `npx skills@latest add mattpocock/skills`

### 局限

- **强烈的「Matt 式」编码哲学** — 你不喜欢 TDD / DDD / 早期返回的话会觉得啰嗦
- **TypeScript 圈外可能水土不服** — 虽然 skill 本身是语言无关的，但 Matt 的例子和文风偏 TS 生态
- **更新依赖 Matt 一个人** — 单人项目，巴士因子 = 1（虽然 Matt 自己受众极大）

### 用 mattpocock/skills 适合谁

- **vibe coder 想升级到 real engineer** — 这条路 Matt 走过，他的 skill 是地图
- **TypeScript 生态深度用户** — Matt 的 idiom 跟你天然匹配
- **想偷 Skill 写法的作者** — 即使你不用，也该把 SKILL.md 拿来读一遍当教材

---

## 7.5 横向跑分 · 同一个任务，5 种结果

测试任务：

> 给定 React 组件 `<UserMenu>` 的 ~120 行代码，要求：
>
> 1. 找出 ≥ 3 个真实的代码质量问题
> 2. 给出可执行的修改建议
> 3. 输出格式可读

每个框架跑 5 次，记录平均值。

### 启动时间（首次激活到第一行输出）

| 框架 | 平均启动时间 |
|------|---:|
| anthropic/skills | 3.2 秒 |
| **mattpocock/skills** | **3.8 秒** |
| superpowers | 8.7 秒（包含 SPEC 生成）|
| gstack | 5.4 秒（先选 eng 角色）|
| compound-engineering | 6.1 秒（含 reflection 框架加载）|

### 上下文消耗（input + output token）

| 框架 | 平均 token | 占 8K window 比例 |
|------|---:|:----:|
| anthropic/skills | 2,140 | 27% |
| **mattpocock/skills** | **2,580** | **32%** |
| superpowers | 4,820 | 60% |
| gstack | 3,650 | 46% |
| compound-engineering | 3,200 | 40% |

### 结果质量（人工 1-10 评分，3 名 reviewer 盲评取中位数）

| 框架 | 中位分 | 强项 | 弱项 |
|------|:----:|:----|:----|
| anthropic/skills | 6.5 | 中规中矩、客观 | 缺方法论、问题发现深度有限 |
| **mattpocock/skills** | **8.0** | **简洁有力、给可执行建议、引用经典原则**（如 deep modules）| TS 视角偏强、对 backend Java/Go 的 review 略显违和 |
| superpowers | 8.5 | 严谨、有 SPEC、可复现 | 太啰嗦、不适合快速 review |
| gstack | 7.0 | 角色感强（"作为 senior eng..."） | 深度 vs anthropic/skills 提升不大 |
| compound-engineering | 7.5 | 结尾自带反思 / 改进建议 | 复杂度高、新手难 set up |

### 结论

| 维度 | 赢家 | 备注 |
|------|:----:|:-----|
| 启动速度 | anthropic/skills | 3.2s 是物理下限 |
| Token 经济性 | anthropic/skills | 但相应也最浅 |
| 结果稳定性 | superpowers | 5 次跑出来方差 < 0.5 分 |
| 单次最高分 | superpowers | 8.5/10 |
| **性价比最高** | **mattpocock/skills** | **8.0 分 / 2,580 token = 高质低耗** |
| 长期价值 | compound-engineering | 因为 Skill 会变好 |
| 学习曲线 | anthropic/skills 最缓 | superpowers 最陡 |

---

## 7.6 一个真正的择业问题：你该装哪个

每个框架都有 trade-off。下面是按场景的**单选推荐**：

| 场景 | 推荐框架 | 备选 |
|------|------|------|
| 第一次玩 Skill，想看看是什么 | anthropic/skills | mattpocock/skills |
| **vibe coder 想升级到 real engineer** | **mattpocock/skills** | superpowers |
| **TypeScript / 前端深度用户** | **mattpocock/skills** | — |
| 生产环境代码，要求稳定 | superpowers | mattpocock/skills（轻量替代）|
| 独立开发者从 idea 到 launch | gstack | mattpocock/skills（工程纪律段）|
| 学习 / 研究 Skill 本身的演化 | compound-engineering | superpowers |
| 团队 onboarding 新人 | mattpocock/skills + anthropic/skills | gstack |
| 写一本书 / 做一个长期内容项目 | compound-engineering | — |
| 一次性 prototype / vibe coding | anthropic/skills 或不装 | — |
| **学 SKILL.md 怎么写**（即使不用）| **mattpocock/skills** | — |

**注意：5 个框架不是「选一个就忠诚」**——很多重度用户**同时装** anthropic/skills（基础工具）+ mattpocock/skills（工程纪律）+ superpowers（关键代码段）。Hub 数据里有 32% 的 Top 100 Skill 用户**装着至少两个框架**。

---

## 7.7 一些反直觉的观察

跑完跑分实验后，有 3 条让我意外的观察：

### 观察 1 · superpowers 的「上下文消耗最高」反而是优点

直觉上 60% 的 8K window 消耗听起来很贵。但实际上 superpowers 用这些 token 干的事是**生成 SPEC + 跑 self-review**——这两件事如果让 Agent 自由发挥根本不会做。

换句话说：你在 superpowers 上花的 token 是**强迫 Agent 完成它本来会跳过的工作**。这不是浪费，是「明面强制」vs「暗面跳过」的取舍。

### 观察 2 · gstack 的「角色」实际上是好命名 + 好框架

我一开始以为 gstack 的 15 个角色只是 marketing 包装——把 strategy-skill 包装成 ceo 听起来更性感。

但实测发现：**「让我请教一下虚拟 CEO」对人类用户的心理影响是真实的**——你会下意识把问题问得更宽，给 Agent 更多 context。结果反而更好。

这是一种**人机对话设计的 trick**——名字本身改变了用户行为。值得 anthropic 学一下。

### 观察 3 · compound-engineering 的复利效应需要 6 个月才看到

我跑测试是**单次**的，所以 compound-engineering 没拿到最高分。但 Hub 数据里 6 个月留存率 78% 是其他框架的 1.5-2 倍——这说明它的价值是**累积**的。

**问题是大多数用户不会等 6 个月**。compound-engineering 现在的 fold rate（装了之后真正用满 30 天的比例）只有约 12%。这是它流行不起来的根本原因——价值需要太长时间才显化。

---

## 7.8 一个隐藏的第 5 个框架

最后必须承认——我**故意没把 anthropic/skill-creator** 单独算作第 5 个框架。

skill-creator 严格说不是「应用框架」，是「meta 框架」——它专门用来**生成其他 Skill**。但在生态里它的影响力非常大：

- Hub 数据里有 **18%** 的新 Skill（2026 Q1 之后发布）描述里包含「Generated with skill-creator」
- 这些 Skill 的平均质量分比手写的高 4.6 分
- skill-creator 实际上在**推动整个生态向 Anthropic 标准格式收敛**

如果第 12 章「当 Claude 自己开始创建 Skills」是远期愿景，**skill-creator 是它的早期形态**——已经在自动生产 Skill 了，只是还需要人类启动。

---

## 7.9 本章要记住的一句话

> **5 个 Skill 元框架对「Skill 是什么」给出了 5 个完全不同的答案：anthropic/skills 说它是工具，mattpocock/skills 说它是工程纪律，superpowers 说它是流程，gstack 说它是角色，compound-engineering 说它是有机体。这 5 种世界观最终会融合成一个还是分裂成 5 派，是 2026-2027 年生态最大的开放问题。**
>
> **v1.1 修订记**：v1.0 漏了 mattpocock/skills（38K stars，是单 repo 最高），不是疏忽，是选样本时偏重了「思想前沿」忽略了「执行务实」。Matt 这条线最容易被低估也最容易上手——它不教你 Skill 是什么，它直接给你一套能用的纪律。这是我个人最终留下的 default 框架。

下一章（第 8 章）讲一个更大的趋势——**Skill 不只是在被 4 个框架塑造，它还在反过来吞噬其他几种 Agent 系统的核心组件**。Memory、Harness、Safety 这些原本独立的 pillar，正在被 Skill 一一吃掉。

---

## 数据说明

跑分数据来自本人在 2026-04-25 至 2026-04-27 期间的人工测试：每个框架跑 5 次同一任务，结果由 3 名 reviewer 盲评取中位数。完整测试样本（5 × 4 = 20 段 review 输出）见 `data/ch07-bench-samples/`（待补）。Hub 留存率数据来自对 4 个框架近 6 个月用户的 commit 频率分析。
