# Pro 会员搜索 — 安全影响说明 + 上线手册

> 对应迁移:`supabase/migrations/017_pro_membership.sql`
> 定价决策(2026-07-11 定稿):**早鸟前 100 名 ¥199/年,之后 ¥365/年;续费同价(锁定入会价)**。key 按年发,到期不自动续。
> 产品红线:**基础搜索永远免费**(SEO/流量命脉);只锁深度:README 全文 · 200 条/页 · 导出 · API(RPC 即 API)。
> 已免费的能力(多词全文、组合筛选)**绝不**重新包装成付费 —— 信任层品牌不吃这个亏。

## ✅ 上线状态(2026-07-11 已激活)

- 迁移 017 已应用生产;假 key→42501、真 key 通过、Python↔PG sha256 哈希一致 全部实测
- 回填完成:**135,044 行 readme_search_vector 全填,0 残留 NULL**,零错误(分块守住 57014 伤疤)
- 深度验证:README 搜 "sandbox escape" = 200 命中 vs 免费层 3 命中(**66× 深度差,付费价值坐实**)
- 修复:pgcrypto digest → 内置 sha256(避开 Supabase extensions schema 陷阱)
- **发首批早鸟命令**:`backend/venv/bin/python ops/issue_member_key.py 真实邮箱 --note 早鸟199`

## RLS / 权限变更审查(Hard Stop 要求)

| 变更 | 内容 | 安全影响 |
|---|---|---|
| 新表 `member_keys` | RLS ENABLE + **零 policy**(deny-all)+ REVOKE anon/authenticated | anon key 读不到任何行;只有 service_role 与 SECURITY DEFINER RPC 可及。**表内只存 sha256 哈希**,库泄露也不暴露可用 key。email 是唯一 PII,同 deny-all 保护 |
| 新 RPC `pro_search` | SECURITY DEFINER + `SET search_path = public` | definer 权限仅用于读 member_keys 校验;返回的仍是 skills(本就公开可读),**没有扩大数据暴露面**。无效 key → 42501,无信息泄露。LIMIT 硬顶 500 防拖库 |
| skills 新列 `readme_search_vector` | 新 tsvector + GIN + 触发器 | 无权限变化;**免费端 `search_vector` 完全不动**,零回归风险 |
| 攻击面结论 | 客户端(含 localStorage 存 key)只是便利层;**唯一强制点在 Postgres** | devtools 绕过前端只会拿到 42501 |

## 上线顺序(分块,勿一把梭)

1. **应用迁移 017**(Supabase SQL Editor 整段跑;DDL 轻,不含大 UPDATE)
2. **回填**(挑低峰、避开 sync 窗口):`python ops/backfill_readme_search_vector.py`(1,500 行/批,逐批 commit,断线自动续,~133K 行预计 20-40 分钟)
3. **验证**:`SELECT pro_search('假key')` 应报 42501;发一把测试 key 后同查应返回行
4. 前端 `/pro/` 页已优雅降级(RPC 不存在/无 key 都显示引导卡),**先发前端不炸**

## 运营流程

- **发 key**:`python ops/issue_member_key.py 会员邮箱 [--note 早鸟199]` → 把 `ash_pro_...` 明文发会员(入会欢迎语),明文不留存
- **撤销**:`python ops/issue_member_key.py --revoke ash_pro_xxx`(泄露/退款场景)
- **API 用法**(就是 RPC,给会员的文档一句话):
  `curl 'https://vknzzecmzsfmohglpfgm.supabase.co/rest/v1/rpc/pro_search' -H 'apikey: <站点公开anon key>' -H 'Content-Type: application/json' -d '{"p_key":"ash_pro_你的key","p_query":"browser automation sandbox"}'`
- key 到期续费 = 重新 issue(旧 key revoke);**续费价 = note 里记录的入会价**(早鸟199 永远 199)。早鸟名额:`SELECT count(*) FROM member_keys WHERE note='早鸟199'` 到 100 停售

## 权益表(对外口径,jasonzhu.ai/club 用)

| 能力 | 免费 | Pro(前 100 名 ¥199/年,后 ¥365/年,续费锁价) |
|---|---|---|
| 名称/作者/描述/tag 搜索 + 组合筛选 | ✅ | ✅ |
| **README 深度全文检索**(13 万仓库正文命中) | ❌ | ✅ |
| 单页条数 | 20 | **200** |
| **结果导出 CSV / JSON** | ❌ | ✅ |
| **API 调用**(脚本/自动化,curl 即用) | ❌ | ✅ |
