# SEO / GEO 行动编年史(2026-03 → 2026-07)

> 用途:复盘 + 新站抄作业。每条动作标注水系构件(①进水口 ②水库 ③架构 ④内链 ⑤撑子页 ⑥活水 ⑦排水 ⑧回流 ⑨迭代;🌊 = GEO 专项)。
> 配套:[水系模型](seo-watersystem-model.md) · [执行手册](seo-execution-guide.md) · [外链行动板](backlink-todo.md)

## 阶段总览

| 阶段 | 时间 | 主题 | 一句话 |
|---|---|---|---|
| P0 | 03-06 ~ 03-08 | 上线周 | 三天从 0 到上线:域名、sitemap、JSON-LD、newsletter 全套底子 |
| P1 | 03-30 ~ 04月 | 程序化 SEO 铺开 | 撑子页量产 + 排水闸 + E-E-A-T,GSC 体检驱动修复 |
| P2 | 05月 | Trust Layer 转向 | 定位从"目录"转"信任层",博客/企业页/场景页三线扩产 |
| P3 | 06月 | 资产化 + 外链启动 | 117K 安全报告 = 第一个 linkable asset;搜索质量大修;付费目录试水 |
| P4 | 07-03 ~ 07-05 | Trust-Layer 重构上线 | 7,924 audit 页 + $49 收银台 + MCP/npm 分发 + skill.md |
| P5 | 07-04 ~ 07-08 | 数据四件套 + 水系成型 | GSC/GA/Plausible/Clarity 全通,水系模型定稿,盲飞终结 |
| P6 | 07-09 ~ 07-10 | 进水口总攻 | 单日 12+ 开口:学术三连(HF/Kaggle/Zenodo)+ 实体双环 + 外链爆发 |

---

## 2026-03(P0:上线周)

- **03-06** 首 commit:全栈聚合器 + 评分系统上线(③架构 一次定型)
- **03-07** 部署自定义域名 **agentskillshub.top**;动态 sitemap(6,175 URL)+ JSON-LD + meta 全套(⑦排水 Day 1 就做);newsletter 自动化 + 邮箱验证(⑧回流)
- **03-07** IndexNow key 上线(⑦收录加速,一次配好零维护)
- **03-08** OG 图 + Twitter Card;Star Velocity 周快照(⑥活水雏形)
- **03-30~31** 日报自动化 + badge 外联脚本 + RSS/徽章生成器(①外链基建);comparison 页 + Schema markup;Plausible 接入(⑨数据);场景页 41→53

## 2026-04(P1:程序化 SEO 铺开)

- **04-02** P0 SEO 修复:首页预渲染、trust 页、博客骨架
- **04-05** AEO 优化 + 首篇博客(🌊 GEO 意识萌芽)
- **04-06** 代码分割 + OG 压缩 + hreflang
- **04-08** 三层安全体系上线(secret-scan hook + 质量安全维度)——**后来一切"安全分级"资产的地基**
- **04-14~15** GSC 体检驱动的修复潮:安全头/meta/H1/schema;**爬虫预算保卫战**(query 参数屏蔽、sitemap 阈值 30★、砍 noindex 链)(⑦排水第一次大修)
- **04-16** 品牌统一为 **AgentSkillsHub**(②水库:品牌一致性);阈值 30→50★
- **04-20~23** 撑子页扩产(/best/ 场景页 +7)+ **/author/ 聚合页** + 每个 skill 页加 Alternatives 块(④内链);标题截断/H2/meta CTA 三连修
- **04-24** **E-E-A-T 强化**:About 页 + Person schema + 新鲜度信号(②实体)
- **04-26** GA4 接入(⑧回流数据源;埋下"错 property"的坑,7 月才发现)
- **04-28~29** **蓝皮书 12 章挂 /book/**(linkable asset #0)+ PDF 当 newsletter 磁铁;sitemap 收紧修 4,592 个"已发现未收录"(⑦)
- **04-30** /best/ FAQ 从 3 问升 6 问(AEO)

## 2026-05(P2:Trust Layer 转向)

- **05-01~05** /submit/ + /verified-creator/ 商业化页;场景页冲到 75;**CTR 急救**:重写 /best/+首页 title(修 0.1-0.3% CTR——后来才明白是 AI Overviews 吃点击,🌊 GEO 的反面教材)
- **05-07** /arena/ PK 投票页(后砍掉——教训:没有搜索需求的功能页是死水)
- **05-08** P0 视觉重构(dark-first,#5B5FE9)
- **05-10~11** 博客双语化 + 场景页 79
- **05-13** *(库外)* proompteng/bilig 等社区提交开始进 extra_repos——**社区自发投喂开始**
- **05-15~17** **战略转向落地**:/enterprise/ 落地页 + Trust Layer 首页 banner + **转向宣言博文"Directory → Trust Layer"**(EN+zh)(②水库:定位换锚)
- **05-18** extra_repos 社区通道常态化

## 2026-06(P3:资产化 + 外链启动)

- **06-04~14** Supabase 稳定性战役(materialize/keyset/chunked scan——57014 全回滚教训);**ash CLI + CDN 搜索索引**上线,`@agentskillshub/cli` 发 npm(🌊 **GEO:装进终端 = 不走搜索的常驻触点**)
- **06-13** enterprise 双语合并;43% 无源数据换成有源 26.1%(**诚实原则入档**);awesome-list 目标清单首建(①)
- **06-14~16** 安全徽章成 Trust 信号;**中文双语搜索索引**(w 字段)
- **06-17~18** 场景搜索精度大修(权重打分 + 同义词 + 排除词,79→84 场景)
- **06-20** CLI 使用追踪四路方案(GA4/Plausible/CF/npm)
- **06-22** **第一个真正的 linkable asset:《We security-graded 117,854 AI agent skills》数据报告** + 发布 playbook + 安全徽章一键嵌入(①诱饵 + badge 战役基建)
- **06-23** Dev.to 首次寄生投稿(canonical→blog);品牌 title 重排;ppt-presentation 标题重定向(**第一次数据驱动改标题**);sitemap-blog 补漏
- **06-26** **Toolify $99 付费目录**(后验收 ✅ 40 sessions/28d——付费导航站唯一验出回报的);目录/guest-post 分层清单
- **06-27~28** i18n 全站双语;浏览器翻译插件崩溃守卫(**留住中文用户的隐形 SEO**)

## 2026-07 上旬(P4+P5:重构上线 + 数据四件套)

- **07-03** **Trust-Layer 重构日**(单日 15 commit):**/audit/{owner}/{repo}/ 7,924 页**上线("is X safe" 护城河,⑤撑子页最大一波)· 评分 ×1.42 重标定 · $49 深度审计入口 · **`@agentskillshub/mcp` 发 npm** + **/skill.md agent 引导页**(🌊 GEO 三件套)· /organization/ 创作者页 · canonical 统一 + lint 清零
- **07-04** **数据四件套打通**:GA MCP + Plausible 建站 + Clarity 接入(死点击 14.2% 基线);**GSC API 接通**(`fetch_gsc.py` 五子命令);browser-automation 标题数据驱动重定向;作者页静态化(热路径零 DB)
- **07-05** /category/ 静态壳手写文案;per-category SEO 文案 + agent 安装 tab
- **07-06** **哥飞方法论学习日**:会议内容逐篇读 → `gefei-seo-playbook.md`;**GSC 实证:ppt 曝光 4230 断层第一** → /best/ppt-skills/ 数据驱动建页;撞车 ppt-presentation → **合并**(自相竞争教训);obsidian/ai-video 场景页;**arXiv 大纲 + HF 数据集导出(130,173 行)**;品牌词 GSC 监控;四工具交叉验证法入档
- **07-07** **水系模型 v1/v2 成稿**;**内链通水日**:7,924 audit 孤儿页接回主路 + skill→audit + skill→/best/ 三段管(④);**转化事件埋点**(gtag 四件,⑧盲飞终结);**GitHub Actions 云端日扫**(⑨);HF 数据集入 sameAs;arXiv Related Work + endorser 锁定 Lunghi
- **07-08** **收银台日**:$49 Stripe Payment Link 三连(URL builder + CTA 事件 + 上线)💰;**水系模型 v3 定稿**(十构件单表,封笔);**llms.txt 上线**(🌊);**/daily/ 活水页**(日报存档 → 网页,⑥);arXiv LaTeX 编译就绪(数字刷新);digest 邮件化;/enterprise 卡片死点击修复;dingyi 设计清单补录 4 个目录缺口

## 2026-07-09 ~ 07-10(P6:进水口总攻)

- **07-09** /daily/ 获首页双入口(header "Daily" + NewThisWeek 链);日报断流 8 天后复通(**"管道建好≠水会流"教训**);digest 邮件 lang=zh;中文同义词 epoch 2
- **07-10 上午** cron 提前到 00:20 UTC(送达先于习惯);**GEO 水位进日报**(AI 引荐会话表,🌊);**首页 title↔文案定位对齐**(security-graded 贯穿两层 meta)+ 全站数字统一 130,000+;**Bing Webmaster 开通**(XML 验证)→ **竞品外链侦察**(LobeHub 490 域 vs 我们 32;github.com 450 条 = badge 战役靶心);**Kaggle 数据集镜像**(-u 公开教训);creati.ai $79/9 链;**Ahrefs WT 开通 → DR 6 基线**(权威病量化);工具清单 A1-F5 + 执行手册(15 避坑)
- **07-10 下午(单日 12+ 开口)**:
  - ①学术三连:**Zenodo DOI**(10.5281/zenodo.21292799)+ HF 卡片回填 + **Kaggle 分析 notebook**(🌊 3 回链)
  - ②实体双环:**Wikidata Q140478987**(P31/P856/P571 全绿)↔ 站点 sameAs 双向确认上线;**AlternativeTo** 收录
  - ①Awesome PR:新提 travisvn #965 + BehiSecc #445,刷新 punkpeye #9142 + Composio #747(数字保鲜);wong2/hesreallyhim 判死/暂缓
  - ①Tier 1 清点 17 站:**LibHunt 秒收录**;deepwiki 白得;**SKILL.md 挂进 MCP 仓喂 3 个被动爬取站**(🌊);skillget/navi/mdskills 人工提交;aitoolnet $9.9;8 站划掉
  - ①内容:**Dev.to 教程文发布**(how to vet an MCP server,2 dofollow)
  - 社区闭环:4 个 GitHub issue 处理(2 收录 + tweetclaw 纠错 + bilig 已收录说明)——**外人开始给我们报数据质量问题 = 信任层定位起效**
  - Site Audit 首爬排定(5,000 页采样,周五报告)

---

## 里程碑水位(记账用)

| 日期 | 指标 | 值 |
|---|---|---|
| 03-08 | 上线 | 0 流量起步 |
| 04-16 | 收录规模 | 55K skills |
| 06-22 | 报告资产 | 117,854 graded 报告发布 |
| 07-04 | GSC 周 clicks | +124%(修复验证生效) |
| 07-04 | Clarity 死点击 | 14.2% 基线 → 07-08 修复后 10.57% |
| 07-06 | 目录规模 | 130,173(数据集导出口径) |
| 07-08 | GEO 引荐 | 40 会话/28d(ChatGPT 28 + 豆包 12)🌊 |
| 07-10 | 权威基线 | **DR 6 · 引用域 313(Ahrefs)/ 32(Bing 优质)· 品牌词 pos 11 · Ahrefs AI responses 0** |
| 07-10 | 付费台账 | $275.9(Toolify 唯一验出回报) |

## 教训时间轴(何时踩的坑 → 何时立的规矩)

- 04-26 GA 接错 property → **07-04 才发现**(盲飞 10 周教训:数据先行)
- 05-02 CTR 恐慌改标题 → 07 月才懂是单页错配 + AI Overviews(先按页/词切分再动手)
- 05-07 /arena/ 上线 → 06-13 砍掉(没有搜索需求的功能页 = 死水)
- 06-13 43% 无源数据下架(诚实原则:每个数字可溯源)
- 06-14 scan_all 单事务超时全回滚 → 分块提交铁律
- 07-06 ppt-skills 撞 ppt-presentation → 建页前三查(目录/slug/Plausible)
- 07-09 /daily/ 上游断流 8 天 → 活水必须配自动化,建完当天就定
