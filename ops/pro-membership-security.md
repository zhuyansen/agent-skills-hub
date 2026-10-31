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

### 会员欢迎信模板(三种用法 —— 发信时把 `ash_pro_你的key` 替换成该会员的真 key)

> ⚠️ **安全红线**:真 key 只出现在**发给单个会员的这封信**里。公开页 `/pro/`、git、社媒、文档一律用占位符 `ash_pro_你的key`。真 key 进公开面 = 付费墙当场失效(任何人复制即白嫖),必须 `--revoke` 重发。

```
欢迎加入 Agent Skills Hub Pro 🎉 你的会员 Key:
ash_pro_你的key   ← 换成真 key

三种用法(不用注册、不用登录):

① 网页端:打开 https://agentskillshub.top/pro/,把 Key 粘进输入框,即刻解锁全库深度搜索、社区精选榜、Top3 解读。

② CLI:
ASH_PRO_KEY=ash_pro_你的key npx @agentskillshub/cli search "关键词"

③ MCP(Claude Code):
claude mcp add agentskillshub -e ASH_PRO_KEY=ash_pro_你的key -- npx -y @agentskillshub/mcp
配好后 agent 会自动用 pro_search 工具做全库深度检索。

Key 是你的会员凭证,请勿公开分享。到期续费同价(锁定入会价)。
```

> `/pro/` 页内也内置了这份"三种用法"折叠说明(`ProPage.tsx` 的 `UsageHelp`),同样用占位符 —— 会员登录粘 Key 后照着换即可。

## 权益表(对外口径,jasonzhu.ai/club 用)

| 能力 | 免费 | Pro(前 100 名 ¥199/年,后 ¥365/年,续费锁价) |
|---|---|---|
| 名称/作者/描述/tag 搜索 + 组合筛选 | ✅ | ✅ |
| **README 深度全文检索**(13 万仓库正文命中) | ❌ | ✅ |
| 单页条数 | 20 | **200** |
| **结果导出 CSV / JSON** | ❌ | ✅ |
| **API 调用**(脚本/自动化,curl 即用) | ❌ | ✅ |

## 免费试用改为服务端限额(迁移 034,2026-10-31)

- 之前:`/pro/` 把一把共享会员 key(`VITE_TRIAL_PRO_KEY`)打进公开 JS,"免费 3 次"只记在 localStorage,`pro_search` 不计次。读得到 bundle 的人可以拿这把 key 无限调用 `pro_search`(每次最多 500 条)。
- 现在:没 key 的访客走 `pro_search_trial`(不收 key)。每个 IP 每天 6 次(3 次试用 + 分享奖励 3 次),全站每天 1000 次,每次最多 20 条、不能翻页;超限返回 PT429(HTTP 429,message `trial_exhausted`)。前端试用结果不给导出。
- 新表 `pro_trial_usage`:RLS 开 + 零 policy + REVOKE anon/authenticated,只存 `sha256(ip:日期)` 和计数,不存原始 IP。
- 上线顺序:① SQL Editor 跑 034 ② 推前端 ③ 线上验证试用能搜、同一 IP 第 7 次返回 429 ④ `--revoke` 旧的公共试用 key ⑤ 删掉 GitHub Secret `VITE_TRIAL_PRO_KEY` 和 `frontend/.env` 里那一行。
- 调额度:改 034 里的 `c_per_ip_daily` / `c_global_daily` 常量,`CREATE OR REPLACE` 重跑函数即可。

## 宽泛词搜索超时修复(迁移 035,2026-10-31)

- 原因:`pro_search` / `pro_search_trial` 按 `stars DESC NULLS LAST` 排序,现有 `ix_skills_stars` 是升序,倒着扫只能给出 `NULLS FIRST`,用不上。常见词("mcp" 约 10 万行命中)只能把全部命中行读出来再排序,冷启动 10~14 秒,超过 anon 角色 3 秒的 statement_timeout,返回 500。空查询只按分类/评级筛也是全表排序。
- 修法:两个函数共用 `_pro_search_core`,先用规划器估命中行数:≥ 2,000 行或空查询时允许按 stars 索引倒着走(到 LIMIT 就停);少于 2,000 行沿用 bitmap + 排序。新增 `(category, stars)`、`(security_grade, stars)` 两个索引,带筛选条件时只在该分类/评级里按 stars 走。
- 实测(线上库事务内试跑后回滚):47 个词 × LIMIT 20/200 + 15 种筛选组合,最慢 0.99 秒(含约 0.23 秒网络往返),结果与旧查询一致。
- 权限:两个内部函数 `_pro_search_core`、`_pro_search_match_estimate` 不验 key、不限量,已对 PUBLIC/anon/authenticated REVOKE EXECUTE,只能经由 `pro_search` / `pro_search_trial` 调用。key 校验、试用限额、行数上限、返回列都没变。
- 调参:改 035 里的 `c_index_walk_min`(当前 2,000),`CREATE OR REPLACE` 重跑 `_pro_search_core` 即可。
- 迁移 036:`pro_search`、`pro_search_trial` 两个函数单独把 statement_timeout 设成 8 秒(PostgREST 调用时按函数设置生效,其他 anon 请求仍是 3 秒)。原因是统计信息里没有的中等频率词(估算一律 1,278 行,实际 5k~15k 行)冷启动要 3~6 秒。上线后公开接口复测:22 个冷门词全部 200,'rust' 冷启动 6.3 秒。回退:`ALTER FUNCTION ... RESET statement_timeout`。
- 可选维护:skills 表 19% 死元组、只有 47% 的页是全可见,手动 `VACUUM (ANALYZE) skills;` 会让 bitmap 扫描少读一些堆页。

## 按星数分档检索(迁移 037,2026-10-31)

- 原因:035 按规划器估算二选一,估错时两条路都慢。估算 < 2,000 的词(统计里没有的中频词一律估成 1,278)走"取全部匹配再排序",每个匹配读一页堆:'rust'(实际 10,003 条)LIMIT 200 读 9,993 页,冷启动 3~6 秒。估算 ≥ 2,000 的词按 stars 倒着走、逐行解压 README 的 tsvector(平均压缩后 13 KB,约 6.5 页/行):'resume' 10,500 页、'prompt injection' 10,169 页。带引号的短语 GIN 判断不了词序,每个候选都要解压:'"best practices"' 11.1 秒、'"skill marketplace"' 18.7 秒。
- 修法:新增内部函数 `_pro_search_tier_ids`,按星数分档从高往低找(≥10000、1000–9999、100–999、10–99、3–9、2、1、0),凑够就停。这个函数只允许 bitmap 计划(函数级 `enable_indexscan`/`enable_seqscan` 关掉,不影响调用方),每档是 GIN 和 `ix_skills_stars` 的 BitmapAnd,只读档内的匹配行。库里 53% 的仓库 0 星、约 1% 有 1,000 星以上,所以大多数搜索在前一两档就结束。`_pro_search_core` 只在"不是短语、且估算显示走 1,000 行内就能凑够一页"时才按 stars 走('mcp'、'agent' 这类常见词),其余都走分档。
- 实测(VACUUM (ANALYZE) 之后,在生产事务里装上 037 测完回滚,结果与 035 逐条一致,只有同星数的先后可能不同;页数 = 触碰的缓冲页):'rust' LIMIT 200 从 9,110 页降到 1,174 页(LIMIT 20 降到 181);'prompt injection' 10,169 → 1,309(0.81 → 0.07 秒);'resume' 10,500 → 1,196;'browser automation' 5,824 → 1,460。短语 LIMIT 200:'"best practices"' 7.7 → 0.09 秒(LIMIT 20 时 035 超过 12 秒,037 0.02 秒),'"security audit"' 6.4 → 1.4 秒,'"skill marketplace"' 超过 12 秒 → 4.2 秒。'mcp'、'agent'、'workflow' 等常见词照旧按 stars 走,不变。代价:冷门词多扫几档 GIN('homework' 389 → 1,251 页,0.14 秒),常见短语不再按 stars 走('"agent skill"' LIMIT 200 从 0.02 秒变 0.42 秒)。
- 仍然慢:三个常见词组成、又很少相邻的短语,比如 '"code review agent"',LIMIT 20 约 1.2 秒(035 约 1.0 秒)、LIMIT 200 约 20 秒(035 也一样)。GIN 不存词的位置,只能逐个解压候选,036 的 8 秒超时对它仍然有用。
- 权限:`_pro_search_tier_ids` 不验 key、不限量,已对 PUBLIC/anon/authenticated REVOKE EXECUTE,只在 `_pro_search_core` 里调用。key 校验、试用限额、行数上限、返回列都没变;没有新表、新索引、新 policy。
- 回退:重跑 035 里 `_pro_search_core` 那一段(`CREATE OR REPLACE`)即可;`_pro_search_tier_ids` 留着不用也无害。

## 短语按候选分批检查 + 搜索限时(迁移 038,2026-10-31)

- 原因:037 之后还会超时的只剩"由常见词组成、又很少相邻出现"的带引号短语。GIN 不存词的位置,含全部词的每一行都要解压 README 的 tsvector(约 13 KB)才能确认词序。公开接口实测:'"skill marketplace"' LIMIT 200 冷启动 7.8 秒(036 的上限是 8 秒),'"code review agent"' LIMIT 200 约 20 秒、必失败。
- 修法:① 短语先把词序去掉(`<->` 换成 `&`)在 GIN 里取候选,这一步不解压任何东西;候选按星数从高到低,每次解压 50 个检查词序,凑够就停(新内部函数 `_pro_search_phrase_tier`)。被否定的短语(`-"open source"`)去掉词序会漏行,仍走 037 的做法。② 每次搜索限时 2.5 秒(从这次搜索开始算):到点后不再开新的一档、也不再查下一批候选,直接返回已找到的结果。因为是按星数从高到低找的,返回的就是完整结果的前 N 行,只是更短。
- 实测(生产只读重放新路径,服务端时间;037 能跑完的,结果都与 037 的前 N 行一致):'"code review agent"' LIMIT 20 从 1.2 秒降到 0.45 秒;LIMIT 200 从约 20 秒失败变成 2.6 秒返回 60 行;'"skill marketplace"' LIMIT 200 从 4.2 秒变成 2.5 秒返回 191/200 行(不限时 2.7 秒全部 200 行);其余常见短语 LIMIT 200 都在 0.1~1.3 秒内返回全部 200 行。不带短语的搜索本来就远在时限内,只多了每档前的时间检查。
- 代价:超时的搜索会少给几行,少多少看缓存冷热;换来的是不再在 8 秒处失败。试用搜索能正常返回就会计入每日限额(超时的会把计数一起回滚)。
- 权限:`_pro_search_phrase_tier` 不验 key、不限量,已对 PUBLIC/anon/authenticated REVOKE EXECUTE,只在 `_pro_search_tier_ids` 里调用。`pro_search`、`pro_search_trial`、`_pro_search_core` 都没动;key 校验、试用限额、行数上限、返回列都没变;没有新表、新索引、新 policy。
- 回退:重跑 037 里 `_pro_search_tier_ids` 那一段(`CREATE OR REPLACE`);`_pro_search_phrase_tier` 留着不用也无害。调时限改 038 里的 `c_budget`。

## 试用搜索先查额度、搜完再计数(迁移 040,2026-10-31)

- 原因:`pro_search_trial` 先给计数加 1 再搜索。加 1 用的是 `INSERT ... ON CONFLICT DO UPDATE`,会把这一行锁到整次调用结束;而全站共用一行 `('all', 日期)`,所以每个试用请求在搜索期间都占着这把锁,其他访客的试用请求只能排队。一个慢搜索(038 之后最多约 2.5 秒)就能卡住所有人的试用,同时来一波人就会排队排到 036 的 8 秒超时。
- 修法:搜索前先用普通读查一下是否已到上限(不加锁),到了就直接 429、不搜索;搜索完成后再给本 IP 和全站各加 1,锁只从加 1 那一刻持续到提交,几毫秒。并发时恰好越过上限的请求,加 1 之后还会再检查一次,超了就 429,整次调用(含结果)回滚,和原来一样。
- 实测(本地 Postgres 17 装 034–038,并让每次搜索固定耗时 1 秒):5 个不同 IP 同时试用,修复前依次 1.1/2.1/3.1/4.1/5.1 秒(都在等全站那一行),修复后全部 1.07 秒;20 个同时也都在 1.3 秒内。上限在并发下仍准确:某 IP 已用 5/6 时同时来 3 个 → 1 个成功 2 个 429、计数 6;全站 999/1000 时 3 个新 IP 同时来 → 1 个成功、计数 1000;已到上限的请求 0.05 秒就 429,不会去搜索;同一 IP 连续 8 次 → 6 次成功后 429。
- 权限:只改 `pro_search_trial` 的函数体;签名、返回列、上限(每 IP 每天 6 次、全站每天 1000 次)、429 错误都不变。`CREATE OR REPLACE` 会保留 owner 和 grant,但会替换函数上的 SET 设置,所以 036 的 8 秒 statement_timeout 在 040 里重新写了一遍(上线后已核对 proconfig 里还有它)。没有新表、新索引、新 policy。代价:并发恰好卡在上限时,被拒的那个请求会多跑一次搜索(最多 038 的 2.5 秒)。
- 上线:2026-10-31 12:25 UTC 单事务应用。提交前核对 owner、grant、签名、SECURITY DEFINER 和两项 SET(search_path、statement_timeout=8s)都与 035 版一致,三个内部函数仍不对 anon/authenticated 开放。之后以 anon 身份用文档保留 IP(203.0.113.x)模拟、事务回滚:新 IP 返回 20 行,本 IP 计数 1、全站 +1;已到上限的 IP 直接 429,两个计数都不动。本机走公开接口(当天额度已用完)返回 HTTP 429。
- 回退:重跑 035 里 `pro_search_trial` 那一段,再执行 `ALTER FUNCTION pro_search_trial(text, text, text, int) SET statement_timeout = '8s';`。
