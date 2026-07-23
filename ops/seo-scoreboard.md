# SEO/GEO 水位记分板(纵向时间序列,只加行不改行)

> 五件套的最后一块:模型=理论 · 手册=方法 · 行动板=执行 · 编年史=历史 · **本表=数字**。
> 规则:**每周一复盘时加一行**(周表),每月 10 号加一行(月表);历史行永不修改 —— 数字错了就在备注里勘误。
> 数据来源:DR/引用域/AI responses ← Ahrefs;优质域 ← Bing;clicks/曝光/品牌词 ← `fetch_gsc.py`;GEO 会话/转化 ← `fetch_ga.py`;死点击 ← Clarity。

## 周表(每周一填,验收上周动作)

| 周一日期 | GSC clicks/周 | GSC 曝光/周 | 品牌词 pos | Bing 优质引用域 | GEO AI 会话/28d | 转化事件/周(checkout·cta·copy·订阅) | Clarity 死点击% | 备注 |
|---|---|---|---|---|---|---|---|---|
| 2026-07-10(基线,非周一) | ~56(≈8/天) | — | 11 | 32 | 40(ChatGPT 28+豆包 12) | 漏斗 3/3/3 起步 | 10.57 | 进水口总攻日;awesome PR ×5 在途、收录 6 在途 |
| 2026-07-13 | | | | | | | | ← 第一个正式周检 |

## 月表(每月 10 号填,对账权重线)

| 日期 | DR | UR | Ahrefs 引用域 | Ahrefs organic kw | **Ahrefs AI responses** | 付费台账累计 | 备注 |
|---|---|---|---|---|---|---|---|
| 2026-07-10(基线) | **6** | 4.4 | 313 | 0(词库门槛,以 GSC 为准) | **0**(GA 实测 40 会话,引用在其抽样外) | $275.9 | DR 6 = 权威病量化;本月对账看 arXiv+外链波的效果 |
| 2026-08-10 | | | | | | | ← 第一次月对账 |

## Ahrefs Site Audit 基线(2026-07-11 首爬,5,006 页采样)

| 指标 | 值 | 判定 |
|---|---|---|
| **Health Score** | **62(Fair)** | 基线,周五自动爬看趋势 |
| 孤儿页(采样内) | 1,871 | **audit 页=采样假象**(其唯一入链的 skill 父页没被爬到);**author/organization 页=真孤儿**(skill 页根本没链 author 页,待修);skill 页=部分假象 |
| 404 | 2(`gege-circle/.github` skill+audit) | 根因:**仓库名叫 `.github` 的组织配置仓**(库里共 30 个)不是 skill,生成了坏 URL;42 条内链指向它 |
| 3xx | 3 | 忽略 |
| Title 过长 | 3,666 | 模板级(audit 页标题式样超 60 字符),P3 |
| Meta desc 过长 | 3,368 | 同上,P3 |

## 在途验收窗口(到期就查,查完移进上表备注)
- **2026-07-13(周一)**:5 个 awesome PR 状态(`gh pr list`);Bing 引用域 32 → ?(本周口径 50+)
- **2026-07-24 前后(2 周)**:libhunt/skillget/navi/mdskills/aitoolnet/creati 9 链 在 Bing/Ahrefs 报表现身?SKILL.md 三站爬到没?
- **2026-08-10**:DR 6 → ?;AI responses 0 → ?(arXiv 若上线,重点看)
- **付费外链首单(若下周启动)**:顺序 = Stripe 捐赠页(免费先做)→ Adsy 垂类站试单 1-2 条 → GitHub 仓库置换谈判;每条按 8 项清单 + 台账 ROI 门槛验收,支出记付费台账
- **GEO 引用侧月检(每月 23 日前后)**:Bing AI Perf citations(基线 359/3mo)· Clarity Citation(基线 116/7d)· SoA(基线 15.76%)——三数进月表备注,看趋势不看单点

## 指标口径(防止将来自己骗自己)

- **GSC clicks/曝光**:site 全域、周窗口(周一至周日),`fetch_gsc.py queries` 汇总
- **品牌词 pos**:"agent skills hub" 精确词,`fetch_gsc.py brand`。**终态验收 = SERP 出现 sitelink**(出现后基本抢不走,每月搜一次截图存档,比位次更硬的护城河信号)
- **Bing 优质引用域**:Bing Webmaster Backlinks 面板的 referring domains 数(比 Ahrefs 严,当质量口径——部分差异来自 Ahrefs 会计入过期域名注水型外链)
- **GEO AI 会话**:GA sources 匹配 AI_SRC 元组(chatgpt/openai/perplexity/doubao/gemini/copilot/claude/kimi/deepseek),28 天窗口。**已知盲区**:只捕捉"AI 产生了可归因点击",测不到"被引用但未点击"(pos 6-9 CTR 0.1-0.4% 正是 AI Overviews 吃点击的证据)——引用侧观测靠 Clarity AI Visibility Citation(B3)/ Bing AI Performance(A2)/ Ahrefs AI responses(F5)三免费表互补,升级选项 DataForSEO LLM Mentions
- **转化事件**:deep_audit_checkout · enterprise_cta_click · install_command_copied · newsletter_subscribe 四件的周计数;checkout 事件带 value/currency 后可看转化金额
- **死点击**:Clarity dead-click 会话占比,28 天窗口(注:Clarity API 只有 3 天窗,28 天口径实际来自 dashboard)

## GEO 引用侧首批读数(2026-07-23 开通日,零成本双表上线)

**Bing AI Performance(3 个月窗,Copilot 系)**:Total Citations **359** · Avg. Cited Pages 12。GA 同期 AI 引荐仅 ~40 会话 → **"被引未点击"盲区实锤(引用量≈会话量 9 倍)**。
**Clarity AI Visibility Citation(7 天窗)**:Citations **116** · **Share of Authority 15.76%**(其他域名合计 620 次/84.24%)· AI referral traffic <1%。
**被引 Top 页**(两表交叉):/skill/routatic/proxy(35/3mo)· /skill/waybarrios/opencode-power-pack(32)· 首页(30)· /skill/Noi1r/beamer-skill(13/7d)· **/audit/langgenius/dify(10)= 信任层被 AI 引用的直接证据** · /best/authentication/(5)。
**Grounding queries 情报**:大头是具体 skill 名(opencode-power-pack 32、windy3f3f3f3f 系 22)+ 品牌词 agent skill hub(21,导航型)+ 真自然语言查询 "**free authentication tools for autonomous agents**"(5 次,SoA 20%,落 /best/authentication/)——后者是 /best/ 场景页吃 AI 引用的范式,选题池优先补同型 "free X tools for agents" 词。
**顺手发现(Bing 首页三条红色建议,待处理)**:①近期新页未走 IndexNow;②sitemap 缺重要新页;③爬取容量受限(crawl capacity)——排水线待查项。
**账号注意**:Bing Webmaster 登录身份 = **Google 主账号**(m17551076169@gmail.com),不是微软账号(WoodrowOlsonutt 那个微软号是空的,别用)。

## 新增观测项(2026-07-23 大师库对照起,进周/月表备注或下轮加列)

- **前 20 名页面总数**(月):哥飞"新站毕业线"= 100 个(与单词 pos 阈值互补的整站校验;GSC pages 榜可算)
- **GEO 会话转化质量**(月):GA4 建 AI_SRC 比较对象,AI 引荐 vs 整体的转化事件率——验证"AI 用户更值钱"
- **平均停留时长**(周,GA):行为侧反馈先于排名出现;audit 页"查完即走"页型的先行指标
- **渠道 CAC 口径**:该渠道累计支出 ÷ 该渠道归因**付费转化**数(不是会话数;转化为 0 记"∞,支出 $X 在途")——Toolify $99 的"验出回报"目前只到会话层,升级到订单层验收(utm 编进 Stripe client_reference_id)
- **付费台账记净额**:收入按到手净额(扣手续费/汇损 2-3%),不按 Stripe 面额
- **品牌被提及数**(月,可选):无链接提及对 AI 可见性相关 0.66-0.71 >> 外链 0.28;有 LLM Mentions 工具后正式入列
- **看别人站四指标**(竞品/大佬抄盘复核口径):峰值留存率(现值/峰值月)· 注册→达标间隔 · 直接访问占比(>50% = 品牌记忆信号)· Top keywords 是否品牌词
- **外链节奏自查**(2026-08-10 对账加验):07-10"单日 12+ 开口"总攻后,看 Ahrefs 引用域曲线是否单月陡增异常;曝光≠排名,真排名周期 ~180 天,DR/引用域的 6 个月长周期检查点 = 2027-01
