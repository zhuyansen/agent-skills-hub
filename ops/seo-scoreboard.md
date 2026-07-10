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

## 在途验收窗口(到期就查,查完移进上表备注)

- **2026-07-11(周五)**:Ahrefs Site Audit 首爬报告(断链/孤儿页/canonical/零入链四类)
- **2026-07-13(周一)**:5 个 awesome PR 状态(`gh pr list`);Bing 引用域 32 → ?(本周口径 50+)
- **2026-07-24 前后(2 周)**:libhunt/skillget/navi/mdskills/aitoolnet/creati 9 链 在 Bing/Ahrefs 报表现身?SKILL.md 三站爬到没?
- **2026-08-10**:DR 6 → ?;AI responses 0 → ?(arXiv 若上线,重点看)

## 指标口径(防止将来自己骗自己)

- **GSC clicks/曝光**:site 全域、周窗口(周一至周日),`fetch_gsc.py queries` 汇总
- **品牌词 pos**:"agent skills hub" 精确词,`fetch_gsc.py brand`
- **Bing 优质引用域**:Bing Webmaster Backlinks 面板的 referring domains 数(比 Ahrefs 严,当质量口径)
- **GEO AI 会话**:GA sources 匹配 AI_SRC 元组(chatgpt/openai/perplexity/doubao/gemini/copilot/claude/kimi/deepseek),28 天窗口
- **转化事件**:deep_audit_checkout · enterprise_cta_click · install_command_copied · newsletter_subscribe 四件的周计数
- **死点击**:Clarity dead-click 会话占比,28 天窗口
