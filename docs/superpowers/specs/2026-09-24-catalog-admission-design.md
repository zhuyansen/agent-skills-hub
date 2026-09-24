# 目录覆盖:分级收录 + 一键审核 + 浪潮查询切片

日期:2026-09-24 · 状态:待实施 · 范围:A(目录覆盖),政策已定:高星 + 主题词双门槛自动收录,其余人工一键

## 1. 问题

目录进新仓库只有一条自动路:sync 的固定搜索查询(40 条,每条最多 3 页 × 100,按星排序)。查询没措辞到的仓库永远进不来,于是有了三个手动环节:

- **漏**:每周覆盖扫描(`.github/workflows/catalog-coverage.yml` → `ops/find_missing_repos.py`,12 条带星数下限的查询)能找到漏收的,但**只报告不写库**——2026-08-20 定下的红线:"a bad search query can never pollute the catalog on its own"。#21(2026-09-19):19 个未收录,含 dream-num/univer 14,411★、seleniumbase/SeleniumBase 13,025★、Tencent/BrowserSkill 5,565★,至今没进目录。
- **审**:投稿有两条路,都停在人工。站内表单 → `POST /submit`(`routes.py:615`)写 `extra_repos`(status=pending,is_active=false),要管理端点 `PUT /extra-repos/{id}/approve` 才生效;GitHub issue 投稿(#14–#18,标题 `Submit repository: …` / `[Submission] …`)**没有任何代码读它们**,5 个开着。
- **截断**:sync 每条查询翻满 3 页就停,且静默。`jev in:name,description,topics created:>=2026-09-15` 在 GitHub 已 6,986 条,每轮只看到按星前 300;/best/typesafe-jev/ 的门槛 50★ 目前只有 145 条合格,暂时无损,但 ≥20★ 的长尾进不来,且没人知道被截了。

`extra_repos` 的机制本身是对的:激活行每轮 sync 按名抓取、不受 push 时间过滤,入库当轮抓 README 评级。缺的是**谁把行写进去**。

## 2. 目标与非目标

**目标(验收):**
1. #21 那 19 个里满足自动规则的(≥1000★ 且命中主题词,预计 11 个)在实施后的下一轮 sync 出现在目录里且有评级。
2. 5 个投稿 issue 全部处于三种终态之一:已收录 / 待定并附 `/approve` 命令 / 已拒绝;此后新投稿 issue 在打开后 5 分钟内得到预审评论。
3. 下一次周扫描的 issue 分「已自动收录」「待你定」两段,后者每行带命令;你在 issue 上回一条命令,行状态在 2 分钟内改变并得到确认评论。
4. sync 日志对每条翻满 3 页的查询打出 `total_count`;浪潮查询(`created:>=`)按星段切片后,GitHub 上 ≥20★ 的 Jev 仓库进入目录的比例 ≥ 95%(用 `ops/find_missing_repos.py` 的方法对照)。

**非目标:**
- 不改管理端点(`admin_routes.py`),不做前端投稿状态页。
- 不动 sync 普通查询的翻页(3 页够高星的;长尾靠覆盖扫描和回填)。
- 不做"自动拒绝"——不满足规则只是待定,不是拒绝。
- 0★/fork/archived 仓库一律不自动收录(fork 和 archived 由规则排除,不需要人看)。

## 3. 方案比较(政策已选 B)

| | 方案 | 结论 |
|---|---|---|
| A | 保留人工门,只把门做成一键 | 零误收,但每周仍要点十几下,#21 那种 14K★ 的也要等人 |
| **B** | **≥1000★ + 主题词自动收录,其余一键门** | **采用**。误收概率低(两道门槛),误收的代价只是多一个有评级的页面 |
| C | 全自动 | 放弃 08-20 的红线;投稿里有营销号 |

## 4. 设计

### 4.1 准入规则(一处实现,三处调用)

`backend/app/services/catalog_admission.py`,纯函数,无 IO:

```python
AUTO_APPROVE_MIN_STARS = 1000
TOPIC_WORDS = re.compile(r"\b(skills?|mcp|agents?|claude|codex|openclaw)\b", re.I)
EXCLUDE = re.compile(r"awesome-|curated list|jevois|jevons", re.I)   # 与 scenario 页排除词同源

def admission(repo: dict) -> Literal["approved", "pending", "excluded"]:
    #  repo: GitHub API 的仓库对象(full_name, description, stargazers_count, archived, fork)
    if repo.get("archived") or repo.get("fork"):                     -> "excluded"
    text = f"{full_name} {description or ''}"
    if EXCLUDE.search(text):                                         -> "excluded"
    if stars >= AUTO_APPROVE_MIN_STARS and TOPIC_WORDS.search(text): -> "approved"
    else:                                                            -> "pending"
```

`excluded` 不写库、不列在 issue 里(fork/archived/已知碰撞不值得人看)。规则的正反例进单测,包括边界项 seleniumbase/SeleniumBase(13,025★,描述含 "AI agents" → approved,记录为已知边界:它是浏览器自动化库,目录已收类似项)。

### 4.2 写库(一处实现)

同一模块里的 `upsert_extra_repo(conn, full_name, verdict, submitted_by, note)`:

- `INSERT … ON CONFLICT (full_name) DO UPDATE SET status = EXCLUDED.status, is_active = EXCLUDED.is_active, submitted_by = EXCLUDED.submitted_by WHERE extra_repos.status = 'pending'`——**只有 pending 行会被改写**;已 approved/rejected 的行不回退,再投稿也不会重开。
- approved → `is_active = true`;pending → `is_active = false`(与现有 `/submit` 一致)。
- `submitted_by` 记来源:`coverage-auto`、`coverage-pending`、`issue-<n>`、`command-<login>`。
- 返回 `inserted | updated | unchanged`,供评论文案用。

复用 `ExtraRepo` 模型的列,不加列、不迁移。

### 4.3 入口 1:周覆盖扫描分级写入

`ops/find_missing_repos.py` 加 `--write`(默认不写,保留 report-only 供手动核对):找到的未收录仓库逐个过 `admission()`,approved/pending 写库。workflow 的 issue 正文改为两段:

```
## 已自动收录(≥1000★ 且命中主题词)      n 个,下轮 sync 可见
- dream-num/univer ★14,411 — The Office Harness for AI Agents …
## 待你定                               m 个
- Hisn00w/ASu-skills ★4,847 — …        /approve Hisn00w/ASu-skills · /reject Hisn00w/ASu-skills
```

站内表单进来的 pending 行(status=pending 且 `submitted_by` 不以 `coverage-` / `issue-` / `command-` 开头)也追加到「待你定」段,让两条投稿路汇到同一个 issue。

### 4.4 入口 2:投稿 issue 预审

新 workflow `.github/workflows/submissions.yml`,`on: issues: [opened]`,仅当标题匹配 `^(Submit repository:|\[Submission\])`。步骤(`ops/triage_submission.py`):

1. 从正文取第一个 `github.com/{owner}/{repo}` 链接;取不到 → 评论"没找到仓库链接",贴 `needs-info` 标签,结束。
2. `GET /repos/{owner}/{repo}`(Actions 令牌);404 → 评论"仓库不存在或私有",结束。
3. `admission()` → 写库。
4. 预审卡评论:星数、许可证、archived/fork、主题词命中与否、**README 安全评级预览**(拉 README,跑 `SecurityScanner().scan_single`,不写库;需要 `pip install -r backend/requirements.txt`),以及结论:「已收录,下轮同步(≤8h)可见」或「待定:维护者回复 `/approve owner/repo` 收录」或「已排除:fork/archived」。
5. approved 的加标签 `admitted`,pending 的加 `pending-review`。

现有 5 个 issue:workflow 支持 `workflow_dispatch` 传 issue 号,上线后逐个跑一次。

### 4.5 入口 3:一键门(评论命令)

新 workflow `.github/workflows/admission-commands.yml`,`on: issue_comment: [created]`,`ops/admission_command.py`:

- 只处理 `author_association` ∈ {OWNER, MEMBER, COLLABORATOR} 的评论,其余忽略(不回复,避免被刷)。
- 命令语法:每行一条,`/approve owner/repo` 或 `/reject owner/repo`;一条评论可含多条。解析失败的行原样列在回复里。
- 执行:approve → `status=approved, is_active=true, submitted_by=command-<login>`;reject → `status=rejected, is_active=false`。行不存在时 approve 直接插入(允许你在任何 issue 里点名收录一个仓库)。
- 回复一条确认评论,列每个仓库的结果。若该 issue 是投稿 issue 且其仓库已到终态,关闭 issue;周扫描 issue 不自动关。

### 4.6 截断:可见 + 浪潮切片

`jobs.py` Phase 1:
- 每条查询翻满 3 页且 `total_count > 300` 时 `logger.warning("query truncated: %s total=%d read=300")`。
- `with_push_filter` 判定为浪潮查询(含 `created:>`)的,在 3 页主查询之外再跑两个星段:`{query} stars:50..199` 和 `{query} stars:20..49`,各最多 3 页,结果并入 `all_repos`。纯函数 `wave_slices(query) -> list[str]` 放 `sync_selection.py`,单测覆盖;普通查询返回 `[]`。每条浪潮查询多花 ≤6 次搜索请求(配额 30/分钟,现有 40 条查询 × 3 页已在预算内)。

### 4.7 权限与安全

- 两个新 workflow 用 `secrets.SUPABASE_DB_URL`(服务连接)写 `extra_repos`,和 sync 相同;`permissions: issues: write, contents: read`。
- 命令来源用 GitHub 的 `author_association` 判定,不看用户名;评论正文中的仓库名只允许 `[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+`,其余拒绝——正文是不可信输入,永远不拼进 SQL 或 shell。
- 预审卡里的 README 摘要不回显正文(投稿 README 可能含注入文本),只给评级和标记名。

## 5. 错误处理

| 情况 | 行为 |
|---|---|
| GitHub API 限流/失败 | 评论"稍后重试",贴 `needs-retry`;job 不失败 |
| DB 不可达 | job 失败,沿用 `notify-failure` 开 issue 的模式 |
| 重复投稿 | pending 行改状态;approved/rejected 行不动,评论说明当前状态 |
| 同一评论多个命令部分失败 | 逐条报告,成功的不回滚 |
| 周扫描发现的仓库后来被删 | sync 按名抓取 404 → 现有逻辑跳过;`refresh-stale` 标 gone |

## 6. 测试与门禁

- 单测:`admission()` 正反例(含 SeleniumBase 边界、fork、archived、awesome- 排除、999★ 不过线);`upsert` 的 SQL 只改 pending 的断言;URL 解析(多种写法、无链接);命令解析(权限、非法仓库名、多条);`wave_slices()`。
- YAML 校验两个新 workflow + 改过的 `catalog-coverage.yml`。
- **上线顺序**:先 report-only 干跑——对 5 个投稿 issue 和 #21 的 19 个各打出会落到哪一档,贴给你看;确认后再开 `--write`。
- 验收看:下轮 sync 后 #21 自动档仓库有评级;5 个 issue 的终态;下次周扫描 issue 的两段结构。

## 7. 实施顺序

1. `catalog_admission.py` + 单测(规则、upsert)。
2. `find_missing_repos.py --write` + 周扫描 issue 两段式;对 #21 干跑 → 真跑。
3. `submissions.yml` + `triage_submission.py`;对 5 个 issue 干跑 → 真跑。
4. `admission-commands.yml` + `admission_command.py`。
5. `jobs.py` 截断日志 + 浪潮切片(单独提交,下轮 sync 验证 Jev 覆盖比例)。

每步独立提交、可回滚;3 和 4 只在 2 验证通过后启用。
