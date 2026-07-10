# 本周行动板(2026-07-10 定版)

| # | 进水口 | 谁 | 动作 | 状态 |
|---|---|---|---|---|
| 1 | **Awesome 列表 PR** ×3 | 🤖 我全自动 | fork→按格式加条目→PR(awesome-mcp-servers + Claude 系两个),一列表一 PR 不群发 | ✅ 07-10:新 PR ×2(travisvn [#965](https://github.com/travisvn/awesome-claude-skills/pull/965) · BehiSecc [#445](https://github.com/BehiSecc/awesome-claude-skills/pull/445))+ 刷新存量 ×2(punkpeye [#9142](https://github.com/punkpeye/awesome-mcp-servers/pull/9142) · Composio [#747](https://github.com/ComposioHQ/awesome-claude-skills/pull/747) 均更到 130K+安全分级);wong2 互动受限、hesreallyhim 暂停收件(详见 §Awesome PR 战报) |
| 2 | **Tier 1 自助收录** ~17 站 | 🤖 我跑大半 | 无头浏览器逐站提交(MCP 群/Skills 群/导航群);要登录/验证码的留人工 | 🔄 07-10 侦察中;deepwiki ✅ 已有我们仓库页;npm.io 整站 503 待复查 |
| 3 | **Zenodo DOI** | 🧑 你 10 分钟 | GitHub OAuth 登录 zenodo.org→拖 CSV→Publish→**DOI 发回** | ⏳ |
| 4 | **Wikidata 实体** | 🧑 你 15 分钟 | 照 intake kit F3 填五个字段 | ⏳ |
| 5 | **AlternativeTo + StackShare** | 🧑 你 各 15 分钟 | 文案抄 kit F4;标 LobeHub/Smithery alternatives | ⏳ |
| 6 | **Ahrefs 免费站长版** | 🧑 你 10 分钟 | ahrefs.com/webmaster-tools 注册→验证域名(GSC 授权最快)→外链监控第二视角 | ✅ 07-10 开通 |
| 7 | creati.ai 验收 | 🧑 你 5 分钟 | 收录页 F12 跑 rel 检查 + 向客服要 9 链清单 | ⏳ |
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
| 4 | **GitHub `awesome-mcp-servers` / 官方 servers PR** | awesome list | DR 高 | nofollow | 提 PR | 低 | ✅ 高 | punkpeye ✅已开PR / wong2 / modelcontextprotocol/servers。见 mcp-registry 文件 |
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

### A. GitHub awesome 列表 PR(最高优先 —— DR 高、开发者精准、永久)
给这些列表提 PR,把 Hub 作为「discovery / directory」资源加进去。🟢 文案我起草。

- [ ] `punkpeye/awesome-mcp-servers`(MCP 最大列表)→ 加到 "Resources / Directories"
- [ ] `wong2/awesome-mcp-servers`
- [ ] `modelcontextprotocol/servers`(官方)→ README 的社区资源区
- [ ] `hesreallyhim/awesome-claude-code` / `awesome-claude-code-agents`
- [ ] `e2b-dev/awesome-ai-agents`
- [ ] `Shubhamsaboo/awesome-llm-apps`
- [ ] `f/awesome-chatgpt-prompts` 类(若有 skills 区)
- [ ] **已核实存在的 `awesome-claude-skills` 列表(逐个提"Directories/Resources"区,草稿 3)**:
      `travisvn/awesome-claude-skills` · `ComposioHQ/awesome-claude-skills` · `BehiSecc/awesome-claude-skills` ·
      `mingrath/awesome-claude-skills` · `GetBindu/awesome-claude-code-and-skills` · `Chat2AnyLLM/awesome-claude-skills` ·
      `rohitg00/awesome-claude-code-toolkit` · `jqueryscript/awesome-claude-code`
- [ ] 继续搜 `awesome-mcp` / `awesome-claude` 新兴列表,逐个提(一天≤2)

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

## ⭐ 本周先发这 3 个(为什么)

> 用一句话选:**先建"资产"(别人愿意引的东西),再让资产去攒链** —— 这样绕开了 `.top` + 通用品牌词的双重不信任,靠数据说话。

1. **Hugging Face 数据集页(草稿 2)** —— 本周第一个,因为**零门槛、零审核、纯 dofollow、DR 90+**。card 已写好、parquet 已导出,今天就能建库上线。它同时是后面 arXiv / HN / HARO 三条草稿共用的"权威锚点"(都指向同一个开放数据集),先立起来。
2. **Hacker News Show HN(草稿 4)** —— 因为**故事已经成立**("13 万 skill,83% 无人审计"),而且 HN 是 GEO 高地 + 会外溢到二次报道/Reddit。等 HF 数据集上线后当天发,评论里挂数据集链,一次点燃流量+讨论+潜在媒体注意。
3. **awesome-claude-skills PR ×2(草稿 3)** —— 因为**最省力、最精准、可立即做**:已核实 6+ 个真实 repo,我能直接起草 PR,加到 Resources 区。开发者精准流量 + LLM 训练重 awesome-list(GEO)。本周挑 travisvn + ComposioHQ 两个先提(锚文本各异)。

> arXiv(草稿 1)是**最高价值但最慢**(要 endorser + 定稿),本周并行启动"约 endorser",不进本周交付。PH(草稿 6)按 launch-playbook 择日,不抢本周。

---

## Awesome PR 战报(2026-07-10 "提"点火)

| 列表 | 星数 | 动作 | 状态 |
|---|---|---|---|
| travisvn/awesome-claude-skills | 14K | 新 PR [#965](https://github.com/travisvn/awesome-claude-skills/pull/965),Tools 区,"searchable directory…security grade" | ⏳ 待 merge |
| BehiSecc/awesome-claude-skills | 9.8K | 新 PR [#445](https://github.com/BehiSecc/awesome-claude-skills/pull/445),Collections 区(agentskill.sh 旁),"open directory…" | ⏳ 待 merge |
| punkpeye/awesome-mcp-servers | 最大 MCP 列表 | 存量 [#9142](https://github.com/punkpeye/awesome-mcp-servers/pull/9142) 刷新:117K→130K(条目+标题) | ⏳ 待 merge(4 月开的) |
| ComposioHQ/awesome-claude-skills | 67K | 存量 [#747](https://github.com/ComposioHQ/awesome-claude-skills/pull/747) 刷新:67K→130K + 安全分级定位(条目+PR 描述) | ⏳ 待 merge(4 月开的) |
| modelcontextprotocol/servers(官方) | — | 存量 [#4060](https://github.com/modelcontextprotocol/servers/pull/4060) 仍 OPEN | ⏳ 待 merge |
| wong2/awesome-mcp-servers | 4.2K | ⚠️ 仓库开了互动限制,API 提不了 PR。分支已推好,**你浏览器点这个链接试**: https://github.com/zhuyansen/awesome-mcp-servers-1/pull/new/add-agent-skills-hub | 🧑 需人工 |
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
|  |  |  |  |  |  |

---

## 注意(别踩坑)
- **价值优先**:Reddit/HN 重 spam 检测,先做真贡献再带链,否则封号 + 反效果。
- **锚文本多样**:别全是 "AgentSkillsHub" —— 混用 "MCP server directory"、"open agent skills catalog"、裸 URL。
- **节奏**:同一平台别一天发多条;awesome PR 一天最多 1–2 个。
- **nofollow 也要**:Reddit/HN 多是 nofollow,但带真实流量 + 提及信号,照做。
- **记录**:跟踪表是为了不重复、能复盘哪类渠道转化高。

## 付费导航站台账(累计 $266)
| 站 | 花费 | 日期 | 承诺 | 验收状态 |
|---|---|---|---|---|
| Toolify | $99 | ~06月 | 收录页 | ✅ 已见 GA referral(40 sessions/28d)|
| aibase | $39 | ~06月 | 收录页 | GA 未单独现身,待查 |
| TAAFT | $49 | ~06月 | 收录页 | GA 未单独现身,待查 |
| creati.ai | $79 | 2026-07-10 | **9 条外链** | ⏳ 待验:dofollow?指向?(Cloudflare 拦自动验证,人工查:见下)|

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

### Tier 1 · 自助提交,本周可清(它有我没有,均为收录型)
- [ ] libhunt.com(它 165 条)— GitHub 项目索引站,提交仓库
- [ ] skillavatars.com(116)— skills 目录
- [ ] mcpmark.ai(150)· mcp-container.com(106)· mcpworld.com(80)· mcp-servers.info · model-context-protocol.com — **MCP 目录集群**,我们的 MCP server 挨个提交
- [ ] findskills.org(54)· mdskills.ai(30)· skillsmp.com(23)· skillget.dev(17)· openskillindex.com — **skills 目录集群**
- [ ] navi.tools(49)· mytoolist.com(84)· free2aitools.com(21)· aitoolnet.com · popularaitools.ai — AI 工具导航
- [ ] deepwiki.com(17)— 仓库 wiki 化,提交主仓
- [ ] npm.io(80)— npm 包索引,查我们两个包被收录没

### Tier 2 · 随星数自动来(不用动,盯着)
gitstar-ranking · trendshift.io · gittrend · fossies.org · ecosyste.ms(已有 27)

### Tier 3 · 战略型(已在 backlog/规划中)
- github.com 450 条 → **P2 badge 战役**(对手最大金矿)
- producthunt.com(40)→ backlog #6 PH 发布
- dev.to(29 vs 我们 1)→ 寄生虫 SEO,等 arXiv 弹药
- linkedin.com(45 vs 0)→ 暂不开新平台(避坑 15)

### 验收:每清一个,2-4 周后应在本报告复查中出现
