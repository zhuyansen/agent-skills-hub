---
title: 附录 D · 参考文献 + 延伸阅读
status: published
data_snapshot: 2026-04-29
---

# 附录 D · 参考文献 + 延伸阅读

> 写蓝皮书的过程是一次大型阅读综合。这个附录列出关键引用源 + 推荐阅读路径，方便读者深挖任何一章。

---

## D.1 Anthropic 官方资料（必读）

**Skill 标准**
- [Stop Building Agents, Build Skills](https://www.anthropic.com/blog/stop-building-agents-build-skills) — Anthropic 官方博客，Mahesh / Barry 类比来源
- [SKILL Spec RFC](https://github.com/anthropics/skills) — 三层加载机制 + frontmatter 标准
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — Anthropic 研究博客
- [skill-creator skill 源码](https://github.com/anthropics/skills/tree/main/skill-creator) — Skill 怎么自动生成 Skill 的官方实现

**MCP 标准**
- [Model Context Protocol Spec](https://modelcontextprotocol.io/) — MCP 协议官方
- [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) — 官方 MCP server 实现集
- [Anthropic Quickstarts](https://github.com/anthropics/anthropic-quickstarts) — 含 MCP 示例

**评估方法**
- [Anthropic Evals Cookbook](https://docs.anthropic.com/en/docs/build-with-claude/evals) — 「评估驱动开发」的官方实践

---

## D.2 蓝皮书引用过的中文 KOL 代表作

### 宝玉（Skill 设计哲学的中文最系统讨论者）
- 微博 [@宝玉xp](https://weibo.com/baoyu) — 长期更新 Skill / Agent 设计观察
- 「Skill 的 Agent 视角设计原则」系列文章
- 「Skill 原子化、自我迭代、脚本优先」三条核心论点
- **Ch4 全章主要受其启发，并用 Hub 67K 数据回测了他的论断**

### lovstudio（南川 · 商业化三角论）
- [《商业化三角不可能定理》](https://x.com/lovstudio) — Skill 商业化经典论述
- 三角：标准化 Runtime × 本地运行 × 源码保护
- **Ch9 的「第四条边 Distribution」直接承接此论**

### 花叔（alchaincyf）· Skill 自我繁殖案例
- [女娲.skill](https://github.com/alchaincyf/nuwa-skill) — 蒸馏任何人思维的元 skill
- [obsidian-ai-orange-book](https://github.com/alchaincyf/obsidian-ai-orange-book) — 橙皮书系列
- **Ch12 的「Claude-Generated」阶段以此为早期案例**

### tw93
- [Kami](https://github.com/tw93/Kami) — Mac 原生 AI 助手
- 各种轻量 Skill 工具链

### 刘小排（中文 AI 测评内容奠基人）
- [《我们前两天深度体验了 Kimi K2.6》](https://mp.weixin.qq.com/) — 中文 AI 圈高质量评测样板
- 十字路口社群（Bloome 评测来源）

### Datawhale（中文 AI 教育）
- [hello-claw](https://github.com/datawhalechina/hello-claw) — OpenClaw 中文教程
- 长期内容深度 + 教育友好

---

## D.3 蓝皮书引用过的英文 KOL 代表作

### Matt Pocock（Total TypeScript / AI Hero）
- [mattpocock/skills](https://github.com/mattpocock/skills) — 38K stars，工程纪律 over vibe coding
- AI Hero Newsletter — 60K subscribers
- **Ch7 v1.1 补充的第 5 个框架**

### Jesse Vincent（obra）
- [obra/superpowers](https://github.com/obra/superpowers) — 强制方法论
- TDD + SDD + Atomic Commits 在 Skill 里的极致执行
- **Ch7 框架对比第 2 项**

### Garry Tan（YC CEO）
- [garrytan/gstack](https://github.com/garrytan/gstack) — 虚拟工程团队，15 个 role-skill
- **Ch7 框架对比第 3 项**

### Kent C. Dodds（Testing Library / Epic React）
- [kentcdodds/compound-engineering](https://github.com/kentcdodds/compound-engineering) — Skill 复利机制
- **Ch7 框架对比第 4 项**

### Emil Kowalski（Sonner / Vaul / next-view-transitions）
- [emilkowalski/skill](https://github.com/emilkowalski/skill) — 极简派 Skill 哲学（27KB 单文件）
- **Ch4 活案例之一**

### Leonxlnx
- [taste-skill](https://github.com/Leonxlnx/taste-skill) — 9 个变体的原子化 + 参数化设计
- **Ch4 活案例之一**

### Cclank
- [news-aggregator-skill](https://github.com/cclank/news-aggregator-skill) — MISTAKES.md 模式典范
- **Ch4 活案例之一（自我迭代哲学）**

---

## D.4 行业关键论文 / 标准

- **Anthropic Constitutional AI** — [Bai et al., 2022](https://arxiv.org/abs/2212.08073) — Skill 的安全边界设计参考
- **MCP Protocol Spec** — [modelcontextprotocol.io/specification](https://modelcontextprotocol.io/specification)
- **NousResearch Autoreason** — [2026 Q1 paper](https://github.com/NousResearch) — Skill 自我迭代机制的理论原型，Ch5 引用
- **A Philosophy of Software Design** — John Ousterhout（书）— Matt Pocock 的核心引用源，「deep modules」概念
- **Pragmatic Programmer** — Hunt & Thomas（书）— Ch7 第 5 框架的智识来源
- **Domain-Driven Design** — Eric Evans（书）— Ch7 + 附录 B 的 ubiquitous-language 概念

---

## D.5 数据来源

蓝皮书所有 Hub 数据源自 [agentskillshub.top](https://agentskillshub.top) 的 Supabase backend：

- **Skills 表**：67,196 条（截至 2026-04-29 快照）
- **Weekly Trending Snapshots**：跨 12+ 个完整周
- **Skill Masters**：Verified Creator 公开 metadata
- **Quality Score**：6 维度 + 复合 Score 算法

**完整数据集查询脚本**：
- [data/ch03_analysis.py](https://github.com/zhuyansen/skill-blue-book/blob/main/data/ch03_analysis.py)
- [data/ch04_atomicity.py](https://github.com/zhuyansen/skill-blue-book/blob/main/data/ch04_atomicity.py)
- [data/ch06_charts.py](https://github.com/zhuyansen/skill-blue-book/blob/main/data/ch06_charts.py)

可复现：跑同样脚本对当前 Hub 数据，应该能看到与书中数字 ±10% 内的偏差（数据持续更新）。

---

## D.6 「想深挖某一章」的推荐路径

| 章 | 想深挖 | 推荐资源 |
|---:|---|---|
| 1 | Mahesh vs Barry 的认知心理学背景 | Anthropic Constitutional AI paper + Ousterhout *A Philosophy of Software Design* |
| 2 | 三层加载的工程权衡 | SKILL Spec RFC + Anthropic SDK 源码 |
| 3 | Gini 0.983 跟其他生态对比 | Tornike Gigineishvili *Inequality in App Store Economies* (2023) |
| 4 | 宝玉哲学 + 工程纪律 | mattpocock/skills 全部 + 宝玉 weibo 历史 |
| 5 | 评估驱动开发深度 | NousResearch Autoreason paper + Anthropic Evals Cookbook |
| 6 | 9 类型 × 4 路径分类学 | Hub `/category/` + 上面 mentioned-in awesome lists |
| 7 | 5 框架横向对比 | 各自 GitHub repo + 自己跑相同测试 |
| 8 | Skill 吞噬其他柱子 | mem0、LangSmith、Guardrails AI 各家公司博客 |
| 9 | Distribution 第四条边 | lovstudio《商业化三角》原文 + Hub /best/ 页面 |
| 10 | Verified Creator 设计原型 | GitHub Verified Publisher + Apple Developer Verified Identity |
| 11 | Service-on-Open 商业模式 | Tidelift / Sourcegraph 公开博客 |
| 12 | Claude 自创 Skill 的未来 | OpenAI / Anthropic 内部 RFC（公开部分） |

---

## D.7 蓝皮书自身的二次创作授权

**License**：CC BY-NC-SA 4.0

允许：
- ✅ 引用、转载、翻译（任何语言）
- ✅ 拆章发公众号 / X / blog（**注明来源 + 原文链接**）
- ✅ 商业培训用作课件（前提：非营利场合 + 注明来源）
- ✅ 二次创作衍生（Adaptation）

不允许：
- ❌ 不署名 / 不提及 AgentSkillsHub
- ❌ 用作商业出版物（商业出版需联系 [editor@agentskillshub.top](mailto:editor@agentskillshub.top) 单独授权）
- ❌ 再发布的衍生作品不附 CC BY-NC-SA 4.0

---

## D.8 蓝皮书 2027 跟踪页

每年蓝皮书发新版时，会维护一个 [followup.md](https://github.com/zhuyansen/skill-blue-book/blob/main/followup.md)（待开），记录：

- 哪些预测应验了
- 哪些预测落空了
- 哪些数字被证伪
- 哪些新趋势 v1.0 没看到

**自我打脸**是这本书的核心承诺之一。明年这个时候来检阅。

---

## D.9 致谢

蓝皮书写作期间得到以下人 / 项目的启发或帮助：

- **Anthropic 团队** — 让 Skill 这个概念有了规范
- **宝玉、lovstudio、花叔、tw93、刘小排** — 中文 AI 圈的持续输出
- **Matt Pocock, Jesse Vincent, Garry Tan, Kent C. Dodds** — 英文 Skill 框架四大开拓者
- **AgentSkillsHub 的 58 位 verified subscribers** — 你们读了所有日报和周报
- **Claude Code / Claude Opus 4.6** — 蓝皮书一半以上的初稿是我和 Claude 对话出来的；Claude 不是合著者，但是不可或缺的工作伙伴

---

## 一句话总结

> **这本书不是学术著作，是 2026 年 4 月这个时点的实地观察 + 数据快照。所有引用的 KOL、所有跑过的代码、所有声称的数字——都可以追溯、可以打脸。**
>
> **如果你看完蓝皮书写出了第 13 章，或者证明我哪一章错了——请发邮件到 [editor@agentskillshub.top](mailto:editor@agentskillshub.top)。下一版蓝皮书会引用你。**

附录 D 完。蓝皮书 v1.0 全本至此完结。

— Jason Zhu (@GoSailGlobal) · 2026-04-29
