# Competitor Notes / Battlecards

Quick intel on adjacent products. Use for positioning, enterprise sales, and
deciding what to borrow vs differentiate.

---

## iflytek/skillhub (讯飞)
GitHub: https://github.com/iflytek/skillhub · 3.6k★ · enterprise self-hosted skill registry

**What it is:** a self-hosted, open-source skill **registry + governance layer** —
you publish/version/govern skills *into* it (team namespaces, RBAC Owner/Admin/Member,
review workflows, semantic versioning + beta/stable tags, audit logging, social
ratings/downloads, CLI + REST + ClawHub-compatible protocol).

**What it does NOT have:** automated quality scoring, security grading, or skill
validation beyond file-extension allowlisting. ← **our differentiator.**

**Positioning vs us (battlecard line):**
> "iflytek SkillHub is where enterprises **host** their skills.
>  AgentSkillsHub is where you **vet** any open-source skill before you host it."
Complementary, not a direct competitor: they're a private registry backend; we're a
public discovery + trust layer over the whole open ecosystem.

**What it validates for us:** the enterprise demand for self-hosted + governance
(namespace/RBAC/review/audit/on-prem) is real — backs our `/enterprise/` direction
(on-prem mirroring + audit-ready evidence). Cite as proof-of-demand in enterprise pitches.

**What to borrow:** their formal skill manifest/schema (capability declarations, I/O
contracts, versioning) → a **spec-compliance signal** for our quality score + SkillSpector
audit. Tracked in [audit-layers-todo.md](./audit-layers-todo.md) "Future enhancement".

---

## LobeHub — lobehub.com/skills
Larger scenario taxonomy than ours was; we borrowed missing scenario buckets
(Search & Research, Productivity) during the 79→84 scenario expansion. Reference
when reviewing scenario coverage.

## NanoSkill — nanoskill.ai
Fine-grained marketing-agent skill verticals; inspired our job-based marketing
scenarios (paid-ads / lead-generation / marketing-analytics).

## 品牌名蹭词群(name-squatters)· 2026-07-24 首录

品牌词 `agent skills hub` 卡 pos 11 的另一半原因:SERP 正在被同名者分食。盯梢名单:

| 站 | 定位 | 威胁面 | 弱点 |
|---|---|---|---|
| **agentskillshub.dev** ⚠️ 主要 | 标题原样抄:"Agent Skills Hub - Secure MCP Server Directory";"security-reviewed MCP servers" | **名字+安全叙事整套复制**;Next.js 内容站,带 editorial-policy/review-methodology 信任页,建了 /guides/agent-skills-hub/ 蹭词页,SEO 内容打法 | **无数据护城河**:零规模宣称(无 13 万级目录)、无自动评分/分级管道,纯人工编辑体 |
| agentskill.wiki | 同名 wiki 体 | 分食品牌词 SERP | 未深查 |
| agent-skills-hub.github.io + GitHub org "agent-skills-hub" | "global library of AI agent skills" | 占 GitHub 命名空间 | 未深查 |
| Open VSX "agent-skills-hub" 扩展 | VS Code 扩展同名 | 占插件市场心智 | 未深查 |

**对策(2026-07-24 定)**:不打口水仗、不发律师函(.top 反被动)。**用抄不走的打**:
1. 权威实体信号:Wikidata Q140478987 ✓ / arXiv 论文(ID 待发)/ 独立媒体报道(客座 5 连 ✓,继续攒到 Wikipedia notability 门槛)
2. 数据护城河外显:135K 目录规模、8h 刷新、真实分级数据——每处对外物料都带硬数字,让"同名但没数据"一眼可辨
3. 每月复盘顺手查一次这批站的 SERP 占位变化(品牌词前 20 结果里它们占几席)

**battlecard 一句话**:
> ".dev 抄走了我们的名字和故事,抄不走 135,044 行分级数据和每 8 小时的管道。"
