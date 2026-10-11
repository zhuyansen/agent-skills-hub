# 目标词的 Google 前 10 名形态核对(2026-10-11)

AIsa → DataForSEO `serp_google_organic_live_regular`,Google 美国桌面,14 个词,$0.028。原始数据 `serp.json.gz`。
起因:10-06 只按搜索量和 KD 定了目标词(`ops/research/scenario-keywords-2026-10-06/`),没看前排是什么页面(子木小册子第 3 章)。

| 词 | 前 10 名是什么 | 意图 | 我们的列表页接得住吗 | 处理 |
|---|---|---|---|---|
| claude design skills | 列表为主:typeui「48 design skills」、open-design.ai、composio、uxplanet 榜单 | 找一批 | ✅ 完全对口 | 保持 |
| codex skill | 目录和列表:skillsllm.com 第 1、gradually.ai「421 Skills」;其余是新闻和入门 | 找一批 + 了解 | ✅ | 保持 |
| obsidian mcp | pulsemcp「Top 104 Obsidian MCP Servers」第 2、mcpservers.org 第 3;其余教程 | 找一个/一批 | ✅ | 保持 |
| github mcp | 前排很弱:无名仓库的 Actions 页、mcpservers.org、mcpmarket ×2 | 找一个 | ✅ 目录页在排,前排质量差 | 保持(机会) |
| prompt engineering tool | 榜单文章(braintrust「7 best」、medium、helicone) | 比较 | ✅ 形态对,对手是实测文 | 保持 |
| code refactoring tool | 榜单文章(sourcegraph「10 best」、augment「19」)+ 概念解释 | 比较 | ✅ | 保持 |
| frontend design skill | 官方(GitHub 第 1、claude.com 第 5)+ 榜单(snyk「Top 8」、composio「10 best」、YouTube「Top 10」) | 找官方那个 + 找一批 | ✅ 现在"官方介绍 + 列表"的小节正好两头都接 | 保持小节,不必拆页 |
| humanizer skill | 单个 skill 的页面:blader/humanizer、shyft、myclaw、mcpmarket;没有榜单 | 找那一个 | ⚠️ 一半:要让 blader/humanizer 在首屏 | 保持,检查首屏 |
| remotion skill | 单个 skill 的介绍和教程:remotion-dev/skills、mcpmarket、medium 指南 | 找官方那个 + 怎么用 | ⚠️ 一半:页面没有专门讲官方 Remotion skill | 加一节(同 frontend-design 的做法) |
| multi agent orchestration | 概念讲解和平台对比(gartner、redis「top 8 platforms」、微软文档) | 了解 + 比较 | ⚠️ 偏讲解,列表页只对上一部分 | 保持,不投入 |
| best vibe coding tool / vibe coding tool | 全是商业产品榜单(zapier「6 best」、g2、xda「tried every」):Cursor、Lovable 这类 | 比较产品 | ❌ 形态对,内容不对:我们是 25 个开源模板 | 待定 |
| playwright mcp | 单个服务器的教程和视频(YouTube、qatouch、medium)、mcp.so 单页 | 学怎么用这一个 | ❌ 列表页接不住 | 已撤目标词 |
| supabase mcp | supabase.com 占 5 席 + 官方 GitHub | 导航(找官方) | ❌ 赢不了 | 已改为 database mcp |

结论:14 个词里 7 个对口、3 个对一半、3 个不对。只看搜索量会把"找官方那一个"的导航词当成列表词。
以后定目标词:搜索量 + KD + 前 10 名形态三样都看,一次约 $0.002/词。
