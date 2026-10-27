# backlink-guard 目录提交 · 记分板(2026-10-26 起)

仓库 github.com/zhuyansen/backlink-guard(1 个 skill + 1 个 MCP 服务器,0.10.0 起)。清单照 `new-term-radar-submissions.md`:雷达投过的 skills 和 MCP 站,backlink-guard 也投一遍。各站的提交方式沿用雷达 10-13/10-20 的核实。

## 顺序

PyPI → 官方 MCP 注册表(Release 触发 workflow 自动发)→ Glama 收录并认领 → punkpeye/awesome-mcp-servers 的 PR。

## 记分板(10-26)

| 站 | 状态 | 备注 |
|---|---|---|
| PyPI / 官方 MCP 注册表 | ✅ 0.11.0(10-27) | `io.github.zhuyansen/backlink-guard` active latest;0.11.0 = `competitors --early`(竞品上线头 90 天的外链、同龄对比、发布清单)+ `vet --newcomers`;0.10.1 = MCP 工具报错原因能到 agent;Release 触发 publish.yml(build、PyPI、registry 三步都成功) |
| skills.sh / Agent Skills Hub / Claude Code 插件市场(仓库自带) | ✅ | skills.sh 2 次安装;**Hub 页面还显示 ★17、最后更新 10-18(GitHub 已 23★)** |
| SkillsMP / skillsdirectory / skillget | ✅ 自动收录(10-26 核) | skillsdirectory Grade A;SkillsMP 数据停在 10-14;skillget 星数旧 |
| Agensi | ✅ 已上线(Live · Free) | 自动填写先清掉再自己写;演示用 README 10-13 的真实 vet 表;工具权限勾了 5 项(不含 Browser) |
| Tessl | ✅ 75 分(10-26 核) | Quality 94%、Security Low;版本 140a236(0.10.0);tessl.io/registry/skills/github/zhuyansen/backlink-guard |
| ClawHub | ✅ 0.11.0(10-27,v0.11.0 标签),扫描 CLEAN(scanner.llm.clean,07:58 UTC) | `npx clawhub@0.23.3 publish`,首发 0.10.0 source commit 140a236;**clawhub.ai 走代理 7897 不通、直连通,命令要去掉代理变量**;MIT-0 同雷达 |
| cursor.directory | ✅ 已公开,10-27 改成 0.11.0(skill 正文 = v0.11.0 SKILL.md,哈希 234e9d77…;MCP 配置锁 0.11.0) | cursor.directory/plugins/backlink-guard:Skill 1 + 手动加的 MCP Server 1,传了 logo;站内能搜到。存后组件 id 会变;未登录打开公开页显示 0.11.0;页面数据 `scan_status: pending`(重扫中) |
| 魔搭 MCP + Skill | ✅ | modelscope.cn/mcp/servers/JasonZhuyansen/backlink-guard(仅本地可用、中文描述、两个 key 改成选填);modelscope.cn/skills/JasonZhuyansen/backlink-guard(市场推广、MIT、图标换成 logo、自动同步) |
| Skillstore | ✅ 已上(10-26 核) | skillstore.io/skills/zhuyansen-backlink-guard,安全审计 Safe;10-27 用 Submit 页重交仓库 → 更新 PR aiskillstore/marketplace#3964(medium risk,上次 safe;两次理由一样,都是 PyPI 包不在审计范围内),合并后页面才变 |
| mdskills | ⏳ 3 周内上线 | Plugin / Free / Standard 免费档,名称和描述手填 |
| mcp.directory | ⏳ 24 小时内 | 表单不填邮箱 |
| serpapi/awesome-seo-tools #478 / BehiSecc/awesome-claude-skills #990 | ⏳ 10-19 已含 backlink-guard | 和雷达同一个 PR |
| agenticskills.io | ⏳ 10-19 表单已交 | |
| Anthropic 插件目录 | ⏳ 10-26 已提交,首次扫描中 | v0.10.1 @0c9a566。Validate 通过但有 8 个 policy hold(锁版本 uvx 必然人工审;「Uses a credential」7 处是各家 key 发给各家自己的主机),所以会转人工审。提交前补了 PRIVACY.md 和 plugin.json 的隐私/支持/文档链接(文档链接原先被取成 README 里的 logo)。选了 GitHub push webhook,但 webhook 还没在仓库设置里加(不加也每 6 小时查一次新提交) |
| WorkBuddy 开放平台 | ⏳ 10-26 已提交,审核中 | 连接器 oc_b6d687a4c8cb5e92,v0.10.1;类目「商业服务 - 公关/推广/市场调查」「工具 - 信息查询」;包在 `ops/workbuddy/`。开发者主页资料 21:46 已过审(昵称 JasonZhu、官网 jasonzhu.ai)。**10-27 用户定撤回重交**:17:32 撤回 0.10.1、上传 0.11.0 的包(哈希核过,第 2、3 步解析出 0.11.0)后重新提交;列表接口的 currentVersion 还是 versionId 8981 / 0.10.1,看不出审的是不是新包,过审后核对 |
| LobeHub | ✅ 0.11.0 published(10-27 07:43 UTC `plugin update`,页面显示 0.11.0) | 10-26 `lhm plugin publish` → zhuyansen-backlink-guard@0.10.0,10 个工具,中文名「外链检测」,🛡️;GitHub 授权用完已 `github disconnect`。验证通过前 lobehub.com/mcp/zhuyansen-backlink-guard 显示 Plugin not found;雷达当时同样 not_validated,后来自动变 published |

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
- **要你撤销授权**:GitHub Settings → Applications → Authorized OAuth Apps → LobeHub → Revoke(CLI 已断开,这一步彻底收回 token)。
- **表单要填联系邮箱**:mcpservers.org(免费档)、MCP Market(免费队列,默认勾的 $29 要改)。用哪个邮箱你定。
- **只能你本人**:hesreallyhim(10-27 起,网页表单)。
- **邮件**(你从 Gmail 发):skillselion(info@skillselion.com)、claudemarketplaces(hi@claudemarketplaces.com)。

## 第 3 批:等条件

heilcheng/awesome-agent-skills(要 ≥20★,**10-26 晚已 23★,门槛满足**)、VoltAgent(11 月)、punkpeye(Glama 认领后)。

## 不投

沿用雷达的「不投」:agentskill.sh、PulseMCP(自动从官方注册表拉)、Cline Marketplace、Smithery、travisvn、navi.tools、各站付费加速档;bmpi-dev/awesome-seo(雷达 #104 以「太新、依赖付费 API」被关,backlink-guard 同样情况)。
