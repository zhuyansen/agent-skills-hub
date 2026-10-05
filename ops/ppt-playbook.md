# PPT 页打法

`/best/ppt-presentation/` 是怎么一步步成为全站第一搜索页的,以及换一个主题照着复刻的清单。2026-10-05 整理。

## 现状

- **GSC 近 3 个月**:**1,103 次点击、50,006 次曝光、平均排名 7.5**,约占全站搜索点击的三分之二。
- **`ppt skills`**(KD 39.8,"容易"):**排第 4**,我们 DR 只有 12。前面是两个 github.com 结果(平台固定位,任何网站都抢不到)和 kimi.ai(DR 77)。哥飞 SEO 工具箱的 SERP 解密把这个页面评为"页面派范本":靠页面上位,不靠域名权重。
- **`codex ppt skill`**:**排第 2**,全站点击最多的词。
- **On Page 体检**(哥飞工具箱):10-05 优化后从 88 升到 **93**。
- **GitHub 榜单**:zhuyansen/awesome-codex-ppt-skills,每天自动更新。

## 按时间做了什么

| 时间 | 动作 | 作用 |
|---|---|---|
| 05-04 | "推文 → 落地页对齐"(24ed67e):用 featured 把推文要提到的项目钉在页面最前面 | 从推文点进来的人,看到的正是推文里承诺的内容。 |
| 05-05 | 建页(172f023) | |
| 05-09 | @GoSailGlobal(3.67 万粉)[发推](https://x.com/GoSailGlobal/status/2053103395863699594):5 种 AI PPT 风格,每种配一个开源 skill,附页面链接。16.7 万浏览、971 赞、248 转发、1,302 收藏 | 页面此前搜索曝光为 **0**,发推那一周冲到 **30,687**。Google 当周发现并收录了它,最早的搜索词正是推文里的:`ppt skills`、`guizang ppt skill`、`github ppt skill`。 |
| 06-23 | 标题从 `PPT & Presentation Skills` 改为 `AI PPT & Slide Generators`(2a1e59c) | 全站 96% 的曝光来自 "presentation skills",搜的人想学演讲,零点击。改成明确的工具意图。 |
| 07-06 | 按词聚类 GSC 曝光,发现 ppt 断层第一;先去目录确认背后有足够多工具,再决定投入 | GSC 只显示已经在排的词,看不到品类深度,目录能看到。 |
| 07-06 | 决定**不**另开 `/best/ppt-skills/` | 第二个页面会分走已在排名页面的信号。 |
| 07-13 | 加内链(8245091):首页热门、页脚、三个相关页面都指向它 | 一周内 `codex ppt skill` 每周点击从 0 涨到 17,排名 9.0 → 5.2。 |
| 7 月 | 头部词卡住时选择等待,不改页面 | 排名靠内链和时间在涨;每周复盘的结论都是"继续等"。 |
| 10-03 | 改成审核页:GitHub 全星级搜索 + 目录,Jev 逐个读 README,6 个类型可筛选,中文描述经 Jev 核对;标题改为 "PPT Skills for Codex & Claude Code" | 页面回答"该用哪个工具",比关键词自动选出来的更全、更干净。 |
| 10-03 | 配 GitHub 榜单 awesome-codex-ppt-skills,双向互链,每日任务自动补充 | "PPT skills GitHub" 本身就是相关搜索;榜单是第二个入口,也是可被引用的来源。 |
| 10-05 | 标题 ≤60 字符;每张卡片的 "View details / GitHub" 文字换成一个 GitHub 图标;补图片宽高;用两条 FAQ 回答相关搜索(`extra_faq`) | On Page 体检的扣分项全部处理;FAQ 直接回答 "PPT skills GitHub" 和 "Guizang PPT skill"。 |

## 复刻清单

0. **先发推,不只是建页。** 先建好页面,用 `featured` 把推文要提到的项目钉在最前面,再在 X 上发带链接的推文。内容要是具体的清单(比如"5 种风格,每种一个开源 skill"),让人愿意收藏。PPT 那条推文让页面一周内从 0 涨到 3 万曝光。收藏(1,302)比点赞(971)还多,说明要写成"可以收藏备查的参考资料"。
1. **用数据选题,不靠感觉。**
   - **GSC**:按词聚类近 3 个月的查询,排在 5–15 名的主题已经接近能排上来。40 名开外是权重问题,换页面救不了,跳过。
   - **AIsa(DataForSEO)**:查 "skill / MCP for X" 这种说法的搜索量和 KD。**KD 比搜索量重要**:ppt 词簇每月只有约 840 次搜索,KD ≤5,却带来 5 万曝光。
   - **目录**:背后有没有 30 个以上真实工具?只有一个知名仓库的主题是导航型搜索,会被 GitHub 拿走。
2. **一个主题只做一个页面。** 已经有页面在排这个主题,就升级它;同一种意图不要另开网址。
3. **标题写清工具意图和 agent 名字**(如 "… Skills for Codex & Claude Code"),不超过 60 字符(生成器会自动控制)。避开有歧义的词(比如 "presentation skills" 搜的是演讲技巧)。
4. **审核内容,不靠关键词自动选卡**(`ops/jev-review/page_profiles.py` → `upgrade_page.py collect/split/publish`,`scenario_gate.py judge/types`):
   - 每个上页的仓库都由 Jev 读 README:是否切题、是不是软件、README 质量;
   - 分 5–7 个类型,页面上可筛选;
   - 50★ 以下的,只收 README 能展示效果的;
   - 超过 300 个就用严格规则:切题分 ≥0.8,50★ 以下只收高质量档。
5. **在页面上回答 SERP 里的相关搜索**(`extra_faq`):用哥飞工具箱跑 `/serp/?keyword=<头部词>&gl=us`,拿到"相关搜索",把真实问题各写成一条 FAQ,答案点名具体仓库。同时写进 FAQPage 结构化数据。
6. **配 GitHub 榜单**(适合大家会去"GitHub 上找"的主题;`build_video_list.py`、`list_text_pages.py`):同一批仓库、同样分类,双向互链,加入每日任务。
7. **站内链接**:首页热门区、页脚、相邻页面的 related。**站外链接**:权重层外链(客座文章、媒体提及)直接链到专题页,而不是首页;见下面"外链"一节。
8. **每日维护**:每日任务自动审核新仓库,去掉已删除和改名的仓库,重建榜单;报告发在 issue #26。
9. **测完就等。** 用哥飞工具箱 `/audit/?url=&kw=` 复测分数;每周按页面和词看 GSC。排名在涨的页面不要动,内链和时间会复利。

## 外链:PPT 页实际靠的是什么

10-05 用 AIsa(DataForSEO)核实:**PPT 页本身没有任何外链域名**。推文里的链接走 t.co 跳转,而且是 nofollow。全站有 117 个外链域名,几乎都指向首页。所以 PPT 页能排上来,靠的是页面内容、全站权重和那条推文,而不是指向它的外链。

全站权重来自 `ops/backlink-todo.md` 里的两层外链(7-23 定的,见 `ops/research/niko-meeting-2026-07-23.md`):

| 层 | 做法 | 已做的 |
|---|---|---|
| 权重层:真实网站的 dofollow 链接 | 付费客座文章,每天最多 1–2 篇,每条核对 `rel` 属性 | 07-16:programminginsider、nerdbot、thedatascientist、techbullion、aijourn,共 10 条 dofollow。带 dofollow 收录页的付费导航站:creati.ai、Toolify、TAAFT、aibase(合计约 $276)。 |
| 权重层:可被引用的数据 | 别人会引用的数据源 | Zenodo DOI、Kaggle notebook、Dev.to 文章、Wikidata 实体、Hugging Face 数据集卡片。 |
| 发现层:帮助收录和 AI 引用,不传权重 | 免费目录和列表:只验收,不再扩量 | libhunt、AlternativeTo、mcpservers.org、deepwiki;awesome 列表 PR(nofollow,面向开发者,也是大模型训练会读的内容)。 |
| 明确拒绝 | 买 PH 投票、买 GitHub 星 | 和"信任层"的定位冲突;我们自己的审计就专门识别这类刷量。 |

Ahrefs DR:6(07-10)→ 7(07-16)→ 12(10-05)。

**接下来的页面,缺的是深层链接。** 目前所有权重层外链都指向首页。下一批客座文章和媒体提及要直接链到专题页(`/best/claude-video-skills/`、`/best/claude-code-hooks/` 等),锚文本用主题词;再把我们的 GitHub 榜单投到所在主题的大型 awesome 列表(nofollow,不传权重,但能带来读者,也是大模型会读的内容)。

## PPT 页还没做的

- **一条 "ppt skills" 的 YouTube 视频**:Google 第一页的 10 个结果里有 2 个是 YouTube。
- **减少字数**:每页约 9,000 词,体检工具建议 1,200–1,800;要明显减少只能少放卡片。

## 已经复刻到哪些页面

10-03 到 10-05 用同一条流水线升级了:视频、Jev、skill 管理、Telegram、设计、知识库 / LLM Wiki、Claude Code Hooks、Obsidian、去 AI 味(都配了 GitHub 榜单);code review、浏览器自动化、Codex、数据库 MCP(只升级页面);生图页(配榜单,进行中)。第 5 步(用 FAQ 回答相关搜索)和第 7 步(站内链接)已在 10-05 补到所有审核页(c1a2436)。第 0 步发推和深层外链,目前只有 PPT 页做过发推,深层外链还都没有。
