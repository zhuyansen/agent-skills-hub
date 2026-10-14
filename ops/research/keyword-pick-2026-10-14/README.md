# 在线场景页目标词：加上「流量潜力」和「业务价值」（2026-10-14）

工具：`ops/seo/keyword_pick.py --live-pages`（33 个在线页里设了 `seo_keyword` 的 19 个）。原始数据 `raw.json`，本次 $0.62。
两列的来历：熠辉IndieDev 的 SEO 课（`ops/research/yihui-seo-course-2026-10/`）筛词五步里的第 2、3 步，我们之前只看搜索量、KD 和前 10 名形态。

| 词 | 月搜 | KD | 意图 | 流量潜力 | 业务价值 | 前 10 名（实时） | 潜力按这一页 | 价值理由 |
|---|---|---|---|---|---|---|---|---|
| humanizer skill | 1,300 | 7 | informational | 3,500 | 3 | 仓库 2 · 单个工具 5 · 视频 1 · 论坛 1 | github.com | Searchers want to find or compare humanizer agent skills; graded list answers completely. |
| claude design skills | 1,600 | 15 | commercial | 2,418 | 3 | 榜单 3 · 仓库 1 · 单个工具 3 · 视频 1 · 论坛 1 | github.com | Searchers want to find/compare design skills for Claude Code; graded list answers completely. |
| github mcp | 6,600 | 32 | navigational | 1,999 | 3 | 目录 1 · 仓库 3 · 教程 2 | github.com | Searchers want to find/compare GitHub MCP servers; graded list answers completely. |
| claude seo skill | 480 | 3 | navigational | 1,593 | 3 | 榜单 1 · 仓库 1 · 单个工具 5 · 论坛 1 | github.com | Searchers want to find or compare SEO skills for Claude Code; graded list fits perfectly. |
| remotion skill | 1,300 | 17 | informational | 1,297 | 3 | 目录 1 · 单个工具 4 · 教程 2 · 视频 1 | remotion.dev | Searchers want to find/compare Remotion skills for Claude Code; graded list answers completely. |
| codex skill | 4,400 | 7 | transactional | 746 | 3 | 榜单 1 · 目录 1 · 仓库 3 · 单个工具 2 · 教程 1 · 论坛 1 | github.com | Searchers want to find or compare Codex agent skills; graded list answers completely. |
| claude code review skill | 590 | 0 | transactional | 619 | 3 | 榜单 2 · 目录 2 · 仓库 2 · 单个工具 1 · 论坛 2 | github.com | Searchers want to find/compare Claude Code skills for code review; graded list answers perfectly. |
| obsidian mcp | 2,400 | 3 | navigational | 404 | 3 | 目录 3 · 单个工具 3 · 教程 1 · 论坛 1 | community.obsidian.md | Searchers want to find/compare Obsidian MCP servers; graded list answers completely. |
| database mcp | 480 | 3 | navigational | 210 | 3 | 目录 1 · 单个工具 5 · 教程 1 · 视频 2 | github.com | Searchers want to find/compare database MCP servers; graded list is a complete answer. |
| claude code skills | 12,100 | 30 | informational | 26 ⚠ | 3 | 榜单 1 · 仓库 2 · 单个工具 3 · 教程 1 · 论坛 1 | reddit.com | Searchers want to find or compare Claude Code skills; a graded list is a complete answer. |
| claude code hooks | 3,600 | 16 | navigational | 3,469 | 2 | 仓库 1 · 单个工具 5 · 教程 1 · 视频 1 · 论坛 1 | code.claude.com | Searchers want docs/tutorials on hooks; list page is one good answer among official docs. |
| claude skills manager | – | – | – | – | 2 | 榜单 1 · 目录 1 · 仓库 2 · 单个工具 3 · 论坛 2 | – | Searchers want a specific tool or docs; list page is one good answer among others. |
| open source telegram bot | 10 | – | informational | – | 2 | 榜单 1 · 目录 1 · 仓库 2 · 单个工具 3 · 论坛 2 | – | Searchers want open-source bots; list page is a good answer but first page mixes GitHub repos and tutorials. |
| vibe coding tool | 590 | 41 | informational | 3,411 | 1 | 榜单 4 · 单个工具 4 · 论坛 1 | xda-developers.com | Searchers want commercial vibe coding platforms; first page shows product listicles, not agent skills. |
| multi agent orchestration | 720 | 22 | commercial | 512 | 1 | 榜单 1 · 单个工具 6 · 教程 1 · 文档 1 | platform.claude.com | Searchers want guides, frameworks, or definitions; not primarily a skill/plugin comparison. |
| prompt engineering tool | 210 | 24 | navigational | 98 | 1 | 榜单 4 · 单个工具 2 · 教程 1 · 视频 1 · 论坛 1 | reddit.com | Searchers want tutorials, techniques, or commercial tools, not agent skill comparisons. |
| code refactoring tool | 170 | 9 | informational | 38 | 1 | 榜单 3 · 单个工具 4 · 论坛 2 | reddit.com | Searchers want commercial/general tools; first page shows listicles of products, not agent skills. |
| ai reverse engineering | 70 | 0 | informational | 66 | 0 | 单个工具 4 · 论坛 3 | reddit.com | Searchers want tutorials, news, or commercial tools for reverse engineering, not agent skills. |
| jev skill | – | – | – | – | 0 | 单个工具 6 · 教程 1 · 视频 1 | – | First page shows Jev is a TypeSafe AI decision model, unrelated to agent skills hub listings. |

流量潜力 = Semrush 里这个词排第一的页面在美国的月自然流量估算：该网址排进前 20 的词，搜索量 × 该位置点击率，加总（Ahrefs 的定义，换成 Semrush 的数据）。Semrush 没有第一名的数据时用下一名，表里注明第几名。⚠ = 不到「月搜 × 第一名点击率」的四分之一：Semrush 对这页的数据少，只能当下限看。「前 10 名（实时）」来自 DataForSEO 的实时结果，只用来看页面形态和判断业务价值。
业务价值 0–3 由 claude-sonnet-4-6 根据词和首页标题起草，可在 ops/seo/keyword-value-overrides.json 里改。本次 $0.622。

## 怎么读

- **流量潜力**：Ahrefs 的定义（这个词排第一的页面的总自然流量）换成 Semrush 的数据。第一名取自 Semrush 自己的结果（按月更新，两次查询一致）；它的流量 = 该网址排进前 20 的词 × 该位置点击率，加总。搜索量小的词可能挂在一个大话题上（claude seo skill：月搜 480，第一名页面的流量约 1,600），反之亦然。
- **业务价值 0–3**：一个带安全评级的开源 skill / MCP 列表能多完整地回答这个搜索。claude-sonnet-4-6 根据词和实时首页的标题起草，附理由；**这是草稿**，不同意的写进 `ops/seo/keyword-value-overrides.json`，下次运行以人为准。
- 「–」是 Semrush 没有数据；⚠ 是 Semrush 对第一名页面的数据少，数字只能当下限看（claude code skills：月搜 1.2 万、KD 30，潜力显然不止 26）。

## 能看出什么

- **值得继续投入的**（价值 3、潜力过千）：humanizer skill、claude design skills、github mcp、claude seo skill、remotion skill。
- **价值 3、潜力几百**：codex skill、claude code review skill、obsidian mcp、database mcp。量不大，但对口。
- **潜力大、价值低**：vibe coding tool（3,411，价值 1）。前排是商业产品榜单，和 10-11 前 10 名形态核对的结论一致（「形态对，内容不对」）。multi agent orchestration（512，价值 1）也是这样。
- **两头都低**：code refactoring tool、prompt engineering tool、ai reverse engineering。这些页面的目标词可以换，或者接受它们只是长尾页。
- **模型判 0 分、要人看一眼的**：jev skill（搜的人想了解 Jev 这个模型本身，我们那页是用 Jev 做的项目合集）、ai reverse engineering。

## 试过但放弃的算法（都在 10-14）

1. DataForSEO 按网址估流量：「seo agent」（月搜 2.7 万）第一名页面只估出每月 1 次访问，GitHub 页面直接没数据。
2. DataForSEO 的「网址排名词」接口：AIsa 上没开放。
3. 用实时搜索结果里的第一名去查 Semrush：同一个词两次取到的第一名不同（一次 GitHub 仓库、一次 YouTube 视频），有一次「vibe coding tool」返回的是 Tool 乐队的页面。所以现在第一名改从 Semrush 自己的结果里取，实时结果只用来看形态。
