# new-term-radar 目录提交 · 记分板(2026-10-13 起)

仓库 github.com/zhuyansen/new-term-radar(3 个 skill + 1 个 MCP 服务器)。各站今天的提交方式由子任务逐站核实过(10-13)。
上一轮(agentskillshub-mcp,07 月)的记分板在 `mcp-registry-submissions.md`。

## 顺序(后面的依赖前面的)

PyPI → 官方 MCP 注册表 → Glama 收录并认领 → punkpeye/awesome-mcp-servers 的 PR。
07 月那次 punkpeye 的 PR(#9142)就是因为没在 Glama 认领,挂了 6 周后被关闭。

## 记分板

| 站 | 状态 | 怎么进 | 备注 |
|---|---|---|---|
| agentskillshub.top | ✅ 10-13 已受理(#21 `/approve`) | 下轮 sync 入库并评级 | 已从 mcp-for-github / mcp-for-google 排除(452a1e0);对口页 seo-tools 正在重新启用 |
| GitHub 主题词 | ✅ 10-13 | `mcp` `mcp-server` `agent-skills` `claude-skills` `claude-code` `google-trends` | SkillsMP 按 `claude-skills` 主题词每天抓 |
| skills.sh | ✅ 10-13 三个 skill 都装过一次 | 有人 `npx skills add` 才出现,没有提交入口 | 徽章 `https://skills.sh/b/zhuyansen/new-term-radar` |
| skillget.dev | ✅ 已自动收录 | 自动 | |
| Claude Code 插件市场 | ✅ 10-13 清单已入库(b2c8ab3) | `.claude-plugin/marketplace.json`;claudemarketplaces.com 自动发现 | `/plugin marketplace add zhuyansen/new-term-radar` |
| PyPI | ⏳ 等用户在 PyPI 加 pending publisher | `publish.yml`,发 GitHub release 触发 | 包名 `new-term-radar`,装进环境的模块叫 `new_term_radar` |
| 官方 MCP 注册表 | ⏳ 跟 PyPI 同一次 release 自动发 | `server.json` + GitHub OIDC | 名字 `io.github.zhuyansen/new-term-radar` |
| Glama | ⏳ 注册表发布后看是否自动收录;认领要用户登录 Glama | Add Server + 管理页配 Dockerfile + Make Release | punkpeye 的前置条件。认领只为这个:backlink-guard 0.3.0 查到 Glama 自己的美国 Google 流量 2026-04 掉了 94%(排名关键词 20,535 → 432,Semrush 同样),别指望它带搜索流量 |
| punkpeye/awesome-mcp-servers | ⏳ 等 Glama 评分 | PR,🎯 Marketing 区,标题末尾加 🤖🤖🤖 | 1–2 天合并 |
| mcp.directory | ⏳ PyPI 之后,靠官方注册表自动发现即可 | 免登录表单;也会从官方注册表自动发现 | backlink-guard:9 月访问量比 8 月掉 57%(7.4 万/月),不值得专门填表。0.3.0 再查:美国 Google 搜索流量同期掉 68%,排名关键词 945 → 173,正赶上 8 月、9 月两次垃圾更新 |
| mcpservers.org | ⏳ 要填邮箱,等用户同意 | 免费队列约 2 周 | 只走免费队列:它的 $39 档明写卖 dofollow;免费收录页的链接实测全是 nofollow,价值在流量(71.5 万/月) |
| agentskill.sh | ❌ 不投了 | 免登录,填仓库地址 | 10-13 提交被限流;随后用 backlink-guard 查:月访问 3 月 5.7 万 → 9 月接近 0,发了也没人看 |
| SkillsMP / claude-plugins.dev / openskillindex / findskills | ⏳ 自动抓 SKILL.md | 不用提交 | 1–2 周后查 |
| hesreallyhim/awesome-claude-code | 🧑 只收真人在网页表单提交 | issue 表单 `recommend-resource.yml` | 规则写明"需要注册或付费的工具难以审核",AIsa key 可能被卡 |
| ClawHub | 🧑 要 GitHub 登录;发布后 skill 改为 MIT-0 许可 | `clawhub skill publish` | 许可变更要用户定 |
| VoltAgent/awesome-agent-skills | ⏸ 不收刚建的仓库 | PR `Add skill: author/skill-name` | 11 月初再提 |

## 不投

mcp.so(issue 队列已死,表单只有 $39 付费)、PulseMCP(暂停收录,会从官方注册表自动拉)、Cline Marketplace(2025-12 后无人处理)、
Smithery(只收 MCPB 包或托管的 HTTP 服务)、travisvn / ComposioHQ / BehiSecc 三个列表(PR 队列不动)、navi.tools(域名过期)、
各站付费加速档($29–39,卖的是 dofollow 链接,10-06 起不买)。

## 提交前检查(10-13 起)

目标站先过一遍 `~/content/backlink-guard`(`python -m backlink_guard vet <站点>`),结论为 avoid 或触达为 low 的不投。
