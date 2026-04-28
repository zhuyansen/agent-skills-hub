# 第 5 章｜迭代优化的闭环：从踩坑到飞轮

> 上一章用宝玉的四条哲学把"怎么写一个好的 Skill"讲清了。但即使你严格按 4 条哲学写出来的第一版 Skill，依然活不过 6 个月——如果你不建立**迭代机制**。
>
> 这一章讲 Skill 从"一次性产物"进化到"自我强化系统"需要的完整闭环。三个活案例：**NousResearch/autoreason 的 3 路锦标赛 + Borda 投票**（技术旗舰）、**LufzzLiz/news-aggregator 的 MISTAKES.md**（工程复盘派）、**Hub 原创数据**（持续 commit 的 skill 58.8% 还在涨 stars，冷冻的只有 3.8%，15× 差异）。
>
> 一个结论会贯穿全章：**Skill 的生命周期不是写出来的那一刻，是第 N 次更新的那一刻。**

---

## 5.1 为什么"写完就扔"这件事在 Skill 上特别致命

用一个常见场景来定义问题——

你写了一个 `code-review.skill`。装进 Claude Code。第一周：帮你发现了 3 个 bug，很爽。第三周：它对某类 TypeScript generics 判断错了，你手动修了一次。第二个月：你改了 prompt，效果好了一点。第四个月：你已经懒得打开这个 skill 了，因为修它比手动审 review 还累。

这个过程我在 AgentSkillsHub 里见过 2000+ 次。

Hub 的 62,000 条 skill 里，有一个数据特别刺眼——**把创建在 2025 年 4 月到 10 月之间（6-12 个月前）的 1000 个核心 skill 挑出来，23.7% 已经 90 天没有新 commit**。这 237 个 skill 不是没人看（median 209 stars），但它们**已经死了**——只有 3.8% 还在涨 stars，而持续迭代的那 76.3% 有 58.8% 仍在增长。

**15 倍的 star 生长率差距**。写完就扔和持续迭代之间，不是"差一点"，是**两个物种**。

这一章要回答：**如何让你的 skill 进到那 76% 的活着阵营**。

---

## 5.2 迭代的 3 个隐藏 bug（来自 Autoreason 论文）

2026 年 3 月底，NousResearch（SHL0MS + Hermes Agent）发了一篇叫 *Autoreason: Self-Refinement That Knows When to Stop* 的论文。这篇论文从数学层面揭示了**为什么"让 AI 自己改 AI 的输出"在大多数时候不 work**。

三个结构性 bug：

### Bug 1 · Prompt bias（批评偏见）

> "请帮我评价这个代码" → LLM 一定会找出缺点，即使代码是对的。

原因：模型被 "评价" 这个 prompt 触发，就会**自动寻找批评目标**，即使不存在。

这个 bug 直接解释了大多数 Skill 自我迭代机制失效的原因——你让 Claude "review" 自己上一次的输出，它**总会找出新问题**，然后"改进"，然后"改进"之前的"改进"……**最后输出退化**（autoreason 论文数据：Haiku 3.5 在 15 轮 critique-and-revise 后输出字数缩减 59-70%，完全丢失信息）。

### Bug 2 · Scope creep（规模蔓延）

每一次 "让 AI 改进 skill"，输出都比上一次**更长一点**。因为添加比删减容易，每次改进都倾向于"再加一条规则"。

Hub 数据能印证这一点——Top 500 里 README 从 <5KB 改到 >40KB 的 skill，**平均 quality_score 会从 48 降到 45**（见第 4 章）。不是加规则错了，是**加规则**没有对应地**减规则**。

### Bug 3 · Lack of restraint（缺乏克制）

最致命的一条。模型被训练成"helpful"——它**几乎从不会说"这次不用改"**。所以你每次让它迭代，它都会改点什么，**即使上一版已经够好了**。

这三个 bug 联合起来的结果是：**朴素的"让 AI 改 AI" 模式，迭代次数越多，质量越差**。

这是 Skill 自我迭代领域最反直觉的一个发现。也是为什么需要 autoreason 这种机制。

---

## 5.3 活案例 A · Autoreason 的 3 路锦标赛

Autoreason 给出的解法，干净得像一个数学公式——

```
当前版本 A  ←─────────────────┐
   │                            │
   ├─ 批评者（独立 agent）→ 批评  │
   │                            │
   ├─ 作者 B（独立 agent）→ 修订 B  │
   │                            │
   └─ 合成者（独立）→ 合成 AB    │
                                │
             3 个版本一起盲评    │
         (A 不变 / B 修订 / AB 合成)│
                ↓                │
           7 个评委 Borda 投票    │
                ↓                │
          赢家成为新的 A ─────────┘
          （A 连赢 2 次则收敛）
```

4 个关键设计：

### 1. "什么都不改"永远是一等选项

A（原版）跟 B（修订）、AB（合成）**平等参赛**。Bug 3（lack of restraint）就被这一条解决了——如果修订确实没改进，投票就会选 A，系统自然收敛。

### 2. 批评者、作者、合成者、评委都是"独立 agent"

每个 agent 都是 fresh context，**看不到别人的 reasoning**。这消除了 Bug 1（prompt bias）的级联放大。批评者不知道作者是谁，评委不知道谁是原作。

### 3. 三选一比二选一好

如果只让 A 和 B 对决，系统会陷入"要不要改"的震荡。**加一个 AB（合成版）**作为第三选项，让评委可以选"一部分改一部分不改"——这是收敛机制的关键。

论文消融数据：**去掉 B 或 AB 任何一个**，锦标赛在 2-3 轮就崩溃（本来 24 轮才收敛）。

### 4. Borda 投票，不是多数决

Borda count 让每个评委对 3 个版本**排序**而不是投票。这消除了"评委联盟"现象——哪怕某个版本大部分评委都觉得一般，只要它被排到第 2 的比例最高，它仍然可能赢。

### 冲击力的数据

| 配置 | 模型 | 任务 | 通过率 |
|------|:---|:---|---:|
| 单次生成 baseline | Haiku 3.5 | CodeContests | 31% |
| Autoreason（3 路 × Borda）| Haiku 3.5 | CodeContests | **40%** |
| Best-of-6 同算力 sampling | Haiku 3.5 | CodeContests | 31%（没提升）|
| Autoreason | Sonnet 4.6 | CodeContests | 77% vs 73% |

关键对比：**同样计算资源下，best-of-6 sampling 毫无提升，autoreason +9pp**。这说明**结构化的三路辩论**比**多跑几次取最好**优越——不是采样的问题，是**机制**的问题。

### 对 Skill 设计的启发

Autoreason 目前还是研究原型，但它的 3 路结构**可以被抽象成一个 Skill 文件**：

```markdown
---
name: skill-iteration-judge
description: When reviewing a proposed skill update, run 3-way tournament...
---

## Protocol
1. Keep current version (A) as incumbent.
2. Generate revision (B) from independent agent.
3. Generate synthesis (AB) from third agent.
4. Have 7 blind judges rank via Borda count.
5. Winner becomes new A. If A wins 2x consecutive, converge.

## Do Not
- Share agent context across roles.
- Assume "change is good" — A is always eligible.
```

这个 skill 还没有人完整实现（我在 Hub 里查过）。**第一个把 autoreason 机制做成 Skill 格式的人**，会拿到一个"自我迭代"类目的头部 share。

---

## 5.4 活案例 B · LufzzLiz/news-aggregator 的 MISTAKES.md

Autoreason 是技术旗舰，但**过于昂贵**——每次迭代要跑 3 个独立 agent + 7 个评委，10 个模型调用，一般小作者跑不起。

另一种迭代机制，成本低、可复制、最近被越来越多 Skill 作者采纳——**MISTAKES.md**。

`LufzzLiz/news-aggregator-skill`（1,001 stars）在 repo 根目录放了一个 6,319 字节的 `MISTAKES.md`，记录每次踩坑。每条都是四段式：

```markdown
## 📌 Issue: WallStreetCN Timestamp Ambiguity (2026-01-24)

### 1. The Error (错误现场)
"OpenAI Revenue... 1h ago"（但实际事件 12h 前）

### 2. Root Cause (根本原因)
Data Loss: 把 Unix timestamp 转成 "HH:MM" 破坏日期信息。

### 3. Fix (修复方案)
ALWAYS use full date-time:
datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')

### 4. Lesson (教训)
Don't format for "Human Readability" in the raw data layer.
```

这个简单做法解决了 3 个迭代 bug 里的 2 个：

- **解决 Bug 1**：不是让 AI 评价自己，而是**把已经发生的错误当作 ground truth** 写入。没有批评偏见的空间。
- **解决 Bug 2**：每次只为"真发生过的错"加规则。Scope 不会无缘无故扩张。
- **没解决 Bug 3**：这个 pattern 依然要求人工克制。

Hub 数据能量化这件事的效果——我搜了 Top 500 里 repo 根目录含有 `MISTAKES.md`、`LESSONS.md`、`POSTMORTEM.md` 这类文件的 skill（排除 fork 和模板），**只有 6 个**，但他们的平均 quality_score 是 **55.8**，比 Top 500 整体的 47.2 高 **8.6 分**。

6 个的样本很小，但信号清晰：**愿意系统化记录自己失败的人，做出来的东西整体更好**。

这也暗示了 MISTAKES.md 机制的**瓶颈**——它不是技术门槛，是**心理门槛**。大多数作者想展示自己的好作品，不想曝光自己踩过的坑。这个心理门槛在 Hub 数据里体现得淋漓尽致：**只有 1.2% 的 skill 作者做了这件事**。

对你的含义：**如果你做，你立刻就在 top 1%**。

---

## 5.5 活案例 C · Hub 数据 · 持续 commit 的生存曲线

Autoreason 是未来，MISTAKES.md 是现在，但还有一个更基础的问题：**一个 skill 到底要多积极地迭代，才算"活着"？**

我用 AgentSkillsHub Top 1000 的数据（cohort 是 2025-04 到 2025-10 创建的 skill，≥20 stars，观察窗口到 2026-04）做了一次生存分析：

### 核心发现

| 指标 | ACTIVE（last commit ≤ 90 天）| FROZEN（last commit > 90 天）|
|:---|:---:|:---:|
| 数量 | 763（76.3%）| 237（23.7%）|
| 中位 stars | 249 | 209 |
| 均值 stars | 2,637 | 642 |
| 平均 quality_score | 43.5 | 37.4 |
| **% 还在涨 stars** | **58.8%** | **3.8%** |

**最关键的一行是最后一行。**

持续迭代的 skill，**15 倍**于冷冻 skill 在获取新关注。这不是"差一点"的差距，是**活着和死了的差距**。

### 不同的 star tier，迭代率不同

| tier | 仍活 % |
|:---|---:|
| Top 10%（≥2,633 stars）| 92.0% |
| Bottom 50%（≤235 stars）| 74.5% |

**高质量 skill 的作者更可能继续维护**（有反馈正向激励），低星 skill 的作者更容易放弃。这是典型的**马太效应**，也是为什么 Hub 里 54% 的 skill 是 0 star——**它们在第一周没有被看见，就永远不会被看见了**。

### 按年龄看生存率

| 创建月龄 | 样本 n | 仍活 % |
|:---:|---:|---:|
| 6 个月 | 175 | 80.6% |
| 7 个月 | 127 | 83.5% |
| 8 个月 | 151 | 79.5% |
| 9 个月 | 158 | 77.2% |
| **10 个月** | 189 | **69.3%** ⚠️ |
| 11 个月 | 161 | 69.6% |
| 12 个月 | 39 | 79.5%（小样本）|

**死亡拐点在 10 个月**。6-9 个月生存率稳定在 77-83%，第 10 个月跌到 69%，跌幅 8-10 个百分点。

这跟 SaaS 产品的 churn 曲线结构很像——早期月度流失稳定，某个点后开始显著加速。对 Skill 作者来说，**第 10 个月是最关键的 retention 窗口**。错过这个窗口，流失率会一直衰减下去。

（生存曲线的 matplotlib 可视化见 `data/ch05-fig1-survival-curve.png`）

### 可操作的含义

给 Skill 作者的 3 条建议：
1. **第 10 个月之前至少更新 1 次**——即使只是 README 改字。这会把你推出 "frozen" 分类。
2. **把"第 6 个月复盘"放进日历**。6 个月时你还有 20-25% 的同龄人停更了，此时维护有最高相对优势。
3. **一个 update cadence 的新规则**：每 90 天必须 commit 一次，哪怕只是 typo 修正。系统不关心你 commit 了多少，它只关心"还在呼吸"。

---

## 5.6 三个机制如何组合使用

不需要三个都用，但**一个都不用基本等于赌命**。

一个现实的成长路径（对 Skill 作者）：

```
Month 1:  写第一版 skill。照第 4 章四哲学做。
Month 2:  收集真实使用反馈。建 MISTAKES.md，记 3-5 条。
Month 3:  把 MISTAKES 里的 "Fix" 写回 SKILL.md。
Month 4-6: 每月至少 1 次 commit（Hub 数据告诉你这件事）。
Month 6: 如果 Skill 涨到 >100 stars，考虑上 autoreason 式的
         3-路评估机制（自动化）。如果 <100 stars，
         保持 MISTAKES 习惯就够了。
Month 10: 做一次大复盘。如果这时候不做，大概率会
          滑进 frozen 阵营。
```

**三个机制是递进的**：
- MISTAKES.md 是**手动 + 诚实**
- 规律 commit 是**手动 + 律己**
- Autoreason 是**自动 + 无记忆**

对大多数 Skill 作者，**MISTAKES.md + 每 90 天 commit 就够了**。Autoreason 只对 Top 1% 的 skill 值得投入。

---

## 5.7 自我解剖：迭代也会杀死 skill

这一章一直在夸迭代。最后要泼一盆冷水。

**过度迭代的 skill 同样危险**。

Hub 里有几个典型的"迭代死亡"例子——作者每周都 commit，但每次都在**加新规则 / 改措辞 / 重构结构**。结果：

- SKILL.md 从 5KB 涨到 50KB（超过第 4 章发现的 sweet spot）
- 每次用户装新版本，都要重新记忆新规则
- Agent 执行时**规则互相矛盾**（新规则没跟旧规则对齐）
- quality_score 从 60 降到 45

**迭代是双刃剑**。好的迭代是**定点修复 + 删减冗余**，坏的迭代是**无限追加**。

一个简单的自查 checklist：

- ✅ 每次 commit 至少删掉 1 行旧内容，或修复一个具体 bug
- ✅ 有人反馈问题之后再迭代，不是"心血来潮"
- ✅ 重构前先看 MISTAKES.md 里记过的坑，别重蹈覆辙
- ❌ 不是每次 Claude / Cursor 新版本都要改 skill
- ❌ 不是看到别人写了一条有意思的规则就抄进来
- ❌ 不是"好久没 commit 了，随便改一下"——这种 commit 比不 commit 更糟

---

## 5.8 本章要记住的一句话

> **Skill 的生命周期不是写出来那一刻，是第 N 次更新的那一刻。持续 commit 的 skill 58.8% 在涨 stars，冷冻的只有 3.8%——这不是差距，是阵营差别。**
>
> **三个迭代机制：MISTAKES.md（诚实成本）、规律 commit（律己成本）、Autoreason（算力成本）。大多数人做前两个就够。但一个都不做，你的 skill 10 个月内就会死。**

---

## 5.9 下一章预告

第 6 章开始换一个视角——**从"怎么写一个好 Skill"转到"Skill 的整个类型学"**。

Hub 里 62,000+ skill 大致可以分成 9 种类型（库参考 / 数据获取 / scaffolding / CI-CD / monitoring / composition / meta 等），每种类型的分布、平均 stars、死亡率都不一样。

也会引入 Anthropic 提到但未展开的**"4 级分享路径"**——个人用 / 项目用 / 团队用 / 全球用。这两个维度（9 × 4）画出的矩阵，决定了**任何 Skill 作者都应该问自己一个问题：我这个 skill 应该面向哪个格子？**

下一章见。

---

**数据说明**：本章所有 Hub 数据取自 2026-04-24 AgentSkillsHub 快照，cohort 是 2025-04-24 到 2025-10-24 之间创建的 stars ≥ 20 的 skill，共 1000 条。完整 Python 分析脚本见 `data/ch05_survival_analysis.py`。

**下一章**：[第 6 章 · 9 种 Skill 类型 × 4 级分享路径](ch06-types-and-tiers.md)
