---
title: 第 10 章 · Verified Creator：不是花钱买的认证
chapter: 10
part: 4 · AgentSkillsHub 运营手记
status: draft
data_snapshot: 2026-04-23
---

# 第 10 章 · Verified Creator：不是花钱买的认证

> "如果一个认证能用 999 元买到，它就不是认证，是订阅服务。"
>
> ——这章的全部论点，可以浓缩成这一句。

---

## 10.0 引子：为什么 99 元买徽章是反 PMF

2026 年 2 月，我第一版 Verified Creator 的设计文档里写过一行字：

> "推出 999 元/年的 Verified Creator 订阅，享受 Trending 加权 + 徽章 + 专属客服。"

写完我看了 30 分钟，把它删了。

理由很简单：**如果 999 元能买到 Verified，那这个徽章对用户来说就毫无意义**。用户看到一个 Verified 徽章会做什么？会假设这个作者是被 Hub 筛选过的、值得信任的。一旦"花钱就能拿"被坐实，用户会立刻调整预期：Verified ≠ 质量 = 营销噱头。

这是一个 PMF 死亡螺旋：
1. 卖徽章 → 短期收入 → 作者觉得"花了钱我就有特权"
2. 用户发现徽章无信任价值 → 用户不再点 Verified 链接
3. Verified 流量贬值 → 作者发现没回报 → 不续费
4. Hub 失去这个收入来源 + 信任也跟着塌

**Verified 不能是花钱买的，必须是赚来的**。这一章讲我们怎么定义"赚来"，以及为什么这个定义本身比规则细节更重要。

---

## 10.1 三段历史：Verified Creator 怎么走到今天

### 第 0 阶段（2026 年 1 月）：根本没有 Verified

Hub 上线时只有"创作者主页"——任何人提交一个 GitHub 仓库到 Hub 都可以拿到一个 `/author/{username}/` 页面。没有任何认证机制。

问题很快出现：**Top 50 作者里有 6 个是 batch dump 账号**——一个人 1 周内创建 30 个仓库，全部上传相同的"Skill 模板"，靠数量虚高排名。

那时候我加了"作者污染清理"流程：人工识别批量发布、连同账号 + 关联仓库一起从 Hub 清掉。这是第 3 章里讲的"漏洞 4"——cleanup 总会有，但人工不可持续。

### 第 1 阶段（2026 年 2 月）：第一版 Verified 设计（被自己否决）

第一版设计就是上面那个 999 元订阅版。我自己看了一遍觉得不对，又花了 2 周重新想。

期间我读了 GitHub 的 Verified Publisher、npm 的 Trusted Publisher、Apple Developer 的 Verified Identity 等几个对标。最重要的发现是：**所有靠谱的"Verified"机制都把"是个真人"和"作品有质量"分开做**。

GitHub Verified Publisher = 你是真人/真公司
GitHub Sponsors = 你的作品有人愿意付费

我之前把这两件事搅成一件，所以写出 999 元订阅这种四不像。

### 第 2 阶段（2026 年 3 月）：Founding Members 翻车 + 重做

第二版设计后我做了一件**当时认为聪明、现在看是错的**事——我列了一份"Founding Members 名单"，里面包括 lovstudio、tw93、antfu、garrytan 等开源圈知名作者，**没问他们就发布了**。

逻辑是："他们的作品已经在 Hub 排名前列，我提前把 Verified 给他们，他们出于面子或好奇会回应，社区也能立刻看到几个'有名字'的 Verified Creator"。

发出去 4 小时，收到 lovstudio 那边的友好但坚定的反馈："南川（lovstudio）应该没加入啊"。

我立刻撤掉了所有 Founding Members 名单，把页面状态改回"暂无 · 首批邀请制进行中"。

**这次翻车的核心教训**：**用别人的名字给自己背书是诱惑，但那是骗信任而不是赢信任**。如果 Verified 的核心价值是"用户可信任",那么连"招募过程"本身都必须是干净的。否则一个未经同意的列表就足以毁掉所有信誉。

### 第 3 阶段（2026 年 4 月-至今）：当前的设计

经过两次失败之后，当前的 Verified Creator 设计是：

- **不卖、不送、不预填名单**
- 只有作者**主动申请** + 满足明示标准 才能拿到
- 标准全部公开、可验证、可追溯
- 失格条件也公开（什么情况下会撤销）
- 全程透明：每季度公布申请数、通过数、撤销数

下面是具体规则。

---

## 10.2 评估三个维度（明示且可验证）

Verified Creator 评估有且只有 **3 个维度**，每个维度有具体可量化的指标。

### 维度 1 · 迭代频率（Iteration Frequency）

**问题它在回答**：你写完 Skill 之后还在不在维护？

**指标**：
- 过去 90 天内有 ≥ 4 周 commit 活动（不要求每周都有，但 90 天内至少 4 个不同的 ISO 周）
- 过去 30 天内至少 1 次 commit
- ⚠️ commit 不能是纯文档/typo 修改（Hub 自动检测：commit diff < 5 lines 不算数）

**为什么这个维度**：第 6 章数据已经讲了，发布后 30 天 commit 频率 ≥ 5 次的 Skill 6 个月留存率 62%；从未更新的 < 8%。**持续迭代是质量的最强信号**。

**坑**：这个标准对"已完成、不需要再改"的 Skill 不友好。但我做了取舍——宁可漏掉一些"已完工"的好 Skill，也不能让"装完就走"成为标杆。

### 维度 2 · 质量分（Quality Score）

**问题它在回答**：你的 Skill 写得怎么样？

**指标**：
- Hub 的 6 维质量评分（completeness / clarity / specificity / examples / readme_structure / agent_readiness）
- 过去 6 个月内至少有 1 个 Skill 的 quality_score ≥ 65（A 级）
- 或 ≥ 3 个 Skill 的 quality_score ≥ 50（B 级）

**为什么这个维度**：作品本身要够格。如果一个作者连一个 65 分以上的 Skill 都没有，"Verified" 就成了纯人格背书，跟作品脱钩。

**坑**：质量分本身有 bug。第 3 章已经承认 Hub 的 quality_score 算法在 readme_structure 上过度奖励"形式完整"——一个写满了空 H2 的 README 能拿到比一个朴素但有干货的 README 更高的结构分。算法这一年内会迭代，但目前评分阈值的偏差控制在 ±10 分以内。

### 维度 3 · 社区反馈（Community Signal）

**问题它在回答**：除了你自己说"这 Skill 好用"，有没有别人也这么觉得？

**指标**：
- 过去 6 个月你发布的 Skill **总 stars** ≥ 200，或总 forks ≥ 30
- 或者你的 Skill 出现在 ≥ 1 个第三方 awesome list / 教程文章里（需要作者提交链接、Hub 人工核实）
- ⚠️ 自我刷 stars 检测：单日 ≥ 30 stars 增长且无外部链接的会标记复查

**为什么这个维度**：第 1 章讲过，Skill 不是"我觉得好用就好用"。需要外部信号。

**坑**：社区反馈对**新作者**不友好。一个写了 6 个月才发出第一个 Skill 的作者很难短期内拿到 200 stars。所以这个维度有一个**例外通道**——通过 Hub 编辑团队的"创新提名"，给那些质量极高但还没积累社区的新作者一个机会。这个例外通道每季度上限 5 人。

---

## 10.3 评分公式（可验证）

把三个维度合并成一个 0-100 的 Verified Score：

```
verified_score =
    iteration_score × 0.40   # 迭代频率（最重）
  + quality_score   × 0.40   # 作品质量
  + community_score × 0.20   # 社区反馈
```

每个子分的计算细节：

```python
# Iteration score (0-100)
def iteration_score(author_repos):
    # 过去 90 天活跃周数 / 13（90天≈13周）× 70
    active_weeks = count_distinct_weeks(commits_last_90d) 
    base = (active_weeks / 13) * 70
    # 过去 30 天 commit 数 × 2，封顶 30
    recent = min(count_commits_last_30d * 2, 30)
    return min(base + recent, 100)

# Quality score (0-100)
def quality_score(author_repos):
    # 取最高 quality_score 的 Skill 作为基础（× 1.0）
    best_qs = max(repo.quality_score for repo in author_repos)
    # 加上 B 级及以上 Skill 的数量奖励（每个 +5，封顶 +25）
    b_count = sum(1 for r in author_repos if r.quality_score >= 50)
    bonus = min(b_count * 5, 25)
    return min(best_qs + bonus, 100)

# Community score (0-100)
def community_score(author_repos):
    # log10(总 stars) × 30，封顶 60
    total_stars = sum(r.stars for r in author_repos)
    star_part = min(math.log10(max(total_stars, 1)) * 30, 60)
    # 第三方背书（awesome list / 教程引用）每个 +20，封顶 40
    refs_part = min(count_external_refs(author) * 20, 40)
    return star_part + refs_part
```

**通过门槛**：`verified_score ≥ 65`

**为什么是 65**：参考 Hub 的 quality_score A 级阈值。65 这个数字本身没什么神圣性，但它对应的是：一个作者要么在迭代上**非常勤快**（70 分起跳），要么在质量上**非常出色**（85 分起跳），要么在两者都中等的同时社区反馈强劲。

**全部通过路径只有这三种**——也就是说**没有"全方位平均"路径**。这是有意为之：Verified 不奖励平庸。

### 算 1 个具体例子

假设作者 X：
- 过去 90 天有 8 个不同周有 commit，过去 30 天 6 次有效 commit
  - iteration = (8/13)×70 + min(6×2, 30) = 43.1 + 12 = **55.1**
- 最高 Skill 是 quality_score 72，B 级及以上 Skill 共 4 个
  - quality = 72 + min(4×5, 25) = 72 + 20 = **92**
- 总 stars 850，外部背书 1 个
  - community = log10(850)×30 + 1×20 = 88.4 + 20 = capped at 60+20 = **80**
- verified_score = 55.1×0.40 + 92×0.40 + 80×0.20 = 22.04 + 36.8 + 16 = **74.84**

**74.84 ≥ 65，通过**。这位作者主要靠 quality + community 拉分，iteration 其实只是中等。这是健康的——一个有名作品 + 持续被认可 + 偶尔更新的作者，是 Verified 该奖励的群体。

---

## 10.4 申请表完整模板

这是当前 Verified Creator 申请表的完整版本（公开，任何人可看）：

```yaml
# Verified Creator Application
# 提交至：verified@agentskillshub.top
# 审核周期：每月 1 次，审核结果会发邮件通知

# Section 1 · Identity 身份基础信息
github_username: 必填，例如 zhuyansen
email: 必填，会用于核实 + 通知
real_name: 选填，公开徽章上是否展示由你决定
bio: 选填，1-2 句话自我介绍（中英文都可）

# Section 2 · Works 你想用来 verify 的作品
primary_skills:
  - github.com/{user}/{repo}    # 必填，至少 1 个
  - ...                          # 最多 5 个
how_long_maintained: 1-3-6-12-24+ 月
total_users_estimated: 你能粗略估的活跃用户数（可以填 unknown）

# Section 3 · External signals 社区背书（如有）
mentioned_in:
  - awesome list URL
  - blog post URL
  - tutorial / video URL
total_external_refs: 自报数字，Hub 会人工核实

# Section 4 · Why verified 你的诚实回答
why_verify: 50-200 字
  - 你期望 verify 之后能解决什么问题？
  - 你愿意承担什么义务（持续维护、回复用户问题、参与 Hub 的 quality 改进等）？

# Section 5 · Self-check 自查
- [ ] 我没有 batch-dump 账号（即同一人多账号刷数量）
- [ ] 我同意 Hub 在公开页面展示我的 GitHub 头像、用户名、bio
- [ ] 我了解 Verified 状态可以被撤销（见 10.7 节）
- [ ] 我同意 Hub 在我的 Skill 出现重大质量问题时联系我

# Section 6 · Optional 自选
- 期望被推荐到的 scenario 页（如 /best/python-mcp-servers/）
- 期望接的合作类型（咨询 / open source / 招聘）
```

**这份表里没有的东西**：
- 任何付款链接
- 任何"快速通道"选项
- 任何"VIP" / "Premium" / "Plus" 字眼

这是有意为之的。

---

## 10.5 透明数字承诺

Verified Creator 项目从启动开始我就承诺**每季度公开**以下数字：

| 数字 | Q1 2026 | Q2 2026 (预测) |
|------|--------:|--------:|
| 申请数（总） | — | 30-50 |
| 通过数 | — | 5-10 |
| 撤销数 | 0 | 0-1 |
| 申请通过率 | — | 15-25% |
| 平均申请到决议时长 | — | 14-21 天 |
| 例外通道使用 | — | 0-2 |

**Q1 数字为空**是因为 Q1 项目还在两次失败重做的过程中，没有正式开放申请。**Q2 是首个真正运行的季度**——这一章定稿之后会启动公开招募。

为什么要承诺通过率 15-25%——这不是任意数字。它来自三个考量：

1. **太高（>50%）= Verified 没含金量**。如果 80% 申请的人都通过，那 Verified 就是"门槛极低的徽章"，跟一开始要避免的"花钱买"没本质区别。
2. **太低（<5%）= 设计自身有问题**。如果 95% 申请被拒，要么是标准定得太高没人能达到，要么是 Hub 在劝退用户。
3. **15-25% 是一个有挑战但合理的范围**——意味着大约每 5 个真心想拿的人能有 1 个通过。

如果 Q2 实际通过率掉到 5% 以下，我会**公开承认设计问题**，而不是继续硬撑标准。透明本身是这个项目的核心，不是工具。

---

## 10.6 第一次失败教训：一份事后复盘

我说过 10.1 那个 Founding Members 翻车不是普通错误。值得在这一章单独留 1 节做复盘。

### 当时的决策链
1. 我看到 Hub 已经有几位有名作者的 Skill 排名前 100
2. 我想"如果给他们提前发 Verified 徽章，可以让 Verified 项目立刻有面子"
3. 我假设"他们会觉得这是好事"
4. 我没问，直接加上了
5. 4 小时后被指出，立刻撤掉

### 错在哪里
- ❌ 错 1：**用别人的名字给自己背书是骗信任**。这条已经在 10.1 讲过。
- ❌ 错 2：**"事后通知 vs 事先征求"是两件完全不同的事**。Verified 这种带社会关系的标记，必须 opt-in。我当时假设别人"应该会同意"——这是设计 Verified 项目最不该犯的错。
- ❌ 错 3：**犯错本身不可怕，最可怕的是没有立刻撤回**。如果我那天硬撑 24 小时再撤，损失会大很多倍。
  - 撤回的速度本身是信誉的一部分。

### 不会再做的事
- 不会预填任何 Verified 名单
- 不会给"创始合作伙伴"任何特别优待（哪怕他们真的同意），因为那等于在标准之外开了一个口子
- 不会把"第一年免费"当作邀请条件（看起来无害但其实是 bait-and-switch）

### 已经做的修复
- 当前 `/verified-creator/` 页面状态：**「暂无 · 首批邀请制进行中」**
- VERIFIED_CREATORS 数组：**空**
- 标记规则：作者主动申请并通过 verified_score ≥ 65 之后，由 Hub 编辑团队人工二审，再写入数据库 + 显示徽章

复盘到这里。**这件事让 Verified 项目晚出 6-8 周**，但晚出来的版本结构是干净的。

---

## 10.7 Verified 的撤销条件

如果 Verified Creator 没有"撤销机制"，它就还是一个**静态徽章**，会逐渐失去信号价值。下面这 5 条是公开的撤销条件：

### 撤销条件 1 · 长期不活跃
- 6 个月内 0 commit + 0 新 Skill 发布 → 触发"半休眠"标记
- 12 个月内继续 0 活动 → 自动撤销 Verified 状态
- 撤销前 60 天会发邮件提醒

### 撤销条件 2 · 质量下降
- 已发布 Skill 的 quality_score 平均跌出 50 分以下 → 触发复审
- 复审 60 天内未恢复 → 撤销

### 撤销条件 3 · 用户 / 社区严重投诉
- ≥ 5 个不同用户投诉同一作者（恶意误导、安全问题、明显抄袭等）
- → 进入 30 天调查期（Hub 联系作者 + 听双方陈述）
- 投诉成立 → 撤销 + 公开记录

### 撤销条件 4 · 利益冲突未披露
- Verified Creator 不能同时做 Hub 的明显竞品而不披露
- 不能在自己的 Skill 里隐藏推广自有付费服务但不告知用户
- → 复审 + 撤销

### 撤销条件 5 · 主动放弃
- 作者可随时通过邮件主动放弃 Verified 状态
- 立即生效，无追问、无尴尬流程
- 这一条很重要：**自由进、自由出**，否则 Verified 就有锁定感

---

## 10.8 我不会做的事（明示）

为了避免后续的"feature creep"，下面是我承诺**不会做**的几件事：

### 不做 · 收费 Verified
- 不会推 999 元/年版本
- 不会推 199 元/月版本
- 不会推任何"加速审核"的付费选项
- 即使 Hub 商业化压力变大，也不会用 Verified 做收入工具

如果未来要在 Hub 上加付费功能（咨询撮合、企业目录等，详见第 11 章），那是**完全独立的产品**，不会跟 Verified 标志混淆。

### 不做 · 隐藏排序加权
- Verified Creator 在 Hub 里**不会**有隐藏的搜索排名加权
- Trending 算法对 Verified Creator **没有**任何特殊系数
- 唯一的视觉差异是：作者卡片上显示一个 ✓ 标志、`/author/{user}/` 页面上显示 Verified 徽章
- 这条规则的存在原因：**让用户决定 Verified 值不值钱，而不是让 Hub 暗箱替用户做决定**

### 不做 · 邀请制门槛
- Verified 不需要"被推荐"才能申请
- 任何作者都可以主动提交申请
- Hub 不会建立"内部圈"——不会有"内推有捷径、自申请要排队"的双轨制

### 不做 · 数量限制
- Q2 通过率预测是 15-25%，但**没有数量上限**
- 如果某个季度有 200 个合格申请，那就通过 30-50 个
- 数量限制会让 Verified 变成**资源稀缺品**而不是**质量信号**

---

## 10.9 给 Skill 作者的现实建议

如果你正在考虑申请 Verified，下面这些是基于上面所有规则的现实操作建议。

### 建议 1 · 不要盯着 Verified 来设计你的 Skill
**Verified 应该是你做出好作品之后的副产品，不是目标本身**。如果你为了拿 Verified 而强行 commit、强行刷 stars、强行写文档——你能拿到 Verified，但你的 Skill 不会因此变好。

而 Verified 撤销机制会持续观察你，长期不实质迭代会被收回。所以盯着 Verified 设计是负和游戏。

### 建议 2 · 选 1 个深耕的 Skill，比 5 个广撒的强
评分公式里，质量分用的是**最高分 Skill** × 1.0 + 数量奖励 × 5。也就是说一个 80 分的 Skill 比 5 个 50 分的 Skill 更有价值（80 vs 50+25=75）。

第 6 章第 5 节讲过：声明 "for myself, sharing in case useful" 的 Skill 6 个月存活率 51%，声明 "for everyone" 的 23%。**深耕 vs 广撒**这个原则在 Verified 评分上得到了再次验证。

### 建议 3 · 第三方背书比刷 stars 重要
社区分里，每 1 个外部背书 = 20 分。10 个外部背书直接拉到上限（封顶 40）。而你需要 1000 stars 才能拿到等量的分。

意思是：**与其花 3 个月去推广刷 stars，不如花 1 个月去**：
- 给 1-2 个 awesome list 提 PR 加上你的 Skill
- 写 1 篇说明你的 Skill 做什么的 blog post
- 在某个相关 issue / discussion 里分享你的 Skill 解决方案

### 建议 4 · 申请被拒不丢人
Q2 通过率 15-25% 意味着大多数申请会被拒。被拒不代表你的作品不好，可能只是当下还没满足"持续迭代 90 天"或"社区反馈"等具体条件。

Hub 的 review 反馈会**明确告诉你欠在哪一项**——不是模糊的"再努力"。修补之后任何时候都可以重新申请。

### 建议 5 · 不要为了 Verified 而做 batch dump
那 6 个 batch dump 账号是 Hub 里被永久封禁的少数案例。Verified 项目对 batch dump 是**零容忍**的——一旦被识别，账号本身被封禁，相关仓库被从 Hub 移除。

你可能觉得"我多发几个 Skill 提高曝光率"，但 Hub 的 fraud detection 会识别**新仓库 + 相同模板 + 短时间内 stars 异常**这些信号。**得不偿失。**

---

## 10.10 一个开放问题

写完这一章我心里有个想不清楚的事：**Verified Creator 真的能解决 Hub 的核心问题吗？**

第 3 章讲过 Hub 的核心问题是 Gini 0.983——99% 的作者拿 17% 的 stars。Verified Creator 把"被信任的作者"标出来，理论上能让用户**绕开沉默大多数**直接找到值得的人。

但 Verified Creator **不会**改变 Gini 系数。它只是**让 Top 1% 更容易被找到**——不会让 Bottom 99% 的作品质量提升。

某种意义上，Verified Creator 是一个**承认现状**的设计：既然 99% 拿 17%，那就帮 1% 让用户找得到。这是务实，但也是放弃了"让长尾活下来"的野心。

第 11 章的咨询撮合 + 企业目录是另一个尝试——通过收入路径让 Bottom 99% 里有"非头部但有专业能力"的作者活下来。Verified 是品牌信号，那个是经济信号。两条路一起跑，看 12 个月后哪个真有效果。

---

## 数据来源 + 修订记录

- 评分公式：基于 Hub `skills` 表 + GitHub `commits` API
- 申请表：当前版本 v0.3（2026-04-23），随用户反馈持续迭代
- 撤销条件：截至 2026-04-23，无任何 Verified Creator 被撤销（因为 Founding Members 翻车后名单已清空）
- 这一章的所有规则**会随实践调整**。本书的 GitHub repo 会持续更新最新版本，纸质版 / PDF 版只代表写作时点的状态。

下一章（第 11 章）讲咨询撮合 + 企业目录 + 完整定价推导。
