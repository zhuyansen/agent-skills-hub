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

## 三、工具必上清单(六类,带说明)

### A. 站长后台(搜索引擎自家:管收录、词、外链)

- **A1 GSC(Google Search Console API)**
  是什么:Google 官方的搜索表现数据源 —— 每个词的曝光/点击/位次。
  我们怎么用:`ops/gsc/fetch_gsc.py`,五个子命令(queries/compare/brand/pages/dump);compare 抓 rising 词 = 新词雷达;brand 盯品牌词位次。
  坑:数据滞后 ~2 天;国内必须走 Clash 代理 + requests 传输(httplib2 不认代理,见避坑 14)。

- **A2 Bing Webmaster**
  是什么:必应站长后台,给两样 Google 不给的东西。
  我们怎么用:①Index Explorer 看"已收录/已提交比"= 排水水位;②Backlinks 免费对比任意竞品外链(lobehub 490 域 vs 我们 32 就是它查的)。
  坑:验证走 XML 文件最稳(GSC 导入不一定弹);数据也有几天滞后。

- **A3 [候选·未实战] Yandex Webmaster**
  触发条件:GSC 里出现稳定俄语流量再上,现在不动。

### B. 行为分析四件套(看用户在站上干什么)

- **B1 GA4**
  是什么:站内行为 + 转化事件的权威数据源,历史最全。
  我们怎么用:`ops/ga/fetch_ga.py`(REST 直连,不依赖 MCP);看热门页/来源/转化事件;GEO 水位(AI 引荐)从它的 sources 里算。
  坑:先确认 gtag 流向哪个 property —— 我们的数据在"新媒体运营"(485523739)里,专属 property 是空的(避坑 4);查询必须带 hostName 过滤。

- **B2 Plausible**
  是什么:轻量隐私友好的真实 PV 统计,近实时。
  我们怎么用:`ops/plausible/fetch_plausible.py`;热门页列表是"建页前查重"的关键一环(靠它抓到 ppt 重复页自相竞争)。
  坑:站点 2026-07-04 才建,此前数据为 0 属正常;数据格式是 {metrics,dimensions} 数组。

- **B3 Clarity**
  是什么:微软免费的死点击/怒点/录屏/热力图。
  我们怎么用:`ops/clarity/fetch_clarity.py`(每日 10 次限额);死点击率是 UX 摩擦主指标(12.15%→10.57% 就是它验证的)。
  坑:API 只到页面级;元素级必须进 dashboard 热力图(无头浏览器+cookie 可进);clarity.ms 必须直连不走代理。

### C. 转化埋点(看钱和意图)

- **C1 gtag 自定义事件**
  是什么:GA4 的转化打点,漏斗可见性的全部来源。
  我们怎么用:`src/lib/analytics.ts` 类型安全封装;起步四件:install_command_copied / audit_run / enterprise_cta_click / newsletter_subscribe,后加 deep_audit_checkout。
  坑:没埋点 = 盲飞(我们盲飞了 10 周);事件要在"确认成功"后触发,别在点击瞬间。

- **C2 Stripe Payment Link**
  是什么:零后端的收银台,本身就是最诚实的计量器。
  我们怎么用:$49 深度审计;client_reference_id 把 repo 附进订单(斜杠要转义成 --);PAYMENT_URL 空则回退 mailto,永不出死按钮。
  坑:mailto 是转化杀手(避坑 7);文案要跟着付费模式换("先交付后付款"≠预付费)。

### D. 自动化/仪式(让数据自己来找你)

- **D1 GitHub Actions cron(云端日扫)**
  是什么:每天 08:30 前四件套全跑一遍 + Resend 邮件进收件箱。
  我们怎么用:`.github/workflows/analytics-daily.yml`;凭证走 Secrets;digest 标题自带转化事件数,扫一眼知道漏斗动没动。
  坑:GitHub schedule 有 0-40 分钟排队延迟,送达时刻要设计在用户习惯之前(避坑 11);邮件带 lang="zh" 防 Gmail 误判。

- **D2 本地 scheduled task**
  是什么:桌面 App 的定时会话(带完整本地环境:venv/凭证/git)。
  我们怎么用:日报每天 08:19(生成→去重→归档→push→X 文案);周复盘每周一 09:09(3 胜 3 忧 + 恰好 1 个实验)。
  坑:App 关着就顺延到下次启动;首次点 Run now 预授权工具,否则每天卡权限弹窗。

- **D3 IndexNow**
  是什么:向 Bing/Yandex 即时推送新 URL 的协议,收录加速。
  我们怎么用:build 链末尾 `submit-indexnow.mjs` 自动提交,零维护。

### E. 发布/进水口 CLI(把资产推出去)

- **E1 hf(HuggingFace)**:数据集进水口一号。`hf auth login` → `repos create --repo-type dataset` → `upload`。坑:组织命名空间要先在网页建,否则 403。
- **E2 kaggle**:数据集镜像。新版是 KGAT_ token 存 `~/.kaggle/access_token`(没有 kaggle.json 了);**创建必须带 `-u` 否则默认私有=零反链价值**;id 用真用户名不是显示名。
- **E3 npm**:CLI/MCP 包 = 常驻分发。坑:国内镜像会毒化 lockfile 和 publish,`--registry` 显式指 npmjs。
- **E4 mcpb**:Smithery 打包(`npx @anthropic-ai/mcpb pack`);manifest 里别带 tools 数组(400)。
- **E5 Overleaf**:arXiv 只收 LaTeX;pdfLaTeX + article 类;裸 `|` 和 `\~{}` 是渲染陷阱。

### F. 体检/侦察(发现问题和机会)

- **F1 AITDK 类 SEO 体检插件**
  是什么:浏览器插件,10 秒读出任意页的 title/desc/keywords 长度与实体。
  我们怎么用:每月扫一遍首页+核心页;它 10 秒暴露了我们仨月没发现的 Helmet 覆盖旧 title(避坑 5)。

- **F2 gh CLI**
  是什么:GitHub 官方 CLI,侦察利器。
  我们怎么用:验刷星(`gh api users/X/repos` 看作者履历:单仓爆星+其余全<20★=嫌疑);查仓库真实星数/规范大小写;搜 awesome 列表。

- **F3 无头浏览器 + Chrome cookie 导入**
  是什么:gstack browse,把你浏览器的登录态借给自动化。
  我们怎么用:进 Clarity 后台抓元素级热力图、抓 X 长文(note_tweet 只有这条路);**必须先 goto 目标域再 import**;OAuth 型登录(Bing/微软账号)借不动,别硬闯验证码。
  纪律:用完 `$B stop`,登录态不留。

- **F4 agent-reach**
  是什么:多平台抓取安装器(X/Reddit/微信/YouTube 等 13 平台)。
  我们怎么用:xreach 抓推文(undici 不认环境变量代理,坑);Jina Reader 兜底任意网页。

- **F5 Ahrefs Webmaster Tools 免费版**
  是什么:第三方外链/站点健康监控(ahrefs.com/webmaster-tools),Bing 之外第二视角,免费版够用。
  我们怎么用:注册→验证域名(GSC 授权最快)→盯两个报表:Backlinks(新增/丢失外链,付费外链验收用)+ Site Audit(技术健康)。
  坑:免费版只能看自己验证的站,竞品外链还得靠 Bing(A2)。

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
