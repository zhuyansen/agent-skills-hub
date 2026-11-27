# Bing 收录排查（2026-11-26）

起因：Bing 给 agentskillshub.top 的点击只有 Google 的约 1%，还在往下走；jasonzhu.ai 在 Bing 的点击约是它在 Google 的一半。这份记录查了站点这一侧能查的所有环节，结论在最后。BWT（Bing Webmaster Tools）里才能看的东西单独列出，要 Jason 登录看。

## 一、数字

Bing 导出（`~/出海/specs/bing-ai/*_SearchPerformanceOverview_2026-11-26.csv`，2026-08-26 到 11-24，91 天，每 14 天合计）：

| 时段 | ASH 点击/天 | ASH 展示/天 | ASH CTR | jasonzhu.ai 点击/天 | jasonzhu.ai 展示/天 |
|---|---:|---:|---:|---:|---:|
| 08-26 起 | 2.7 | 131 | 2.07% | 4.9 | 137 |
| 09-09 起 | 2.2 | 171 | 1.30% | 4.1 | 139 |
| 09-23 起 | 0.8 | 80 | 0.98% | 9.4 | 170 |
| 10-07 起 | 1.5 | 80 | 1.89% | 24.3 | 302 |
| 10-21 起 | 1.2 | 107 | 1.13% | 28.3 | 306 |
| 11-04 起 | 1.6 | 98 | 1.61% | 30.1 | 358 |
| 11-18 起（7 天） | 2.1 | 119 | 1.81% | 36.0 | 530 |
| **91 天合计** | **155 次** | **10,165 次** | | **1,667 次** | **23,478 次** |

同期 Google（`ops/seo-scoreboard.md` 周表）：11-02 那周 1,794 次点击、93,680 次展示，11-09 那周 2,279 次、117,159 次。ASH 在 Bing 一天约 100 次展示，Google 一天一万多次：差距在展示量上，不在 CTR 上。展示少，要么是 Bing 收录的页少，要么是 Bing 上搜这些词的人少，两者都要看。

## 二、站点这一侧：逐项检查

| 检查项 | 结果 | 证据 |
|---|---|---|
| robots.txt | 正常 | 200；`User-agent: *` 下 `Allow: /`，只挡 `?search=` `?tab=` `?page=` `?sort=` `?repo=` 和 `/best-runs/*.html$`；`Sitemap:` 指向 `/sitemap.xml`。线上还是 `ai-train=no`（81ea1c2 改成 yes，还没部署，跟 Bing 搜索无关）。 |
| sitemap 索引和 9 个子 sitemap | 正常 | 全部 200、`application/xml`、XML 可解析；最大的是 sitemap-audit.xml 4,772 条、sitemap-top.xml 4,700 条 / 914 KB，远低于 5 万条和 50 MB；共 9,647 个不同网址；没有未来日期，没有带参数或不带斜杠的网址。skill 页的 lastmod 是仓库最后一次提交的日期（最早 2012-06-17），不是页面改动日期。 |
| IndexNow | 在用，且 Bing 接收 | key 文件 `/a52f1d0890354e5b84d0e4e1ba17bd84.txt` 线上 200；`deploy.yml` 的 notify-search-engines 每次部署后比对 sitemap 快照、只推新增/改日期/删除的网址。抽查日志：781、753、43、2 个网址的批次都是 `api.indexnow.org` 返回 HTTP 200，10 次部署每一步都成功。 |
| meta robots / X-Robots-Tag / canonical | 正常 | sitemap 里随机抽 8 个 /skill/、6 个 /audit/、3 个 /category/、首页、一个 /best/、/daily/：全部 200，没有 X-Robots-Tag，没有 noindex，canonical 都指向自己。 |
| 跳转 | 正常 | http→https、www→裸域、缺斜杠→加斜杠都是一跳 301（`http://www.…/skill/…` 也是一跳到最终地址）。 |
| Cloudflare 对 Bingbot UA | 没拦（弱证据） | 用 bingbot UA 和 Chrome UA 请求同一批网址，状态码、robots、canonical 完全一样。冒充的 UA 不等于真 Bingbot，所以只能算弱证据；更强的证据见下一行。 |
| 真实 Bingbot 抓取（edge-proxy KV 日志） | 在抓，且 29% 撞 404 | 11-21 起 Worker 记下了 UA 为 Bingbot 的访问（只覆盖 `/`、`/best/*`、`/audit/*`、sitemap 等 Worker 路由）：每天 110–120 个不同路径，和 Googlebot 同一量级。11-22 到 11-25 的 293 个 /audit/ 抓取里 **86 个是 404**，/best/ 都是 200 或 304。 |

### /audit/ 404 是怎么来的

把 Bingbot 撞到 404 的 86 个审计页拿去查库：76 个是「SAFE 且不到 500 星」，按 07-28 的规则不再有审计页；9 个星数已跌到 50 以下；1 个已不在库里（原名可能已改名跳转）。评级随每次扫描变化，页面跟着出现又消失（index-health-2026-10-14.md 里的「N 不稳定」）。86 个里 **85 个的 /skill/ 页线上是 200**，页上有同样的评级。

修法（本分支，`ops/edge-proxy/worker.js`）：GitHub Pages 对 `/audit/<owner>/<repo>/` 回 404、而 `/skill/<owner>/<repo>/` 存在时，Worker 回 301 到 skill 页；其他 404 原样返回，`/best/*` 不碰。同时把 Bing 公布的 Bingbot IP 段（bingbot.json，29 段）加进 `bot-ranges.js`，以后 KV 里能分清真假 Bingbot。Worker 不会自动部署，要 `npx wrangler deploy`。

## 三、和 jasonzhu.ai 的 IndexNow 比

| | jasonzhu.ai（scripts/indexnow.mjs + indexnow.yml） | agentskillshub.top（deploy.yml notify-search-engines） |
|---|---|---|
| 触发 | 内容文件改动的 push，或每日任务完成后 | 每次部署之后 |
| 推哪些网址 | 由改动的 md/json 推出网址，和线上 sitemap 取交集，等新网址进 sitemap 再推 | 线上 sitemap 和上次快照比：新增、lastmod 变了、被删的网址 |
| 端点 | api.indexnow.org，200/202 算成功 | api.indexnow.org，5xx 时退到 bing.com/indexnow；4xx 让任务失败 |
| 结论 | 两边都在正常推送。ASH 这套覆盖面更大（数据驱动的页面也会推），不缺 IndexNow。 | |

ASH 唯一推不到的是不在 sitemap 里的网址：50–499 星的 skill 页是 noindex（有意为之），作者页 08-16 撤出了 sitemap。这次新加的 `/browse/` 目录页进 sitemap-top.xml，部署后会被当作「新增」推一次。

## 四、结论

站点这一侧没有挡住 Bing 的东西：robots、sitemap、IndexNow、canonical、跳转、Cloudflare 都正常，真实 Bingbot 每天在抓。查到的唯一实锤问题是审计页忽有忽无造成的 404（Bingbot 审计页抓取的 29%），已在 Worker 里修，等部署。

展示量低更可能是这两件事，要 BWT 里的数据才能定：
1. **Bing 收录了多少页。** Google 也只认识约三分之一的可收录网址（index-health-2026-10-14.md），Bing 对低外链新站更保守。看 BWT 的 Index Explorer / Site Explorer。
2. **Bing 上的需求本来就小、而且在中国。** `frontend/scripts/skill-page-copy.mjs` 的注释写过：ASH 的 Bing 展示大多来自中国用户搜仓库名。jasonzhu.ai 以中文页为主，它的 Bing 点击 10 月起涨到原来的 5–6 倍（上表）。两站的差距可能主要是受众语言不同，而不是技术问题；这是推测，要看 BWT 的 Search Performance 按国家/查询拆开才能确认。

## 五、只有 Jason 能在 BWT 里做的

1. **Sitemaps**：确认提交的是 `https://agentskillshub.top/sitemap.xml`，看每个子 sitemap 的状态、上次读取时间、发现的网址数和报错。
2. **Index Explorer / Site Explorer**：/skill/、/audit/、/best/ 各收录了多少（这是判断「收录少」还是「需求少」的关键数）。
3. **URL Inspection**：抽 3–5 个 sitemap-top 里的 /skill/ 页和 /audit/ 页，看是否「已收录」、Bing 看到的渲染结果、最后抓取时间。
4. **Crawl Control / 抓取统计**：07-23 记过「爬取容量受限」，看抓取速率设置是不是被调低了、有没有抓取错误（尤其 404 的数量和来源）。
5. **Recommendations / Site Scan**：07-23 的三条红色建议（新页未走 IndexNow、sitemap 缺重要新页、爬取容量受限）现在还在不在。
6. **IndexNow 面板**：确认能看到最近的提交（应有 11-25、11-26 的批次）且没有被拒。
7. **Search Performance 按国家和查询拆开**：两站对照，验证第四节第 2 条。
8. 部署 edge-proxy 的改动（`cd ops/edge-proxy && npx wrangler deploy`），然后 `curl -sI https://agentskillshub.top/audit/bitwarden/mcp-server/` 应该回 301。

一周后复查：KV 日志里 Bingbot 的 /audit/ 404 比例（现在 29%）应该接近 0，换成 301。
