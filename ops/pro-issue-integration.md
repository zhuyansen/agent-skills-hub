# jasonzhu.ai → Agent Skills Hub 自动发码对接

> jasonzhu.ai/club 付款成功后,调一个 RPC 就能自动发 Pro 激活码。本文档是 jasonzhu.ai 那侧的对接契约。
> 对应迁移:`supabase/migrations/019_issue_pro_key_rpc.sql`。凭证在本仓库 `.env.local`(gitignore),复制进 Vercel。

## 一、Vercel 环境变量(jasonzhu.ai 项目 · Production)

| Key | 从哪拿 |
|---|---|
| `AGENTSKILLSHUB_SUPABASE_URL` | `https://vknzzecmzsfmohglpfgm.supabase.co` |
| `AGENTSKILLSHUB_ANON_KEY` | 本仓库 `.env.local`(eyJhbGci… 开头,公开 anon key) |
| `AGENTSKILLSHUB_ISSUE_SECRET` | 本仓库 `.env.local`(ashjw_ 开头,**发码密钥,绝不进前端/git**) |
| `RESEND_API_KEY` | 本仓库 `.env.local`(re_ 开头,发欢迎邮件用) |

## 二、发码接口(付款成功回调里调一次)

```
POST {AGENTSKILLSHUB_SUPABASE_URL}/rest/v1/rpc/issue_pro_key
Headers:
  apikey: {AGENTSKILLSHUB_ANON_KEY}
  Authorization: Bearer {AGENTSKILLSHUB_ANON_KEY}
  Content-Type: application/json
Body:
  {
    "p_secret":  "{AGENTSKILLSHUB_ISSUE_SECRET}",
    "p_email":   "买家邮箱",
    "p_note":    "早鸟199",          // 或 "标准365"
    "p_order_id": "你的订单号(唯一,用于幂等)"
  }
```

**Node 示例(jasonzhu.ai 的 webhook handler):**
```js
const res = await fetch(`${process.env.AGENTSKILLSHUB_SUPABASE_URL}/rest/v1/rpc/issue_pro_key`, {
  method: "POST",
  headers: {
    apikey: process.env.AGENTSKILLSHUB_ANON_KEY,
    authorization: `Bearer ${process.env.AGENTSKILLSHUB_ANON_KEY}`,
    "content-type": "application/json",
  },
  body: JSON.stringify({
    p_secret: process.env.AGENTSKILLSHUB_ISSUE_SECRET,
    p_email: buyerEmail,
    p_note: isEarlyBird ? "早鸟199" : "标准365",
    p_order_id: orderId,
  }),
});
const out = await res.json();
// out.status: "issued" | "already_issued"
// out.key:    "ash_pro_xxx"(仅 issued 时有,只此一次!)
// out.downgraded_to_standard: true 表示早鸟满 100 已降为标准价 —— 据此调价/提示
if (out.status === "issued") {
  await sendWelcomeEmail(buyerEmail, out.key);   // Resend 发欢迎邮件,带 key
}
// already_issued:webhook 重试,别再发邮件
```

## 三、返回值

| status | 含义 | 你要做的 |
|---|---|---|
| `issued` | 首次发码成功,`key` 字段是明文激活码(**只此一次返回**) | 存/发欢迎邮件;若 `downgraded_to_standard=true` 说明早鸟已满、实际按标准价发,据此对账 |
| `already_issued` | 同 `p_order_id` 已发过(webhook 重试) | **别重复发邮件**,已经发过了 |

错误(HTTP 4xx,body 含 code):`42501` 密钥错;`22023` 邮箱格式错。

## 四、欢迎邮件应包含两样(一份入会 = 两处交付)

1. **Agent Skills Hub 激活码**:`out.key` → 引导去 agentskillshub.top/pro/ 粘贴即用
2. **三个私有 club skill**:gosail-club GitHub org 邀请 / 私有仓库授权(这步 jasonzhu.ai 侧另做)

## 五、安全 & 运维

- **发码密钥 = 钱**:只在 jasonzhu.ai 服务端环境变量里,绝不出现在前端 bundle / 公开仓库 / 客户端请求。
- **泄露轮换**:生成新密钥 → 算 sha256 → 替换迁移 019 的 `v_expected_secret_hash` → 重跑该文件 → 更新 Vercel 变量。已发出的 key 不受影响。
- **早鸟名额**:服务端强制 100 个,满了自动降标准价并回报,不用你在 jasonzhu.ai 侧数。
- **幂等**:务必传 `p_order_id`(用你的订单号),否则 webhook 重试会重复发码。
- **对账**:`SELECT count(*), note FROM member_keys WHERE source='jasonzhu.ai' GROUP BY note` 看自动发了多少早鸟/标准。
