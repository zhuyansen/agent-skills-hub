# SkillSpector Integration — Spec v0.2

> 用 NVIDIA 开源的 [SkillSpector](https://github.com/NVIDIA/SkillSpector)(Apache-2.0)做 agent skill 的安全深扫。

## 安全评级架构:两层(面 + 点)

AgentSkillsHub 的安全信号是**分层**的,SkillSpector 只占其中「按需深扫」这一层 —— 不参与全库自动评级。

```
                         AgentSkillsHub 信任层 · 安全评级

┌─────────────────────────────────────────────────────────────────────┐
│  第 1 层 · 规则评级  —— 面:全库 · 自动 · 免费                          │
│  SecurityScanner.scan_all(SlowMist 11 类正则,零成本)                 │
│  在每次 sync 里对「有 README」的 skill 自动跑:                          │
│      safe / caution / unsafe / reject                                 │
│  没 README → unknown(诚实:"还没审",不是"危险")                       │
└─────────────────────────────────────────────────────────────────────┘
                ⋮  (可选)第 1.5 层 · LLM 二次判定
                ⋮  LLMSecurityAnalyzer(MiniMax)对高价值/歧义项复核
                ⋮  需 LLM_API_KEY;当前 CI 未配 → 暂时关闭
                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  第 2 层 · SkillSpector 深扫  —— 点:单个 · 按需 · 人工复核             │
│  NVIDIA SkillSpector(64 模式 / 16 类,AST + 污点 + YARA)             │
│  仅在有人主动要深审时,针对【单个】skill 触发:                          │
│      ash audit --deep  ·  博客免费审计  ·  企业线索                     │
│  每次有人复核。 ⛔ 绝不批量自动跑(见下:实测 10 个 9 个误报)             │
└─────────────────────────────────────────────────────────────────────┘
```

| | 第 1 层 · 规则评级 | 第 2 层 · SkillSpector 深扫 |
|---|---|---|
| 覆盖 | **全库**(所有有 README 的) | **单个**(被点名深审的) |
| 触发 | 自动(每次 sync) | 按需(CLI / 博客 / 企业线索) |
| 成本 | 零(纯正则) | 高(AST/LLM,单个 49s–856s) |
| 复核 | 无需 | **每次人工复核** |
| 写入 | `security_grade` 全库 | 深扫报告(详情页 `#audit` / 企业证据包) |
| 角色 | **打底的面**(便宜、诚实、可全覆盖) | **深挖的点**(贵、准、要人盯) |

> **两层不串联自动跑** —— 规则评级是面(全库便宜诚实),SkillSpector 是点(单个深挖按需)。后者**不**接在前者后面对全库扫,否则就会触发下面这个灾难。

> ## ⛔ 实测结论(2026-06,v0.2):不做批量自动评级
>
> 经过把 LLM 模式真正跑通(真 OpenAI key + 注册模型 + 429 重试)后,对 **10 个高价值 skill**
> 的试扫证明:**SkillSpector 即使配 gpt-4o(强模型)也会灾难性过度标记** ——
> **10 个里 9 个被判 `unsafe`/`reject`**,包括 firecrawl 官方 MCP server 和两个纯 markdown 的
> awesome 列表。误报依据已实锤:把 **二进制 PNG 字节** 判为"工具参数滥用"、把 README 里的
> **star-history 徽章链接** 判为"数据外泄"、把文档里的 **`tools:*`** 判为"过度代理"、把 MIT license
> 的 **"NOT LIMITED TO"** 判为"范围蔓延"。后过滤 LICENSE/测试文件也救不回来(误报在 README/markdown/
> 二进制里)。单个耗时 49s–856s(Tier-1 限速),全量 19,600 个需数十小时 + 真金白银。
>
> **把这种结果写进生产 `security_grade` = 90% 目录被打上假"危险"标签,直接砸 Trust Layer 招牌。**
> 比 `unknown` 黑箱更糟 —— `unknown`("我们没审过")是诚实的;假 `unsafe` 是主动制造错误信息。
>
> **决策:SkillSpector 只用于「按需深扫」**(`ash audit --deep` / 博客免费审计 / 企业线索),
> **每次有人复核**;全库保持诚实 `unknown`。批量自动评级路线作废。
> 试扫工具:`backend/skillspector_runner.py`(staging-only,raw vs 过滤后双视图)。

---

## 1. 为什么是它

| 我们的窟窿 | SkillSpector 提供 |
|---|---|
| 没有扫描器 → 97.8% skill 是 `unknown` 黑箱 | 64 个漏洞模式 / 16 类(prompt injection、数据外泄、供应链、MCP 安全、危险代码 AST、污点追踪、YARA) |
| `security_grade` 没人填 | 输出 `0-100 风险分 + LOW/MEDIUM/HIGH/CRITICAL + SAFE/CAUTION/DO NOT INSTALL`,**几乎一对一映射我们的 enum** |
| 审计要花钱 | **离线 `--no-llm` 可跑**(静态规则+AST+YARA),批量零 API 成本;可选 LLM(支持 Anthropic key)提精度 |
| 法律/合规风险 | Apache-2.0,可商用、可当基建 |

**验证过**:已 `uv sync` 装在 `/Users/zhuyansen/content/skillspector`,离线扫我们自己的 `agentskillshub-cli` → `5/100 · LOW · SAFE`。研究背书:arXiv 2601.10338(Liu et al. 2026,n=31,132)。

---

## 2. 目标字段(零建表 —— 列已存在)

`skills` 表已有四列,直接落:

| 列 | 写入内容 |
|---|---|
| `security_grade` | 映射后的 enum:`safe / caution / unsafe / reject`(见 §4) |
| `security_flags` | JSON:命中的 category/pattern 列表(去重、按 severity 排序) |
| `security_llm_grade` | LLM 模式下的二次判定(仅高价值/歧义项跑,见 §5) |
| `security_llm_analysis` | LLM 模式的解释文本(给详情页 `#audit` 区) |

附加(可选,需迁移):`security_score INT`(0-100)、`security_scanned_at TIMESTAMP`、`security_scanner_version TEXT`(便于增量 + 审计追溯)。

---

## 3. 架构:增量 + 离线优先 + LLM 兜底

```
sync (现有 6 phase) ──► Phase 8: SkillSpector 扫描(新增)
                          │
   只扫「新增 or pushed_at 变化 or 从未扫过」的 skill ── 增量
                          │
        ┌─────────────────┴─────────────────┐
        ▼ 默认                                ▼ 仅当 (score 边界 40-70) or (HIGH/CRITICAL 命中)
   skillspector scan <repo> --no-llm      skillspector scan <repo>(挂 ANTHROPIC_API_KEY)
   离线、免费、快                           语义复核、过滤误报、写 llm_grade/llm_analysis
        │                                    │
        └──────────────► 映射 → 落库 ◄───────┘
```

- **增量键**:`pushed_at`(skill 仓库最后 push)。存 `security_scanned_at` + 比对,只重扫变更过的。
- **离线优先**:绝大多数走 `--no-llm`(零成本)。只有**风险分落在灰色区间(40-70)或命中 HIGH/CRITICAL** 的才升级到 LLM 复核 —— 把 API 钱花在刀刃上。
- **跑在哪**:独立 worker / GitHub Actions job(扫描是 clone+AST,CPU 密集,不要塞进主 sync 进程阻塞 GitHub API 配额)。建议每日批,从 `stars>=5` 起步(~19,600 个),逐步下沉。

---

## 4. 输出映射(SkillSpector → 我们的 `security_grade`)

| SkillSpector recommendation | severity | → `security_grade` |
|---|---|---|
| SAFE | LOW | `safe` |
| CAUTION | MEDIUM | `caution` |
| DO NOT INSTALL | HIGH | `unsafe` |
| DO NOT INSTALL | CRITICAL + 命中 malicious-intent 类 | `reject` |

边界由 `risk_assessment.score` 兜底(如 score≥80 强制 ≥unsafe),具体阈值在实现时用真实分布校准。

---

## 5. 必须处理的坑(来自实扫)

1. **LICENSE / 法律样板误报** 🔴 —— 离线模式把 MIT LICENSE 里的 `"INCLUDING BUT NOT LIMITED TO"` 判成 "Excessive Agency / Scope Creep"(实扫我们 CLI 时复现,confidence 0.7)。
   **对策**:扫描前**排除 `LICENSE*` / `COPYING` / `THIRD_PARTY_NOTICES` / `NOTICE`** 等纯法律文件;或对 `Excessive Agency` 这类高误报 pattern **强制走 LLM 复核**再采信。
2. **osv.dev 实时查询限速** —— SC4 会打 `api.osv.dev`。批量时加重试/退避 + 缓存;离线 fallback 已内置。
3. **clone 成本** —— 每次扫描 clone 一个 repo。用 `--depth 1` + 扫完即删 + 按 `pushed_at` 增量,避免重复 clone 已扫过的。
4. **Python 版本** —— SkillSpector 要 `>=3.12,<3.14`;我们后端 venv 是 3.12.12(达标),但 worker 环境要锁版本。

---

## 6. MVP 范围

| 阶段 | 内容 |
|---|---|
| **MVP** | 独立脚本 `backend/skillspector_runner.py`:取 `stars>=5 AND (security_scanned_at IS NULL OR pushed_at > security_scanned_at)`,排除法律文件,`--no-llm` 扫,映射落 `security_grade`/`security_flags`/`security_score`/`security_scanned_at`。每日 GitHub Actions 批量。 |
| **第二步** | 灰色区间(40-70)+ HIGH/CRITICAL 升级 LLM 复核(Anthropic),写 `security_llm_grade`/`security_llm_analysis`。详情页 `#audit` 区展示。 |
| **第三步** | 把这套接到 `ash audit --deep` / MCP `audit_skill(depth=deep)` 的付费墙后(见 [mcp-server-spec.md](./mcp-server-spec.md));库外任意 GitHub URL 现场扫 = Pro。 |

**先把免费的离线批量扫做实,把 97.8% unknown 打下来;LLM 复核和付费深扫等有数据了再上。**

---

## 7. 一句话

SkillSpector 是现成的、官方的、开源的 skill 安全扫描器,输出几乎一对一映射我们既有的 `security_grade` 列。
**离线批量扫 = 几乎零成本地把目录从"97.8% 黑箱"变成"有依据的信任数据"** —— 这是 Trust Layer 最便宜、最高杠杆的一块拼图。
