# SEO 水系执行手册(实践顺序 · ROI · 工具 · 避坑)

> 姊妹篇:`ops/seo-watersystem-model.md`(结构)· `ops/gefei-seo-playbook.md`(方法论)。
> 本篇只收 AgentSkillsHub 实战验证过的,每条背后有伤疤或实测数字。

## 一、实践顺序(按依赖,不是按舒服)

```
第 0 步  数据先行:接 GSC/GA + 埋转化事件 ——【我们最大的时序错误:第 10 周才埋点,盲飞一路】
第 1 步  架构 + 排水闸:URL 结构、noindex 门槛(stars≥50)一次定型,页量暴涨后改不动
第 2 步  进水口 Day 1 开做:HF 数据集 20 分钟,llms.txt 5 分钟 ——【我们拖到第 10 周,GEO 白等】
第 3 步  收银台先于流量优化:有需求信号立刻接支付 ——【mailto 挂了数周,enterprise 90 会话 0 转化】
持续     撑子页只在 GSC 出数据后建(pos 8-20 临门一脚);内链拓扑页量>1000 就该排查孤儿
之后     回流/告警等 funnel 数据说话;仪式化:日报每天、复盘每周、体检插件每月
```

**一句话:数据 → 排水 → 进水 → 收银台 → 才轮到堆页。我们实际是反着走的,补课花了一周。**

## 二、ROI 排序(实测单位小时回报,从高到低)

| # | 动作 | 成本 | 实测回报 |
|---|---|---|---|
| 1 | **llms.txt + robots 放行 AI 爬虫** | 5 分钟 | GEO 前提;上线两天 ChatGPT+豆包 40 会话冒头 |
| 2 | **HF/Kaggle 数据集** | 20 分钟/个 | DR~90 反链 + 实体 sameAs + 天然被 AI 引用 |
| 3 | **埋转化事件(gtag)** | 半天 | 从盲飞到有表 —— 后续一切优化的前提 |
| 4 | **mailto → 真支付按钮** | 半天 | 拆掉变现的唯一物理阻断(此前 0 转化不是需求问题) |
| 5 | **死点击修复(Clarity 元素级定位)** | 半天 | 死点击 12.15%→10.57%、怒点清零,3 天内可验证 |
| 6 | **拆内链孤儿岛** | 1 天 | 7,924 页从死水岛接回主路,audit 页才有资格排 "is X safe" |
| 7 | **数据驱动场景页** | 2 小时/个 | 便宜但回报有限:best ppt skill 到 pos 3.1 仍是零星曝光 |
| 8 | ❌ **堆更多撑子页** | — | 饱和后边际趋零,还引发自相竞争 |
| 9 | ❌ **改 pos 50+ 词的标题** | — | 权威病,措辞无效,纯浪费 |

## 三、工具必上清单(六类)

**A. 站长后台**(搜索引擎自家:收录/词/外链)
- A1 GSC API(词/位次/rising;代理坑见避坑 14)
- A2 Bing Webmaster(已收录/已提交比 = 排水水位;Backlinks 免费扒竞品外链)
- A3 [候选·未实战] Yandex Webmaster —— GSC 出现俄语流量再上

**B. 行为分析四件套**(看用户)
- B1 GA4(转化事件;先确认 gtag 流向哪个 property —— 见避坑 4)
- B2 Plausible(轻量真 PV;靠它抓到重复页自相竞争)
- B3 Clarity(免费元素级死点击/录屏;API 只到页面级,元素级须进 dashboard 热力图)

**C. 转化埋点**(看钱)
- C1 gtag 自定义事件 ×4 起步:install/audit/cta/subscribe
- C2 Stripe Payment Link(收银台本身就是计量器:client_reference_id 附单)

**D. 自动化/仪式**(让数据自己来找你)
- D1 GitHub Actions cron(四件套日扫 + Resend 邮件送达)
- D2 本地 scheduled task(日报每天 / 周复盘每周一)
- D3 IndexNow(build 链里挂 submit-indexnow,收录加速)

**E. 发布/进水口 CLI**
- E1 hf · E2 kaggle(数据集)· E3 npm(CLI/MCP 包)· E4 mcpb(Smithery 打包)· E5 Overleaf(arXiv)

**F. 体检/侦察**
- F1 AITDK 类 SEO 体检插件:每月扫核心页 —— 10 秒暴露了我们仨月没发现的 Helmet 覆盖
- F2 gh CLI(验刷星:单仓爆星+作者其余仓库<20★;查作者履历)
- F3 无头浏览器 + Chrome cookie 导入(X 长文抓取 / Clarity 后台热力图)
- F4 agent-reach(多平台抓取:X/Reddit/微信等)
- F5 Ahrefs Webmaster Tools 免费版(ahrefs.com/webmaster-tools)—— 自家外链/健康监控,Bing 之外第二视角;注册后验证域名(可复用 GSC 授权或 DNS),看 Backlinks + Site Audit 两个报表

## 四、避坑指南(15 条,每条一个伤疤)

1. **GSC 曝光榜 ≠ 品类深度**。建页前三查:目录广度、grep 现有 slug、Plausible 热门页。(ppt-skills 撞 ppt-presentation,自相竞争 3 天才发现)
2. **pos 50+ 是权威病**,不是措辞病。建页、改标题都无效,归权重线。
3. **小样本位次是幻觉**:pos 3.1 = 28 天仅 19 次曝光、跨 9 国的平均;"我怎么搜不到"是常态,别恐慌也别吹。
4. **先查 gtag 流向再信 GA**:我们的数据流进错的 property,正确的那个是空的,差点全盘误读。
5. **SPA 的 meta 有两层**:Helmet 会覆盖 index.html。改 title/desc 必须两层同改,否则改了个寂寞。
6. **数字写地板不写精确**:"130,000+" 可活数月;精确数会烂在页面里(我们清了三代共 18 处:62K/100K/117K)。
7. **mailto 是转化杀手**。想收钱就上支付链接,Stripe Payment Link 半天通。
8. **死点击三大惯犯**:带动画的状态元素(呼吸灯)、卡片身不可点、标题点了开新标签(Clarity 判死+弹窗拦截)。修法:给动画元素目的地、整卡可点(closest('a') 保护内链)、标题行为全站统一。
9. **刷星识别**:单仓爆星 + 作者其余仓库全 <20★ + unknown 评级 → 保守排除并注明。信任型站点荐错一个,人设塌方。
10. **20 万+文件的 GitHub Pages 会在 syncing_files 抽风**:build 绿 deploy 红 = 平台问题,`gh run rerun <id> --failed`,别动代码。
11. **cron 要算平台排队延迟**:GitHub schedule 晚 0-40 分钟。送达时刻设计在用户习惯**之前**(我们连续两天比邮件早 2 分钟去查)。
12. **管道建好 ≠ 水会流**:/daily/ 上线后上游断流 8 天没人发现。活水必须配仪式或自动化,建完当天就定。
13. **X 长文抓取**:syndication API 不给 note_tweet 正文;无头浏览器 + Chrome cookies 是唯一稳路(抓完停会话)。
14. **代理矩阵要记死**:googleapis 走 Clash(gRPC 只认小写 env);clarity.ms 必须直连;undici 系 CLI 不认 env 代理。
15. **渠道打透一个**:X 906 会话 vs Google organic 84。全平台铺 = 全平台死;先把已验证的打透,再开下一个。

---
*更新纪律:只加带伤疤的条目。没有新伤疤就不要动这份文件。*
