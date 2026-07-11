# 本周行动板(2026-07-10 定版)

| # | 进水口 | 谁 | 动作 | 状态 |
|---|---|---|---|---|
| 1 | ~~**Awesome 列表 PR** ×3~~ | 🤖 我全自动 | fork→按格式加条目→PR(awesome-mcp-servers + Claude 系两个),一列表一 PR 不群发 | ✅ 07-10:新 PR ×2(travisvn [#965](https://github.com/travisvn/awesome-claude-skills/pull/965) · BehiSecc [#445](https://github.com/BehiSecc/awesome-claude-skills/pull/445))+ 刷新存量 ×2(punkpeye [#9142](https://github.com/punkpeye/awesome-mcp-servers/pull/9142) · Composio [#747](https://github.com/ComposioHQ/awesome-claude-skills/pull/747) 均更到 130K+安全分级);wong2 互动受限、hesreallyhim 暂停收件(详见 §Awesome PR 战报) |
| 2 | ~~**Tier 1 自助收录** ~17 站~~ | 🤖 我跑大半 | 无头浏览器逐站提交(MCP 群/Skills 群/导航群);要登录/验证码的留人工 | ✅ 07-10 清完我这半:**libhunt 已收录**([页面](https://www.libhunt.com/r/agent-skills-hub),自动过审)· deepwiki ✅ · SKILL.md 已挂进 MCP 仓库(喂 3 个被动爬取站)· 5 站确认死站/无入口划掉 · **剩 6 站需你人工**(见 §Tier 1 战报,文案已备)|
| 3 | ~~**Zenodo DOI**~~ | 🧑 你 10 分钟 | ✅ 07-10 发布:[10.5281/zenodo.21292799](https://doi.org/10.5281/zenodo.21292799)(CC-BY-4.0);已回填论文 §Availability + HF 卡片(HF 推送待网络恢复)+ sameAs | ✅ |
| 4 | ~~**Wikidata 实体**~~ | 🧑 你 15 分钟 | ✅ 07-10 全绿:[Q140478987](https://www.wikidata.org/wiki/Q140478987) — P31=website(带 reference)· P856=agentskillshub.top · P571=2026;站点 sameAs 双向确认已上线 | ✅ |
| 5 | ~~**AlternativeTo + StackShare**~~ | 🧑 你 各 15 分钟 | ✅ AlternativeTo 上线([收录页](https://alternativeto.net/software/agent-skills-hub/about/));❌ StackShare 拒收("does not fit supported categories"——它只收 SaaS/技术栈组件,目录站不在框内,**放弃不再试**) | ✅(半) |
| 6 | ~~**Ahrefs 免费站长版**~~ | 🧑 你 10 分钟 | ahrefs.com/webmaster-tools 注册→验证域名(GSC 授权最快)→外链监控第二视角 | ✅ 07-10 开通 |
| 7 | ~~creati.ai 验收~~ | 🧑 你 5 分钟 | ✅ 07-10 收录页验毕:4 链中 **3 条 dofollow**(2 条带 utm_source=creati.ai,GA 归因干净)+1 nofollow —— 真权重位,$79 值。**剩:向客服要 9 链完整清单**(本页仅 4 条) | ✅(剩要清单) |
| — | arXiv→媒体→Reddit/HN | 等背书 | 弹药链不拆开动 | ⏸ |
| — | PH / PwC / HARO | 押后 | arXiv 波之后 | ⏸ |

**周末验收口径**:外链域 32 → 50+(Bing 报表复查);GA 来源出现新 referral。

## Ahrefs 基线(2026-07-10 首测,以后每月对账)

| 指标 | 值 | 解读 |
|---|---|---|
| **DR** | **6** | 权重线问题的量化病根:品牌词 pos 11、pos50+ 词、Ahrefs 关键词 0 —— 全由它解释 |
| UR(首页) | 4.4 | — |
| Backlinks / Ref.domains | 10.7K / **313** | 比 Bing 的 32 域多 10 倍(Ahrefs 索引含大量采集站/镜像,质量子集依旧小)|
| Organic keywords / traffic | **0 / 0** | Ahrefs 词库有量级门槛,我们的长尾位次进不了它的索引 —— **不代表没流量**(GSC 实测每天 ~8 clicks),别恐慌 |
| **AI responses(全平台)** | **0** | Ahrefs 新出的 AI 引用指数(抽样热门 prompt);GA 实测已有 40 会话 AI 引荐 —— 说明引用发生在它的抽样之外。**这是 ①b GEO 的第三块水位表,每月看** |

**验收基准**:本周行动(Awesome/Tier1/Zenodo/Wikidata)+ arXiv 之后,下月对账看 DR 6 → ? 和 AI responses 0 → ?


---

# 外链建设 Todolist — agentskillshub.top

> 目标:稳定增长高质量外链,提升域名权威 + 开发者精准流量。
> **为什么这是本站 SEO 的真瓶颈**:`.top` 是低信任后缀 + 品牌名 "Agent Skills Hub" 是通用大词,
> 两刀叠加 → 缺权威、缺独特性,靠 on-page 优化打不穿天花板。唯一的杠杆是**真实的外部信任票**
> (权威反链)。GEO 同理:2026 Google/Bing 指南把反链当作 AI 搜索引擎决定"引谁"的最强品牌权威信号。
>
> 用法:**Tier 1 两周内做完**(一次性、高价值);**Tier 2 每天挑 3–5 个做**(轮换);
> 每做一个在 §跟踪表 记一行,避免重复 / 被当 spam。
>
> 🟢 = 我可以帮你起草文案/PR;🔴 = 必须你本人发布(账号/发帖)。
> **铁律**:每条都带真实价值(回答真问题、补真资源),别同一条链到处刷,锚文本要变。
>
> **与其它 ops 文件的关系(别重复劳动)**:
> - MCP 注册站(Glama / mcp.so / PulseMCP / Smithery / mcpservers.org)已在 [`mcp-registry-submissions.md`](./mcp-registry-submissions.md) 单独跟踪 —— 本文件不重复,只在下表标 ✅ 引用。
> - 徽章回链外联在 [`badge-outreach.sh`](./badge-outreach.sh) + [`master-outreach-tweets.md`](./master-outreach-tweets.md)。
> - PH / 发布日节奏在 [`launch-playbook.md`](./launch-playbook.md)。
> - 竞品/定位话术在 [`competitor-notes.md`](./competitor-notes.md)。

---

## 🎯 排序总表 · 按 (GEO+SEO ROI × .top 可行性) 排

> **可行性 = .top 域名能否被收录**。高门槛人工审核目录常拒 `.top`(标注了);
> 面向"资源/study"而非"AI 工具"的渠道基本不看后缀,可行性反而高 —— 这正是本站该主攻的方向。
> **ROI 分**:综合 DR 权重 + 开发者精准度 + GEO(被 LLM 引用概率)。

| # | 渠道 / 平台 | 类型 | DA/DR 量级 | do/nofollow | 提交门槛 | 难度 | .top 可行性 | 备注 |
|---|---|---|---|---|---|---|---|---|
| 1 | **arXiv**(cs.CR 发论文) | 学术引用源 | DR 90+ | dofollow(PDF/HTML 内链) | 需 endorser + 真论文 | 中 | ✅ 高(看内容不看域名) | 已有 130K 数据集论文草稿。最高权威 + "study 不是 tool" 定位,被后续论文/媒体反复引 |
| 2 | **Hugging Face Datasets** | 数据集托管 | DR 90+ | dofollow(dataset card 内链) | 免费,传 parquet+card | 低 | ✅ 高 | 已有 `hf-dataset-card.md` + 导出好的 parquet/csv。card 内链回站,HF 页本身进 Google+被 LLM 抓 |
| 3 | **GitHub `awesome-claude-skills` 系列 PR** | awesome list | 各 repo DR 中-高 | nofollow(GitHub) | 提 PR | 低 | ✅ 高 | 真实存在多个:travisvn / ComposioHQ / BehiSecc / mingrath / GetBindu / Chat2AnyLLM。开发者精准 + GEO 高(LLM 训练重 awesome-list) |
| 4 | **GitHub `awesome-mcp-servers` / 官方 servers PR** | awesome list | DR 高 | nofollow | 提 PR | 低 | ✅ 高 | punkpeye #9142 ⏳ / 官方 #4060 ⏳ / wong2 ❌双关闭。状态见 §Tier1-A |
| 5 | **Hacker News — Show HN** | 社区讨论 | DR 90 | nofollow | 需账号+硬故事 | 中 | ✅ 高 | 用"审计了 13 万 skill,83% 无人审计"这个数据故事发,不是"看我的目录"。前 6h 全程回帖 |
| 6 | **Product Hunt** | 工具目录/发布 | DR 90 | dofollow(产品页) | 需账号+发布日 | 中 | ✅ 高 | 单日流量+dofollow 大爆发;择 hunter、按 launch-playbook 走 |
| 7 | **Reddit** r/ClaudeAI · r/mcp · r/LocalLLaMA · r/ChatGPTCoding | 社区讨论 | DR 90 | nofollow | 需养号真回答 | 中 | ✅ 高 | GEO 极高(ChatGPT ~12% / Perplexity ~18% 引 Reddit)。搜 "where find MCP servers" 类真问题作答 |
| 8 | **There's An AI For That (TAAFT)** | AI 工具目录 | DA 60+ | dofollow | 表单(部分收费加速) | 低 | ⚠️ 中(收但审核偏严) | 最大 AI 工具目录、被 AI Overviews 引用。定位成 "MCP/agent-skill directory" |
| 9 | **Futurepedia** | AI 工具目录 | DA 65+ | dofollow | 表单 | 低 | ⚠️ 中 | 高 DA,68 万月访;审核有队列 |
| 10 | **AlternativeTo** | 软件替代目录 | DA 80+ | nofollow(多) | 账号提交 | 低 | ✅ 高 | 列为 LobeHub / mcp.so 的替代品,精准截流 |
| 11 | **claudemcp.org / claudemcp.com** | 垂类 MCP 目录 | DR 中 | 多 dofollow | 表单/PR | 低 | ✅ 高 | 垂直精准,专收 MCP/Claude 资源 |
| 12 | **Dev.to**(自有文章) | 开发者博客 | DA 90 | dofollow(正文链) | 免费发文 | 低 | ✅ 高 | 发"如何挑安全的 MCP server"类真干货,自然引 Hub。已有 `devto-securing-117k.md` 草稿基础 |
| 13 | **SaaSHub** | SaaS 目录 | DA 60+ | dofollow | 账号提交 | 低 | ✅ 高 | 收 `.top`;附带 alternatives 页 |
| 14 | **StackShare** | 技术栈目录 | DA 80+ | nofollow | 账号 | 低 | ✅ 高 | 建 tool 页,进技术选型语境 |
| 15 | **Lobsters** | 技术社区 | DR 高 | nofollow | 需邀请码 | 高 | ✅ 高(若有邀请) | 比 HN 更硬核;没邀请码跳过 |
| 16 | **HARO / Featured.com / Qwoted** | 专家引用→媒体 PR | 目标媒体 DR 高 | 多 dofollow | 真人答记者问 | 中 | ✅ 高(链出现在第三方媒体) | 用 "13万 skill 安全普查" 数据当引用弹药,答 AI-agent 安全类记者问 |
| 17 | **theresanaiforthat 替代目录群**(dofollow.tools / thesaasdir / toolify) | AI 工具目录 | DA 40-55 | 部分明示 dofollow | 表单 | 低 | ✅ 高 | 一次别刷太多(3-4 个/发布周);低 DA 目录堆多反稀释 |
| 18 | Cline MCP Marketplace(github.com/cline/mcp-marketplace) | 垂类 marketplace | DR 高 | nofollow | 开 issue | 低 | ✅ 高 | 见 mcp-registry 文件"第二波" |
| 19 | **Wikidata → Wikipedia**(长线) | 实体/知识图谱 | DR 极高 | 混 | 需 5+ 独立权威源 | 极高 | ⚠️ 靠内容非域名 | **先攒 5 篇独立媒体报道再动**(#1/#5/#16 是弹药)。先建 Wikidata 实体(门槛低,LLM 重之) |
| 20 | 通用低 DA 目录 / guest post | 泛目录 | DA 低 | 混 | 各异 | 低 | — | 前 19 项没做完前**别碰**,2026 GEO 价值极低 |

**门禁陷阱(.top 明确会卡的)**:G2 / Capterra 要企业邮箱+验证,`.top` 独立开发者站基本进不去,**跳过**(它们对我们这种目录站 ROI 也低);Wikipedia 正文条目卡 notability 不卡域名,但要 5+ 独立源,属长线(#19)。

---

## 💎 3 个 "Linkable Asset" 点子(基于已有资产,撬动不同链)

> 反链的本质是"别人愿意主动链的东西"。我们已有的资产刚好能造 3 类诱饵。

### 资产 1 · 130K Agent-Skill 安全普查数据集(最强)
- **是什么**:已导出的 `agent-skills-security-grades.parquet/csv`(13 万+ skill/MCP 的安全等级+质量分)+ arXiv 论文草稿 + HF dataset card。
- **撬动哪类链**:
  - **学术链**(arXiv #1 / HF #2):这是活跃研究领域 —— 已有多篇 arXiv 论文在做 agent-skill 安全实证(SkillFortify、AgentThreatBench 等),我们是**唯一开放全量分级数据集**的,会被后续论文/综述反复引(dofollow + 极高权威)。
  - **媒体/HARO 链**(#16):"13 万 skill,83% 无人审计,3.3% UNSAFE" 是记者要的数据钩子。
  - **HN/Reddit 讨论链**(#5/#7):数据故事天然适合 Show HN。
- **为什么强**:把定位从"又一个 AI 目录"(大家不链)升级成"发布了研究的机构"(大家引)。直击品牌大词无独特性的病根。

### 资产 2 · 公开的质量评分 + 安全分级方法论
- **是什么**:6 维质量分 + SAFE/CAUTION/UNSAFE/UNAUDITED 安全分级(源自 SlowMist agent-security taxonomy),已有 `scoring-algorithm.md` / `mcp-server-spec.md`。
- **撬动哪类链**:
  - **"How we grade" 方法论页** → awesome-list 里当"评测标准"资源被链(#3/#4);写博客的人引"某某站是这么给 MCP 打安全分的"。
  - **HARO 专家引用**:回答"如何判断一个 MCP server 安不安全"类记者问,链回方法论页。
- **为什么强**:方法论页是"参考资料"性质,比首页更容易被自然引用(裸链+dofollow 概率高)。

### 资产 3 · `ash` CLI(npm `@agentskillshub/cli`)+ 免费 MCP server
- **是什么**:开源 CLI + `@agentskillshub/mcp`,`npx` 即用、离线缓存、装前带安全分。
- **撬动哪类链**:
  - **awesome-list / registry 收录**(#3/#4/#11/#18):CLI/MCP 是"工具",天然进 awesome-mcp / cline-marketplace / Glama(已✅)。
  - **Dev.to 教程链**(#12):"用一行 npx 在装 MCP 前先查安全分"——工具类教程正文链。
  - **GitHub repo 互链**:被收录的 skill 作者 repo 加 "indexed on AgentSkillsHub" 徽章(见 badge-outreach)。
- **为什么强**:免费工具 = 开发者会自发写进自己的 dotfiles/教程,产生我们不用外联的"被动链"。

---

## ✉️ Top 10 目标 · 即发外联/提交草稿

> 每条标注:**do/nofollow**、**需不需真人手动发**、**预计通过率**。语言按目标平台。

### 草稿 1 — arXiv(#1)· 论文提交(dofollow · 🔴 真人 · 通过率 高,门槛在 endorser)
论文本体走 `ops/research/arxiv-paper-draft.md`。这里是**找 endorser 的邮件**(cs.CR 首投必须):
```
Subject: arXiv cs.CR endorsement request — security survey of 130K agent skills

Hi Prof. [Name],

I'm Jason Zhu, an independent researcher. I've written an empirical paper,
"The Long Tail Is Unaudited: A Security Survey of 130,173 Open-Source AI Agent
Skills and MCP Servers." It security-grades the full public catalog with an
11-category scanner and finds 3.3% UNSAFE / 83% entirely unaudited — the risk
sits in the long tail no marketplace flags.

The full graded dataset is released openly (CC-BY-4.0). Given your work on
[their agent-security / supply-chain paper], I'd be grateful if you'd consider
endorsing this for cs.CR. Draft PDF + dataset attached. Happy to add any
caveats you'd want to see.

Thanks for your time,
Jason Zhu — agentskillshub.top
```
> ⚠️ endorser 早点约(#1 备注)。数字提交前用 Supabase 刷新(草稿里已标 2026-07-06)。

### 草稿 2 — Hugging Face Datasets(#2)· dataset 页(dofollow · 🔴 真人建库 · 通过率 极高)
建库 `huggingface.co/new-dataset` → repo `agentskillshub/agent-skills-security-grades`,README 直接贴 `hf-dataset-card.md`(已含回站链)。传 `ops/research/out/*.parquet`。
配套一条 announce(发 X / 贴 dataset 页):
```
Released: security grades + quality scores for 130,173 open-source AI agent
skills & MCP servers, as an open dataset (CC-BY-4.0).

3.3% grade UNSAFE. 83% are completely unaudited.

Data + methodology → huggingface.co/datasets/agentskillshub/agent-skills-security-grades
Live index → agentskillshub.top
```

### 草稿 3 — awesome-claude-skills PR(#3)· (nofollow · 🟢 我起草PR · 通过率 中-高)
对 travisvn / ComposioHQ / BehiSecc / mingrath 各提一个 PR,加到 "Directories / Resources" 区(**别加到 skill 列表主体,会被拒**):
```markdown
- [Agent Skills Hub](https://agentskillshub.top/) — Searchable directory of
  130K+ open-source Claude skills & MCP servers, each with a quality score and
  a SAFE/CAUTION/UNSAFE security grade checked before you install.
```
PR 描述:
```
Adds Agent Skills Hub to the Resources/Directories section. It's a discovery
+ trust layer over the open skill ecosystem — every entry carries an automated
security grade and quality score, which complements the curated picks in this
list. Not a skill itself; a directory to find and vet them. No affiliation ask,
just a resource for readers. Thanks for maintaining this list!
```
> 一天最多提 1–2 个,锚文本轮换("MCP server directory" / "open agent skills catalog")。

### 草稿 4 — Hacker News Show HN(#5)· (nofollow · 🔴 真人 · 通过率 中,靠故事)
标题(不写 "directory",写数据发现):
```
Show HN: I security-graded 130K AI agent skills — 83% are unaudited
```
正文首帖:
```
I run agentskillshub.top, an index of open-source AI agent skills and MCP
servers. Installing one runs third-party code with your agent's full
permissions, so I built an 11-category scanner and graded the whole public
catalog — 130,173 artifacts.

Findings: of the ~21.5K popular enough to grade (>=5 stars), 3.3% are UNSAFE
and 8.8% carry at least a CAUTION flag. But the real story is the long tail:
83% of the catalog has no trust signal from any marketplace at all.

The full graded dataset is open (CC-BY-4.0, link in a comment). The site lets
you search and see each skill's grade before installing. Happy to answer
questions on the methodology / false-positive rate — it's rule-based, not
perfect, and I'd genuinely like feedback on the taxonomy.
```
> 周二 9am ET 发;前 6h 全程回帖。数据集链放**评论**里(帖里放太多链易被降权)。

### Reddit 作战卡 v2(2026-07-11,吸收 Alisa 230 万 views 复盘 mp.weixin.qq.com/s/r_xvZtQ_fm9qW5-ntV1G4w)

**为什么升级优先级**:Perplexity 46.7% 的 AI 引用来自 Reddit、Google AIO 占 21% —— Reddit 是 ①b GEO 的主放大器,不是 nofollow 鸡肋。昨天日报 perplexity 刚现身(3 会话),这是杠杆点。

**三个修正(对照旧草稿 5)**:
1. **养号先行,今天就开始,不等 arXiv**:CQS(贡献者质量分)需要周级积累。姿势:选定 r/mcp + r/ClaudeAI 垂直深耕,每天 20 分钟看 Rising、点赞、写 20 词+的干货评论;不买号、不去 karma 农场、先别带任何链接。arXiv 弹药到位时账号才是热的。
2. **评论寄生改打长尾新帖**:泛词(best mcp servers)搜出的是老帖,新评论易被 Automod 干掉;用具体场景词找 7 天内新帖 + 盯 Rising。**回自己老帖补 UPDATE 是成功率最高的动作**(时间戳体:"UPDATE (Aug 2026): numbers refreshed…"——月报每月给一次全帖保鲜的理由)。
3. **首帖用数据故事体**(文章实测最易起量的形式):"I security-graded 130,000 MCP servers — 83% have never been audited. Patterns inside." 正文 TL;DR+表格(对人对 LLM 都友好),链接放评论区,发后前 2 小时守评论。

**官网反哺(新增,零成本)**:
- [ ] blog 写一篇 slug 带 reddit 的承接页:`/blog/safe-mcp-servers-reddit/`("Safe MCP Servers: What Reddit Users Actually Recommend")—— LLM 检索会在 query 里带 "reddit",这是承接位
- [ ] 把 Reddit 上关于 MCP 安全的高频真问题收进 audit/best 页 FAQ(比拍脑袋写的更贴真实搜索意图)

**节奏**:养号从现在起日常化(⏱ 每天 20 分钟,人时红线内);发帖等 arXiv 弹药链点火同波打。

### 草稿 5 — Reddit r/mcp(#7)· (nofollow · 🔴 真人养号 · 通过率 中)
**不要开新帖推广**。搜 "how do I know if an MCP server is safe" / "where to find MCP servers" 真问题,作答后自然带链:
```
Depends what you're worried about — the two failure modes are (1) the server
doing something sketchy with your creds/filesystem, and (2) just being
abandoned/low-quality.

For (1), read the actual tool definitions and what scopes it asks for before
adding it to your config; a surprising number request far more than they need.
I've been grading the public catalog for this (agentskillshub.top shows a
SAFE/CAUTION/UNSAFE flag per server) — but honestly even eyeballing the
requested permissions catches most of it.

For (2), check last-commit date and whether issues get answered. Stars lie;
maintenance doesn't.
```
> 先在这些 sub 攒 karma 到 500+;10 条回答最多 1 条带链;裸提站名>贴链更安全。

### 草稿 6 — Product Hunt(#6)· 产品页文案(dofollow · 🔴 真人发布日 · 通过率 高)
Tagline:
```
Find and vet 130K+ AI agent skills — with a security grade before you install
```
Description:
```
Agent Skills Hub indexes 130K+ open-source Claude skills and MCP servers.
Every result carries an automated quality score and a SAFE/CAUTION/UNSAFE
security grade — so you vet before you install, instead of after. Search by
scenario, compare alternatives, and grab the ash CLI (npx @agentskillshub/cli)
to do it from your terminal. Free, no login.
```
First maker comment:
```
Maker here 👋 I built this after realizing installing an MCP server = running
someone's code with my agent's full permissions, and no marketplace flagged
that risk. So I graded the whole public catalog (130K artifacts). The dataset's
open too. Would love feedback on the security taxonomy — what would you want
flagged?
```
> 按 launch-playbook 选 hunter + 预热。

### 草稿 7 — AlternativeTo(#10)· 提交(多 nofollow · 🔴 真人账号 · 通过率 高)
- **Name**: Agent Skills Hub
- **Short description**: `Searchable directory of 130K+ open-source AI agent skills and MCP servers, each with a quality score and a SAFE/CAUTION/UNSAFE security grade checked before install.`
- **Listed as alternative to**: LobeHub, mcp.so, Smithery, Glama
- **Categories**: AI Tools, Developer Tools, Directory
- **Tags**: mcp, claude, ai-agents, security, directory

### 草稿 8 — Dev.to(#12)· 文章引流(dofollow 正文链 · 🟢 我起草 / 🔴 你发号 · 通过率 高)
标题:`How to vet an MCP server before you install it (I graded 130K to find out)`
结构:痛点(装 = 跑别人代码)→ 4 个手查信号(scopes / last-commit / tool 定义 / 维护)→ "或者用一行 npx 查安全分" 自然引 CLI + 站。正文放 2 个 dofollow 链(站首页 + 方法论页),文末 canonical 视情况指向站上原文。可复用 `devto-securing-117k.md` 骨架(**数字更新到 130K**)。

### 草稿 9 — There's An AI For That(#8)· 提交(dofollow · 🔴 真人 · 通过率 中,审核偏严)
- **Tool name**: Agent Skills Hub
- **URL**: https://agentskillshub.top
- **Category**: Developer Tools / AI Agents
- **One-liner**: `Directory of 130K+ AI agent skills & MCP servers with a security grade before you install.`
- **Longer**: 同 PH description。
> `.top` 可能被审慎对待;若被拒,转投 Futurepedia(#9)+ SaaSHub(#13),话术同款。

### 草稿 10 — HARO / Featured.com(#16)· 记者问回复(目标媒体多 dofollow · 🔴 真人 · 通过率 15-25%)
盯 "AI agent security" / "MCP" / "AI supply chain" / "how to vet AI tools" 类 query:
```
I run agentskillshub.top, where I security-graded 130,173 open-source AI agent
skills and MCP servers. One concrete, citable finding for your piece:

Of the ~21,500 popular enough to evaluate, 3.3% grade UNSAFE and 8.8% carry a
security caution — but the bigger issue is that 83% of the catalog is entirely
unaudited. Installing any of these runs third-party code with the agent's full
permissions, and popularity (stars) doesn't correlate with safety.

Happy to share the open dataset or a longer quote.
— Jason Zhu, agentskillshub.top
[Disclosure: I run the site; sharing the data as a useful stat, no link expected.]
```
> 开头就给数字 + 机制 + takeaway(50–100 词);记者要的是可引用的数据,不是形容词。

---

## Tier 1 · 一次性高价值提交(两周内做完,DR 高、一劳永逸)

### A. GitHub awesome 列表 PR(状态版,07-10 大清点后)

**在途(周一复盘 `gh pr list` 逐个查)**
- [x] `punkpeye/awesome-mcp-servers` → PR #9142(4月开,07-10 刷新 130K)⏳
- [x] `modelcontextprotocol/servers`(官方)→ PR #4060 ⏳
- [x] `travisvn/awesome-claude-skills`(14K★)→ PR #965 ⏳
- [x] `ComposioHQ/awesome-claude-skills`(67K★)→ PR #747(4月开,07-10 刷新)⏳
- [x] `BehiSecc/awesome-claude-skills`(9.8K★)→ PR #445 ⏳

**判死 / 暂缓(别再花时间)**
- [x] ❌ `wong2/awesome-mcp-servers` — PR+issue 双关闭,只出不进
- [x] ⏸ `hesreallyhim/awesome-claude-code`(49.7K★)— 暂停收件,重开后走 Web 表单(见战报)
- [x] ❌ `e2b-dev/awesome-ai-agents` — agent 项目档案体,目录站不合格式
- [x] ❌ `mingrath/awesome-claude-skills` — 3★,不值一个 PR

**第二波候选(第一波有 merge 后再提,一天≤2)**
- [ ] `rohitg00/awesome-claude-code-toolkit`(2.3K★)
- [ ] `jqueryscript/awesome-claude-code`(460★)
- [ ] `GetBindu/awesome-claude-code-and-skills`(162★)· `Chat2AnyLLM/awesome-claude-skills`(141★)
- [ ] `Shubhamsaboo/awesome-llm-apps`(117K★,先核格式是否收目录)
- [ ] 继续搜 `awesome-mcp` / `awesome-claude` 新兴列表

### B. AI / SaaS 工具目录(一次性提交,多为 dofollow)
🔴 大多需你账号提交;🟢 描述文案我写好你贴。

- [ ] **Product Hunt**(择日 launch,单日流量+外链大爆发,需准备)
- [ ] AlternativeTo(列为 "MCP directory / AI agent tools" 替代品)
- [ ] SaaSHub
- [ ] theresanaiforthat.com
- [ ] futurepedia.io
- [ ] toolify.ai / aitools.fyi / topai.tools
- [ ] BetaList / Indie Hackers(产品页)
- [ ] llmstxt 类目录(我们已有 /llms.txt 的话)
- [ ] dang.ai / aitoolhunt / sider.ai 等新兴 AI 目录
- [ ] **claudemcp.org / claudemcp.com**(垂类 MCP 目录,#11)
- [ ] **dofollow.tools · thesaasdir.com · toolify.ai**(明示 dofollow 的一批,#17;一发布周≤3-4 个)
- [ ] **AlternativeTo · SaaSHub · StackShare**(列 LobeHub/mcp.so 替代品,#10/#13/#14)

### C. 开发者平台自有主页(建档 + 链接)
- [ ] Dev.to 个人/组织页(发文链回,见 Tier 2)
- [ ] Hashnode 博客(把 jasonzhu.ai 的审计文 republish + canonical)
- [ ] Medium(republish,canonical 指向原文)
- [ ] GitHub:`zhuyansen/agentskillshub-cli` README 顶部链官网;Blue Book repo 互链

---

## Tier 2 · 每日轮换(每天 ~30 分钟,挑 3–5 个)

按星期轮,避免单一渠道刷太狠:

| 周 | 动作 | 渠道 |
|---|---|---|
| **一** | 回答 1–2 个真问题,自然带链 | Reddit r/ClaudeAI · r/mcp · r/LocalLLaMA · r/ChatGPTCoding(搜 "where find MCP servers" / "claude skills directory") |
| **二** | 提交 2–3 个目录 | Tier 1·B 清单逐个划掉 |
| **三** | 提 1 个 awesome-list PR | Tier 1·A 清单逐个划掉 |
| **四** | 发/评 1 篇技术内容 | Dev.to · Hashnode(写"如何挑安全的 MCP server"等,自然引 Hub) |
| **五** | 1 封伙伴/互链邮件 | 见 Tier 3 |
| **六** | 有真里程碑才发 | Hacker News(Show HN)· Lobsters(需够硬的故事,如"审计了 10万 skill") |
| **日** | Q&A + 社媒 | Quora / X:回答"best MCP directory"类,@相关账号 |

**每天收尾**:在 §跟踪表 记下今天发了哪几条。

---

## Tier 3 · 伙伴 / 互链(持续,转化高、最稳)

- [ ] 🔴 **高德**:认证合作里要求**互链**(他们 skillzone 页链回 Hub)—— 真实高 DR
- [ ] 🔴 **Cherry Studio**:他们主动来谈过,争取"内置/推荐 MCP 来源"互相提及
- [ ] 🟢 **目录里的 skill 作者**:给被收录的作者发"你已上 AgentSkillsHub"通知 + "Featured on" 徽章/链接,他们常会回链
- [ ] 🟢 **被收录的官方组织**(firecrawl、阿里云等):提供"as featured on AgentSkillsHub"徽章,放他们 README
- [ ] 🟢 **Verified Creator 计划**:认证作者主页互链(权益之一)

---

## ⭐ 本周三优先(07-10 复盘:全部完成)

1. ~~HF 数据集~~ ✅ 已上线 + Kaggle 镜像 + Zenodo DOI(学术三连收官)
2. ~~awesome PR~~ ✅ 5 个在途(含官方)
3. HN Show HN → **移入 arXiv 弹药链**(等论文上线当天发,弹药更硬)

## 🚀 下一波弹药(2026-07-10 定,按周排)

> 原则不变:先资产后攒链。本波主题:**发布台 + 实体 + 自传播工具**。

| 周 | 动作 | 谁 | 说明 |
|---|---|---|---|
| 下周二起(每周发 1 站) | **indie 发布台四小站**:Uneed → Fazier → Microlaunch → Peerlist | 🧑 各 15min | 免费档、多 dofollow、开发者精准;文案用数据故事("扫了 130K,83% 无人审计"),别用目录腔 |
| 下周 | **openalternative.co** | 🤖 先侦察 | 开源替代品目录,正对 "LobeHub 开源替代" 语义位;以 agent-skills-hub 主仓提交 |
| 下周 | **Crunchbase 免费档案** | 🧑 15min | DR 91 实体信号,与 Wikidata Q140478987 交叉确认,治品牌词 pos 11 |
| 周末档 | **HF Space "Is this skill safe?"** | 🤖 半天出活 🧑 按发送 | Gradio 单框查询器,读 HF 数据集零后端;DR 90 dofollow + GEO 饵 + 可自传播 |
| arXiv 上线日 | **弹药链点火** | 🧑 提交 → 🤖 备料 | 媒体 pitch(Register/BleepingComputer/kdnuggets)→ 3 天后 Show HN → Papers with Code → PH → HARO |
| 下月 | **badge 战役(P2 大石头)** | 🤖 分批执行器 | github.com 450 域金矿;给 SAFE 级仓库发徽章通知,按周分批防 spam |

---

## Awesome PR 战报(2026-07-10 "提"点火)

| 列表 | 星数 | 动作 | 状态 |
|---|---|---|---|
| travisvn/awesome-claude-skills | 14K | 新 PR [#965](https://github.com/travisvn/awesome-claude-skills/pull/965),Tools 区,"searchable directory…security grade" | ⏳ 待 merge |
| BehiSecc/awesome-claude-skills | 9.8K | 新 PR [#445](https://github.com/BehiSecc/awesome-claude-skills/pull/445),Collections 区(agentskill.sh 旁),"open directory…" | ⏳ 待 merge |
| punkpeye/awesome-mcp-servers | 最大 MCP 列表 | 存量 [#9142](https://github.com/punkpeye/awesome-mcp-servers/pull/9142) 刷新:117K→130K(条目+标题) | ⏳ 待 merge(4 月开的) |
| ComposioHQ/awesome-claude-skills | 67K | 存量 [#747](https://github.com/ComposioHQ/awesome-claude-skills/pull/747) 刷新:67K→130K + 安全分级定位(条目+PR 描述) | ⏳ 待 merge(4 月开的) |
| modelcontextprotocol/servers(官方) | — | 存量 [#4060](https://github.com/modelcontextprotocol/servers/pull/4060) 仍 OPEN | ⏳ 待 merge |
| wong2/awesome-mcp-servers | 4.2K | ❌ 07-10 实锤:仓库 **PR 和 issue 双关闭**("An owner has disabled the ability to open pull requests"),列表只出不进、纯站长自选 —— 划掉,不再碰 | ❌ 无路 |
| hesreallyhim/awesome-claude-code | 49.7K | ⚠️ 明文禁 PR/CLI,只收 Web 表单 issue 且**须真人提交**;且 CONTRIBUTING 说暂停收件("disabling recommendations for a little while")。**先不提**,等它重开。表单: https://github.com/hesreallyhim/awesome-claude-code/issues/new?template=recommend-resource.yml ;届时填:URL=agentskillshub.top,描述(一行、无 emoji、陈述式)="Searchable directory of 130,000+ open-source Claude skills and MCP servers with a security grade and quality score per entry, refreshed every 8 hours." | ⏸ 等重开 |

**纪律复盘**:锚文本三家三样 ✅;一列表一 PR ✅;e2b-dev/awesome-ai-agents 格式不合(agent 项目档案体)主动跳过,不硬塞 ✅。
**跟进**:每周一复盘时 `gh pr list` 查五个 PR 状态;被 merge 一个,Bing/Ahrefs 2-4 周后应见 github.com 引用域。

## 进度跟踪表(每发一条记一行)

| 日期 | 站点/渠道 | 类型 | 提交内容/锚文本 | 状态 | DR/备注 |
|---|---|---|---|---|---|
| 2026-07-10 | travisvn/awesome-claude-skills | awesome PR | "searchable directory…SAFE/CAUTION/UNSAFE" | pending | PR #965 |
| 2026-07-10 | BehiSecc/awesome-claude-skills | awesome PR | "open directory of 130,000+…" | pending | PR #445 |
| 2026-07-10 | punkpeye #9142 / Composio #747 | 存量刷新 | 117K/67K → 130K + 安全分级 | pending | 数字保鲜 |
| 2026-07-10 | deepwiki.com | 自动收录 | 仓库页已存在(200) | ✅ | Tier1 划掉 |
| 2026-07-10 | Zenodo | 数据集 DOI | [10.5281/zenodo.21292799](https://doi.org/10.5281/zenodo.21292799) | ✅ live | DR 90+ · 可引用文献 |
| 2026-07-10 | Dev.to | 教程文(2 dofollow) | [how-to-vet-an-mcp-server](https://dev.to/yansen_zhu_9b0dae1c4cc0da/how-to-vet-an-mcp-server-before-you-install-it-i-graded-130000-to-find-out-2gh6) | ✅ live | DR 90 |
| 2026-07-10 | Kaggle Code | 分析 notebook(3 回链) | [130k-security-grades-analysis](https://www.kaggle.com/code/yansenzhu/ai-agent-skills-130k-security-grades-analysis) | ✅ live | DR 90 |
| 2026-07-10 | Wikidata | 实体+3 statements | Q140478987 ↔ sameAs 双向 | ✅ live | 知识图谱 |
| 2026-07-10 | AlternativeTo | 收录页 | agent-skills-hub | ✅ live | DA 80+ |
| 2026-07-10 | StackShare | 提交 | — | ❌ 拒收 | 类目不符,放弃 |
| 2026-07-10 | libhunt.com | 仓库收录 | [/r/agent-skills-hub](https://www.libhunt.com/r/agent-skills-hub) | ✅ live | 自动过审 |
| 2026-07-10 | skillget.dev / navi.tools / mdskills.ai | 目录提交 ×3 | 通用文案 | ⏳ 审核中 | navi 承诺 dofollow/72h |
| 2026-07-10 | aitoolnet.com | 付费收录 $9.9 | 通用文案 | ⏳ 待上线 | 上线后验 rel |
| 2026-07-10 | agentskillshub-mcp 仓库 | SKILL.md 被动钩子 | commit 07d8d539 | ⏳ 等爬取 | 喂 findskills/skillsmp/openskillindex |
| 2026-07-10 | creati.ai | 付费验收 | 收录页 3/4 dofollow(2 条带 utm) | ✅ 部分验毕 | 剩向客服要 9 链清单 |
| 2026-07-11 | **techbullion.com(计划外!)** | 媒体文章 dofollow | ["Framework for Agent Tool Selection"](https://techbullion.com/from-data-overload-to-data-driven-decisions-a-framework-for-agent-tool-selection/) 正文链首页,`rel="follow"` 实测 | ✅ 自然长出 | 科技媒体 DA 60 级;GA 已 50 sessions;①a 第一条自来媒体链 |
| 2026-07-11 | xmsumi.com 苏米客(计划外) | 中文博客横评 dofollow | [《10 个主流 AI Agent Skill 市场平台横向对比》](https://www.xmsumi.com/detail/2925) 列第 7,`rel="noopener"` 无 nofollow ✅;201 sessions | ✅ 已定位 | ⚠️ 条目数据旧(写 29K,实际 134K、无安全分级卖点)→ 联系作者致谢+供新数据;文内竞情:腾讯云 SkillHub、Qoder 58K |
|  |  |  |  |  |  |

---

## 注意(别踩坑)
- **价值优先**:Reddit/HN 重 spam 检测,先做真贡献再带链,否则封号 + 反效果。
- **锚文本多样**:别全是 "AgentSkillsHub" —— 混用 "MCP server directory"、"open agent skills catalog"、裸 URL。
- **节奏**:同一平台别一天发多条;awesome PR 一天最多 1–2 个。
- **nofollow 也要**:Reddit/HN 多是 nofollow,但带真实流量 + 提及信号,照做。
- **记录**:跟踪表是为了不重复、能复盘哪类渠道转化高。

## 付费导航站台账(累计 $275.9)
| 站 | 花费 | 日期 | 承诺 | 验收状态 |
|---|---|---|---|---|
| Toolify | $99 | ~06月 | 收录页 | ✅ 已见 GA referral(40 sessions/28d)|
| aibase | $39 | ~06月 | 收录页 | GA 未单独现身,待查 |
| TAAFT | $49 | ~06月 | 收录页 | GA 未单独现身,待查 |
| creati.ai | $79 | 2026-07-10 | **9 条外链** | ⏳ 待验:dofollow?指向?(Cloudflare 拦自动验证,人工查:见下)|
| aitoolnet | $9.9 | 2026-07-10 | 收录页 | ⏳ 上线后:F12 查 rel + GA 盯 aitoolnet referral |

### creati.ai 验收方法(浏览器 20 秒)
1. 打开我们在 creati.ai 的收录页
2. F12 控制台粘贴:
```js
[...document.querySelectorAll('a[href*="agentskillshub"]')].map(a=>({href:a.href,rel:a.rel||'✅dofollow'}))
```
3. 看输出:rel 含 "nofollow" = 只买到流量位;空/✅ = 真 SEO 权重
4. 9 条外链若分布在多个页面(分类页/榜单页),向 creati.ai 客服要清单逐条验
### 度量:GA 来源里盯 creati.ai referral(日报 digest 会自动带出);GSC/Bing Backlinks 2-4 周后应出现 creati.ai 域

## Bing 竞品外链踩点(2026-07-10,agentskillshub 32 域 vs lobehub ~490 域)

### 结构洞察
- LobeHub 第一护城河 = github.com 450 条(README/issues 提及)vs 我们 2 条 → **badge 战役直接对标这块**
- 它 ~100 条来自自家产品群(lobechat/vidol/pho.chat)—— 虚高,不可复制,忽略
- 我们第一外链域 = jasonzhu.ai(330,自有)→ 真第三方外链≈个位数

### Tier 1 战报(2026-07-10 "跑"点火,17 站全部侦察完毕)

**✅ 已完成(🤖)**
- [x] **libhunt.com — 已收录**:表单自动过审,页面 [libhunt.com/r/agent-skills-hub](https://www.libhunt.com/r/agent-skills-hub) 已 200
- [x] **deepwiki.com — 早已收录**(deepwiki.com/zhuyansen/agent-skills-hub 200)
- [x] **findskills.org / skillsmp.com / openskillindex.com — 被动爬取站**:三站都自动爬 GitHub 的 SKILL.md,已给 agentskillshub-mcp 仓库补 SKILL.md(commit 07d8d539),等它们下轮爬取,2-4 周复查

**🧑 人工提交(07-10 完成 3/6)**
- [x] **skillget.dev** ✅ 07-10 已提交
- [x] **navi.tools** ✅ 07-10 已提交(72h 审核,dofollow;盯 GA referral 验收)
- [x] **mdskills.ai** ✅ 07-10 已提交(有人工审核队列)
- [x] ❌ **free2aitools.com** — 划掉:API 发帖 FORBIDDEN、预填链接也发不出(仓库锁了外部 discussion),无可用提交路径;它聚合开放数据,有缘自然收录
- [x] ❌ **skillavatars.com** — 划掉:唯一联系方式是 iCloud 隐私中继邮箱,拒收外部邮件(550 Delivery not authorized),无提交路径
- [x] 💰 **aitoolnet.com** — 07-10 已付 $9.9 提交(用户决策);验收进付费台账

**❌ 划掉(5 站,别再回头看)**
- mcp-container.com / mytoolist.com(无提交入口)· model-context-protocol.com(无流程,只能发邮件)· mcp-servers.info(疑似死站)· mcpmark.ai(是 MCP 基准测试站,不是目录,不适用)

**⏳ 待复查**:npm.io 整站 503(它自己挂了),改天查 @agentskillshub/cli 和 /mcp 收录没

### 通用提交文案(人工 6 站通用)
- **Name**: Agent Skills Hub
- **URL**: https://agentskillshub.top
- **Category**: Developer Tools / AI Agents
- **Description**: Searchable directory of 130,000+ open-source AI agent skills and MCP servers with a security grade (SAFE/CAUTION/UNSAFE) and quality score per entry, refreshed every 8 hours. Free, no login.
- **Pricing**: Free · **Open source**: github.com/zhuyansen/agent-skills-hub(MIT)

### Tier 2 · 随星数自动来(不用动,盯着)
gitstar-ranking · trendshift.io · gittrend · fossies.org · ecosyste.ms(已有 27)

### Tier 3 · 战略型(已在 backlog/规划中)
- github.com 450 条 → **P2 badge 战役**(对手最大金矿)
- producthunt.com(40)→ backlog #6 PH 发布
- dev.to(29 vs 我们 1)→ 寄生虫 SEO,等 arXiv 弹药
- linkedin.com(45 vs 0)→ 暂不开新平台(避坑 15)

### 验收:每清一个,2-4 周后应在本报告复查中出现
