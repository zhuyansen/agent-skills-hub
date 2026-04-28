---
title: 第 2 章 · 三层渐进加载：Skill 的真正魔法
chapter: 2
part: 1 · 基础
status: draft
data_snapshot: 2026-04-28
---

# 第 2 章 · 三层渐进加载：Skill 的真正魔法

> 第 1 章讲了 Skill 要解决什么问题——Agent 缺乏 Barry 的 30 年经验。这一章讲一个更具体的工程问题：**当你给 Mahesh 配一本 30 年的小本子，怎么让他不被这本本子噎死？**
>
> 答案就是「三层渐进加载」。这是 Skill 区别于 System Prompt / RAG / Tool Use / MCP Server 的核心机制——也是它能在不爆上下文的前提下无限扩展的技术底座。

---

## 2.0 一个让 Anthropic 头痛的悖论

2025 年中旬 Anthropic 内部讨论 Skill 设计时，有一条悖论卡了几个月：

> **「Skill 越多越好」 vs 「上下文越短越好」**——这两件事天然冲突。

如果你只装 1 个 Skill，体验也许不错；装 10 个，每个都把完整 instructions 塞进 system prompt，模型还能扛；装 100 个，token 数直接爆炸——而且大多数 Skill 这次任务根本用不上。

这是一个看似无解的问题。直到三层渐进加载（**three-stage progressive loading**）方案出现，它的核心洞察很简单：

> **不是所有 Skill 内容都需要在每次对话开始时就被加载。Agent 只需要先看到「索引」，决定要不要展开「正文」，再在执行时按需 fetch「资源」。**

这跟数据库设计里的「索引 vs 表」、跟 IDE 的「Lazy Loading」、跟操作系统的「Virtual Memory」是同一个思想——**先描述，后加载**。

但 Anthropic 的特殊在于：他们把这套机制**烧进了 SKILL.md 的格式里**，让所有作者必须遵守，于是这个分层加载变成了**生态级的资产**。

---

## 2.1 三层是哪三层

三层加载机制的官方定义在 Anthropic 的 SKILL Spec RFC 第 3.2 节。简化版本：

| 层 | 内容 | 加载时机 | Token 量 |
|----|-----|--------|--------|
| **L1 · description** | 一句话「这个 Skill 在做什么 + 何时该激活」 | 每次对话启动时全部加载 | ~50 tokens |
| **L2 · instructions** | 详细操作步骤、约束、输出格式 | Agent 决定激活后才加载 | ~500-3,000 tokens |
| **L3 · resources** | 代码、模板、示例数据、large files | 执行过程中按 ID 拉取 | 不计入 prompt |

Hub 数据里的 SKILL.md 大小分布印证了这个设计——**Top 500 中 86% 的 SKILL.md 体积在 5-30KB**。这不是巧合：5KB 是「能装下 description + 简短 instructions」的下限，30KB 是「instructions 全部塞下还不爆 8K context window」的上限。**作者集体收敛到这个区间，是被三层加载的格式压力筛出来的**。

下面分别拆。

---

## 2.2 L1 · description：Skill 唯一对所有 Agent 可见的入口

L1 是一句话。这句话决定了 Skill 的命运。

Anthropic SDK 处理 Skill 时的逻辑大致是：

```
对话启动
  ↓
扫描所有可用 Skill 的 description
  ↓
拼成一个「Skill 目录」放进 system prompt
  ↓
Agent 收到用户消息后，根据 description 判断
  「这个任务需要哪些 Skill 激活」
  ↓
对激活的 Skill 才加载完整 instructions（L2）
```

也就是说，**99% 的 Skill 在每次对话里都会以 description 形式出现，但只有少数被实际激活**。description 写得不好，Skill 永远不会被打开。

第 4 章已经讲过宝玉的「Agent 视角」哲学，对应到这一层是非常具体的：

**❌ 人类风的 description**（来自 Hub uncategorized 类的常见样本）：

```yaml
description: A helpful skill for code review
```

**✅ Agent 风的 description**（来自 emilkowalski/skill）：

```yaml
description: |
  Review UI code for animation timing, transition smoothness,
  and motion design taste. ALWAYS use when the user shares
  React component code involving CSS transitions, framer-motion,
  view-transitions, or asks "review this animation".
  Output format: markdown table with Before/After/Why columns.
```

差别不在长度，在**信息密度**：

| 维度 | 人类风 | Agent 风 |
|------|:----:|:----:|
| 触发条件明示 | ❌ | ✅（「ALWAYS use when...」）|
| 输入类型限定 | ❌ | ✅（CSS transitions / framer-motion）|
| 输出格式预声明 | ❌ | ✅（markdown table with...）|
| Token 投入 | ~10 | ~50 |

Hub 数据：**含「Use when / MUST / Output format」三类显式短语的 description，平均 quality_score 比纯叙事型高 7.7 分**（第 4 章详述）。这条 +7.7 直接来自 L1 的精度。

### description 的 50 token 限制

Anthropic SDK 实际上对 description 字段有一个软限制：**~80 tokens（约 50 中文字 / 60 英文词）**。超过会被截断展示给 Agent。这意味着 description 不只是一句话，是**一句话能装下多少有用信号**。

最经济的 description 公式：

```
[这个 Skill 解决什么问题] + [何时该激活] + [输出形态预告]
```

举几个 Hub 高 quality_score 样本的 description（已脱敏简化）：

- `Review code for SQL injection / OWASP-Top-10. Use when reviewing PR diff or git diff. Output: severity-grouped table.` （55 tokens）
- `Convert any folder of code/docs/papers into queryable knowledge graph. Use after user shares a folder URL. Output: Cypher query examples.` （48 tokens）
- `Fetch + summarize WSJ/FT/Bloomberg news. Use when user asks about「今天/昨天 X 行业的新闻」. Output: bullet list with source links.` （54 tokens）

**三段式都齐**——这是 description 写好的最小单位。

---

## 2.3 L2 · instructions：被激活之后才加载的「正文」

description 让 Skill 进入 Agent 的视野，instructions 决定它能不能把任务做漂亮。

L2 的设计有 4 条普遍规律（基于 Hub Top 500 的 instructions 文本聚类得出）：

### 规律 1 · 必须在前 200 字内回答 5 个问题

Agent 加载 instructions 的第一段时，是**先扫一眼判断「这个 Skill 真的能做我要的事吗」**，没耐心看 5KB 才知道答案。所以前 200 字必须回答：

1. 这个 Skill 准确做什么（不是 description 那种概括）
2. 它的输入是什么（文件？文本？URL？）
3. 它的输出是什么（结构化 JSON？markdown 表？修改文件？）
4. 它有什么前置依赖（某个 CLI 工具？某个 API key？）
5. 失败时该怎么办（重试？fallback？ask user？）

Hub Top 500 里 **74% 的 instructions 前 200 字至少答了其中 4 个问题**。剩 26% 把这些答案散在 instructions 各处——**这 26% 平均 quality_score 低 6.8 分**。

### 规律 2 · 决策树 > 散文

instructions 不是教程，是**决策树**。Agent 不需要你讲清楚「为什么要这样做」，需要你讲清楚「在 X 情况下做 Y」。

对比两段同主题的 instructions（来自不同的 code-review skill）：

**❌ 散文版**：
```
代码审查时应该综合考虑代码质量、可读性、性能、安全性等多个方面。
对于复杂的 PR，建议先理解整体架构再 deep-dive 细节。注释和命名也很重要。
```

**✅ 决策树版**：
```
1. If diff has > 200 lines:
     a. Run `git log -10 --oneline` for context
     b. Read CHANGELOG.md for in-flight features
     c. Skim full diff before scoring
2. For each changed file:
     a. If file has tests/ → check test diff first
     b. If file has SQL → MUST flag injection risks
     c. If file has any URL → MUST check for credential leaks
3. Severity rubric:
     CRITICAL: security issue / data loss
     HIGH: regression risk / wrong abstraction
     MED: style / naming / minor refactor
4. Output: table grouped by severity
```

Agent 处理「散文版」时会自由发挥；处理「决策树版」时会**逐条执行**，结果方差小一个数量级。

### 规律 3 · 把 anti-pattern 显式 ban 掉

Agent 比人更容易陷入 hallucination 模式（「我应该展示我的能力」），所以好的 instructions 会**显式列出禁止动作**。

Anthropic 官方 Skill 模板里有一段值得抄的范本：

```markdown
## DO NOT

- Do NOT modify files outside the user's explicit request scope.
- Do NOT install npm packages without first asking permission.
- Do NOT run `npm test` if it's already known to be broken
  (check the user's last message for "tests are red" / "fix later").
- Do NOT make up file paths if you can grep for them instead.
```

这些规则单独看都是常识，但写在 instructions 里**给了 Agent 不那么发挥的合法理由**。

### 规律 4 · instructions 大小的 sweet spot 是 5-20KB

第 6 章数据已经讲过：**< 2KB 的 SKILL.md 平均 quality 36.3，10-20KB 的 51.4，> 40KB 的 45.2**。

L2 是这个数据的主要贡献者——instructions 太短信息不足，太长 Agent 难以全部 retain。**5-20KB 是 Agent 能 fully retain + 行为收敛的范围**。

---

## 2.4 L3 · resources：执行时按需 fetch

L1 和 L2 都是「文本」，L3 是「文件」。

Hub Top 500 里有 28% 的 Skill 用到 L3——它们的 SKILL.md 之外还有 `resources/` 目录，里面装：

- 代码模板（`templates/api-client.ts`）
- 示例数据（`examples/sample-input.json`）
- 大型查表（`data/iso-currency-codes.csv`）
- 分步骤的更细 instructions（`steps/01-init.md`、`steps/02-config.md`）
- 测试用例（`tests/case-001.json`）

L3 不算进 prompt token，只在 Agent 明确说「我现在需要 templates/api-client.ts」时由 SDK 拉过来。

### 一个真实例子 · Leon's taste-skill

第 4 章已经分析过 `Leonxlnx/taste-skill`。它的 `resources/` 结构是这样：

```
taste-skill/
├── SKILL.md                  (L1 + L2 → 21KB)
├── resources/
│   ├── easings.css           (CSS easing 常量)
│   ├── animation-timings.md  (按场景查表)
│   ├── color-palettes/       (不同风格的色板)
│   │   ├── minimalist.json
│   │   ├── brutalist.json
│   │   └── soft.json
│   └── reference-sites.md    (灵感参考)
```

SKILL.md 里只有这样的引用：

```markdown
For specific easing curves, fetch resources/easings.css.
For palette by style, fetch resources/color-palettes/{style}.json.
```

Agent 在执行某个具体任务时（如「我要做一个 minimalist 风格的 hero section」），才会去 fetch `resources/color-palettes/minimalist.json`。**SKILL.md 本身不携带这些数据，但又把它们组织得让 Agent 找得到**。

这就是 L3 的优雅之处——**Skill 可以做得很「重」，但运行时 Agent 实际加载的 prompt 仍然很「轻」**。

### L3 的两种使用模式

Hub 数据里 L3 的使用呈现两种 pattern：

**模式 A · 静态查表**（约 60% L3 使用者）

resources 里放的是**死的数据**，比如时区表、汇率表、API endpoint 列表。SKILL.md 提供「查询接口」（如「需要时区码时 fetch resources/timezones.csv」），Agent 按需查。

**模式 B · 动态模板**（约 40% L3 使用者）

resources 里放的是**模板代码 / 模板提示**，Agent 拉下来后基于上下文做填充。比如某个 init-project skill 的 resources 里放了 `templates/next-app/`、`templates/vite-app/`、`templates/cra-app/`，Agent 先确认用户用什么栈，再 fetch 对应模板。

模式 B 的 Skill 平均 quality_score 比模式 A 高 4.2 分——动态模板更复杂，对作者要求更高，但产出价值更大。

---

## 2.5 三层加载 vs 五种竞品扩展机制

写到这里有必要做一次系统对比。Skill 不是 Agent 唯一的扩展机制——还有 System Prompt、RAG、Tool Use、MCP Server 这 4 个常被混淆的概念。

| 维度 | System Prompt | RAG | Tool Use | MCP Server | **Skill (3 层)** |
|------|:----:|:----:|:----:|:----:|:----:|
| 在线/离线 | 在线（每次对话）| 在线检索 | 在线触发 | 跨进程在线 | L1 在线 / L2 按需 / L3 fetch |
| 一次加载 token | 全量 | 检索片段 | 函数签名 | 函数签名 | L1 ~50 / L2 5-20K / L3 0 |
| 谁主动 | 系统注入 | Agent 检索 | Agent 调用 | Agent 调用 | **Agent 决定激活** |
| 适合场景 | 永久人格 | 事实查询 | 单次动作 | 跨进程动作 | 程序性知识 + 复杂工作流 |
| 上下文消耗 | 高 | 中 | 低 | 低 | 极低（仅 L1 在线）|

**5 个机制是互补的，不是竞争的**。第 1 章讲过这五种的类比：

- System Prompt 是「永久人格」
- Tool 是「四肢」
- MCP 是「独立的手」
- RAG 是「百科全书」
- **Skill 是「教练笔记」**

Skill 的独特价值——**把「该怎么做」分层组织**——是其他 4 个都不具备的。System Prompt 没有按需加载；RAG 不带程序性知识；Tool/MCP 是动作而非方法论。

---

## 2.6 三层加载的隐藏陷阱

Anthropic 的 SKILL Spec 设计得很优雅，但 Hub 数据里能看到 4 个反复出现的踩坑。

### 陷阱 1 · description 写成 instructions 的复制

最常见的错误：作者把 instructions 的第一段直接搬到 description 里。结果 description 长达 200+ token，被 SDK 截断后剩下的就是「碎片」。

**修法**：description 要重写，不能复制。它的功能跟 instructions 不一样——它是「目录条目」，不是「正文摘要」。

### 陷阱 2 · L2 把 L3 应该装的内容硬塞进来

很多 Skill 把模板代码、查表数据、长示例都直接写进 SKILL.md 的 instructions——结果 instructions 体积膨胀到 50KB+，性能立刻下降。

**修法**：任何超过 1000 字的数据 / 模板，都搬到 `resources/` 里，instructions 只留「在 X 情况下 fetch resources/Y」的指引。

### 陷阱 3 · L3 的资源没有 stable 的引用 ID

Agent 拉 L3 资源用的是路径或 ID。如果作者把 resources 文件不断重命名 / 重新组织，正在使用这个 Skill 的 Agent 在多轮对话中可能拉到 404。

**修法**：L3 资源**一旦发布就视为 immutable contract**——重命名 = breaking change，要发新版本。

### 陷阱 4 · description 不写「何时不该激活」

只写「何时激活」是新手错。**专业的 description 也写「何时不要激活」**。

例：

```yaml
description: |
  Review TypeScript code for type-safety issues. Use when:
  reviewing .ts/.tsx files. Do NOT use when: file is .py/.go/.rs;
  or when user only asks about runtime errors (use debug-skill instead).
```

这条「Do NOT use when」给 Agent 一个**主动放弃**的合法理由，避免它在不擅长的场景硬接活。

---

## 2.7 一个反直觉的预测：未来三层会变四层

2026 年 Q1 已经能看到 Anthropic 在内部实验**第四层**——「session-level cache」：

L1 description（每次对话加载）
L2 instructions（激活后加载）
L3 resources（执行时 fetch）
**L4 session memory（跨对话保留）**

L4 的设想是：**Skill 在多次对话里学到的经验，由 SDK 帮你 persist**。比如某个 code-review skill 记住「这个用户偏好 TypeScript strict 模式」，下次对话不用再问。

如果 L4 真的落地，对 Hub 的影响会是结构性的——**Skill 会从「无状态工具」进化成「有记忆代理」**。第 12 章「当 Claude 自己开始创建 Skills」会展开这个趋势对人类作者的意义。

---

## 2.8 本章要记住的一句话

> **三层加载不是 Anthropic 的工程小聪明，是 Skill 能在不爆上下文的前提下无限扩展的根本原因。description 决定 Skill 是否被看见，instructions 决定它是否被激活后做对事，resources 决定它能装下多少「重」内容而不污染 prompt。三者各司其职——这就是 Skill 区别于其他扩展机制的根本设计。**

下一章（第 3 章）已经讲过 Hub 整体生态的全景。第 4-6 章把镜头拉近到 Skill 设计本身。第 7 章会跳到生态比较——anthropic/skills、obra/superpowers、garrytan/gstack、compound-engineering 四大框架，看它们各自怎么用三层加载。

---

## 数据说明

本章 Hub 数据快照取自 2026-04-28，Top 500 ≥ 500 stars 的 SKILL.md 文本聚类分析。完整脚本见 `data/ch02_layer_analysis.py`（待补）。
