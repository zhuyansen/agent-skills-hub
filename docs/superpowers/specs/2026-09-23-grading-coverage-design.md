# 评级覆盖:README 回填 + 增量扫描 + 诚实的 unknown

日期:2026-09-23 · 状态:待实施 · 范围:B(评级覆盖),A 档先做、B 档后台低速常驻

## 1. 问题

信任层卖的是安全评级,而目录里 199,057 行只有 31,107 行(15.6%)有评级。今天量出来的事实:

- **每一行有 README 的都已评级**(`unknown_with_readme = 0`)。评级覆盖 = README 覆盖,扫描器本身不是瓶颈。
- 168K 个 `unknown` 按星数分布:0★ 110,217 · 1–4★ 49,867 · 5–19★ 5,921 · 20–99★ 1,506 · 100–999★ 423 · ≥1000★ 16。**≥5★ 未评级 7,866 个(其中 155 个已死),1–4★ 49,867 个。**
- 抓 README 的两条路都到不了沉寂仓库:sync 的 Phase 5 只给**这轮搜索看见的**仓库抓(`jobs.py:583-605`,三个选择器 1000/100/400 上限);独立脚本 `backend/readme_backfill.py` 只手动跑过一次(2026-06-13/14,`stars >= 5`),没有接进任何 workflow。
- 没有"抓过没抓过"的标记:404 在 sync 里什么都不写(留 NULL),在脚本里写 `''`,而所有选择器把 `''` 当 NULL,**没有 README 的仓库会被两条路永远重抓**(今天 426 行 `''`)。
- 每次 sync 的 `scan_all` 对**全部**有 README 的行重评(31K 行,极端一次 70 分钟);最近六次 sync 跑了 48–88 分钟,任务上限 120 分钟。覆盖翻倍会撞超时。
- 每次 README 写入触发 `trg_skills_readme_search_vector`(`017_pro_membership.sql:37-55`):对 ≤50K 字符做 `to_tsvector` + GIN 维护。批量写必须限速,且不能和 sync/deploy 重叠(Supabase 单实例脆弱;6 月的回填曾在和建索引并发时 504)。
- 前端把三种状态混成一个灰色 UNAUDITED:"没抓过"、"GitHub 上没有 README"、真正扫描过。分析器对**空 README 给 SAFE**(`AnalyzerPage.tsx:236-239` + `securityScanner.ts:494-506`)——这是假阴性。徽章 alt 文本写 "Security-graded" 而 SVG 画的是 UNAUDITED(≥5★ 的 7,866 个仓库都会拿到)。分类页/作者页文案 "each … security-graded" 与 15.6% 的现实不符。

## 2. 目标与非目标

**目标(验收指标):**

1. ≥5★ 且未死的仓库,`unknown` 从 7,711 降到 **≤ 50**(剩余应全是 GitHub 上确实没有 README 的),3 天内。
2. 1–4★ 仓库由同一任务低速续补,约 2 周内从 49,867 降到只剩"确无 README"。
3. **sync 时长在整个过程中 ≤ 90 分钟**(增量扫描生效的证据)。
4. 每个 `unknown` 在所有界面上分为两种可区分的状态:「尚未抓取」/「GitHub 上无 README,无法评级」;分析器对空 README 不再返回 SAFE。
5. 没有任何一次回填运行与 sync 或 deploy 重叠;GitHub 核心配额在 sync 开始时剩余 ≥ 1,500。

**非目标:**

- 0★ 的 111K 仓库不抓(没人看的页面不花配额;它们仍是「尚未抓取」)。
- 不引入 LLM 评级(`llm_security_analyzer.py` 无上限、失败写成 caution,另案处理)。
- 不重构 `jobs.py`/`routes.py` 的大文件,不改扫描规则本身。
- 不改 `/audit/` 页的收录门槛。

## 3. 方案比较

| | 方案 | 优点 | 代价 | 结论 |
|---|---|---|---|---|
| 1 | **独立的定时回填 workflow**,复用 `readme_backfill.py`,错开 sync 时段 | 沉寂仓库也能到;不占 sync 的 120 分钟;可随时关掉;分批可控 | 要接 workflow、要加"抓过"标记、要和 sync 共享配额 | **采用** |
| 2 | 扩大 sync Phase 5,去掉"本轮看见"的限制 | 改动集中在一处 | sync 已 48–88 分钟;每轮多几百次抓取 + 更大的 scan_all,直接撞超时;失败时整轮 sync 一起失败 | 否 |
| 3 | 搭在 `refresh-stale.yml` 上(它每天 3 次访问 ≥20★ 的沉寂仓库) | 零新任务 | 只到 ≥20★(1,945),到不了 5–19★(5,921);用的是 Actions 自带令牌(1,000/小时) | 否,但它的调度形状(3 次/天、错峰)被方案 1 借用 |

方案 1 有两个**前置**,地图里量出来的,不做就会在 B 档出事:抓取标记(否则 404 仓库永远重抓,配额白烧)和增量 `scan_all`(否则 sync 超时)。

## 4. 设计

### 4.1 数据模型(一次增量迁移,只加列)

`supabase/migrations/024_readme_fetch_marker.sql`:

```sql
ALTER TABLE skills
  ADD COLUMN IF NOT EXISTS readme_fetched_at    TIMESTAMPTZ,   -- 上次抓取尝试得到明确结果的时间
  ADD COLUMN IF NOT EXISTS security_scanned_at  TIMESTAMPTZ,   -- 上次评级写入时间
  ADD COLUMN IF NOT EXISTS scanner_version      TEXT;          -- 评级时的规则指纹
CREATE INDEX IF NOT EXISTS idx_skills_readme_todo ON skills (stars DESC)
  WHERE security_grade = 'unknown' AND repo_status <> 'gone';
```

语义(所有读写方共同遵守):

- `readme_content IS NULL AND readme_fetched_at IS NULL` → **尚未抓取**。
- `readme_content = '' AND readme_fetched_at IS NOT NULL` → **GitHub 上无 README**(404 或空文件);30 天后可重试一次。
- 200 → 写内容(≤50,000 字符)+ `readme_fetched_at = now()`。
- 网络错误/限流 → 什么都不写(下次再来)。
- 现有 426 行 `''` 在迁移里补 `readme_fetched_at = now()`(它们是 6 月回填的 404,已知无 README)。

RLS 不改;新列走现有的 `skills_public_read`(前端要读 `readme_fetched_at` 来区分两种状态)。安全影响:无,列里没有敏感数据。

### 4.2 回填任务(方案 1 的主体)

**`.github/workflows/readme-backfill.yml`**

- cron:`0 3,11,19 * * *`(sync 在 0/8/16 UTC 起跑、最长 2 小时,deploy 紧随;3/11/19 是它们之间最空的点)。
- `concurrency: { group: github-writers, cancel-in-progress: false }`,**sync.yml 加同一个 group**——两者串行,回填遇到正在跑的 sync 就等,永不重叠(这同时满足"DB 重活串行"的约定)。
- 用 `secrets.GH_TOKEN`(和 sync 同一个 PAT,5,000/小时),不用 Actions 自带令牌(1,000/小时)。
- `timeout-minutes: 45`,失败不重试(下一个时段自然续)。

**`backend/readme_backfill.py` 改造**(保留 1 req/s 全局节拍、4 线程、每行 autocommit;去掉过期的 docstring):

- 选择集:`security_grade = 'unknown' AND repo_status <> 'gone' AND stars >= :floor AND (readme_content IS NULL OR (readme_content = '' AND readme_fetched_at < now() - interval '30 days')) ORDER BY stars DESC LIMIT :cap`。
- `--floor`:默认 **5**(A 档);当 `floor=5` 的候选数 < 50 且传了 `--allow-floor-drop` 时,**同一次运行自动降到 1**(B 档接上),日志打印切换。该开关在增量扫描(§4.4)上线后才加进 workflow。0★ 永不进入。
- `--cap`:每次运行 **1,500**(≈ 25 分钟)。三次/天 = 4,500/天:A 档 7,711 个 ≈ 2 天;B 档 49,867 个 ≈ 11 天。用户要求 B 低速,这就是低速。
- **配额底线**:每 50 行读 `X-RateLimit-Remaining`,**低于 1,500 立即停止**(给随后可能开始的 sync 留额度)。
- 404 → 写 `''` + `readme_fetched_at`;200 → 写内容 + `readme_fetched_at`(触发 tsvector 触发器,1 行/秒是 6 月验证过的安全速率);其他 → 不写。
- 抓取时跟随重定向(改名的仓库 GitHub 会 301;现在 `httpx` 不跟随,会被当成"没有 README")。
- 结尾打印:抓到/无 README/失败/剩余候选数,并作为 Actions job summary。

### 4.3 sync 的 Phase 5 只做两处小改

- 选择器 A/C 的"缺 README"条件加上 `readme_fetched_at IS NULL OR (readme_content = '' AND readme_fetched_at < now() - 30d)`,和回填一致(`sync_selection.select_readme_targets` 加一个 `fetched_none` 集合参数,单测覆盖)。
- 404 时写 `''` + `readme_fetched_at`(现在什么都不写);200 时也写 `readme_fetched_at`。

不动上限(1000/100/400),不动"本轮看见"的语义。

### 4.4 增量 `scan_all`(B 档的前置,A 档进行中即上线)

`security_scanner.py`:

- `RULES_FINGERPRINT = sha256(所有 pattern 列表的正则源 + 严重度归属)[:16]`,**导入时自动计算**,不需要人记得改版本号。
- `scan_all(db, full=False)`:
  - 若表里存在 `scanner_version <> RULES_FINGERPRINT` 或 `SCAN_FULL=1` 环境变量 → **全量**(与今天行为相同,规则一改 ≤8h 内全库重评的约定不变)。
  - 否则 → 只扫 `readme_fetched_at > security_scanned_at OR security_scanned_at IS NULL`(且有 README)的行。
  - Phase 2(把无 README 的行标 unknown)同样只处理 `security_scanned_at IS NULL` 的行。
  - 每次写入同时写 `security_scanned_at = now()` 和 `scanner_version`。分块提交(500 行)不变。
- 日志加一行 `scan mode=incremental rows=N` / `mode=full reason=fingerprint`,以后看 Actions 日志就能核实。

效果:稳态每轮只扫这 8 小时新到的几百条 README;规则变更时一次全量。sync 时长回到 README 抓取和 upsert 决定的 ~40 分钟。

### 4.5 诚实的界面

- 状态判定集中在一处:前端 `lib/gradeState.ts`(SPA)和 `shared-utils.mjs`(静态页)各一个 `gradeState(row)` → `graded | not_fetched | no_readme`,输入 `security_grade` + `readme_fetched_at` + `readme_content 是否为空`(列表接口只带布尔 `has_readme`,不带正文)。`LIST_COLUMNS` 和 `fetchAllSkills` 加 `readme_fetched_at`。
- 文案:`not_fetched` → "尚未抓取 · 排队中" / "Not fetched yet · queued";`no_readme` → "GitHub 上无 README,无法评级" / "No README on GitHub — cannot be graded"。徽章 SVG 两种灰色文字对应,alt 文本改为 "Security status: …",不再对 unknown 说 "Security-graded"。
- **分析器**:GitHub 返回无 README 时,结果为 `unknown` + 上面那句解释,**不再跑空字符串扫描得出 SAFE**。Python 侧 `routes.py:674-691` 已经拒绝扫描空 README,TS 对齐它;parity 脚本加这个用例。
- 分类页/作者页/首页的 "each … security-graded" 改为 "security-graded wherever a README exists"(静态页生成时带真实比例)。

### 4.6 顺手关掉的一个坑

`deploy.yml` 的 `workflow_run` 触发加 `if: github.event.workflow_run.conclusion == 'success'`——现在 sync 失败也会重建并发布全部静态页。

## 5. 错误处理

| 情况 | 行为 |
|---|---|
| GitHub 403/429 | 脚本:等到 `X-RateLimit-Reset`,最多 4 次;低于 1,500 底线直接停,下个时段续 |
| 仓库 404/已改名 | 404 → `''` + 标记;301 跟随后按目标仓库 200/404 处理 |
| DB 语句超时 / PgBouncer 断连 | 每行 autocommit,已写的不丢;脚本退出非零,Actions 标红但不重试 |
| sync 正在跑 | concurrency group 让回填排队等待;等待超过 45 分钟被 timeout 取消,下个时段再来 |
| 规则指纹变化 | 下一次 sync 自动全量扫描,日志写明原因 |
| 回填把 scan_all 推大 | 增量扫描下每轮只多几百行;若 sync 时长连续两次 > 90 分钟,把 `--cap` 降到 750 |

## 6. 测试与门禁

- 单测(`backend/tests`):`select_readme_targets` 跳过 30 天内标记为无 README 的行;回填选择集在 floor=5 候选 < 50 时切到 1、永不含 0★;配额底线触发停止;`scan_all` 指纹不同→全量、相同→只扫变更行、`SCAN_FULL=1`→全量;404 写 `''` + 时间戳。
- 前端:分析器空 README → `unknown`(TS);Python↔TS parity 语料加空 README 用例;`gradeState` 三态各一个用例;`tsc -b` + `build:check`。
- 迁移在本地 Postgres 上跑一遍再上 Supabase;新列是增量的,失败可整体 `DROP COLUMN` 回滚。
- **第一次真实运行**用 `--cap 200` 手动触发(`workflow_dispatch`),看 job summary 和随后一次 sync 的时长,再放开到 1,500。
- 验收看三处:DB 的 `unknown` 分布(每天一次的只读查询)、Actions 里 sync 的时长、`scan mode=` 日志行。

## 7. 实施顺序

1. 迁移 + 模型字段 + 回填脚本改造 + workflow(A 档开始跑,cap 200 → 1,500)。
2. sync Phase 5 的两处小改(可与 1 同一提交)。
3. 增量 `scan_all`(在 A 档跑完前上线;这是 B 档自动接上的前提)。
4. 界面三态 + 分析器假阴性修复 + 文案。
5. `deploy.yml` 条件过滤。

每步独立提交、独立可回滚;3 未上线前不调低 floor(脚本默认 5,自动降 1 的逻辑随 3 一起启用,用一个 `--allow-floor-drop` 开关控制)。
