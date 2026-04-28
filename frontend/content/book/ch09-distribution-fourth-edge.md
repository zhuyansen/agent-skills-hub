# 第 9 章｜Distribution：商业化三角少的那条边

> 这一章承接 lovstudio（南川）那篇广为流传的《商业化三角不可能定理》。原文里他指出：Skill 作者要同时实现"标准化 Runtime × 本地运行 × 源码保护"是不可能的——三选二，永远要牺牲一个。
>
> **我同意三角是对的，但要补一刀**：
>
> 大多数 Skill 作者**根本走不到三角面前**，他们卡在更早的一步——没有用户。AgentSkillsHub 65,729 条 skill 里，**53.8% 是 0 star**。这不是商业化失败，是连 distribution 都没启动。
>
> 这一章会用 Hub 数据把"找用户"这件事的真实成本量化（中位 320 天到 100 stars），然后讲三个走通了的活案例（emilkowalski / vercel-labs/skills / steipete），最后讨论为什么 **Distribution 是三角缺失的第四条边**——也是 AgentSkillsHub 这种基础设施型项目存在的真实理由。

---

## 9.1 三角不可能定理 · 简要重述

南川的论点（用我的话复述，原文请看 [lovstudio_AI](https://x.com/lovstudio_AI)）：

Skill 作者想商业化时，面前有 3 个 desirable 属性：

1. **标准化 Runtime**——用户能用熟悉的命令一行装上（`npx skills add ...` / `~/.claude/skills/`）
2. **本地运行**——不用云端，在用户的机器上完整执行
3. **源码保护**——作者保留对 prompts、scripts、IP 的控制权

**南川的不可能定理**：你不能同时实现三个。**三选二，永远牺牲一个**。

落到三条具体路径：

| 选哪两个 | 牺牲了 | 路径名 | 典型形态 |
|:---:|:---:|:---|:---|
| 1 + 2 | 源码保护 | **Open Source** | MIT / Apache 全公开 |
| 1 + 3 | 本地运行 | **Hosted SaaS** | npx 装 client，逻辑在云 |
| 2 + 3 | 标准化 Runtime | **Closed Runtime** | 闭源 binary，自己装 |

每条路径都有真实案例，每条路径都有真实痛点。这个框架本身没毛病。

**但这不是 90% 作者面对的真实问题。**

90% 作者面对的真实问题是：**没人知道我的 skill 存在**。三角讨论只对**已经有用户的人**有意义。对**还没有用户的人**，三角是奢侈品。

---

## 9.2 Hub 数据 · 找用户的真实成本

我跑了 AgentSkillsHub 全量 65,729 条 skill 的数据。三组关键事实：

### 事实 1 · 53.8% 的 skill 是 0 star

```
总 skills:        65,729
≥1 star:          30,333（46.2%）
≥10 stars:        10,745（16.3%）
≥50 stars:         5,750（8.7%）
≥100 stars:        4,191（6.4%）
≥500 stars:        1,687（2.6%）
≥1000 stars:       1,071（1.6%）
≥10000 stars:        222（0.3%）
```

**约 35,400 个 skill 创建出来后，从未被一个人 star**。这不是质量问题——这是 discovery 失败。这些作者**到不了三角讨论的会议室**。

### 事实 2 · 进入 Top 1000 中位需要 320 天

抽 Top 1000（≥100 stars）的 cohort，从 created_at 到现在的年龄分布：

| 年龄 | 比例 |
|:---|:---:|
| < 30 天 | 4.1%（41 个）|
| < 90 天 | 22.2%（222 个）|
| > 365 天 | **45.3%**（453 个）|
| 中位 | **320 天** |
| 平均 | **513 天** |

**结论**：进入 Hub Top 1000 的中位时间是 **320 天**——快一年。**90 天内能破百 star 的只有 22%**。这是 distribution 的真实成本——**普通作者要熬一年**。

### 事实 3 · Distribution 复利 · 9.6% 的作者占 24.5% 的 Top 1000 slots

Top 1000 skill 的 835 个独立作者中，**只有 9.6%（80 人）拥有多于 1 个 Top 1000 skill**。但这 80 人**占了 245 个 slot（24.5%）**。

Top 15 多产作者：

| 作者 | Top 1000 中的 skill 数 |
|:----|---:|
| steipete | **14** |
| modelcontextprotocol | 13 |
| microsoft | 10 |
| openai | 7 |
| op7418 | 7 |
| langchain-ai | 6 |
| ComposioHQ | 6 |
| tw93 | 6 |
| HKUDS | 6 |
| e2b-dev | 6 |
| alchaincyf | 5 |
| anthropics | 4 |
| github | 4 |
| VoltAgent | 4 |
| rohitg00 | 4 |

**这 15 个 ID 中**：

- 5 个是大公司或官方组织（microsoft / openai / anthropics / github / langchain-ai）
- 4 个是明确的中文圈 KOL 或集体（op7418 / tw93 / alchaincyf / HKUDS）
- 1 个是西方 well-known dev（steipete）
- 5 个是已经有产品/平台 distribution 的组织（modelcontextprotocol / ComposioHQ / e2b-dev / VoltAgent / rohitg00）

**完全靠"我写一个好 skill 然后被发现"的成功案例 ≈ 0**。

这个数据砸碎了一个常见 narrative：**"只要东西做得好，自然会被发现"**。Hub 里 65K 条 skill 里 35K 个是这种 narrative 的失败者。**Distribution 不是营销虚词，是结构性约束**。

---

## 9.3 活案例 A · `emilkowalski/skill` · Service-on-Open

emilkowalski 的 skill 是经典的 **Open Source + Service-on-Open** 路径——同时拿了三角的"标准化 Runtime（npm/直接装）"和"本地运行"，**主动放弃了源码保护**。

**怎么变现**：他不卖 skill。skill 是免费的——只有 1 个 27KB SKILL.md，MIT 等价宽松。**变现入口是 [animations.dev](https://animations.dev/)——他的付费动画工程课**。

**逻辑链**：

```
免费 SKILL.md → 用户用了觉得好 → 想深入学 →
注意到底部 "If you want to dive even deeper, 
check out Emil's course: animations.dev"
→ 付费转化
```

**为什么这个 work**：
1. **作者已有 Distribution 资产**——Sonner 12K stars + Vaul + next-view-transitions，本身就是流量入口
2. **skill 是引子，课程是产品**——skill 把 "taste" 这个抽象的东西变成 Agent 的可执行规则，正好印证课程价值
3. **不依赖 skill 直接变现**——所以可以 100% 开源、不限制使用

**Hub 数据印证**：emilkowalski/skill 894 stars · 创建 2026-03-16 · 5 周 → 894 stars。**这是 distribution 已有的人**——不是普通作者能复制的轨迹。

**Service-on-Open 路径的核心限制**：作者必须**先有 distribution 资产**（粉丝、社区、个人品牌、产品装机量）。新人走这条路 = 0。

---

## 9.4 活案例 B · `vercel-labs/skills` · Hosted Runtime

Vercel 在 2026 年出了 [skills.sh](https://skills.sh)——一个**官方 Hosted Skill 分发平台**。命令行 `npx skills add <repo>` 一行装。

这是经典的 **Hosted SaaS** 路径——拿了"标准化 Runtime"和"源码保护"（你装的是 client，逻辑在 Vercel CDN），**牺牲了完全本地运行**（`npx skills add` 需要从 skills.sh 拉清单）。

**怎么变现**：Vercel 当然不会靠 skills.sh 赚钱——它是**给 Vercel 平台引流的 distribution 池**。但对**第三方 skill 作者**来说，把自己的 skill 注册到 vercel-labs/skills 上 = 蹭官方 distribution。

aaron-he-zhu/seo-geo-claude-skills 就这么干的：

```
npx skills add aaron-he-zhu/seo-geo-claude-skills
```

aaron 没有 fork 整个 vercel-labs，只是注册了一行。这给他带来：
- 官方 npm 一行装的便利性
- skills.sh 网站上的列表曝光
- 跨 35+ AI Agent 的兼容性（OpenClaw / Hermes / Gemini CLI 全在 list）

**Hub 数据印证**：aaron-he-zhu/seo-geo-claude-skills 1,141 stars · 4 个月。其中**多少 stars 来自 vercel-labs 的 distribution 通道？无法精确归因，但通过 npx 安装的占比远高于直接 git clone**。

**Hosted Runtime 路径的核心限制**：你**依赖 Vercel（或别的 host）的政策**。如果 skills.sh 哪天倒闭、或改规则、或封掉某些 skill，你的用户就断了。这是**主权风险**。

---

## 9.5 活案例 C · `steipete/*` · Distribution Channel 复利

steipete（PSPDFKit 创始人 / iOS 圈顶流）在 Hub 的 Top 1000 里**有 14 个 skill**——单人最多。

按本章前面 Top 1000 中位 320 天的数据，普通人造 14 个 Top 100+ stars 的 skill 需要**3-4 年**。steipete 的 14 个 skill 大多数是**最近 6-12 个月**做出来的。

**为什么他能 14× 速度**？不是他写得快，是他**已经有 distribution channel**：

1. **77K X 粉丝**——发条推就有数千次曝光
2. **Mac/iOS dev 圈个人品牌 10+ 年**——同温层立刻 RT
3. **PSPDFKit 卖给 Nutrient 的成功背书**
4. **持续高质量博客 / 演讲 / Open Source 贡献**

steipete 的 **distribution asset 比任何单个 skill 都值钱**。每写一个 skill，都能调用同一个 audience 反复变现 attention。**复利效应**。

这就是为什么 **9.6% 的多产作者占了 24.5% 的 Top 1000**——他们把 distribution 当资产复用，新人每写一个 skill 都从 0 开始。

**对 Skill 作者的含义**：

```
你的 skill 价值 = 内在质量 × distribution 系数
                       (不变)        (1 → 1000+)
```

**没有 distribution 的好 skill ≈ 没人发现的好 skill**。Hub 数据里有大量 "quality_score 60+ 但 stars < 10" 的 skill——质量从未变现成关注。

---

## 9.6 三角 + 第四条边 · Distribution

把南川的三角扩展成**四元结构**——

```
                    Distribution
                  （能不能被发现）
                         ★
                        ╱ ╲
                       ╱   ╲
                      ╱     ╲
                     ╱       ╲
       标准化 Runtime ─────── 本地运行
        （能不能被装）        （能不能不依赖云）
                     ╲       ╱
                      ╲     ╱
                       ╲   ╱
                        ╲ ╱
                       源码保护
                     （能不能保留 IP）
```

南川的三角是**底面**——**作者商业化的成本-收益约束**。

**Distribution 是顶点**——**没有它，三角没有意义**。

3 类作者面对这个四元结构：

| 作者类型 | 已经有的边 | 缺的边 | 战略 |
|:---|:---|:---|:---|
| 大公司/官方 | Distribution + 源码保护 + 标准化 + 本地（全占）| 无 | 自由选 path |
| Already-famous dev | Distribution + 标准化 + 本地（缺源码保护）| 牺牲 IP 走 Open | Service-on-Open |
| 普通新人 | **只有源码保护** | Distribution / 标准化 / 本地全缺 | **先解决 Distribution** |

**90% 作者是第 3 类**。三角对他们没用——他们要做的不是 "选哪 2 条边"，是**"先把第 4 条边凿出来"**。

---

## 9.7 AgentSkillsHub 为什么要做 Distribution 这条边

到这里就能解释 Hub 这个项目本身的存在意义。

**Hub 不是要竞争 Anthropic / Vercel**——Anthropic 把官方 skill 标准化做了，Vercel 把 hosted runtime 做了。**Hub 在做一件他们不做的事**：

> **让 65K 长尾 skill 里的好作品被发现**。

具体动作：

1. **质量评分**——按 10 维信号筛选，让好 skill 浮出
2. **分类索引**——9 个类目让用户按需找
3. **场景化推荐**——`/best/{scenario}/` 页面绑定使用场景
4. **Trending / 日报**——把"新被发现"的 skill 推到 feed
5. **作者主页**——让作者集中展示作品（拥有 distribution channel）
6. **Verified Creator** 计划——给持续优质作者额外曝光（**第 10 章会展开**）

**Hub 的商业模式与南川三角无关**——Hub 不卖 skill，不收作者钱，不限制访问。Hub 卖的是 **distribution 作为服务**——给 skill 作者补 missing edge，给 skill 用户补 missing index。

可类比：

| 已存在 | 缺什么 | 谁来做 |
|:----|:----|:----|
| GitHub repos | discoverability | trending / awesome list |
| npm packages | quality assessment | npm-trends / Snyk / Bundlephobia |
| arxiv papers | curation | Papers with Code / arXiv-sanity |
| **Skills** | **discoverability + quality + curation** | **AgentSkillsHub 试图做的事** |

每一类基础设施都不是新发明轮子，是**把已有的 raw 资产加上 distribution layer**。

---

## 9.8 自我反省 · Distribution 这条边的真实代价

这一章不能没有自我解剖。

### 反省 1 · Hub 自己的 distribution 也很弱

Hub 自己的 X（@GoSailGlobal）只有不到 1K 关注者。Google 索引 4,200 个页面但 GSC impressions 月均 ~1K。**做 distribution 服务的人本身没 distribution channel**——这是讽刺。

往后 6 个月（2026 Q3）的关键 KPI 不是 Hub 的 skill 总量（已经超过 65K），是：
- Hub 月独立访问者从 ~5K → 50K
- skill 作者通过 Hub 触达 user 的比例从 < 5% → 20%

如果做不到，Hub 的 distribution 服务**逻辑上成立但实际上无效**。

### 反省 2 · "中位 320 天破百" 也是 Hub 当前的处境

按前面数据，普通 skill 进 Top 1000 中位 320 天。Hub 自己作为一个项目同样适用——2026-01 上线，到现在 4 个月。我们在第 50-100 天区间——**也在熬同一条曲线**。

写这本蓝皮书是 Hub 自己的 distribution 行动之一。第 4 章在 X 上互动率 2.75%，第 5 章却只有 0.32%。**distribution 不是写完就有，每条推、每个章节、每个 DM 都是独立的 distribution 努力**。

### 反省 3 · 三角第 4 条边可能不止一条

我说"第四条边是 Distribution"——但更深一层可能是**5、6 条边**：

- **Distribution**（被发现）
- **Onboarding**（用户能 5 分钟跑通）
- **Maintenance**（持续更新避免冷冻 · 第 5 章数据）
- **Compounding**（一个 skill 帮另一个 skill 增强）

**南川三角是商业化的约束。我说的第四条边是发现的约束。但发现之后还有更多约束**。把这些都画出来不是拼图比赛，是诚实——**做 skill 这件事远不是"想商业化模式"那么简单**。

---

## 9.9 本章要记住的一句话

> **南川的商业化三角对 10% 已经有用户的作者成立。剩下 90% 的作者卡在更早一步——distribution。Hub 数据：53.8% 0 star · 中位 320 天破百 · 9.6% 多产作者占 24.5% Top 1000。先把 distribution 这条边做出来，三角讨论才有意义。**

> **AgentSkillsHub 在做的不是新型 skill 平台，是为 65K 长尾 skill 补 missing edge——让好 skill 被发现，让用户找到能用的工具。**

---

## 9.10 下一章预告

第 10 章 **Verified Creator**——是 Hub 在 distribution 这条边上的具体动作。怎么用一个**质量信号 + 持续迭代要求 + 透明评估**的认证机制，把 Hub 的 distribution 流量倾斜给"真维护"的作者，而不是"搬运 + 屯囤" 的作者。

会回答的问题：
- 什么样的作者能成为 Verified Creator？
- 评估公式是什么？（公开透明）
- Verified 之后能拿到什么具体好处？
- 怎么撤销？（避免一次认证终身舒服）

下一章见。

---

**数据说明**：本章所有 Hub 数据取自 2026-04-26 AgentSkillsHub 快照。完整 Python 分析脚本见 `data/ch09_distribution_analysis.py`，原始 cohort 数据见 `data/ch09_top1000_snapshot.json`。

**lovstudio 三角原文引用**：本章框架基于南川 [@lovstudio_AI](https://x.com/lovstudio_AI) 公开发表的《商业化三角不可能定理》论点。如有具体表述出入，以原文为准。

**下一章**：[第 10 章 · Verified Creator：不是花钱买的认证](../part4-hub/ch10-verified-creator.md)
