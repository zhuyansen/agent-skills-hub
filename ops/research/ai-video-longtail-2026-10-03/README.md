# AI 视频方向长尾词(2026-10-03)

方法:沿用新词雷达的信号找种子,再用关键词工具扩词、用 Trends 验证。
1. **种子**:toolify 48.5 万个工具名里带 video 的 4,460 个(雷达 ③ 的快照)提炼出需求短语;② 爆发仓库、① 推文里的视频相关名字(Opus 5.5 做视频、Muse、Seedance、Happy Horse)。最后选了 12 个:ai video generator、image to video、photo to video、kissing video、hug video、ai dance video、face swap video、music video generator、seedance、happy horse ai、veo 3、talking photo。
2. **扩词**:DataForSEO Labs keyword suggestions(美国、英文),每个种子 300–1000 个,共 4,675 个不重复的词,带月搜索量、KD、意图和近 12 个月逐月数据。`suggestions.json.gz`
3. **筛长尾**:≥3 个词、月搜 ≥50、KD ≤30,剩 1,713 个,按近 3 个月和之前 9 个月的比值分成新冒头 / 上涨 / 平稳 / 衰退。供给 = toolify 里工具名带这个词核心词的工具数。`analyze.py` → `keywords.csv`
4. **验证**:月度数据只到 8–9 月,挑 15 个用 Trends 看最近 90 天(按 7/8/9 月分段的相对热度)。`trends_90d.json`

花费:AIsa $0.75(扩词 12 次 $0.73,Trends 17 次 $0.02)。

## 结论

**1. 最值得做:视频转实况照片(video to live photo)。** 不是"AI 视频"本身,是相邻的工具需求,但量大、难度低、几乎没人做:

| 词 | 月搜 | KD | 近 3 月 / 前 9 月 | toolify 供给 | Trends 7→8→9 月 |
|---|---|---|---|---|---|
| how to turn a video into a live photo | 6,600 | 2 | ×2.3 | 0 | 0 → 3.1 → 3.3 |
| how to make a video a live photo | 8,100 | 10 | ×2.2 | 0 | |
| video to live photo | 5,400 | 17 | ×1.9 | 0 | 11.2 → 7.4 → 15.1(峰值 9/25) |
| video to live photo converter | 1,600 | 5 | ×1.7 | 0 | 6.1 → 1.0 → 7.9 |
| video to live photo app | 1,300 | 9 | ×4.0(一年 +5,043%) | 0 | |

同一个需求有十几种问法,合计月搜 6 万以上。how-to 问法 = 先写博客;converter / app = 工具页。完整符合万兴的路径。

**2. 模型名长尾:热 2–4 周就没了,只配博客内页,不配新站。**
- `seedance 2.0 pricing`(月搜 90,KD 2,Trends 1.3 → 2.1 → 4.3,峰值 9/29,还在涨)、`cheapest seedance 2`(KD 0,一直在高位)、`seedance 2.0 free`(9,900 / KD 12,开始回落)、`fal ai seedance 2.0 api`(KD 5)。
- `veo 3 free` 9 月又起来了(峰值 9/22)。
- 已经过气:`happy horse ai`(7 月峰值后一路跌)、`wan 2.7 image to video`、`ltx 2.3`(都是发布当月冲高,下个月归零)。

**3. 情感/换脸类:老需求,长期有量。**
- `ai kiss video generator free`:月度数据一年跌了 77%,但 Trends 7 → 9 月从 3 涨到 14(峰值 9/7),**又回暖了**。`video of kissing` 月搜 12,100、KD 0。
- `face swap video` 一族:月搜 1.5 万但一年跌 45%;Trends 9 月略回升。供给 41 个工具,拥挤。
- `ai hug video`:风已经过去(一年 -82%,Trends 9 月归零)。

**4. 不做:** 带别家品牌的词(canva image to video、higgsfield、kling ai video generator、magic hour face swap、capcut…)是导航型,用户要去那个网站;head 词(image to video 2.7 万、KD 28,供给 372)太挤。

## 按万兴的路径走(写进 gefei-seo-playbook.md §3)

新词 → **博客内页**(最快,不写代码)→ 博客在 GSC 拿到曝光和点击 → **工具落地页** + 回改博客、加内链导流 → 工具页拿到排名、有出单 → **新站**。

| 词组 | 现在走到 | 下一步 |
|---|---|---|
| video to live photo | 博客 | 写 how-to 博客(覆盖十几种问法);2 周内 GSC 有曝光就做 converter 工具页 |
| seedance 2.0 pricing / cheapest / free / api | 博客 | 一篇"Seedance 2.0 价格与最便宜的用法"对比文,模型热度过了就停,不建站 |
| ai kiss video | 观察 | 进雷达复盘,看回暖能不能持续两周 |
| veo 3 free | 观察 | 同上 |

这些词都已经写进 `radar_leads`(信号记为 `watch`),10/17 由雷达自动复盘 Trends,看发现之后有没有继续涨。

## 附:intoLive 的 App Store 评论(2026-10-03)

博客方法 2 的补充。Apple 公开评论 RSS(免费、无需 key),七个区(us/gb/ca/au/jp/cn/tw)共 2,056 条文字评论,`intolive-reviews.json.gz`。美区 RSS 只给了 100 条,日本、中国大陆各拉满 500。
2024 年以来 740 条,1–2 星 386 条(总评分 4.6 / 11.4 万个评分,写评论的人偏向吐槽)。差评主题:导出慢、失败或闪退 18%、广告 13%、导出的不被识别为实况或设不了壁纸 8%、试用到期自动扣费 7%、买断后又要订阅 6%、水印 5%、片段只有 1–2 秒或被加速 5%;中国区另有 17 条反映 App 内登录或广告诱导输入短信验证码,实际开通运营商话费包月。
对做 converter 工具页的启发:用户最在意的是"不扣费、不带水印、导出就能当壁纸"。这三点是差异化卖点。
