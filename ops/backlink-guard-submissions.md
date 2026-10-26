# backlink-guard 目录提交 · 记分板(2026-10-26 起)

仓库 github.com/zhuyansen/backlink-guard(1 个 skill + 1 个 MCP 服务器,0.10.0 起)。清单照 `new-term-radar-submissions.md`:雷达投过的 skills 和 MCP 站,backlink-guard 也投一遍。各站的提交方式沿用雷达 10-13/10-20 的核实。

## 顺序

PyPI → 官方 MCP 注册表(Release 触发 workflow 自动发)→ Glama 收录并认领 → punkpeye/awesome-mcp-servers 的 PR。

## 记分板(10-26)

| 站 | 状态 | 备注 |
|---|---|---|
| PyPI / 官方 MCP 注册表 | ✅ 0.10.0 | `io.github.zhuyansen/backlink-guard` active;Release v0.10.0 触发 publish.yml(build、PyPI、registry 三步都成功) |
| skills.sh / Agent Skills Hub / Claude Code 插件市场(仓库自带) | ✅ | |
| Agensi | ✅ 已上线(Live · Free) | 自动填写先清掉再自己写;演示用 README 10-13 的真实 vet 表;工具权限勾了 5 项(不含 Browser) |
| Tessl | ⏳ 评估中 | 网页 Analyze a repository;tessl.io/registry/skills/github/zhuyansen/backlink-guard,已公开 |
| ClawHub | ⏳ 安全扫描中 | `npx clawhub@0.23.3 publish`,0.10.0,source commit 140a236;**clawhub.ai 走代理 7897 不通、直连通,命令要去掉代理变量**;MIT-0 同雷达 |
| cursor.directory | ⏳ 安全扫描中 | cursor.directory/plugins/backlink-guard:Skill 1 + 手动加的 MCP Server 1,传了 logo |
| 魔搭 MCP + Skill | ✅ | modelscope.cn/mcp/servers/JasonZhuyansen/backlink-guard(仅本地可用、中文描述、两个 key 改成选填);modelscope.cn/skills/JasonZhuyansen/backlink-guard(市场推广、MIT、图标换成 logo、自动同步) |
| Skillstore | ⏳ 审计后开 PR | 匿名提交 |
| mdskills | ⏳ 3 周内上线 | Plugin / Free / Standard 免费档,名称和描述手填 |
| mcp.directory | ⏳ 24 小时内 | 表单不填邮箱 |
| serpapi/awesome-seo-tools #478 / BehiSecc/awesome-claude-skills #990 | ⏳ 10-19 已含 backlink-guard | 和雷达同一个 PR |
| agenticskills.io | ⏳ 10-19 表单已交 | |

### GitHub(后台代理 10-26 开)

| 去处 | 链接 | 备注 |
|---|---|---|
| TensorBlock/awesome-mcp-servers | PR #4603 | Marketing, Sales & CRM 顶部 |
| davila7/claude-code-templates (aitmpl) | PR #1277 | `mcps/marketing/backlink-guard.json`,检查全过,review-pending |
| yzfly/Awesome-MCP-ZH | PR #854 | 🔍 搜索,中文一行带费用 |
| davepoon/buildwithclaude | PR #564 | 固定 140a236,sales-marketing;三项检查过 |
| karanb192/awesome-claude-skills | PR #540 | Data & Analysis;链接检查等维护者批准 |
| MobinX/awesome-mcp-list | PR #948 | 🎯 Marketing |
| GetBindu/awesome-claude-code-and-skills | PR #313 | Marketing & Content |
| teles/awesome-seo | PR #265 | Keyword and Competitor Research,标 🔓 |
| raycast/extensions | PR #32784 | MCP 注册表扩展,检查全过 |
| rootsongjc/ai-native-landscape | issue #36 | 表单格式,中英 |
| chatmcp/mcpso | issue #6159 | |
| pathintegral-institute/mcpm.sh | issue #489 | |
| 521xueweihan/HelloGitHub | issue #4112 | [开源推荐],226 字原创描述,附中文动图 |
| ruanyf/weekly | issue #12783 | 【开源自荐】 |

跳过:JackyST0(10-26 起社区项目要 256★)、ComposioHQ(10-22 起只收协作者 PR;分支 `add-backlink-guard` 已推到 zhuyansen/awesome-claude-skills,没开 PR)、github/awesome-copilot(雷达 #5578 10-25 被以「建在付费 API 上的 SEO 工具,不是开发者工作流」拒,backlink-guard 同理,要投由用户定)。

## 待用户

- **要你在 Chrome 登录**:Glama(Add Server + 认领,之后才提 punkpeye)、AIbase。
- **要你点头**:LobeHub(market-cli 要 GitHub 授权 repo 全读写 + workflow + gist,用完即撤,雷达那次就是这样)。
- **表单要填联系邮箱**:mcpservers.org(免费档)、MCP Market(免费队列,默认勾的 $29 要改)。用哪个邮箱你定。
- **只能你本人**:Anthropic 插件目录(claude.ai/directory/manage)、hesreallyhim(10-27 起,网页表单)。
- **邮件**(你从 Gmail 发):skillselion(info@skillselion.com)、claudemarketplaces(hi@claudemarketplaces.com)。

## 第 3 批:等条件

heilcheng/awesome-agent-skills(要 ≥20★,10-26 是 18★)、VoltAgent(11 月)、punkpeye(Glama 认领后)。

## 不投

沿用雷达的「不投」:agentskill.sh、PulseMCP(自动从官方注册表拉)、Cline Marketplace、Smithery、travisvn、navi.tools、各站付费加速档;bmpi-dev/awesome-seo(雷达 #104 以「太新、依赖付费 API」被关,backlink-guard 同样情况)。
