# SEO Tools 页重新启用:目标词数据(2026-10-13)

AIsa → DataForSEO,Google 美国。`keyword_suggestions` 12 个种子 $0.176(`suggestions.json.gz`),
`serp_google_organic_live_regular` 6 个词 $0.012(`serp.json.gz`)。搜索量数据约滞后两个月,最新一个月是 2026-08。

起因:`/best/seo-tools/` 08-23 退役(noindex)。GSC 近 90 天这页 0 条查询。10-13 把
zhuyansen/new-term-radar 收进目录时发现,它唯一对口的场景页就是这张退役页。

## 搜索量

| 词 | 12 个月均值 | 2026-08 | KD | 走势(2026-01 → 08) |
|---|---|---|---|---|
| claude seo skill(s) | 480 | 720 | 3 | 110 → 1,000(3 月)→ 720–880 |
| claude seo | 480 | 1,000 | 8 | 50 → 1,000 |
| seo skill | 320 | 480 | 0 | 210 → 480,3 月起持平 |
| google search console mcp | 480 | 1,000 | 17 | 320 → 1,000,一直在涨 |
| ahrefs mcp | 390 | 320 | 30 | 持平略降 |
| semrush mcp | 390 | 480 | 15 | 210 → 720 → 480 |
| dataforseo mcp | 210 | 320 | 18 | 缓涨 |
| seo skills claude | 110 | 170 | 0 | — |
| seo mcp | 90 | 90 | 6 | 很小 |
| claude code for seo | 90 | 90 | 8 | — |
| seo agent | 27,100 | 22,200 | 19 | 大词,见下 |
| ai seo tool | 2,400 | 1,300 | 26 | 在降 |
| keyword research mcp / geo skill | 无数据 | | | |

## 前 10 名是什么页面

| 词 | 前排 | 意图 | 列表页接得住吗 |
|---|---|---|---|
| claude seo skill | 第 1 是 GitHub 仓库 AgriciDaniel/claude-seo;然后是单个产品站(claudeseoskill.com、claude-seo.md)、seranking 自家 skill、hawkacademy「55 Free Downloads」 | 找那一个 + 找一批 | 对一半:claude-seo 要在首屏 |
| seo skill | 前 4 名全是 Claude 的 SEO skill:博客「8 Free Workflows」、awesomeskill.ai 和 skillsllm.com 的目录页、Reddit;第 5 名起才是"SEO 职业技能" | 找一批 | ✅ 目录页已经在排 |
| claude seo | 教程和视频(YouTube ×2、searchengineland、mcpmarket 单页) | 学怎么用 | ❌ 偏教程 |
| google search console mcp | 目录页:mcp.so 标签页第 2、mcpmarket ×2、mcpbundles;第 1 是一个 GitHub 文档页 | 找一个 | ✅ 目录页在排,前排弱 |
| seo mcp | 榜单文章「Best MCP Servers for SEO: 5 Compared」第 1、mcp.so、mcpserver.so | 找一批 | ✅ 形态对,但只有 90/月 |
| seo agent | 商业产品和概念讲解;kimi.ai「13 AI SEO Skills」排第 4 | 了解 + 找产品 | ❌ 不是我们的词 |

## 目录里有什么

线上索引(10-13)里 SEO / GEO 相关 284 个,其中 118 个 ≥50★,全部评级 safe:
marketingskills 53.7K、open-seo 22.8K、claude-seo 18.3K、geo-seo-claude 11.0K、NotFair 3.3K、
toprank 2.6K、mcp-gsc 1.5K、open-seo-mcp-skills 1.2K、geo-optimizer-skill 1.0K ……

退役前这页按"关键词命中数"排序,前 30 名里没有 claude-seo 和 geo-seo-claude(描述短的大项目被描述啰嗦的小项目挤掉)。
这是它当时拿不到流量的一个原因:搜「claude seo skill」的人要找的那个仓库不在页面上。

## 建议

- 目标词:**claude seo skill**(720/月,KD 3,还在高位),带上 **seo skill**(480,KD 0)。
- 标题:`Claude SEO Skills & SEO MCP Servers`。首屏点名 AgriciDaniel/claude-seo(和 humanizer 页点名 blader/humanizer 同一做法)。
- 加一节 **Google Search Console MCP**(1,000/月且在涨,前排是目录页):mcp-gsc、search-console-mcp、mcp-server-gsc、Suganthans-GSC-MCP。
- 按星数排序;排除无关的 geo(地理、geo-distributed)和纯营销合集里只顺带提 SEO 的。
- 不做:seo agent(产品词)、ai seo tool(SaaS 榜单,同 vibe coding tool 的教训)、claude seo(教程意图)。
