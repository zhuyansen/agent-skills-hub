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
| PyPI / 官方 MCP 注册表 | ✅ 0.5.1(10-25) | `io.github.zhuyansen/new-term-radar`;0.5.1 = skill 跑锁定版本、付费前等同意、读到的内容只当数据、缺 config 用自带示例 |
| Claude Code 插件市场(仓库自带)/ skills.sh / ClawHub / Tessl | ✅ | |
| Glama | ✅ 页面已生成 | 认领后再提 punkpeye |
| LobeHub / mcpservers.org(Marketing)/ cursor.directory / Agensi / Skillstore / 魔搭(MCP + Skill) | ✅ | |
| Jimmy Song AI 原生全景图 | ✅ #34 已合并 | jimmysong.io/ai/new-term-radar/ |
| SkillsMP / skillsdirectory / skillget / skillsllm / agentskillshub.top | ✅ 自动收录 | |
| Anthropic 插件目录 | ⏳ 等人工审 | v0.5.1 @4fd9a0d「Held by directory policy, with Anthropic」(锁版本 uvx 必然人工审)。10-26 发了 0.5.2(报错原因能到 agent)并补 PRIVACY.md 和隐私/支持/文档链接(0b6b164),目录约每 6 小时扫一次新提交 |
| WorkBuddy 开放平台 | ⏸ 连接器包已备好 | `ops/workbuddy/new-term-radar.zip`(锁 0.5.2,表单要 AIsa key 和数据目录);等你实名入驻后上传 |
| mdskills / MCP Market / mcp.directory / AIbase | ⏳ 已提交,还搜不到 | MCP Market 免费队列 4–6 周 |
| mcp.so | ⏳ issue chatmcp/mcpso#5714 | issue 队列很慢 |
| TensorBlock/awesome-mcp-servers / Raycast MCP 注册表扩展 | ✅ 10-21 合并 | #4232、raycast/extensions#32578 |
| GitHub 列表 | ⏳ 11 个 PR 还开着 | serpapi #478、BehiSecc #990、aitmpl #1223、Awesome-MCP-ZH #805、JackyST0 #127(10-26 按维护者三条改完、rebase 成一个提交,检查全过,等复审)、buildwithclaude #555、karanb192 #493、MobinX #867、GetBindu #296、teles #241、ComposioHQ #2328 |
| buildwithclaude | ⏳ #555(0.5.1 重提) | #500 于 10-23 被关:要求付费前报价等同意、跑锁定版本不 clone、抓来的内容只当数据;0.5.1 三条都做了 |
| github/awesome-copilot | ❌ issue #5578 10-25 被拒 | 理由:建在付费 API 上的 SEO/关键词工具,不是开发者工作流(自动检查当时全过) |
| mcpm.sh | ⏳ issue #476 | 机器人没生成 PR |
| HelloGitHub #4051 / 阮一峰周刊 #12613 | ⏳ 等出刊 | 月刊 28 日 / 周刊周五 |
| bmpi-dev/awesome-seo | ❌ #104 被关 | 理由:项目太新、关键词量依赖付费 API |
| punkpeye/awesome-mcp-servers | ⏸ 等 Glama 评分 | PR 进 🎯 Marketing 区 |
| VoltAgent/awesome-agent-skills | ⏸ 不收刚建的仓库 | 11 月初再提 |
| hesreallyhim/awesome-claude-code | ⏸ 只收本人在网页表单提交 | |

## 不投

agentskill.sh(月访问量从 3 月 5.7 万掉到接近 0)、PulseMCP(暂停收录,会从官方注册表自动拉)、Cline Marketplace(2025-12 后无人处理)、
Smithery(10-31 起停止服务)、travisvn(不收需要付费 API 的 skill)、navi.tools(域名过期)、
各站付费加速档($29–39,卖的是 dofollow 链接,10-06 起不买)。

## 提交前检查(10-13 起)

目标站先过一遍 `~/content/backlink-guard`(`python -m backlink_guard vet <站点>`),结论为 avoid 或触达为 low 的不投。
