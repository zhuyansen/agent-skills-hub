---
title: 附录 A · Skill 设计速查表（一页纸）
status: published
data_snapshot: 2026-04-29
---

# 附录 A · Skill 设计速查表（一页纸）

> 把蓝皮书 12 章浓缩成一页可打印的 cheatsheet。
> 适合：写第一个 Skill 之前、卡住时回头看、贴墙上。

---

## A.1 写 description 的 10 条金科玉律

| # | 规则 | 反例 → 正例 |
|--:|------|------|
| 1 | 必须含 **「Use when X」** 显式触发条件 | ❌ "A code review skill" → ✅ "Use when reviewing PR diffs or git diff output" |
| 2 | 必须声明**输入类型** | ❌ "reviews code" → ✅ "Use when reviewing TypeScript/React .ts/.tsx files" |
| 3 | 必须声明**输出格式** | ❌ "gives feedback" → ✅ "Output: markdown table with severity/file/line/fix" |
| 4 | 必须含**「Do NOT use when」** | ❌ 只写正向 → ✅ "Do NOT use when reviewing config / docs" |
| 5 | 用 **MUST / NEVER / ALWAYS** 替代「应该」「建议」 | ❌ "should output a table" → ✅ "MUST output a table" |
| 6 | 控制在 **80 token 以内**（约 50 中文字 / 60 英文词）| 超过会被 SDK 截断展示给 Agent |
| 7 | **不要复制 instructions 的开头** —— description 是目录，不是摘要 | 写 from scratch |
| 8 | 提到 **competing skills** 时明示边界 | "Use this for type errors; use debug-skill for runtime errors" |
| 9 | 含 ≥ 1 个**具体例子触发器** | "Use when user says 'review this' or shares code in a code block" |
| 10 | **测一遍**：把 description 单独给 GPT-4，问「这个 skill 该在什么场景下激活」——能答对再 ship |

---

## A.2 9 种类型 × 4 级路径 推荐矩阵

```
            Personal | Project | Team | Global  
─────────────────────────────────────────────────
1 Reference   主战场 |  高频   | 高频  | 高频
2 Data Acq    常见   |  高频   | 常见  | 主战场
3 Scaffolding 常见   |  主战场 | 高频  | 常见
4 CI/CD       常见   |  主战场 | 主战场| 常见
5 Code Quality常见   |  主战场 | 主战场| 高频
6 Documentation常见  |  高频   | 常见  | ⚠️不推荐
7 Workflow    常见   |  高频   | 高频  | 常见
8 Persona     主战场 | ⚠️不推荐| ⚠️不推荐| 常见
9 Communication常见  |  高频   | 主战场| 常见
```

**做不做的速判**：
- ✅ 优先做：Reference / CI-CD / Code Quality（3 类）
- ⚠️ 谨慎做：Data Acq / Scaffolding / Workflow / Communication（要选垂直）
- ❌ 不推荐：Documentation（生成的没人看）/ Persona（合规风险）

---

## A.3 5 种设计模式 × 9 种类型 交叉推荐

| 类型 / 模式 | 决策树式 | 角色化 | 模板填充 | 评分清单 | 状态机 |
|:----------:|:----:|:----:|:----:|:----:|:----:|
| Reference   | ✅ 主推 | — | ✅ | — | — |
| Data Acq    | — | — | ✅ 主推 | — | ✅ |
| Scaffolding | — | — | ✅ 主推 | — | ✅ |
| CI/CD       | ✅ 主推 | — | — | ✅ | ✅ |
| Code Quality| ✅ 主推 | — | — | ✅ 主推 | — |
| Documentation| ✅ | — | ✅ | — | — |
| Workflow    | ✅ 主推 | ✅ | ✅ | — | ✅ 主推 |
| Persona     | — | ✅ 主推 | — | — | — |
| Communication| ✅ | ✅ | ✅ | — | ✅ |

**5 种模式速注**：
- **决策树式**：if X then Y else Z 的条件链
- **角色化**：以「作为 X 角色思考」开头（gstack 风）
- **模板填充**：给一份 fill-in-the-blank 框架
- **评分清单**：每个维度 0-N 评分 + 总分
- **状态机**：Step 1 → Step 2 → ... → Final

---

## A.4 踩坑清单模板

新 Skill 发布前自检 14 项：

**description 层（5 项）**
- [ ] 含「Use when」+「Do NOT use when」
- [ ] 含输入 / 输出格式
- [ ] ≤ 80 token
- [ ] 用 MUST / NEVER 而非「应该」
- [ ] 单独给 GPT-4 问能不能正确激活

**instructions 层（5 项）**
- [ ] 前 200 字答了 5 个问题（做什么/输入/输出/前置依赖/失败处理）
- [ ] 用决策树而非散文
- [ ] 含「DO NOT」清单
- [ ] 大小 5-20KB（sweet spot）
- [ ] 含至少 2 个反例

**resources 层（2 项）**
- [ ] 大于 1000 字的数据/模板搬到 `resources/`
- [ ] 资源文件路径 immutable（不会重命名）

**生命周期（2 项）**
- [ ] 装到自己 `~/.claude/skills/` 用 1 周再发布
- [ ] 创建 `MISTAKES.md` 准备记踩坑

---

## A.5 决策树：你该写哪种 Skill？

```
你已经写过这件事 ≥ 3 次？
├─ 是 → 继续
└─ 否 → ⚠️ 等踩过 3 次再写

它属于推荐的 3 类（Reference / CI-CD / Code Quality）？
├─ 是 → ✅ 写
└─ 否 → 是垂直定位的 Data Acq / Scaffolding / Workflow / Communication？
   ├─ 是 → ⚠️ 找垂直角度
   └─ 否 → ❌ 重新选题

你打算分享到第几级？
├─ 1 (Personal)  → 直接写、跑、迭代
├─ 2 (Project)   → 写完把 SKILL.md 丢进项目根 `.claude/skills/`
├─ 3 (Team)      → 多写一份合规说明（无 secret、无 PII）
└─ 4 (Global)    → 用 1 个月、写 MISTAKES.md、写 README、再考虑发 Hub
```

---

## A.6 常用 SKILL.md 骨架（直接复制）

```markdown
---
name: your-skill-name
description: |
  [一句话做什么]. ALWAYS use when: [具体触发条件].
  Do NOT use when: [明示边界]. Output: [格式预告].
---

# Your Skill Name

## Required Output Format

You MUST output [structure]. Do NOT use [anti-pattern].

| col1 | col2 | col3 |
| --- | --- | --- |
| ... | ... | ... |

## Before You Start

1. [前置步骤 1]
2. [前置步骤 2]

## DO NOT

- Do NOT [anti-pattern 1]
- Do NOT [anti-pattern 2]
- Do NOT [anti-pattern 3]

## Examples

### Good:
[正例]

### Bad:
[反例]

## Failure Modes

If [fail condition], do [recovery].
```

---

## 一句话总结

> **写 description 像写代码，写 instructions 像写决策树，写 resources 像设计 API，迭代 Skill 像养孩子。**

---

打印用法：A4 单面、字号 9pt、排版紧凑可压到一页。蓝皮书电子版默认排版到 2-3 页。
