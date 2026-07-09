# AgentSkillsHub MCP Server — Spec v0.1

> 把 Hub 从「一个要被想起来才会逛的网站」变成「agent 工作流里的发现 + 信任前置」。
> 开发者和 agent 在 Claude Code / Cursor / Cherry Studio 里**不离开终端**就能 search → audit → install skill。
> 免费搜索 = 获客与分发；深度审计 / 认证 = 变现。

---

## 1. 战略定位（为什么是 MCP，不是又一个网站）

| 现状 | MCP 之后 |
|---|---|
| 用户要"想起来"去 agentskillshub.top 逛 | skill 发现发生在用户已经在的地方（终端 / IDE / agent runtime） |
| 流量靠 SEO，受众窄、PV 低 | 分发靠工具集成，每个需要 skill 的 agent 都先打到你 |
| Trust Layer 只在网站上 | 审计能力直接进 agent 调用链 —— **安装前先审** |

**「token 前置」的含义**：当一个 agent 需要某能力，它的调用链是
`需求 → search_skills（你）→ audit_skill（你）→ install → 消耗 token 干活`。
你的两个 tool 处在**所有 token 消耗的上游**。谁在上游，谁定标准、谁接认证生意。

**Cherry Studio 角度**：Cherry Studio 是多模型客户端、有 MCP 生态。这个 server 一旦做出来，Cherry Studio / Claude Code / Cursor / Cline 都能一行配置集成 → **你白嫖他们的用户量做分发**。这是和高德外链同级的分发机会。

---

## 2. 架构

```
┌─ MCP Client (Claude Code / Cursor / Cherry Studio / Cline) ─┐
│   tools: search_skills · audit_skill · get_skill_install     │
└───────────────────────────┬──────────────────────────────────┘
                            │ stdio (本地) / HTTP+SSE (托管)
                ┌───────────▼───────────┐
                │  @agentskillshub/mcp   │  Node/TS, npx-installable
                │  (薄封装，无业务逻辑)   │
                └───────────┬───────────┘
                            │ HTTPS
        ┌───────────────────▼────────────────────┐
        │  Supabase PostgREST + RPC（现有目录）    │
        │  skills / get_landing_data / quick search│
        │  audit: security_grade + 5维（按需触发） │
        └─────────────────────────────────────────┘
```

- **传输**：先做 **stdio**（`npx @agentskillshub/mcp`，本地、零部署，最广兼容）；第二步加 **HTTP+SSE** 托管版（给 Cherry Studio 远程连接 / 不想本地装的用户）。
- **数据源**：直接打现有 Supabase（anon key 走 RLS 只读，和前端同一套）。审计走专门的 audit endpoint。
- **无状态**：server 本身不存数据，只转发 + 整形。
- **认证分层**：
  - 匿名 → 免费 tier（search + 基础 audit），按 IP/设备限速。
  - `AGENTSKILLSHUB_API_KEY` 环境变量 → Pro/Enterprise（深度审计、任意 GitHub URL 审计、更高限速、CI 批量）。

---

## 3. 三个 Tool 定义

### 3.1 `search_skills` —— 发现（免费，获客前置）

在 10 万+ 目录里按自然语言 + 过滤条件找 skill。

**Input schema**
```jsonc
{
  "query": "string",                 // 自然语言或关键词，必填
  "category": "mcp-server|claude-skill|codex-skill|agent-tool|...",  // 可选
  "platform": "claude-code|cursor|codex|openclaw|...",               // 可选
  "min_stars": "number",            // 可选
  "min_quality": "number",          // 0-100，可选
  "verified_only": "boolean",       // 仅 Verified 作者/机构，默认 false
  "max_security_risk": "safe|caution|any",  // 默认 any
  "limit": "number"                 // 默认 8，最大 25
}
```

**Output**（每条）
```jsonc
{
  "repo_full_name": "owner/repo",
  "name": "repo_name",
  "author": "author_name",
  "verified": true,                 // Verified Creator/Org
  "description": "…",
  "stars": 1234,
  "fork_star_ratio": 0.18,          // 真实使用信号
  "quality_score": 72,             // 6 维质量分
  "category": "mcp-server",
  "platforms": ["claude-code","cursor"],
  "security_grade": "safe|caution|unsafe|reject|unknown",
  "estimated_tokens": 1827,         // 装进上下文大概多少 token
  "hub_url": "https://agentskillshub.top/skill/owner/repo/",
  "install_hint": "npx skills add owner/repo"
}
```

**设计要点**
- 返回里带 `security_grade` 和 `estimated_tokens` —— 让 agent **在选之前**就看到安全 + 成本(token)信号,这是 Hub 独有的、别的目录给不了的。
- 排序综合 quality_score + fork:star + 安全等级,不是纯 star(纯 star 会骗人)。
- 完全免费、匿名可用 —— 这是「前置获客」入口,越多人用越好。

---

### 3.2 `audit_skill` —— 信任(免费基础 / 付费深度,变现核心)

对一个 skill 跑 5 维信任审计。**这是 Trust Layer 的能力直接进 agent 工作流。**

**Input schema**
```jsonc
{
  "target": "string",   // "owner/repo"（库内）或完整 GitHub URL（库外，Pro）
  "depth": "basic|deep" // basic 免费；deep 需 API key
}
```

**Output**
```jsonc
{
  "target": "owner/repo",
  "in_catalog": true,
  "overall": "safe-for-personal|safe-for-production|caution|reject",
  "security_grade": "caution",
  "dimensions": {
    "code":         { "grade": "low",    "notes": "零运行时依赖；无混淆/外联下载" },
    "credentials":  { "grade": "high",   "notes": "OAuth token 远程托管在第三方 SaaS" },
    "vendor":       { "grade": "medium", "notes": "匿名维护者，0 follower，无公司主体" },
    "supply_chain": { "grade": "low",    "notes": "无 typosquat；上游活跃" },
    "operational":  { "grade": "high",   "notes": "服务方被黑→账号可被接管；无 DPA/审计日志" }
  },
  "verdict_line": "个人尝鲜可用；品牌号/生产环境不建议。",
  "flags": ["credential-remote-hosting", "anonymous-maintainer"],
  "report_url": "https://agentskillshub.top/skill/owner/repo/#audit",
  "tier_note": "deep 审计 + 任意 GitHub URL 需 Pro。CI/批量审计 → Enterprise。"
}
```

**分层(变现钩子)**
| | basic(免费) | deep(Pro) | Enterprise |
|---|---|---|---|
| 库内 skill 的 security_grade + flags | ✓ | ✓ | ✓ |
| 5 维完整解读 | 摘要 | ✓ 详细 | ✓ |
| 任意 GitHub URL(库外 / 私有) | ✗ | ✓ | ✓ |
| CI / 批量 / MCP server 全量审计 | ✗ | ✗ | ✓ |
| 合规证据包(SOC2/ISO42001/EU AI Act) | ✗ | ✗ | ✓ |

**设计要点**:basic 免费但有用(够 agent 安装前自检)→ 培养习惯;deep / 任意 URL / 批量是付费墙。**这把"工具内 product-led 变现"做实了**(分析里的②收益路径)。

---

### 3.3 `get_skill_install` —— 安装(免费;返回指令 + bundle,不代执行)

> ⚠️ MCP server **不在用户机器上跑命令**(那是 client 的事)。本 tool 返回「该装什么、怎么装、装之前先看这些」,由 agent/用户执行。

**Input schema**
```jsonc
{
  "repo_full_name": "owner/repo",
  "runtime": "claude-code|cursor|codex|cherry-studio|generic"  // 决定返回哪种安装指令
}
```

**Output**
```jsonc
{
  "repo_full_name": "owner/repo",
  "install_commands": {
    "claude-code": "npx skills add owner/repo",
    "manual": "git clone … && cp -r skills/* ~/.claude/skills/"
  },
  "skill_md": "…(SKILL.md 全文,≤ N KB)…",   // 让 agent 直接看 skill 定义
  "pre_install_safety": {                       // 装之前的一句话风险提示
    "security_grade": "safe",
    "must_check": ["需要 OAuth？凭证存哪？", "维护者可信？"]
  },
  "license": "MIT",
  "hub_url": "https://agentskillshub.top/skill/owner/repo/"
}
```

**设计要点**:返回 `skill_md` 让 agent 不用跳出去就能读 skill 定义;`pre_install_safety` 把审计结果**强行塞进安装动作前**——这就是「装之前先审」的产品化。

---

## 4. 分发 / 集成(一行配置)

**Claude Code / Cursor / Cline / Cherry Studio** 的 `mcp` 配置:
```jsonc
{
  "mcpServers": {
    "agentskillshub": {
      "command": "npx",
      "args": ["-y", "@agentskillshub/mcp"],
      "env": { "AGENTSKILLSHUB_API_KEY": "可选,Pro 用" }
    }
  }
}
```

- 免费用户:不填 key,直接 search + basic audit。
- 发布到 npm `@agentskillshub/mcp` + 在 Hub 首页给「一行装进你的 agent」按钮。
- 给 Cherry Studio:做成它的**内置/推荐 MCP**,他们的用户开箱即用 → 你拿分发,他们拿"我们能搜 10 万 skill"的卖点。**双赢,这是合作谈判的核心筹码。**

---

## 5. MVP 范围(2 周可出)

| 阶段 | 内容 |
|---|---|
| **MVP(第 1 周)** | stdio server + `search_skills`(打现有 quick-search/PostgREST) + `get_skill_install`(读 skills 表 + SKILL.md)。免费、匿名。发 npm。 |
| **第 2 周** | `audit_skill` basic(读 security_grade + flags)。Hub 首页加「一行装进 agent」。 |
| **第 3 步(看反馈)** | API key + Pro 限速 / deep audit / 任意 URL 审计。HTTP+SSE 托管版给 Cherry Studio。 |

**先做免费的 search + install 拿分发,audit 的付费墙等有量了再上。** 别一上来就建一堆付费 feature(对应分析里的"②企业只留一个"纪律)。

---

## 6. 关键决策点(需你拍板)

1. **npm 包名** `@agentskillshub/mcp` 还是 `agentskillshub-mcp`?(scope 包更正规,但要建 npm org)
2. **审计深度**:basic 直接读已有 `security_grade`(但 97.8% 是 unknown)——要不要在 MCP 触发时**对未评级的 skill 现场跑一次轻量扫描**?(更有用,但要算力)
3. **Cherry Studio**:做成他们**内置**(谈合作)还是**用户自己加**(先发 npm,自然增长)?建议两条腿:先发 npm 自然长,同时跟他们谈内置。

---

## 7. 一句话总结

`search_skills`(免费获客前置)+ `audit_skill`(免费基础 / 付费深度,变现)+ `get_skill_install`(把"装前先审"产品化)
→ 把 Hub 从网站变成 **agent 工作流的发现 + 信任前置**,分发靠工具集成而非 SEO,变现靠工具内 product-led 而非订阅。
