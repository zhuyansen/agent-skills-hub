# 媒体 Pitch 三连(引信=Zenodo DOI,即刻可发)

> **2026-08-10 复核**:全文数字已刷新到当日库存(160,265 / 85.4% 未评级 / 1-in-32 UNSAFE /
> 8.6% 带风险标记),三条凭证链重新验活(DOI 200 · HF 200 · /analyzer/ 200)。
> 两处**加强**而非改写:①「11x 长尾风险」升级为**四档单调梯度**(0.35% → 0.71% → 2.54%
> → 4.10%),单调性比单一倍数更难被质疑;②新增**110 个已从 GitHub 消失、但安装指令仍在
> 各处流传**的数字——这是三封里唯一没人报道过的角度,也最像新闻。
>
> 2026-07-24 换引信:arXiv 被拒(账号级"先发期刊"限制,见 backlink-todo §行动板),凭证改用
> **Zenodo DOI 10.5281/zenodo.21292799**(CC-BY-4.0)+ **HF 数据集**(两链均已验活)。
> 记者不分辨 arXiv 还是 Zenodo——他们要的是**可引用的数据**,不是产品。
> 纪律:一家一封、开头即数字、绝不用 "revolutionary/game-changing";标题别改浮夸。
> 三封可同天发(不同媒体不算群发)。发出后在 backlink-todo §跟踪表各记一行。

---

## 1. The Register(英式毒舌科技媒体,吃"行业裸奔"类故事)

**To**: theregister.com/AboutUs/ 的 tips 邮箱,或搜近期写 AI security 的记者(Thomas Claburn / Jessica Lyons 常写这条线)署名邮箱直发
**Subject**: `85% of AI agent skills nobody has ever security-checked — census of 160,265 (open dataset)`

```
Hi,

Quick data point for your AI security coverage: I security-graded every
open-source AI agent skill and MCP server on GitHub — 160,265 of them.

Three findings your readers would care about:

- 85.4% of the catalog has no trust signal from any marketplace — 136,892 artifacts nobody has ever looked at.
- Of the 23,373 popular enough to grade, 3.1% are UNSAFE or worse (1 in 32) —
  credential harvesting, data exfiltration, curl-pipe-sh installers.
- The unsafe rate climbs monotonically as stars fall: 0.35% at 1,000+ stars,
  0.71% at 200-999, 2.54% at 50-199, 4.10% below 50 — a 12x spread. Popularity
  ranking hides the risk exactly where users have no other signal.

Installing one of these means running a stranger's code with your AI agent's full
permissions — often including its credentials.

Dataset + methodology (DOI, CC-BY-4.0): https://doi.org/10.5281/zenodo.21292799
Also on Hugging Face: https://huggingface.co/datasets/jasonzhuyansen/agent-skills-security-grades
Live index: https://agentskillshub.top

Happy to provide quotes, the methodology's limitations (it's rule-based, first-layer),
or specific flagged examples. I run the index independently.

Jason Zhu
agentskillshub.top
```

## 2. BleepingComputer(安全实操向,吃"具体威胁+怎么防")

**To**: tips@bleepingcomputer.com
**Subject**: `Study: 1 in 32 graded AI agent skills is unsafe; 85% of ecosystem unaudited (open dataset)`

```
Hi,

New empirical result for your supply-chain/AI coverage. I graded the entire
public catalog of AI agent skills and MCP servers (Claude Code, Cursor, Codex
ecosystems) — 160,265 artifacts from GitHub, scanned against 35 red-flag
patterns from the SlowMist agent-security taxonomy.

Key numbers:
- 3.1% of graded artifacts are UNSAFE/REJECT (1 in 32); 8.6% carry at least a caution flag
- Most common flags: sudo usage, background service installs, curl | sh installers,
  credential/env harvesting
- 85.4% of the full catalog is entirely unaudited — no marketplace, no review, no signal
- Unsafe rate rises monotonically as stars fall: 0.35% (1,000+) -> 4.10% (<50), a 12x spread
- 110 graded artifacts have since been DELETED from GitHub while install instructions
  for them remain live in READMEs and blog posts. Nothing in the ecosystem tracks this.

Practical angle for readers: before installing any agent skill, grep it for
process.env reads and shell installers, check last-commit recency, and treat
"popular" as a weak proxy for "safe" — our data says it isn't one.

Dataset + methodology (DOI, CC-BY-4.0): https://doi.org/10.5281/zenodo.21292799
Also on Hugging Face: https://huggingface.co/datasets/jasonzhuyansen/agent-skills-security-grades
Free checker (paste any repo URL): https://agentskillshub.top/analyzer

Can share flagged real-world examples with evidence lines, or quotes on what
teams should check before deploying. Independent project, no vendor affiliation.

Jason Zhu
agentskillshub.top
```

## 3. The Hacker News — thehackernews.com(流量最大的安全媒体,吃"数字+威胁面")

**To**: admin@thehackernews.com(官方 tips 口)
**Subject**: `160,265 AI agent skills censused: 85% never security-checked, 1 in 32 graded unsafe`

```
Hi,

Sharing an original dataset your AI/supply-chain readers may find useful.

I run an independent index that security-grades every open-source AI agent
skill and MCP server on GitHub. Full census of 160,265 artifacts:

- 85.4% have never been security-reviewed by anyone — no marketplace vetting,
  no audit, no trust signal of any kind
- Of those popular enough to grade: 3.1% UNSAFE (credential harvesting, data
  exfiltration, curl|sh installers), 8.6% carry caution flags
- Risk concentrates where users are blindest: unsafe rate goes 0.35% -> 0.71%
  -> 2.54% -> 4.10% as you walk down the star tiers, a clean 12x gradient

Why it matters: agent skills execute with the full permissions of the AI
agent that loads them — API keys, file system, shell. It's npm-2016 all over
again, but the packages can read your agent's credentials by design.

Open dataset (DOI, CC-BY-4.0): https://doi.org/10.5281/zenodo.21292799
Hugging Face mirror: https://huggingface.co/datasets/jasonzhuyansen/agent-skills-security-grades
Live index + free repo checker: https://agentskillshub.top

Happy to provide named examples with evidence, methodology details (rule-based
first-layer scan, limitations included), or comment. Independent, no vendor ties.

Jason Zhu
agentskillshub.top
```

---

## 发送清单(发前逐项过)

- [x] 三封的数字与最新库存一致(2026-08-10 刷新至 160,265,全文一致)
- [x] DOI 与 HF 两链点开验活(2026-08-10 复验均 200 ✓)
- [ ] **发送当天**再核一次库存总数——数字每天在动,记者若自己去查发现对不上,
      整封信的可信度一次性归零。核对法:`/analyzer/` 页脚的目录总数,或问我
- [ ] 发送邮箱用 m17551076169@gmail.com,署名 Jason Zhu,不用 noreply 域
- [ ] 发出即在 backlink-todo §跟踪表记三行(状态 pending);7 天无回复不追第二封,换 HARO 路线
- [ ] 任何回复要例子时:从 /analyzer 挑 3 个 UNSAFE 真例(带 file:line 证据),别只给分级标签
