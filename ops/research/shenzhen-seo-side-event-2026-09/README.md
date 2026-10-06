# 深圳 SEO 大会周边活动(9/12)七份 PPT 消化

来源:用户给的 7 份 PDF(JP Zhang 开场/闭幕/9 Steps,Tanya Van Gastel,Magenta Qin,Jacky Lin,Sacha Fournier)。2026-10-06 整理。
每份讲者都有自家生意(Rankingonai、SerpApi、journofinder),数字多数无出处,下面只记能落到我们项目上的部分。

## 五个讲者一句话

| 讲者 | 主旨 | 证据强度 |
|---|---|---|
| Tanya Van Gastel | APEX:Authority(自己写 Best X 榜单)、Presence(SEO 是地基)、Endorsements(别人的榜单/YouTube/Reddit)、eXtractability(结论放前 30%、服务端渲染) | 案例是自家客户 editGPT;多数百分比无出处;P13 算术错(4.33x 写成 4.8x) |
| Sacha Fournier | 反应式 PR:热点 48h 内把专家引语发给正在写的记者;拆成 7 个 SKILL.md,人只审核和按发送 | 84% earned media 来源不明;每步 Best 档都是自家产品 |
| Magenta Qin | 喂给 LLM 的数据 JSON→Markdown,token 降 74–90% | SerpApi 员工;省的大头可能是删字段 |
| Jacky Lin | 工作流七步:Trigger/Context/AI Assist/Human Review/Output/Measure/Improve | 纯框架,无结果数据 |
| JP Zhang | 九步战略:定位句模板、负向 ICP、快渠道验证慢渠道守住、KPI 和预警触发事先定 | 纯框架,"with AI" 部分只在现场演示 |

## 三条交叉主线

1. **AI 引用的主要是第三方,不是你自己的站。** Sacha(84% earned media)和 Tanya(别人的 Best X 榜单、YouTube、Reddit)从两个方向讲同一件事。我们的 v2 已写"被提及 > 被链接",但实际渠道几乎只有自家页面 + 自建 awesome 合集。缺口:别人的榜单、Reddit、媒体报道。
2. **非商品化内容 = 投入。** Tanya 的"Expert with AI 抬高天花板,Thoughtless AI 会拖垮整个域名"和 Google 10-05 更新的 Effort 支柱是同一个意思。我们 31 个场景页共用的模板段落正是"商品化"内容;独有的是安全评级数据和扫描器评测。
3. **流水线要有 Measure/Improve 和事先定好的退出条件。** Jacky 的后两步 + JP 的 Step 9。雷达有复盘,但复盘结果没回写阈值;场景页没有预设的降级条件。

## 落到项目上(按性价比排)

### agentskillshub.top
1. **场景页首屏加一句断言式结论(BLUF)**:如 "The best PPT skill for Claude Code is X (grade A, N★)"。生成器改一处,31 页同时生效。可以跟 P0/P1 一起做。
2. **把安全评级做成一篇"实测方法"文章**:同一批 README、同一套规则,结果对照表 + 作者 + Last updated。素材现成(扫描器二审评测:44.5% 是"引用"不是"行为",AUC 0.916)。这是我们最难被复制的内容,直接回应 Effort/Originality。
3. **查 ChatGPT 对我们主力词引了谁**:问 "best ppt skills for claude" 等,点 Sources,得到要去争取上榜的名单(Tanya P19–22)。手动,10 分钟。
4. **关 JavaScript 看 SPA 路由**:首页、/compare/、/analyzer/、/org-audit/ 是客户端渲染,AI 爬虫可能只看到空壳。场景页和 skill 页已预渲染,不受影响。
5. **反应式 PR(安全事件)**:出现恶意 skill/MCP 新闻时,用库里数据给角度("同类模式出现在 N 个仓库"),三行邮件只发正在写的记者。新闻频率低,适合做成雷达里一个"新闻"来源 + 人工发,不值得搭 7 个 skill。
6. Reddit(r/ClaudeAI、r/mcp)目前是空的;要做必须是真人参与,不能自动发。

### jasonzhu.ai
- video-to-live-photo 文章开头加一句断言式结论;配套写一篇 "Best video to Live Photo apps" 比较页并互链。
- 想拿 ChatGPT 流量,先确保 Google 收录(Ahrefs:88% ChatGPT 引用来自搜索索引)。
- GA 单独盯 chatgpt.com/referral 和 (not set)。

### 新词雷达
- 借 Sacha 的 pick-story 规则做二级筛选:只读标题摘要、同事件合并、0 条也可以、输出"剩余小时数 + 3–5 个搜索词"。
- 复盘结果回写阈值(Jacky 的 Improve):现在 review 只出结论,没调 VELOCITY_MIN/DELTA_MIN。
- 每个词建页前写下进场/退场阈值(如热度跌到峰值 20% 停止投入),对上"浪潮词寿命 ≈2.5 周"。

### 不建议照做
- **自写把自己排第一的榜单 / "X alternative" 品牌词页**:Tanya 的案例有效,但和信任层人设冲突,且有被降权风险,演讲没提。
- **JSON→Markdown 全面改造**:Jev 按次计费不省钱;只对 GPT/FlatRouter 输入有意义,先 A/B。
- **采信无出处的数字**:34%/45%/43.8%/44.2%/0.70/458 天 等别写进文章或 playbook。
