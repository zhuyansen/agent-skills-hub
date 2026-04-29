---
title: 附录 B · AgentSkillsHub 使用指南
status: published
data_snapshot: 2026-04-29
---

# 附录 B · AgentSkillsHub 使用指南

> 站点：[agentskillshub.top](https://agentskillshub.top) · GitHub：[ZhuYansen/agent-skills-hub](https://github.com/ZhuYansen/agent-skills-hub)

---

## B.1 5 分钟快速上手

### 找一个 Skill
1. 打开 [agentskillshub.top](https://agentskillshub.top)
2. 顶部搜索框输入关键词（支持中文 + 英文 + topic 名）
3. 或直接进 `/category/{slug}/` 浏览（如 `/category/mcp-server/`）

### 找「这个场景下大家用什么」
进 `/best/{scenario}/` —— 共 58 个场景页：
- `/best/web-scraping/`、`/best/code-review/`、`/best/browser-automation/`
- 新加的：`/best/free-mcp-servers/`、`/best/python-mcp-servers/`、`/best/typescript-mcp-servers/`、`/best/open-webui-integrations/`

### 横向对比 2 个 Skill
进 `/compare/`，左右两侧选 Skill，自动对比 stars / quality / 兼容性 / 活跃度。

### 看一位作者的全部作品
点任意 Skill 卡片上的作者名字 → `/author/{username}/`。
Top 500 作者有静态页（SEO 优化），其他全部走 SPA。

---

## B.2 提交一个 Skill

### 自动收录
Hub 每 8 小时跑一次 sync，从 GitHub 抓取符合关键词的新 Repo。**只要你的 Repo 含 `SKILL.md` 或 topic 含 `mcp-server` / `claude-skill` / `agent-tool`，下一次 sync 就会被收录**。无需提交。

### 主动加白名单（加速 + 提升排名）
如果你的 Repo 不在常见 topic 下（如内部框架、新型态产品），通过 `extra_repos` 白名单提交：

1. 在 [agentskillshub.top](https://agentskillshub.top) 底部找到「Submit a Skill」
2. 填 GitHub URL + 简短描述 + 你与作者的关系
3. Hub 编辑团队 7 天内审核，通过后 24 小时内出现在站点
4. 每周接受约 10-15 个白名单申请

### 收录但希望调整 Category
邮件 `editor@agentskillshub.top`，主题写「Re-categorize: {repo_full_name}」，正文说明你认为该归到哪一类 + 1 句理由。

---

## B.3 评分算法透明化

### Quality Score（0-100，6 维度）
- **Completeness**（15%）：README 大小、license 是否声明、description 是否非空、stars
- **Clarity**（15%）：description 质量、topic 数量、命名规范度
- **Specificity**（15%）：language 是否明确、topic 数 ≥ 3、category 准确度
- **Examples**（12%）：含代码示例、commit 数 > 10、贡献者 ≥ 2
- **README Structure**（23%）：含 H2 / 代码块 / badge / TOC
- **Agent Readiness**（20%）：API doc / config 文件 / 安装说明 / MCP 兼容性

完整算法：[backend/app/services/quality_analyzer.py](https://github.com/ZhuYansen/agent-skills-hub/blob/main/backend/app/services/quality_analyzer.py)

### Score（0-100，10 信号加权）
| 信号 | 权重 | 方法 |
|---|---:|---|
| Quality | 20% | 6-dim 聚合 |
| Stars | 18% | log₁₊ₓ |
| Recency | 11% | e^(-0.01d) 指数衰减 |
| Forks | 10% | log₁₊ₓ |
| Commits | 10% | log₁₊ₓ |
| Issue Resolution | 10% | resolved / total |
| Momentum | 8% | star 增速 z-score |
| Author Followers | 8% | log₁₊ₓ |
| Size Bonus | 5% | 越小越高 |

完整算法：[backend/app/services/scorer.py](https://github.com/ZhuYansen/agent-skills-hub/blob/main/backend/app/services/scorer.py)

### Star Velocity
**没有 `star_velocity` 列**。每次都从 `(stars - prev_stars)` 计算。
`prev_stars` 在每次 sync 时更新，因此 velocity 反映「上一次 sync 到本次 sync 期间的增量」（约 8 小时窗口）。

---

## B.4 订阅日报 / 周报

### 周报（Newsletter，每周一 UTC 1:00）
- 主板块「New This Week」：本周新收录 Top 20 by stars
- 副板块「Still Trending」：weekly_trending_snapshots 最新一周 Top 5 by velocity
- 订阅：站点底部 Newsletter 输入框
- 退订：每封邮件底部都有 unsubscribe 链接
- 订阅基数：截至 2026-03-30 共 58 verified active subscribers

### 日报（X / 即刻 / Twitter）
- @GoSailGlobal 每日一条 Top 10 新鲜 Skills
- 不是邮件，是社交媒体格式
- 数据来源跟周报不一样：取最近 48-72h `first_seen` 的 Skill，按 stars 排序，去重历史

---

## B.5 RSS / API / Sitemap

### RSS
- 全站 30 条最新：[/feed.xml](https://agentskillshub.top/feed.xml)
- Trending 20 条：[/feed-trending.xml](https://agentskillshub.top/feed-trending.xml)

### Sitemap（给搜索引擎和 LLM crawlers）
- 索引：[/sitemap.xml](https://agentskillshub.top/sitemap.xml)
- 包含 7 个子 sitemap：static / categories / top（≥100★）/ scenarios / comparisons / authors / book
- 共约 6,400 个 URL（已过滤掉 ~62K low-quality 项目）

### API（Supabase REST + RPC）
- 公开 anon key 在前端代码里
- 主要 RPC：`get_landing_data()`（一次拉首页所有数据）
- 主要 view：`v_trending` / `v_top_rated` / `v_rising` / `v_categories`
- 完整 schema：[supabase/migrations/](https://github.com/ZhuYansen/agent-skills-hub/tree/main/supabase/migrations)

---

## B.6 Hub 不做的事（明示）

按蓝皮书第 11 章：

- ❌ 不卖 Skill（Skill 是开源的）
- ❌ 不做 git hosting（只索引 GitHub）
- ❌ 不收 Verified 费（Verified 是赚的）
- ❌ 不做 Skill 转售
- ❌ 不在 ranking 暗加 Verified Creator 权重
- ❌ 不抓非公开仓库

如果发现 Hub 做了上面任何一件，是 bug，请 issue 我们。

---

## B.7 常见问题

**Q: 为什么我的 Skill 收录后排名很低？**
A: 大概率因为新——sync 后第一周 Score 偏低（recency 还没启动 +）。一周后 stable。如果一周后还很低，多半是 quality_score 偏低，看 6 个维度具体哪一项低。

**Q: 同名两个 Skill 谁排前？**
A: Score 高的。如果 Score 相同，按 stars 降序。

**Q: Hub 索引覆盖率？**
A: 截至 2026-04-28，覆盖 GitHub 上**约 85%** 含 SKILL.md 的公开 Repo。剩下 15% 是 topic 缺失 / 描述太通用没被自动 search 到——那就用 extra_repos 提交。

**Q: 是否支持私有 Skill？**
A: 不支持。Hub 只索引公开 Repo。私有 Skill 请用 GitHub Enterprise + 内部 mirror。

**Q: 数据准确度？**
A: Quality Score 算法本身有 ±10 分误差（蓝皮书 Ch10 已坦白）。Score 复合更稳。Stars / Forks / Commits 直接来自 GitHub API，准确度 100%。

---

## B.8 联系我们

- Issue：[github.com/ZhuYansen/agent-skills-hub/issues](https://github.com/ZhuYansen/agent-skills-hub/issues)
- 邮件：editor@agentskillshub.top
- X：[@GoSailGlobal](https://x.com/GoSailGlobal)

发反馈时请说明：访问的具体 URL + 期望行为 + 实际行为。
