# new-term-radar 目录提交 · 记分板(2026-10-13 起)

仓库 github.com/zhuyansen/new-term-radar(3 个 skill + 1 个 MCP 服务器)。各站今天的提交方式由子任务逐站核实过(10-13)。
上一轮(agentskillshub-mcp,07 月)的记分板在 `mcp-registry-submissions.md`。

## 顺序(后面的依赖前面的)

PyPI → 官方 MCP 注册表 → Glama 收录并认领 → punkpeye/awesome-mcp-servers 的 PR。
07 月那次 punkpeye 的 PR(#9142)就是因为没在 Glama 认领,挂了 6 周后被关闭。

## 记分板(2026-10-21 逐站核实;10-25 刷新 GitHub PR 和 issue、发 0.5.1)

打开每个站的页面、看标题和是否出现项目名核过;要登录才看得到的标「审核中」。

| 站 | 状态 | 备注 |
|---|---|---|
| PyPI / 官方 MCP 注册表 | ✅ 0.6.0(10-27) | `io.github.zhuyansen/new-term-radar` active latest;0.5.2 = MCP 工具报错原因能到 agent(0.5.1 = skill 跑锁定版本、付费前等同意、读到的内容只当数据、缺 config 用自带示例) |
| Claude Code 插件市场(仓库自带)/ skills.sh / ClawHub / Tessl | ✅ | |
| Glama | ✅ A 评级(10-26 核) | 页面数据带 `author:claimed`,渲染页上没看到认领标记(证据偏弱);punkpeye 的前提可能已满足 |
| LobeHub / mcpservers.org(Marketing)/ cursor.directory / Agensi / Skillstore / 魔搭(MCP + Skill) | ✅ | |
| Jimmy Song AI 原生全景图 | ✅ issue #34 10-21 以 completed 关闭 | landscape.jimmysong.io/projects/new-term-radar/(Tracked) |
| SkillsMP / skillsdirectory / skillget / skillsllm / agentskillshub.top | ✅ 自动收录 | |
| Anthropic 插件目录 | ⏳ 等人工审 | v0.5.1 @4fd9a0d「Held by directory policy, with Anthropic」(锁版本 uvx 必然人工审)。10-26 发了 0.5.2(报错原因能到 agent)并补 PRIVACY.md 和隐私/支持/文档链接(0b6b164),目录约每 6 小时扫一次新提交 |
| WorkBuddy 开放平台 | ⏳ 10-26 已提交,审核中 | 连接器 oc_02d71d5619d9802a,v0.5.2;类目同 backlink-guard;表单要 AIsa key 和数据目录。**10-27 用户定撤回重交**:17:36 撤回 0.5.2 的审核、上传 0.6.0 的包(哈希核过,第 2、3 步解析出 0.6.0)后重新提交;但列表接口的 currentVersion 还是 versionId 8984 / 0.5.2,看不出审的是不是新包,过审后核对 |
| mdskills / MCP Market / mcp.directory / AIbase | ⏳ 已提交,还搜不到 | MCP Market 免费队列 4–6 周 |
| mcp.so | ⏳ issue chatmcp/mcpso#5714 | issue 队列很慢；网页表单只剩 $39 付费（含 dofollow），不付；10-31 在 issue 里催了一下 |
| TensorBlock/awesome-mcp-servers / Raycast MCP 注册表扩展 | ✅ 10-21 合并 | #4232、raycast/extensions#32578 |
| GitHub 列表 | ⏳ 10 个 PR 还开着 | serpapi #478、BehiSecc #990、aitmpl #1223、Awesome-MCP-ZH #805、JackyST0 #127(10-26 按维护者三条改完、rebase 成一个提交,检查全过,等复审)、karanb192 #493、MobinX #867(10-26 和 main 冲突,已 rebase 成 039f14a,MERGEABLE/CLEAN)、GetBindu #296、teles #241、ComposioHQ #2328;维护者都没新评论 |
| buildwithclaude | ✅ #555 10-26 00:07 UTC 合并(davepoon:Listed) | 对方 marketplace.json 里是 0.5.1 @4fd9a0d。#500 于 10-23 被关:要求付费前报价等同意、跑锁定版本不 clone、抓来的内容只当数据;0.5.1 三条都做了 |
| DeepSeek Harness 清单 | ⏳ 10-27 两个 PR | Dominic789654/awesome-deepseek-harness#697（MCP Servers 节，两个工具一起，自动检查全过）、0xsline/awesome-deepseek-harness#757（Domain & Specialist Skills）；仓库加了 `deepseek-harness` topic；README 加了 DSH 一节（2b63b8e，DSH 0.2.1-rc.2 实测拿到 3 个工具、skill 出现在斜杠菜单）。beancookie/awesome-dsh-plugin 只收声明 `dsh.bundle` 的插件包，没投；libukai 9-12 后没合过 PR，没投 |
| github/awesome-copilot | ❌ issue #5578 10-25 被拒 | 理由:建在付费 API 上的 SEO/关键词工具,不是开发者工作流(自动检查当时全过) |
| mcpm.sh | ⏳ issue #476 | 机器人没生成 PR |
| HelloGitHub #4051 / 阮一峰周刊 #12613 | ⏳ 等出刊 | 月刊 28 日 / 周刊周五;10-23 那期(416 期)没收 |
| bmpi-dev/awesome-seo(已改名 i365dev/awesome-seo) | ❌ #104 10-21 被关 | 理由:项目太新、关键词量依赖付费 API |
| punkpeye/awesome-mcp-servers | ⏳ #18157（10-31） | 🎯 Marketing 区（zaialamm 和 zwznco 之间），Glama 已认领、A 级；check-submission 过，标签 has-glama / valid-name；标题没加贡献说明里那串 🤖🤖🤖 |
| VoltAgent/awesome-agent-skills | ⏸ 不收刚建的仓库 | 11 月初再提 |
| hesreallyhim/awesome-claude-code | ⏸ 只收本人在网页表单提交 | |

## 10-27 公开 0.6.0

本地 v0.5 线（0.5.3/0.6.0/0.7.0）清掉站名后并进公开版，加上新站最先排上的词、首页站点注册时间（只记录）和新站信号修复（AIsa 工具路由 10-15 起拒 whois 的数组筛选，改走 REST），以 **0.6.0** 推到 main（e1ce49e，单个提交接在公开版后面，v0.5 的原始提交没上去）。各平台上架的版本要跟着更新：ClawHub、LobeHub、cursor.directory、Skillstore、WorkBuddy 连接器（锁 0.5.2）。

10-27 更新结果：
- **ClawHub** ✅ 3 个 skill 都是 0.6.0（从 v0.6.0 标签发），扫描 CLEAN（VirusTotal / LLM），07:49–07:56 UTC 过审。
- **LobeHub** ✅ `plugin update` 0.5.2 → 0.6.0，published（07:42 UTC）；页面上「uvx new-term-radar==0.5.2」那句来自它缓存的旧 README（GitHub main 上已没有 0.5.2），等它自己重抓。
- **cursor.directory** ✅ 3 个 skill 正文改成 0.6.0（ai-listening 6 处版本；new-term-radar、seo-new-keywords-research 补了 page_age/age/year 等字段说明和表头新列），存前存后哈希都对（15c8b18d…/f1ee9920…/c1f183bb…）；未登录打开公开页显示 0.6.0。页面数据 `scan_status: safe`（理由写着 Skills pin PyPI 0.6.0），`status: pending`。
- **Skillstore** ⏳ 认领还在 Pending review；用户授权后在 Chrome 用 GitHub 登录（已授权过，没输密码），用 Submit 页重交仓库地址 → 机器人开更新 PR aiskillstore/marketplace#3965（3 个 skill，medium risk），合并后页面才变；附加说明留空、没开 GitHub 通知。
- **WorkBuddy** ⏳ 见上表。

## 10-26 逐站核查(后台代理,只读)

- **ClawHub、Tessl、cursor.directory、Skillstore 上还是 0.5.0 的 SKILL.md**(让 agent clone 默认分支、不锁版本);Skillstore 安全审计 **Medium Risk**(10-20),理由正是 Unpinned External Code Execution。仓库 main 已是 `uvx new-term-radar==0.5.2`。
  - 10-26 晚已重新发布:**ClawHub** 3 个 skill(new-term-radar、ai-listening、seo-new-keywords-research)从 v0.5.2 标签提交 0.5.2,等安全扫描后公开;**LobeHub** `plugin update` 0.5.0 → 0.5.2,published。
  - **cursor.directory 10-26 晚已改成 0.5.2**(编辑页逐项替换插件描述和 3 个 skill 的描述、正文,存后核对 7 项哈希全对;公开页 0 处 git clone)。
  - **Tessl 没法手动刷新**:Analyze a repository 回「All 3 skills in this repository have already been evaluated」,只能等它自己重新同步。
  - **Skillstore 10-26 晚已提交认领**(用户 GitHub 登录后提交;理由写明 r1 是 0.5.0、0.5.1 起已锁版本,证明用仓库所有者、v0.5.2 发布者、PyPI 可信发布、MCP 注册表命名空间),页面显示「Claim submitted · waiting for administrator review」;认领通过后再请它重新审计 v0.5.2。
- 各站数字:skills.sh 59 次安装;ClawHub 120 次下载;Tessl 73/74/77 分;skillsdirectory Grade A;SkillsMP 数据停在 10-13(页面有 Cloudflare 人机验证,状态取自公开搜索 API)。
- MCP Market / mcp.directory / AIbase / mdskills 仍搜不到;mcp.so #5714、mcpm #476 没动静。

## 不投

agentskill.sh(月访问量从 3 月 5.7 万掉到接近 0)、PulseMCP(暂停收录,会从官方注册表自动拉)、Cline Marketplace(2025-12 后无人处理)、
Smithery(10-31 起停止服务)、travisvn(不收需要付费 API 的 skill)、navi.tools(域名过期)、
各站付费加速档($29–39,卖的是 dofollow 链接,10-06 起不买)。

## 提交前检查(10-13 起)

目标站先过一遍 `~/content/backlink-guard`(`python -m backlink_guard vet <站点>`),结论为 avoid 或触达为 low 的不投。

## 10-28 复查

| 站 | 10-28 状态 |
|---|---|
| heilcheng/awesome-agent-skills | **#629**（Marketing 末尾一行，Check submission ✅），和 backlink-guard #628 一起在会话里交（定时任务卡住了） |
| JackyST0/awesome-agent-skills #127 | ✅ 10-27 合并 |
| DSH 清单 | Dominic789654#697 10-27 合并（MCP Servers 末尾）；0xsline#757 没动；10-28 加 topic `dsh-plugin` |
| Anthropic 插件目录 | 仍 Held（Runs a pinned npx or uvx package），10-20 提交至今 7 个版本待审；5ec2c47（只有 skill）Publish 按钮灰，要等整个插件审完 |
| WorkBuddy | 仍审核中，列表版本号还是 0.5.2（versionId 8984） |
| ClawHub | 3 个 skill 0.6.0，VirusTotal clean、LLM benign；SkillSpector CAUTION（主 skill MEDIUM 21 分 1 条，另两个 LOW）；下载 211/189/207 |
| LobeHub | published 0.6.0，旧 README 缓存已刷掉（10-27 20:44 UTC）；A 级、Claimed、16 次安装 |
| cursor.directory | 公开 0.6.0，scan_status safe；还没 logo（要登录上传） |
| Skillstore | #3965 10-27 合并：ai-listening、seo-new-keywords-research 变 Safe，主 skill 仍 Medium；认领还没通过 |
| Tessl | 自己同步到 2b63b8e（SKILL.md 锁 0.5.2，比 0.6.0 落后），分数 75/71/76 |
| 魔搭 | Skill 10-28 同步到 0.6.0；MCP 页没变（README 有 git clone、启动命令不锁版本）→ 要用户登录改 |
| Agensi | 在线，正文还是 10-20 版（pip 不锁版本、写着「或 clone」）→ 要用户登录改 |
| mdskills | 整站报错，看不出 |
| mcp.directory / MCP Market / AIbase / agenticskills.io | 都还没有 |
| skills.sh / SkillsMP / skillsdirectory / skillget | 都在；skills.sh 74 次安装（27/24/23）；SkillsMP 数据到 10-24 |
| GitHub PR（serpapi #478、BehiSecc #990、aitmpl #1223、Awesome-MCP-ZH #805、karanb192 #493、MobinX #867、GetBindu #296、teles #241、ComposioHQ #2328）和 issue（mcpso #5714、mcpm #476、HelloGitHub #4051、ruanyf #12613） | 都开着、维护者没回复（HelloGitHub 只有「邮件已收到」） |

## 10-28 0.6.1：外发前等用户点头

和 backlink-guard 0.11.1 同一条规则（用户：「雷达也同样改一下，加上提交前等我点头」）。雷达本身只读、不往外发东西；三个 skill 各加一节「Nothing goes out without a yes」：用户让 agent 按结果去发帖、上线页面、提 issue/PR、发邮件、提交网站、买域名或广告之前，先给他看去处和原文（或花费），等他对这一件点头；`prioritize`、强线索、要点子都不算点头。MCP 服务 instructions 同步，测试加断言（删掉规则会失败，验过），152 个测试过。

- 公开 main **3cf6515**（从 origin/main 起的临时 worktree 快进推，本地 v0.5 没动），Tests 绿，Release **v0.6.1** → PyPI + 官方注册表 0.6.1 latest。
- `ops/release/propagate.py new-term-radar 0.6.1`：ClawHub 3 个 skill 0.6.1 过扫描已上架；LobeHub 0.6.1 已发；WorkBuddy 本地包换成 0.6.1（审核中，没传）。
- cursor.directory：3 个 skill 正文改成 0.6.1（只改锁版本处和插入新节），哈希 ai-listening 1452145f… / new-term-radar 18dec570… / seo-new-keywords-research f736f10b…，存后重开核对过，公开页只剩 0.6.1。
- Skillstore：Submit 页重交（submission 90514185，3 个 skill），等机器人开更新 PR。
- buildwithclaude：**#599**「Update new-term-radar to 0.6.1」（锁 3cf6515，三项检查过，空配置目录装出 0.6.1、三个 skill 都有新节）。没动：Agensi、魔搭 MCP 页要用户登录改；Anthropic 目录会自己扫到 3cf6515。

## 10-29 DSH 社区插件市场收录

10-28 加的 topic `dsh-plugin` 生效，new-term-radar 进了 DSH 最大的社区插件市场。bradeGithub/DSH-Plugins-Marketplace 的插件索引 registry.json 已收录：最晚在 77bcd35（10-28 23:05 UTC 提交，索引 22:44 生成）那版里就有。10-28 10:20 起那轮全量的插件扫描在加 topic（约 10:55）之前就做完了，没赶上。条目：category `tool`（通用工具）、risk_tier `safe`、没有 risk_flags、`installable: manual`（卡片显示「手动安装」：它判定仓库里没有能自动装的内容，要照 README 装；README 里有 DSH 的装法）。它的 skills 索引（skills.json，按 topic agent-skills / claude-skills 收）在 10-28 那轮全量里就收了，也是 safe。按 topic 实时搜的市场（AwesomeHou）加 topic 当时就能搜到。它每 2 小时增量一次、只搜最近 3 天推送过的仓库，另外每天 04:00 UTC 全量一次（实际晚好几个小时）。
