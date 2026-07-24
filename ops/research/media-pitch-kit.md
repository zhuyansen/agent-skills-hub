# 媒体 Pitch 三连(引信=Zenodo DOI,即刻可发)

> 2026-07-24 换引信:arXiv 被拒(账号级"先发期刊"限制,见 backlink-todo §行动板),凭证改用
> **Zenodo DOI 10.5281/zenodo.21292799**(CC-BY-4.0)+ **HF 数据集**(两链均已验活)。
> 记者不分辨 arXiv 还是 Zenodo——他们要的是**可引用的数据**,不是产品。
> 纪律:一家一封、开头即数字、绝不用 "revolutionary/game-changing";标题别改浮夸。
> 三封可同天发(不同媒体不算群发)。发出后在 backlink-todo §跟踪表各记一行。

---

## 1. The Register(英式毒舌科技媒体,吃"行业裸奔"类故事)

**To**: theregister.com/AboutUs/ 的 tips 邮箱,或搜近期写 AI security 的记者(Thomas Claburn / Jessica Lyons 常写这条线)署名邮箱直发
**Subject**: `85% of AI agent skills nobody has ever security-checked — census of 131,933 (open dataset)`

```
Hi,

Quick data point for your AI security coverage: I security-graded every
open-source AI agent skill and MCP server on GitHub — 131,933 of them.

Three findings your readers would care about:

- 85% of the catalog has no trust signal from any marketplace. Nobody has looked.
- Of the ~20,400 popular enough to grade, 3.3% are UNSAFE or worse — credential
  harvesting, data exfiltration, curl-pipe-sh installers.
- The unsafe rate is ~11x higher in the low-star long tail than among 1,000+ star
  repos. Popularity ranking hides the risk exactly where users have no other signal.

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
**Subject**: `Study: 1 in 31 graded AI agent skills is unsafe; 85% of ecosystem unaudited (open dataset)`

```
Hi,

New empirical result for your supply-chain/AI coverage. I graded the entire
public catalog of AI agent skills and MCP servers (Claude Code, Cursor, Codex
ecosystems) — 131,933 artifacts from GitHub, scanned against 35 red-flag
patterns from the SlowMist agent-security taxonomy.

Key numbers:
- 3.3% of graded artifacts are UNSAFE/REJECT (1 in 31); 8.9% carry at least a caution flag
- Most common flags: sudo usage, background service installs, curl | sh installers,
  credential/env harvesting
- 85% of the full catalog is entirely unaudited — no marketplace, no review, no signal
- Unsafe rate in the sub-100-star long tail is ~11x the rate among 1,000+ star repos

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
**Subject**: `131,933 AI agent skills censused: 85% never security-checked, 1 in 31 graded unsafe`

```
Hi,

Sharing an original dataset your AI/supply-chain readers may find useful.

I run an independent index that security-grades every open-source AI agent
skill and MCP server on GitHub. Full census of 131,933 artifacts:

- 85% have never been security-reviewed by anyone — no marketplace vetting,
  no audit, no trust signal of any kind
- Of those popular enough to grade: 3.3% UNSAFE (credential harvesting, data
  exfiltration, curl|sh installers), 8.9% carry caution flags
- Risk concentrates where users are blindest: the low-star long tail runs
  ~11x the unsafe rate of 1,000+ star repos

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

- [ ] 三封的数字与最新库存一致(131,933 若明显过时,用日报最新总数替换,全文一致)
- [ ] DOI 与 HF 两链点开验活(已验 2026-07-24 ✓)
- [ ] 发送邮箱用 m17551076169@gmail.com,署名 Jason Zhu,不用 noreply 域
- [ ] 发出即在 backlink-todo §跟踪表记三行(状态 pending);7 天无回复不追第二封,换 HARO 路线
- [ ] 任何回复要例子时:从 /analyzer 挑 3 个 UNSAFE 真例(带 file:line 证据),别只给分级标签
