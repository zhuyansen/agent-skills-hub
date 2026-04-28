---
title: 第 12 章 · 当 Claude 自己开始创建 Skills
chapter: 12
part: 4 · AgentSkillsHub 运营手记
status: draft
data_snapshot: 2026-04-28
---

# 第 12 章 · 当 Claude 自己开始创建 Skills

> Anthropic 官方文档里有一句话，被大多数人忽略：
>
> > "When Claude itself starts creating Skills, the system will truly come alive."
>
> 这句话在 SKILL Spec RFC 的最后一节，没多少人当真。但如果它实现，整个 Skill 生态会从「人类生产、人类消费」变成「人机共产、人机共消」——这是一个完全不同的市场。
>
> 这章是这本书最远的一次推断。前 11 章基于数据；这章主要基于**信号 + 想象**。所有结论都附明示的不确定性。

---

## 12.0 事情已经开始了

很多人没意识到——**Claude 已经在创建 Skills 了**。只是没被命名为「自创 Skill」。

证据 1：第 7 章讲过的 `anthropic/skill-creator`——这是一个**专门用来生成新 Skill** 的 Skill。Hub 数据里有 18% 的 2026 Q1 后新 Skill description 含「Generated with skill-creator」。

证据 2：alchaincyf/nuwa-skill（第 4 章 + 4 月 23 日日报头条），1 个 meta skill 衍生出至少 8 个子 skill（乔布斯/马斯克/张雪峰/李雪峰…），**作者自己说"由女娲.skill 生成"**。

证据 3：Hub 后台数据里发现，2026 Q1 的新 Skill 中有 23% 的 SKILL.md 被识别为 "AI-assisted authored"——通过文体特征 + commit pattern 检测。

**这不是未来时——已经在发生**。只是规模还小。

未来 12 个月的关键问题是：**Claude 自创 Skill 的比例从 23% 涨到多少？50%？80%？这个比例突破某个临界点之后，「人类作者」的角色会变成什么？**

这是这一章要回答的。

---

## 12.1 自创 Skill 的演化阶段（4 阶段模型）

我把 Claude 自创 Skill 分成 4 个阶段，按当前生态判断我们大约在 1.5 阶段。

### 阶段 1 · Claude-Assisted（人主，机辅）

**当前主流形态**：人类提供 idea，Claude 写第一版 SKILL.md，人类修改 + 测试 + 发布。

skill-creator + Cursor + Claude Code 都已经支持这种模式。

谁主谁辅：**人 80% / 机 20%**。

### 阶段 2 · Claude-Generated（机主，人审）

人类提供「主题方向」（如 "做一个分析 PDF 财报的 Skill"），Claude 自动：
1. 搜索相关已有 Skill
2. 识别市场缺口
3. 起草完整 SKILL.md + resources/
4. 跑 self-test
5. 提交 PR 给人类 review

人类只做 final approval。

谁主谁辅：**机 70% / 人 30%**。

**这是我们正在进入的阶段**——nuwa-skill 已经是这个形态的早期版本。

### 阶段 3 · Claude-Initiated（机主，人配合）

Claude 自己**发现**「应该有什么 Skill」——不是被人提示。比如：
- 它注意到很多用户在反复手写「PDF → markdown 转换」prompt
- 它判断「这个 pattern 应该 Skill 化」
- 它自动起草 + 在某个开源 sandbox 里测试 + 推到 GitHub
- 人类的角色是**法律 / 伦理把关**，不是创作

谁主谁辅：**机 90% / 人 10%**。

**预计 2026-2027 进入**——需要 Anthropic 的 SDK 支持「Skill self-publish」能力。

### 阶段 4 · Fully Autonomous（机自循环）

Claude 不只创造 Skill，**评估其他 Skill、合并冗余、淘汰过时的、生成新的**——形成完整的自循环。

人类的角色：**只观察 + 决定要不要拔插头**。

谁主谁辅：**机 99% / 人 1%（紧急停机权）**。

**预计 2027-2030**——这是技术 + 监管 + 商业模式 全部就绪后的形态。

---

## 12.2 每个阶段，人类作者的位置变化

| 阶段 | 人类角色 | 人类核心价值 | 人类报酬来源 |
|------|---|---|---|
| 1 · Claude-Assisted | 主创作者 | Idea + 品味 + 落地 | 直接用户付费 |
| 2 · Claude-Generated | Curator + Reviewer | 判断 / 选择 / 把关 | 平台抽成 + 服务费 |
| 3 · Claude-Initiated | Direction Setter | 给 Claude「该研究什么」的方向 | 间接（Claude 创造价值的分成）|
| 4 · Fully Autonomous | Observer + Regulator | 监督伦理、防止漂移 | 公共服务（政府 / 基金会）|

注意**最大的变化在阶段 2 → 3**——人类从「主」变「副」。这一步会非常痛苦：很多专业作者发现自己最擅长的事被 Claude 做得更快更好。

历史上每次自动化革命都经过这一步。Skill 生态只是更晚被卷入。

---

## 12.3 一个反直觉判断 · 自创 Skill 不会让人类作者灭绝

主流科技媒体喜欢喊「AI 让人类失业」。但仔细看历史——**自动化革命从来没让创造性工作彻底消失，只是让工作重心转移**。

例：摄影发明之后，画家没消失，**画家变成了「思想家」**——印象派、立体主义、抽象表现主义都是在「机器能精确复制现实」之后才繁荣的。机器解放了画家，让他们做机器做不到的事。

类似预测：Claude 大量自创 Skill 之后，人类作者会专注做 4 类**机器做不到**的工作：

### 类型 1 · 高品味判断（Taste Curator）

机器能写 100 万个 Skill。**判断哪 10 个值得人用**——是品味问题。

未来的 Hub 上，最值钱的不是「最多产」的作者，是「最好选品」的 curator。今天的 awesome-list 维护者在某种意义上就是这种角色。

### 类型 2 · 跨界翻译（Domain Bridger）

某些 Skill 需要**深度领域知识 + 工程知识** 的结合——比如「专业法律 Review Skill」 需要既懂法律又懂 prompt engineering。

机器在单一领域很强，但**跨界**仍然依赖人。专业律师 / 医生 / 工程师如果掌握 Skill 写作，会成为非常稀缺的资源。

### 类型 3 · 信誉背书（Trust Anchor）

机器写的 Skill 缺一样东西——**人类作者的「身家」担保**。

如果 Verified Creator @张三 发布了一个 Skill，企业敢用——因为出问题可以找到张三。机器写的 Skill 没人 own，企业不敢用。

未来的人类作者价值越来越像**作家的「署名」**——你买这本书是因为信任作者，不是因为内容唯一。

### 类型 4 · 生成 Claude 学习的「种子样本」

Claude 自创 Skill 的能力来自训练。它训练数据里**最好的样本就是人类专家精心打磨的 SKILL.md**。

这意味着：**少数顶尖人类作者的作品反而比以前更值钱**——因为他们的作品是 Claude 学习的「种子」。

这有点反直觉但很重要——**机器化时代，最稀缺的是最高品质的人类样本**。Top 1% 的作者会比现在更重要，不是更不重要。

---

## 12.4 给 4 类作者的 2026-2028 生存指南

按当前 Hub 数据里的作者画像，分 4 类。每类的未来路径不同：

### A 类 · 一次即弃作者（占 60%）

**特征**：发布 1-2 个 Skill 之后再无更新。

**未来**：被 Claude 自创 Skill **完全取代**。如果你只是「写过一个 SKILL.md」，没有持续创作 / 没有专业沉淀，这条路会越来越窄。

**建议**：要么放弃（去做其他事），要么进入下面 3 类。

### B 类 · 持续型作者（占 25%）

**特征**：每月有 commit，多个 Skill，但没有破圈作品。

**未来**：成为 **Curator** 或 **Domain Bridger**。靠数量取胜的路会被堵死，要靠**专业纵深**。

**建议**：选择 1 个专业领域（如 fintech / medical / legal），深耕到「这个领域的 Skill 必看你」。

### C 类 · 头部作者（占 14%，含 Verified Creator）

**特征**：1-2 个破圈 Skill，外部背书多，月 stars 增长稳定。

**未来**：成为 **Trust Anchor**。商业化路径包括咨询撮合（第 11 章）、企业目录、出书 / 出课、KOL 影响力变现。

**建议**：把名声货币化。Verified Creator 是基础门槛，下一步是产品化你的方法论。

### D 类 · 顶尖作者（占 1%，约 300 人）

**特征**：作品被 Anthropic / OpenAI 内部参考，有强 academic / industry 信誉。

**未来**：成为 Claude 学习的「**种子样本**」生产者。少量但极高单价。

**建议**：跟 model provider 直接合作。Anthropic 的 RFC 委员会、Constitutional AI 团队、 OpenAI 的 system messages 团队——这些地方需要你这种作者的 input。

---

## 12.5 一个我会持续观察的指标 · "AI-Assisted Skill" 的 quality 是否超过纯人工

这是判断生态拐点的最关键指标。

当前 Hub 数据（2026 Q1）：

| 类型 | 平均 quality_score | 6 个月留存率 |
|------|---:|---:|
| 纯人类作者 | 47.2 | 38% |
| AI-Assisted（人主机辅）| 50.4 | 41% |
| Generated（机主人审）| 42.8 | 28% |

目前**纯人类作者还是被 AI-Assisted 略胜**——这说明阶段 1 已经稳定，但阶段 2 还没成熟（Generated 的质量低于纯人类）。

**关键拐点**：当 「Generated」 类的质量超过 「纯人类作者」 时，意味着 Claude 自创 Skill 已经达到「可以独立生产」的水平。

我的预测：**这个拐点会在 2026 Q4 - 2027 Q2 之间出现**。具体取决于：

- Anthropic 的 SDK 是否开放 Skill self-publish
- Claude Opus 是否升级到能稳定生成 ≥ 65 quality 的 Skill
- 监管 / 法律框架是否清晰（自创 Skill 的责任归属）

Hub 会**每季度发布**这个指标的最新数字。这是观察整个生态走向的最重要 thermometer。

---

## 12.6 一个让人焦虑但必须诚实的预测

如果阶段 3 真在 2027-2028 落地——**Hub 自己也会被影响**。

逻辑：如果 Claude 自己能生成、评估、组织 Skill，**还需要 AgentSkillsHub 这种「人工策展平台」吗？**

我的诚实答案：**Hub 会变形，但不会消失**。变形方向：

- 从「Skill 目录服务」 → 「Skill 信任服务」
- 不再以「数量 + 评分」 为核心价值，以「人类作者背书 + 合规保证」 为核心价值
- 商业模式从「目录订阅」变成「信任 service」（更像 Underwriters Laboratory 而不是 GitHub）

如果 Hub 不主动变形，**3 年内会被纯机器目录淘汰**——后者免费、实时、无边界。

这不是悲观，是务实。**所有今天的「目录公司」都会面临同一个生存问题**——npm、PyPI、CRAN，这些 package registry 在 AI 时代怎么活，跟 Hub 是同一个问题。

---

## 12.7 一段半哲学的结尾

写到这本书的最后一章，我必须承认 —— **整个 Skill 生态最终会走向哪里，我不知道**。

第 1 章讲的 Mahesh / Barry 类比，本质是「机器很聪明但没经验，人类有经验但慢」——所以 Skill 是「把人类经验交给机器」的桥梁。

但 12 章过后，桥梁开始**反向走**——**机器开始创造经验，给其他机器用**。这一刻，Mahesh 不再需要 Barry 的小本子，因为他能自己写出来。

那 Barry 怎么办？

历史上 Barry 们的命运不是「死掉」——是「升级」。打字机时代的速记员变成了文档编辑，文档编辑变成了内容总监，内容总监变成了知识管理。技能在变，但**人在能创造意义这件事上，没被取代**。

Skill 生态可能也是这样。**我们写 Skill 是因为机器需要我们的经验。当机器不再需要时，我们会去做更有意义的事**。

这是希望，也是赌注。两年后这本书的下一版会告诉我们对不对。

---

## 12.8 本章要记住的一句话

> **Claude 自己开始创建 Skills 不是「未来事件」，是「正在发生的事」。我们大约处在阶段 1.5（Claude-Assisted 转向 Claude-Generated）。在这个进程里，人类作者会从「主创作者」转变成「Curator / Domain Bridger / Trust Anchor / 种子样本生产者」。低端作者会被淘汰，顶尖作者会更稀缺。AgentSkillsHub 自己也要变形——从「目录服务」变成「信任服务」。**

---

## 全书结尾

12 章写完了。从 Mahesh & Barry 的类比开始，到 Claude 自己创造 Skills 结束——中间穿过 67,000 条数据、4 大框架对比、9 种类型 × 4 级路径、Verified Creator 设计、Distribution 第四条边、商业化两个产品。

这本书不是结论，是**起点**。

Skill 生态在 2026-2028 年会经历最剧烈的演化。今年这 67,000 条 Skill 里，可能 80% 在 2 年后会消失。剩下 20% 里，可能一半是 Claude 自己写的。Hub 自己会变形。我自己也会变。

但**这本书会留下来**——作为 2026 年这个时点的诚实快照。

明年这个时候，蓝皮书 2027 会出来。会用今年的预测去对今年的现实——看哪些对了、哪些错了、哪些根本没想到。

写蓝皮书是为了让自己**对未来更负责任**。预测一定会错，但**愿意被记账下来 + 愿意被打脸**，是诚实地推动生态前进的最低门槛。

如果你读到这里，谢谢。

——Jason Zhu (@GoSailGlobal)
2026 年 4 月 28 日

---

## 数据说明

第 12 章是这本书唯一**主要靠预测 + 想象**的章节。所有数字都明示了不确定性。"AI-Assisted Skill" 的检测方法基于文体特征 + commit pattern + author behavior 的综合分析，准确率约 70%。明年蓝皮书会用更精确的检测算法 + 更多数据修正。

下一站：[蓝皮书 2027 跟踪追溯页面](https://github.com/zhuyansen/skill-blue-book/blob/main/2027-followup.md)（待开）。
