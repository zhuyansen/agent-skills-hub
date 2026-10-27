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
| PyPI / 官方 MCP 注册表 | ✅ 0.5.2(10-26) | `io.github.zhuyansen/new-term-radar` active latest;0.5.2 = MCP 工具报错原因能到 agent(0.5.1 = skill 跑锁定版本、付费前等同意、读到的内容只当数据、缺 config 用自带示例) |
| Claude Code 插件市场(仓库自带)/ skills.sh / ClawHub / Tessl | ✅ | |
| Glama | ✅ A 评级(10-26 核) | 页面数据带 `author:claimed`,渲染页上没看到认领标记(证据偏弱);punkpeye 的前提可能已满足 |
| LobeHub / mcpservers.org(Marketing)/ cursor.directory / Agensi / Skillstore / 魔搭(MCP + Skill) | ✅ | |
| Jimmy Song AI 原生全景图 | ✅ issue #34 10-21 以 completed 关闭 | landscape.jimmysong.io/projects/new-term-radar/(Tracked) |
| SkillsMP / skillsdirectory / skillget / skillsllm / agentskillshub.top | ✅ 自动收录 | |
| Anthropic 插件目录 | ⏳ 等人工审 | v0.5.1 @4fd9a0d「Held by directory policy, with Anthropic」(锁版本 uvx 必然人工审)。10-26 发了 0.5.2(报错原因能到 agent)并补 PRIVACY.md 和隐私/支持/文档链接(0b6b164),目录约每 6 小时扫一次新提交 |
| WorkBuddy 开放平台 | ⏳ 10-26 已提交,审核中 | 连接器 oc_02d71d5619d9802a,v0.5.2;类目同 backlink-guard;表单要 AIsa key 和数据目录 |
| mdskills / MCP Market / mcp.directory / AIbase | ⏳ 已提交,还搜不到 | MCP Market 免费队列 4–6 周 |
| mcp.so | ⏳ issue chatmcp/mcpso#5714 | issue 队列很慢 |
| TensorBlock/awesome-mcp-servers / Raycast MCP 注册表扩展 | ✅ 10-21 合并 | #4232、raycast/extensions#32578 |
| GitHub 列表 | ⏳ 10 个 PR 还开着 | serpapi #478、BehiSecc #990、aitmpl #1223、Awesome-MCP-ZH #805、JackyST0 #127(10-26 按维护者三条改完、rebase 成一个提交,检查全过,等复审)、karanb192 #493、MobinX #867(10-26 和 main 冲突,已 rebase 成 039f14a,MERGEABLE/CLEAN)、GetBindu #296、teles #241、ComposioHQ #2328;维护者都没新评论 |
| buildwithclaude | ✅ #555 10-26 00:07 UTC 合并(davepoon:Listed) | 对方 marketplace.json 里是 0.5.1 @4fd9a0d。#500 于 10-23 被关:要求付费前报价等同意、跑锁定版本不 clone、抓来的内容只当数据;0.5.1 三条都做了 |
| DeepSeek Harness 清单 | ⏳ 10-27 两个 PR | Dominic789654/awesome-deepseek-harness#697（MCP Servers 节，两个工具一起，自动检查全过）、0xsline/awesome-deepseek-harness#757（Domain & Specialist Skills）；仓库加了 `deepseek-harness` topic；README 加了 DSH 一节（2b63b8e，DSH 0.2.1-rc.2 实测拿到 3 个工具、skill 出现在斜杠菜单）。beancookie/awesome-dsh-plugin 只收声明 `dsh.bundle` 的插件包，没投；libukai 9-12 后没合过 PR，没投 |
| github/awesome-copilot | ❌ issue #5578 10-25 被拒 | 理由:建在付费 API 上的 SEO/关键词工具,不是开发者工作流(自动检查当时全过) |
| mcpm.sh | ⏳ issue #476 | 机器人没生成 PR |
| HelloGitHub #4051 / 阮一峰周刊 #12613 | ⏳ 等出刊 | 月刊 28 日 / 周刊周五;10-23 那期(416 期)没收 |
| bmpi-dev/awesome-seo(已改名 i365dev/awesome-seo) | ❌ #104 10-21 被关 | 理由:项目太新、关键词量依赖付费 API |
| punkpeye/awesome-mcp-servers | ⏸ 等 Glama 评分 | PR 进 🎯 Marketing 区 |
| VoltAgent/awesome-agent-skills | ⏸ 不收刚建的仓库 | 11 月初再提 |
| hesreallyhim/awesome-claude-code | ⏸ 只收本人在网页表单提交 | |

## 10-27 公开 0.6.0

本地 v0.5 线（0.5.3/0.6.0/0.7.0）清掉站名后并进公开版，加上新站最先排上的词、首页站点注册时间（只记录）和新站信号修复（AIsa 工具路由 10-15 起拒 whois 的数组筛选，改走 REST），以 **0.6.0** 推到 main（e1ce49e，单个提交接在公开版后面，v0.5 的原始提交没上去）。各平台上架的版本要跟着更新：ClawHub、LobeHub、cursor.directory、Skillstore、WorkBuddy 连接器（锁 0.5.2）。

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
