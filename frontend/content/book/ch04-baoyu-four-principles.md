# 第 4 章｜站在 Agent 角度设计 Skill：宝玉四条哲学的活案例

> 上一章用 Mahesh 和 Barry 讲清了 Skill 要解决什么。这一章往下一步——**该怎么写一个好的 Skill？**
>
> 国内 AI 圈讨论 Skill 设计最系统的是宝玉。他在多篇文章、推文里零散提出过 4 条设计哲学——**Agent 视角、原子化、Skill 自我迭代、脚本优先**。这 4 条听起来抽象，但如果拿 AgentSkillsHub 里 62,000+ 条 skill 做对照，会发现每一条都有对应的实践样本。
>
> 本章用 3 个活案例——`emilkowalski/skill`、`Leonxlnx/taste-skill`、`cclank/news-aggregator-skill`——把 4 条哲学落到可观察的代码和数据上。另外用 Hub Top 500 的真实数据，验证"原子化"这件事到底是玄学还是可测量的工程规律。

---

## 4.1 为什么要从"Agent 视角"写 Skill

大多数人写 Skill 的时候，脑子里想的是"我怎么给人解释这件事"。宝玉反复强调一个反直觉的操作——**要从 Agent 的视角去写，不是从人的视角**。

这个差异看起来微小，实际决定生死。

**人视角的 Skill**（错误示范）：

```markdown
# 代码审查助手

这个 skill 帮你做代码审查。

## 怎么用

按需使用即可。
```

**Agent 视角的 Skill**（对的示范）：

```markdown
---
name: code-review
description: Review code for bugs, style, and maintainability. 
  Use when: (1) user explicitly asks for code review, (2) user shares code 
  and says "look at this", (3) before any git commit / PR creation.
---

## Required Output Format

You MUST output a markdown table:

| File:Line | Severity | Issue | Suggested Fix |
| --- | --- | --- | --- |

Do NOT use prose. Do NOT use bullet lists. Use the table format above.

## Before You Start
1. Run `git diff HEAD` first to see what changed
2. If no diff, run `git log -5` to identify last 5 commits
3. Only review files that actually changed
```

两者的差异不是长度，是**对"读者"的假设**。

人写 Skill 时默认读者"会察言观色"——看到"按需使用"能自己推断什么是"按需"。Agent 不会。Agent 需要**显式触发条件**（when）、**显式输出格式**（MUST use table）、**显式前置步骤**（run git diff first）。

### 活案例 · `emilkowalski/skill`

2026 年 3 月出现的一个被低估的 skill——894 stars、1 个 SKILL.md、27KB。作者是 Sonner、Vaul、next-view-transitions 的作者 Emil Kowalski，React 设计工程圈的顶流。

他的 SKILL.md 里有一段让我停下来读三遍的东西：

```markdown
## Review Format (Required)

When reviewing UI code, you MUST use a markdown table with 
Before/After columns. Do NOT use a list with "Before:" and "After:" 
on separate lines. Always output an actual markdown table like this:

| Before | After | Why |
| --- | --- | --- |
| `transition: all 300ms` | `transition: transform 200ms ease-out` 
  | Specify exact properties; avoid `all` |
| `transform: scale(0)` | `transform: scale(0.95); opacity: 0` 
  | Nothing in the real world appears from nothing |
```

注意几个细节：

1. **Required** 而不是 "recommended"——不给 Agent "看情况" 的余地
2. **示例 Before/After/Why 三列**——强制结构
3. **"Do NOT use prose"**——明确排除 Agent 最容易堕落的回答方式（废话）
4. **`Nothing in the real world appears from nothing`**——给 "为什么" 附带可记忆的认知 anchor，帮 Agent 理解而不是死记

这份 SKILL.md 是"把人的 craft sensibility 翻译成 Agent 可读 enforce 规则"的经典样本。

### Hub 数据里 Agent 视角的痕迹

我筛了 Hub Top 500（≥500 stars）里，description 字段里含有 **"Use when"**、**"MUST"**、**"must use"** 这三个关键短语的 skill——它们是 Agent 视角的 telltale signs：

| description 特征 | 占比 | 平均 quality_score |
|---|---:|---:|
| 含"Use when / MUST" | 23% | **51.8** |
| 普通叙事型 | 77% | 44.1 |

**相差 7.7 分。** 在 Hub 的 0-100 质量评分体系里，7.7 分接近一个 tier 的差异（B 变 A）。

这是 Hub 数据第一次直接验证了宝玉的 "Agent 视角" 论断——**不是玄学，是可测量的工程规律**。

---

## 4.2 原子化：不是最小化，是"单一目的 + 充分文档"

宝玉第二条哲学是 **原子化**——一个 Skill 只做一件事，不要搞成大而全。

但这里有个普遍误解：**原子化 ≠ 越短越好**。

我用 Hub Top 500 的 README 大小做了一次 bucket 分析：

| README 大小 | skill 数 | 平均 quality | 平均 stars |
|---:|---:|---:|---:|
| **<2KB** | 102 | **36.3** 🔴 | 7,406 |
| 2-5KB | 36 | 45.6 | 24,201 |
| 5-10KB | 109 | 48.2 | 18,221 |
| **10-20KB** | 122 | **51.4** 🏆 | 21,695 |
| 20-40KB | 88 | 48.8 | 19,216 |
| **40KB+** | 43 | **45.2** 🔴 | 35,186 |

这张表说了两件事：

**1. 太小（<2KB）的 skill 反而质量最低**——36.3 分，低于所有其他 bucket。这些 skill 往往是 "一句话描述 + 一个 npm install"，对 Agent 来说信息量不够。

**2. 最优区间是 10-20KB**——51.4 分是全样本最高。这个区间里能塞下：单一 description、2-3 段 instructions、触发条件、输出格式、1-2 个反例、失败处理。

**3. 超过 40KB 反而下降**——因为 Skill 开始塞多个功能（scope creep），Agent 不知道什么时候激活它。

Pearson r(README size ↔ quality_score) = +0.249，说明正相关但不线性——存在 sweet spot，不是越大越好。

### 活案例一 · `emilkowalski/skill`（极简派原子化）

27KB、1 个 SKILL.md、目标只有 "UI 设计工程的品味"。整个 skill 不做别的事——不教你写业务逻辑、不教你部署、不教你性能优化。

**只管 UI 动画和细节。**

这就是原子化的一种：**维度收窄到极致**。代价：你用它做业务逻辑 review 时毫无用处。价值：做 UI 相关工作时能压到非常高的质量上限。

### 活案例二 · `Leonxlnx/taste-skill`（9 个变体的原子化）

同样做"前端品味"这件事，但 Leon 选了另一条路——**拆成 9 个相关 skill**：

```
taste-skill         通用
gpt-taste           给 GPT/Codex 的严版
images-taste-skill  先生图再落地
redesign-skill      改造老项目
soft-skill          奢侈感
minimalist-skill    Notion/Linear 风
brutalist-skill     Swiss typography 硬派
output-skill        反懒惰（强制完整实现）
stitch-skill        Google Stitch 兼容
```

每个 skill 主功能都是"让 AI 写前端"，但**使用场景不同**——你要改造老项目时激活 `redesign-skill`，要做极简 UI 时激活 `minimalist-skill`。

这是另一种原子化：**不是单一文件，是单一激活场景**。一个工具箱而不是一把瑞士军刀。

Leon 的做法另一个有意思的点——**每个 skill 顶部有 3 个可调参数**：

```
DESIGN_VARIANCE:   1-10 (对称→艺术混乱)
MOTION_INTENSITY:  1-10 (静态→电影级物理)
VISUAL_DENSITY:    1-10 (画廊→飞行员驾驶舱)
```

一个 skill 通过参数化变成 1000 种输出，但核心身份（taste-skill）没变。这是**原子化 + 参数化**的组合——宝玉哲学的一个变奏。

### 两种原子化的数据对比

| | emilkowalski | Leonxlnx/taste-skill |
|---|---:|---:|
| Skill 数 | 1 | 9 |
| 主文件大小 | 27KB | 21KB (taste-skill) |
| Stars（2026-04）| 894 | 12,051 |
| 2 个月星增 | +894 | +12,051 |
| Fork:Star | 8% | 9% |
| Style | 哲学禅意 | 法条主义 |

**市场结果**：Leon 的 13× 更多 stars。

这不是说原子化做大就赢。是说**原子化 + 营销叙事**（Leon 的 "Anti-Slop" meme）的组合比纯原子化传播力更强。**这是宝玉哲学没讲但 Hub 数据直接能看到的一层**。

---

## 4.3 Skill 自我迭代：把踩过的坑写进文件

宝玉第三条哲学——**Skill 应该具备自我迭代能力**。

翻译成人话：**当 Agent 在某个任务上踩了坑，应该把这次踩坑的经验写回 Skill，下次不再踩**。

这个看似简单，但 Hub 里真正这么做的 Skill 不到 3%。

### 活案例 · `cclank/news-aggregator-skill`

1,001 stars、Python、MIT license 缺失但代码质量高。这个 skill 的独特之处是——作者在 repo 根目录放了一个 `MISTAKES.md`，长达 6,319 字节。

内容摘录：

```markdown
## 📌 Issue: WallStreetCN Timestamp Ambiguity (2026-01-24)

### 1. The Error
"OpenAI Revenue... 1h ago"（但实际事件 12h 前）

### 2. Root Cause
Data Loss: 把 Unix timestamp 转成 "HH:MM" 破坏日期信息。
Context Dependent: "09:35" 只在你知道是今天时有意义。

### 3. Fix
ALWAYS use full date-time format:
datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')

### 4. Lesson
Don't format for "Human Readability" in the raw data layer. 
Let the UI decide how to display.
```

这份 MISTAKES.md 里有 7 个这样的 case，每个都是**错误现场 → 根本原因 → 修复方案 → 预防教训**的四段式结构。

这是真正的自我迭代——作者不只是修了 bug，还**把 bug 的元信息写进 skill 能读到的地方**。下次 Agent 处理 timestamp 时会看到这条规则，不再犯同样的错。

### 为什么这种做法很稀有

Hub Top 500 里，repo 根目录含有 `MISTAKES.md`、`LESSONS.md`、`POSTMORTEM.md` 这类文件的 skill 只有 **14 个（2.8%）**。其中 8 个是 fork 或模板，真正主动记录的只有 **6 个**。

为什么这么少？三个原因：

1. **反直觉**：写 Skill 时大多数人想"展示成功"，不是"承认失败"
2. **看似无用**：MISTAKES.md 不直接让 Agent 更聪明，是"第二阶元数据"
3. **要求作者有工程习惯**：不是 vibe coder 能持续做的

但有意思的是——**这 6 个主动记 MISTAKES 的 skill，平均 quality_score 是 55.8**，比 Top 500 整体平均（47.2）高 8.6 分。

样本小，但信号清晰：**愿意写 MISTAKES.md 的作者，整体工程素养也更高。**

这解释了为什么宝玉把 "自我迭代" 列为四条之一——**它不是技术动作，是一种工程品性的外化**。

---

## 4.4 脚本优先：能用代码不要用描述

第四条哲学——**脚本优先**。能用可执行脚本表达的约束，不要用自然语言描述。

原因：自然语言有歧义，脚本没有。

### 活案例 · `Leonxlnx/taste-skill` 的硬编码常量

回到 taste-skill。Leon 没有让 Agent "自己判断合适的动画时长"，而是**把时长表直接写进文件**：

```javascript
// From taste-skill/SKILL.md
transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1)
```

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);  /* iOS 风 */
```

这种写法背后的逻辑：**让 Agent 复制粘贴比让它"自己想一个"更可靠**。

对比 `emilkowalski/skill` 里的同类规则：

```markdown
| Element                  | Duration      |
| ------------------------ | ------------- |
| Button press feedback    | 100-160ms     |
| Tooltips, small popovers | 125-200ms     |
| Dropdowns, selects       | 150-250ms     |
| Modals, drawers          | 200-500ms     |
```

这也是"脚本优先"的另一种形态——**把模糊的"快一点、慢一点"变成可 lookup 的表**。Agent 不用想，只要查。

### 为什么这很关键

Skill 的输出质量直接取决于 **Agent 能多快找到确定答案**。

- 如果 Skill 说 "动画要自然一点"——Agent 会自己发挥，结果方差大
- 如果 Skill 说 "动画用 200ms cubic-bezier(0.23, 1, 0.32, 1)"——Agent 直接复用，结果稳定

工程上叫 **"把决策从运行时挪到编辑时"**——越多决策在你写 Skill 时就做完，Agent 运行时越不容易翻车。

### Hub 数据的佐证

我检索了 Top 500 里 SKILL.md（或主 instruction 文件）中包含以下模式的 skill：

- ≥3 处明确代码块 (` ``` `)
- ≥1 个查询表（markdown table 格式）
- 至少一个硬编码常量

| 特征 | 占比 | 平均 quality |
|---|---:|---:|
| 含"硬编码脚本"特征 | 41% | **52.3** |
| 仅自然语言描述 | 59% | 44.6 |

**相差 7.7 分**——跟 Agent 视角那条几乎一模一样的 delta。

这两条（Agent 视角、脚本优先）实际上是**同一件事的两面**：从 Agent 的视角出发 → 必然得出"脚本比描述可靠"的结论。

---

## 4.5 三角对比：三条路线的互补

把三个活案例放到一张表里做总览：

| 维度 | emilkowalski | Leonxlnx/taste-skill | cclank/news-aggregator |
|---|:---:|:---:|:---:|
| **Agent 视角** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **原子化** | ⭐⭐⭐⭐⭐（单文件）| ⭐⭐⭐⭐（9 变体）| ⭐⭐⭐⭐ |
| **自我迭代** | ⭐⭐（课程外置）| ⭐⭐⭐（版本迭代）| ⭐⭐⭐⭐⭐（MISTAKES.md）|
| **脚本优先** | ⭐⭐⭐⭐⭐（常量表）| ⭐⭐⭐⭐⭐（dial 参数化）| ⭐⭐⭐⭐（Python 脚本主导）|
| **主要风格** | 禅意 / 哲学 | 法条 / 执念 | 工程 / 复盘 |
| **传播力（stars）** | 894 | **12,051** | 1,001 |

**读这张表的方式不是"谁赢"，是"四条哲学各自擅长什么场景"**：

- 做**视觉体验**类 skill，学 emilkowalski——禅意决策框架 + 时长常量表
- 做**操作类 / 生成类** skill，学 Leon——参数 dial + 强制 ban list
- 做**数据处理 / 分析类** skill，学 cclank——工作流 + MISTAKES 归档

三个案例**都严重低于 License**（emilkowalski 和 taste-skill 无 license，cclank 无 license），这是生态的系统性问题——**12K stars 的 skill 在法律上不能被企业采用**。第 10 章"Verified Creator"会展开这个话题。

---

## 4.6 4 条哲学的合集效应

把宝玉四条哲学按照**可测量性**重新排列：

| 哲学 | Hub 数据里的 delta | 说明 |
|---|---:|---|
| Agent 视角 | **+7.7 分** | "Use when / MUST" 类描述 vs 普通描述 |
| 脚本优先 | **+7.7 分** | 含硬编码脚本/查表 vs 纯描述 |
| 原子化 | **+15 分** | <2KB 组（36.3）vs 10-20KB 组（51.4）|
| 自我迭代 | **+8.6 分** | 含 MISTAKES.md vs 整体均值 |

**4 条不是独立相加，但也不是完全重叠。** 一个 skill 同时具备 3-4 条的概率约 8%，这 8% 的 skill 平均 quality_score 达到 **63.4**——比 Top 500 整体的 47.2 高 16 分，几乎是两个 tier 的差异。

**一句话**：宝玉的四条哲学**每一条单独都有统计学意义，叠加时还有放大效应**。

不是口号，是可验证的工程规律。

---

## 4.7 自我反省：这 4 条不够用的地方

作为自我解剖，必须承认**宝玉四条哲学不能解释一切**。

### 限制 1：解释不了"破圈传播"

emilkowalski 内容质量极高但 stars 才 894。taste-skill 质量相似但 stars 12K。差异主要来自 **"Anti-Slop" 这个 meme 的传播力**——这**不是一条能写进 skill 的哲学**。

品味、技术、文档、迭代 4 条哲学加起来解释质量的 **20%-30%**。剩下的 70% 是——**时机、营销、社区、运气**。

### 限制 2：没法量化"创造性"

emilkowalski 的 `transform: scale(0.95); opacity: 0` vs `transform: scale(0)` 这种 insight——**来自 20 年 craft 沉淀**。4 条哲学能帮你组织这个 insight，但不能帮你产生它。

**Skill 质量上限 = 作者认知上限**。这句话宝玉也提过，但具体到量化就很尴尬——你没法打分"作者的 20 年经验"。

### 限制 3：对新人不友好

这 4 条其实都是**事后规律**。新人写第一个 skill 时，既不知道"Agent 视角"是什么，也不会有"MISTAKES.md" 可记——因为还没踩坑。

一个更现实的新人工作流可能是：

```
写一个糟糕的 skill → 装到 Claude Code → 看它失败 → 
修 README → 再次失败 → 加硬编码规则 → 成功一次 → 
继续用 → 遇到新坑 → 加新规则（这就是 MISTAKES.md 的前身）
```

**4 条哲学是这个循环收敛后的总结，不是起点**。

---

## 4.8 本章要记住的一句话

> **Skill 的质量不在 "写得漂亮"，在 "Agent 能不能直接执行"。Agent 视角 + 原子化 + 自我迭代 + 脚本优先 这四条，是让 Skill 从 "像对人写的文档" 进化成 "给 Agent 用的工具" 的最短路径。**

下一章讲**迭代优化的闭环**——Skill 从第一次写出来到持续进化，中间需要怎样的 feedback loop？会用 NousResearch 新发的《Autoreason》论文里的 3-路锦标赛 + Borda 投票机制，作为"Skill 自我迭代"机制的技术前瞻。

---

**数据说明**：本章所有 Hub 数据取自 2026-04-24 AgentSkillsHub 快照，Top 500 ≥500 stars。完整 Python 分析脚本见 `data/ch04_atomicity.py`。

**下一章**：[第 5 章 · 迭代优化的闭环：从踩坑到飞轮](ch05-iteration-loop.md)
