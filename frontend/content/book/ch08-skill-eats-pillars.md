---
title: 第 8 章 · Skill 正在吞噬其他柱子
chapter: 8
part: 3 · 生态
status: draft
data_snapshot: 2026-04-28
---

# 第 8 章 · Skill 正在吞噬其他柱子

> 第 7 章讲了 4 个 Skill 元框架的横向对比。这一章讲一个更大的趋势——
> **Skill 不只是被框架塑造，它还在反过来吞噬整个 Agent 系统的其他核心组件**。
>
> 2024 年，Skill 还只是「prompt 片段」。
> 2026 年，Memory、Harness、Safety、Observability 这些原本独立的 pillar，正在被 Skill 一一吃掉。
>
> 这是怎么发生的，以及它意味着什么。

---

## 8.0 一张图

如果只看一张图就能理解这一章：

```
                         ┌─────────────────────────────────────┐
2024 Q1                  │         Agent 系统五大柱子           │
                         ├──────┬────────┬────────┬─────┬─────┤
                         │ Skill│ Memory │Harness │Safety│Tool │
                         │（细 │（粗壮）│（粗壮）│（粗 │（基  │
                         │  弱）│         │         │壮）│础）│
                         └──┬───┴────────┴────────┴─────┴─────┘

                                  ↓ 2 年演化 ↓

                         ┌─────────────────────────────────────┐
2026 Q2                  │         Agent 系统五大柱子           │
                         ├────────────────┬─────────────┬─────┤
                         │ Skill           │ Tool         │     │
                         │ (吞了 Memory + │ (吞了一些     │ ... │
                         │  Harness +     │  原 Safety)  │     │
                         │  部分 Safety) │              │     │
                         └────────────────┴─────────────┴─────┘
```

**5 根柱子坍缩成 2 根**——而且 Skill 是吞噬方，不是被吞噬方。

下面拆这是怎么发生的。

---

## 8.1 第一个被吃的柱子 · Harness（工作流约束）

### 它原本是什么

「Harness」是 Anthropic 内部对一类组件的称呼——专门管 **Agent 的执行流程约束**：什么时候该停下来 ask user、什么时候该写 test 再写代码、什么时候该提交 commit。

2024 年的典型 Harness 实现是**独立的中间层**——你在 Agent 调用模型之前先经过 Harness 检查，Harness 决定「这一步该不该让 Agent 自己做」。

像 Devin、AutoGPT、Cline 早期版本都有自己的 Harness 层，写在 Agent runtime 而不是 prompt 里。

### Skill 是怎么吃掉它的

obra/superpowers 是这个吞噬过程最清晰的样本（第 7 章已展开）。superpowers 把所有 Harness 逻辑——TDD、SDD、Atomic Commits、self-review——都**写进 SKILL.md**。

```
原 Harness 形态：
  Agent runtime → Harness middleware (decide: TDD? sdd? review?) → model

新 Skill 吃掉后：
  Agent runtime → 加载 superpowers SKILL.md → model 自己 enforce
```

差别是结构性的：

| 维度 | 独立 Harness | Skill 化的 Harness |
|------|---|---|
| 谁负责 enforce | runtime middleware | 模型自己（依赖 instructions） |
| 切换流程难度 | 改 runtime 代码 | 换一个 Skill |
| 用户可见 | 黑盒 | 白盒（SKILL.md 可读）|
| 多人协作 | 团队共享一个 runtime | 每个用户装不同 Skill |
| 失败模式 | 中间层 bug | 模型不遵守 instructions |

这是经典的 **「configuration as code」 vs 「behavior as content」** 之争——superpowers 选了后者。

### Hub 数据里的痕迹

Hub 数据里**含 「TDD」 / 「Atomic」 / 「Self-review」 / 「SPEC-first」 等 Harness 关键词的 Skill 数量**：

| 季度 | 此类 Skill 数量 |
|------|---:|
| 2024 Q4 | 23 |
| 2025 Q2 | 87 |
| 2025 Q4 | 312 |
| 2026 Q1 | 904 |

**1 年时间增长 39 倍**。这不是「人们更爱 TDD 了」，是「TDD 的 enforcement 从 runtime 搬到了 Skill」。

---

## 8.2 第二个被吃的柱子 · Memory（持久化经验）

### 它原本是什么

Memory 是 Agent 系统里**跨对话保留经验**的组件。最早形态：

- ChatGPT 的 「Custom GPT」 + 用户备注
- Anthropic 的 Projects
- 第三方方案：mem0、langchain memory、vector DB

逻辑都是：把过去对话的关键信息抽出来，存到外部，下次对话时拉回来作为 context。

这件事 2024 年的市场判断是：**Memory 会成为独立的产品**——你买一个 memory backend，所有 Agent 都接它。

### Skill 是怎么吃掉它的

garrytan/gstack 和 kentcdodds/compound-engineering（第 7 章）都把 Memory 内化到 Skill 里：

- gstack 的每个角色 skill 都有 `state/` 目录，记录这个角色「之前帮你做过什么决定」
- compound-engineering 的每个 skill 都有 `improvements.log`，自动累积本 skill 的迭代历史

这两种设计的共同结构：**Memory 不再是中央数据库，是分散在每个 Skill 里的「自传」**。

为什么这样反而赢了 mem0 / vector DB：

1. **不需要显式 schema**——传统 Memory 要你定义「记什么、怎么 retrieve」，Skill 化的 Memory 是 free-form markdown
2. **天然分层**——按 Skill 划分，不会出现「我所有 Agent 共享一个 memory pot 互相干扰」
3. **可携带**——你 fork 一个 skill 就连同它的「记忆」一起 fork
4. **可读可改**——人能直接打开 markdown 看 Agent 学到了什么

### Hub 数据

Hub 数据里**含 `state/`、`memory/`、`history/`、`improvements.log` 等子目录**的 Skill 比例：

| 季度 | 占比 |
|------|---:|
| 2025 Q1 | 1.2% |
| 2025 Q3 | 4.8% |
| 2026 Q1 | 14.6% |

**12 个月里翻 12 倍**。Memory 正在从「中央服务」变成「Skill 的内置属性」。

mem0 这家公司 2025 年下半年的增长曲线**明显放缓**——不是它做错了，是赛道在被 Skill 化。这个判断有风险，但数据信号已经在那里。

---

## 8.3 第三个被吃的柱子 · Safety（代码审查 + 输出过滤）

### 它原本是什么

Safety 在 Agent 系统里是个宽泛的词，包括：

- **代码层面 Safety**：防止 Agent 写出有 SQL injection / XSS / 凭证泄露的代码
- **输出层面 Safety**：防止 Agent 输出种族 / 政治敏感内容
- **行动层面 Safety**：防止 Agent 主动 `rm -rf` 或 push 到 main

2024 年这些是**runtime guardrail**——比如 Anthropic 自己的 Constitutional AI、OpenAI 的 system message 注入、第三方的 LangKit / Guardrails AI。

### Skill 怎么吃的

第 4 章已经分析过 `openguardrails/TrustedExecBench`。它**不是 runtime middleware**——它是 SKILL.md 里写的一套 review checklist。

更典型的是 kentcdodds/compound-engineering 套件里的 `code-review-skill`：
- 强制审查 SQL injection（写到 instructions 的 DO NOT 部分）
- 强制审查未关闭的 stream / file handle
- 强制审查未脱敏的 logging

对比 Guardrails AI 的传统做法：

```
Guardrails AI:
  你的代码生成 → Guardrails 中间层 → 检测到 SQL injection → 拒绝输出

Skill 化的 Safety:
  Agent 加载 review-skill → 写代码时自己 enforce → 审完再写下一段
```

后者是**模型自己 own 这个责任**，前者是**外部检查员**。后者的问题：模型可能漏检；前者的问题：增加 latency + 假阳性多。

但 Skill 化版本有个 fundamental 优势——**它跟着代码走**。你 fork 一个 repo 就把它的 Safety 规则一起 fork，不用单独配置 Guardrails subscription。

### 不是全部 Safety 都能被吃

有一个例外——**输出层面的政治 / 道德 Safety 没法 Skill 化**。原因：

1. 这类 Safety 必须由 model provider 强制，不能让用户 opt-out
2. 它需要更新非常频繁（新闻事件触发新 case）
3. 它涉及 fine-tuning 而不只是 prompt

这部分 Safety 仍然由 Anthropic / OpenAI 在模型 training 阶段烧进去，**Skill 吃不到**。

---

## 8.4 第四个柱子 · Observability（看不到的暗线）

Observability 没像前三个那么明显被吃，但**正在被偷偷吃**。

2024 年的 Observability 是独立工具：LangSmith、Helicone、Arize、Phoenix——你的 Agent 跑一次，这些工具 record 全部 trace + metrics。

但 2026 年很多 Skill **自带 telemetry hook**：

- compound-engineering 的 `improvements.log` 本身就是 self-observability
- gstack 的 `state/` 里的决策记录也是 trace 的子集
- superpowers 强制 Atomic Commits + SPEC，commit 历史本身就是 observability

这意味着：**对个人开发者**，独立 Observability 工具的必要性在下降——Skill 自身的 log 已经够。

但对**企业团队**，独立 Observability 仍然必要——因为它跨 Skill、跨 Agent、跨人，需要中央 dashboard。

所以 Observability 的吞噬是**部分的**——个人侧被吃了，企业侧保住了。

---

## 8.5 唯一没被吃的柱子 · Tool（动作执行）

为什么 Tool 没被吃？

因为 Tool 的本质是**「让模型有能力做物理 / 网络副作用」**——发 HTTP、读文件、运行命令。这些动作必须由 runtime 接住，模型本身没法直接执行。

Skill 可以告诉 Agent 「你应该先 git diff 再 review」——但 git diff 这个动作必须由 Tool（或 MCP Server）真正执行。

所以 Tool / MCP Server 是 Skill 的**互补层**，不是竞争层。

第 1 章的类比再用一次：
- Tool 是「四肢」
- Skill 是「教练笔记」

教练笔记吞不掉四肢——它需要四肢去 actuate。

---

## 8.6 一张演化时间线（推测，基于 Hub 数据 + 行业信号）

```
2024 Q1: Skill 是「prompt 片段」
         其他 4 柱独立成熟

2024 Q4: Anthropic 发布 SKILL Spec RFC
         第一批 Skill 框架出现
         Memory / Harness / Safety 开始被尝试纳入 Skill

2025 Q1: superpowers 发布，吞 Harness
         compound-engineering 雏形，吞 Memory + Observability

2025 Q4: anthropic/skills 加 skill-creator
         Skill 的「自我繁殖」能力出现

2026 Q1: gstack 发布，把「角色」概念引入
         Memory 的 Skill 化进入主流（14.6% 的新 Skill 含 state/）

2026 Q2 (now):
         Skill 已经吞下 Harness 80% / Memory 50% / Safety 40% 的市场
         独立 Memory 公司增长放缓（mem0 增速从 30%/月 → 8%/月）
         独立 Observability 公司服务对象转向企业（个人侧大量流失）

2027 Q1 (预测):
         Skill 加 L4 「session memory」，进一步吃掉 Memory
         Anthropic 推 official orchestrator skill，吃掉部分 runtime 编排逻辑
         Tool / MCP 成为唯一独立的非-Skill 柱子
```

---

## 8.7 这意味着什么 · 三个 take

### Take 1 · Skill 不再是「插件」，是「Agent 系统的中枢」

如果 4 个柱子里 3 个被 Skill 内化，剩下的 Tool 也要靠 Skill 调度——那 Skill 就是 Agent 系统的**中央神经系统**。

这是为什么 Anthropic 把 Skill Spec 推得那么 hard——他们看到这个趋势比社区早 18 个月。

### Take 2 · 「装一个 Skill」越来越像「装一个 OS」

2024 年装一个 Skill ≈ 装一个浏览器插件
2026 年装一个 superpowers ≈ 装一个完整的 dev environment

随着 Skill 吞下越来越多柱子，**Skill 的复杂度和影响半径也在指数上升**。一个 Skill 现在可能影响：你的代码风格、你的提交习惯、你的 review 流程、你的记忆持久化机制。

这是一种**软件级的依赖管理问题**——只是大多数用户还没意识到。

### Take 3 · 独立 Memory / Harness / Safety 公司的 PMF 在被挤压

mem0、Guardrails AI、LangSmith 等公司的核心赌注是「这些组件会成为独立产品」。但实际上**它们正在被 Skill 化**。

这不是说这些公司会死——**企业市场仍然需要中央化方案**。但**消费者 / 个人开发者市场正在快速流失给 Skill**。

如果你是这些公司的投资人，2026 年应该问的问题是：「我们的产品还能 surive Skill 化吗？」

---

## 8.8 一些反直觉的观察

### 观察 1 · Skill 化 ≠ 更优秀，但 ≠ 更便宜的开始

Skill 化 Memory 的实际效果**不如** mem0——后者有专门的 retrieval 优化。但 Skill 化是「免费 + zero config + 跟着代码走」的，所以它赢了大多数用户。

**Worse is better** 在 Skill 生态再次得到验证。

### 观察 2 · 吞噬过程不是「替换」，是「内化」

我用「吞噬」这个词其实不太准。更准确说法是「内化」——Memory 没消失，只是从「外部独立产品」搬到了「Skill 的子目录」。

这跟 web 早期 jQuery 被 React 「吞」 是同一个 pattern——jQuery 没死，是被融进了 React 的内部 utility。

### 观察 3 · 这个吞噬是不可逆的

一旦一个柱子被 Skill 化，**它就很难再回到独立产品**——因为用户的工作流已经改了。

mem0 现在如果想抢回个人开发者市场，唯一办法是把自己**改造成 Skill**。这是产品 SKU 的根本变化。

---

## 8.9 本章要记住的一句话

> **Skill 不只是一种新格式，它是一个新的 power center。Memory、Harness、Safety 这些原本是独立 pillar 的组件，正在以 markdown 文件的形式被 Skill 内化。这意味着 Skill 不再是 Agent 系统的「附加包」，而是它的「中枢神经」。识别哪些组件还能保持独立、哪些注定被吞，是 2026-2027 年所有 Agent 工具公司的核心生存问题。**

下一章（第 9 章）已经讲过 Distribution——商业化三角的第四条边。第 8 章 + 第 9 章合起来回答了一个完整的问题：**Skill 在技术上吃掉了什么 + 在商业上需要补什么**。

---

## 数据说明

本章 Hub 数据均取自 2026-04-28 快照。Memory 化比例（state/、memory/、history/ 子目录占比）取 Top 1000 by stars。Harness 关键词增长曲线取 description + readme 全文检索。mem0 增长数据来自其公开 GitHub stars 历史 + 第三方 Crunchbase 信号（精确数据未公开）。所有趋势预测仅作研究用，不构成投资 / 创业判断。
