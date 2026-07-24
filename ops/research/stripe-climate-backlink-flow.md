# Stripe Climate 捐赠页外链 · 操作流程与实测结论(2026-07-24)

> 来源:niko 会议(陈荣涛)"开 Stripe 捐赠页拿 DR90 外链 → DR 快速到 30"。
> 实测结论:**玩法已死**(回链被 Stripe 加了 `rel="ugc nofollow"`),流程留档防重蹈 + 供社群纠偏。

## 完整操作流程(15 分钟)

1. **入口**:Stripe Dashboard → Climate → 「承诺 / Commitment」tab
   直达:`https://dashboard.stripe.com/climate/commitment`
2. **设置捐款**:选捐款比例(最低 0.5% 即可)→ 确认。费用 = Stripe 收款流水 × 比例,小站一年几块钱。
3. **发布专属页**:承诺生效后,同页出现「Custom webpage → Set up」→ 自定义(logo 可跳过)→ Publish
   → 生成专属 URL:`climate.stripe.com/<随机串>`(本次:gx406l)。裸域 climate.stripe.com = 还没发布。
4. **回链指向**:专属页上的"访问网站"按钮读取 **账户级「公开业务信息 → Website」字段**
   (`dashboard.stripe.com/settings/public`)。
   ⚠️ 多产品共用一个 Stripe 账户时只有一个身份——该字段**同时印在所有收据/账单上**,为外链改它会污染其他产品的收据品牌。
   ⚠️ 改完有缓存,页面几小时内才刷新;Custom webpage 编辑器内可能有独立字段,以编辑器为准。

## 验收方法(任何"平台页/客座文/目录页拿链"通用,先验后动手)

### 层 1 · 页面级:链在不在、rel 干不干净(发链当天就能验)

**A. 浏览器 Console 一行式**(首选:过 JS 渲染 + 登录墙,客座 5 连就是这么验的)——打开目标页按 F12,Console 粘贴:

```js
[...document.querySelectorAll('a[href*="agentskillshub"]')].map(a=>({href:a.href,rel:a.rel||'✅dofollow'}))
```

- 返回 `[]` = 页面根本没链到你(或走 JS/base64 跳转,如 feizhuke 的 `/go/`——不传权重)
- `rel` 含 `nofollow`/`ugc`/`sponsored` 任一 = 不传 DR;`noopener`/`noreferrer`/`external`/`follow` 均无害
- 顺带核对 href 指向对不对(共用账户最易指错站)

**B. curl 原始 HTML**(交叉验证:爬虫第一眼看到的是这个,能揪出"只有 JS 渲染才出现"的弱链):

```bash
curl -sL <平台页URL> | grep -oE '<a[^>]*href="https?://[^"]*"[^>]*>' | grep 你的域名
```

**C. AITDK 扩展**(可视化替代:装 aitdk.com 浏览器扩展,开目标页看 Links 面板,外链列表带 follow/nofollow 标注,适合不想开 Console 的场合)

### 层 2 · 索引级:搜索引擎认没认(层 1 干净 ≠ 已入账,要等收录)

| 工具 | 时效 | 看什么 | 备注 |
|---|---|---|---|
| **Ahrefs**(免费站长版,已开通) | 天级,最快 | Site Explorer → Backlinks → 搜来源域名,每条链带 **Follow/NoFollow/UGC 标** | DR 只算 dofollow;新链几天内可见 |
| **Bing Webmaster** | 周级,较勤 | 外链报告 → ref-domains 列表找来源域 | 我们本就每周对 Bing ref-domains 水位 |
| **GSC 链接报告** | **3-6 周批量快照,最慢** | 链接 → 外部链接 → 导出"最新链接"grep 来源域 | ⚠️ 先看报告内最新"上次抓取日期"判断可比性(07-16 踩过:报告停在 06-10,验 7 月新链是徒劳);不显示 rel |

**判定口径:层 1 rel 干净 + 层 2 任一工具收录,才算权重真入账。** 层 1 脏(nofollow/跳转)则层 2 不用等——流量链另算,权重链记零。

## 实测结果(2026-07-24)

```html
<a href="http://www.brickrecipes.ai" rel="ugc nofollow" class="button button--jumbo">
```

- 回链 **`rel="ugc nofollow"`** → DR 提权前提不成立,"直接到 DR30"不会发生
- 早年该页确实干净 dofollow(SEO 圈攻略的由来),被薅多后 Stripe 加了反滥用标记——**所有二手攻略先验时效**
- 初始指向 brickrecipes.ai(账户公开网站字段),验证了共用账户指错站的坑

## 验收记录(层1 页面级,按上方 SOP)

| 时间 | 动作 | 实测(curl 层1) |
|---|---|---|
| 07-24 初验 | 发布公共页 gx406l | 回链 `brickrecipes.ai` + `rel="ugc nofollow"` → 判死 |
| 07-24 改字段后 | 用户改 Business details→Website 为 agentskillshub.top(Stripe 审核 2-3 天) | **未传导**,仍 brickrecipes + ugc nofollow —— 证实公共页网址是发布时快照,不实时联动 |
| 07-24 徽章验 | badge/MOvGBj 原始 HTML | **零外链锚点**(交互走 JS)→ 徽章本身也不构成外链 |
| 待 07-27 | Stripe 审核过后终验一次 | 翻过来就补记一行;没翻就此封存(nofollow 反正不入账) |

站内徽章已上线页脚(commit 024ef70,信任信号定位)。

## 处置与残值

- 0.5% 捐款保留(成本≈0,想停 dashboard 随时 pause,无违约)
- 专属页保留(若 Stripe 未来撤销 nofollow 可捡回)
- 首页**不挂**徽章(SEO 为零,不占首屏位)
- 已入 [backlink-todo.md](../backlink-todo.md) §注意(别踩坑) 首条

## 一句话给社群

> Stripe Climate 页的商家回链现在是 `rel="ugc nofollow"`,Ahrefs DR 不计入,"捐赠页快速提 DR"已失效——curl 一下页面源码即可自验。
