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

## 验收方法(任何"平台页拿链"玩法通用,先验后动手)

```bash
curl -sL <平台页URL> | grep -oE '<a[^>]*href="https?://[^"]*"[^>]*>' | grep 你的域名
```
看三样:
- **有没有链**(不是 JS 跳转/base64 跳转——那种不传权重,如 feizhuke 的 /go/)
- **rel 属性**:含 `nofollow` / `ugc` / `sponsored` 任一 = 不传 DR(Ahrefs DR 只算 dofollow)
- **指向对不对**(共用账户最易指错站)

## 实测结果(2026-07-24)

```html
<a href="http://www.brickrecipes.ai" rel="ugc nofollow" class="button button--jumbo">
```

- 回链 **`rel="ugc nofollow"`** → DR 提权前提不成立,"直接到 DR30"不会发生
- 早年该页确实干净 dofollow(SEO 圈攻略的由来),被薅多后 Stripe 加了反滥用标记——**所有二手攻略先验时效**
- 初始指向 brickrecipes.ai(账户公开网站字段),验证了共用账户指错站的坑

## 处置与残值

- 0.5% 捐款保留(成本≈0,想停 dashboard 随时 pause,无违约)
- 专属页保留(若 Stripe 未来撤销 nofollow 可捡回)
- 首页**不挂**徽章(SEO 为零,不占首屏位)
- 已入 [backlink-todo.md](../backlink-todo.md) §注意(别踩坑) 首条

## 一句话给社群

> Stripe Climate 页的商家回链现在是 `rel="ugc nofollow"`,Ahrefs DR 不计入,"捐赠页快速提 DR"已失效——curl 一下页面源码即可自验。
