# Launch Playbook — Security Report (117K scan)

Anchor asset: **https://agentskillshub.top/blog/securing-117k-ai-skills/**
CLI: `npx @agentskillshub/cli` · Product: agentskillshub.top · Enterprise: /enterprise/

Verified numbers (reproducible from the live catalog):
117,854 indexed · 20,853 (17.7%) graded (≥5★) · 85.5% safe · 8.4% flagged · 3.1% unsafe/reject (≈1 in 32) ·
unsafe rate 4.1% (5–20★) → 0.4% (1k★+) · red flags: sudo 483 / service install 152 / curl|sh 99 /
agent config theft 87 / tunnel 66 / eval 52 / agent memory theft 23 / backdoor 11 ·
deeper semantic study: 26.1% (Liu et al. 2026, arXiv:2601.10338).

Discipline: vary anchor text + descriptions; one channel/sub per day; lead with the finding, not the product;
links in body-end or comment on strict subs; never cross-post identical text.

### Messaging guardrails (aligned with the new blog)
The report now frames the data honestly — keep the launch copy matched so nothing contradicts the post:
- **3% is a FLOOR, not "the vuln rate."** Always pair it with the cited ceiling: 26.1% (Liu et al. 2026, arXiv:2601.10338). Rule-based catches patterns, not intent — that's *why* it's a floor.
- **The deeper layers are ROADMAP, not live.** Semantic LLM review = built, being enabled. SkillSpector deep audit (AST/taint/YARA) = in development, on-demand/enterprise. If asked "do you deep-scan everything?" → "No. Rule-based across the catalog today; semantic + AST/taint deep audit run per-skill on request, and are rolling out." NEVER imply the 117K got deep-scanned.
- **Every number is sourced.** The old unsourced "43%" is retired everywhere — don't reintroduce it.
- **The one-line story**: "not the deepest look at one skill — the broadest honest look at all of them."

Deeper-layers talking point (for HN/Reddit replies + the PH pitch, framed as roadmap):
> Layer 1 (rule-based) is what graded the catalog. A semantic LLM pass and a per-skill AST/taint/YARA deep audit (NVIDIA SkillSpector) are the on-demand/enterprise layers — coming soon, run per-skill not catalog-wide. That's exactly why today's 3% is a floor.

---

## 1. Hacker News  🔴 you post

- Best window: **Tue or Wed, 7–9am PT** (= Beijing 22:00–24:00). Avoid Mon, weekends.
- Title (factual, no marketing): `We security-graded 117,854 AI agent skills; 1 in 32 is unsafe`
- URL: the blog post (not the homepage).
- Immediately post the author comment below (HN rewards methodology + disclosure).
- [ ] Posted, with first comment
- [ ] Stayed in thread for the first 2h, replied to every comment

**First comment:**
> Author here. I run an open directory of AI agent skills / MCP servers, and I kept hitting the same problem: discovery is trivial, but you can't tell if the thing you found is safe to run against your shell and your agent's config. So I scanned the whole catalog with a rule-based engine (modeled on SlowMist's 11 red-flag categories) and wrote up what it found.
>
> The honest headline isn't the unsafe rate, it's the coverage: of 117,854 indexed skills, only 17.7% are popular enough that anyone has graded them. Among those graded, ~3% are outright unsafe and 8.4% carry some concern. The unsafe rate drops from 4.1% in the 5-20 star range to 0.4% above 1,000 stars, so the risk really lives in the long tail you'd hit from a niche search.
>
> The finding I didn't expect: agent-native red flags. 87 skills in my flagged sample read your agent's config files, 23 read its memory. That's an attack surface that only exists because you're running an agent, and traditional scanners don't look for it.
>
> Caveats a skeptic should know: rule-based catches patterns, not semantics, so my 3% is a floor. Academic deep-analysis (Liu et al. 2026, arXiv:2601.10338) puts the rate at 26.1%. Every grade is reproducible from the live catalog or via `npx @agentskillshub/cli audit owner/repo`. Tear it apart.

---

## 2. X / Twitter thread (中文)  🔴 you post

- [ ] Posted from @GoSailGlobal

**1/6**
你装一个 AI agent skill 或 MCP server 之前,怎么知道它安不安全?

大多数人不知道。我扫了全部 117,854 个,数据有点吓人。🧵

**2/6**
最扎心的不是"有多少不安全",是"有多少根本没人审过":

只有 17.7% 火到值得评级。
剩下约 9.7 万个 —— 没人看过。

**3/6**
被评级的里面:
· 85.5% 安全
· 8.4% 有安全顾虑
· 每 32 个就有 1 个直接不安全

而且和其它结果混在同一个搜索列表里。

**4/6**
风险不是均匀的。按 star 分:

5–20★ → 4.1% 不安全
1,000★+ → 0.4%

你听说过的那个没事。危险的是你为冷门需求随手搜到的 7 星仓库。

**5/6**
我没料到的发现:

87 个被标记的 skill 会读你 agent 的配置文件,23 个读它的记忆。

这是个新攻击面 —— 不是你的服务器,是你 agent 的大脑。

**6/6**
全部数据可复核,方法论 + 诚实的免责声明:
🔗 agentskillshub.top/blog/securing-117k-ai-skills/

或装之前先查任意 skill:
`npx @agentskillshub/cli audit owner/repo`

**可选回复推文(自评论,补可信度 + 路线图,防"才 3%?"质疑):**
> 补一句诚实的:这 3% 是规则扫描的**下限** —— 只查模式不查意图。学术深度分析(Liu et al. 2026, arXiv:2601.10338)给的是 26.1%。我们正在上语义复核 + 单 skill 的 AST/污点深扫(按需),所以真实问题只会比 3% 大,不会更小。

---

## 3. Product Hunt  🔴 you post — PIVOT

PH explicitly does NOT feature "Directories or lists" (their stated policy). So do NOT launch the
directory. Two options:

- **Option A (recommended): launch the CLI as a developer tool.** "Audit any AI agent skill before you
  install, from your terminal." The CLI is a tool, not a directory — PH features tools. Directory is just
  the data behind it; the security report is social proof.
- **Option B: skip PH**, put the energy into HN + Reddit + GitHub.

If Option A — tagline: `Check if an AI agent skill is safe before you install it`
Description: AgentSkillsHub CLI security-grades and quality-scores open-source AI agent skills & MCP
servers, and puts the trust signal before the install. `npx @agentskillshub/cli search/audit/install` —
zero backend, runs locally. Paired with a security scan of 117K skills.
- [ ] Decided A or B
- [ ] (if A) Launched the CLI, not the directory

---

## 4. Reddit  🔴 you post — one sub per day, per-sub rules

**Rule of thumb everywhere:** Reddit's sitewide guideline is the ~9:1 ratio (9 genuine contributions for
every 1 self-promo). Participate first; new accounts dropping links get auto-removed.

### r/netsec — strictest. Original research only, NO product promotion in title/body. Link to the writeup is fine if it's substantive technical content. No CLI plug up top.
Title: `Static analysis of 117k open-source AI agent skills: 3% trip unsafe red flags, plus an agent-native class (config/memory exfiltration)`
Body:
> Ran a rule-based static scanner (regex/AST over README + code, SlowMist's 11 red-flag categories) across 117,854 open-source AI agent skills / MCP servers. Findings, because the agent-native part is undercovered:
> - Only 17.7% (20,853) cross 5★, the grading threshold; the rest is unanalyzed.
> - Graded: 8.4% trip ≥1 flag, 3.1% unsafe/reject. Unsafe rate 4.1% (5–20★) → 0.4% (1k★+).
> - Top flags (n=1000): sudo 483, service install 152, curl|sh 99, **agent config theft 87**, tunnel 66, eval 52, **agent memory theft 23**, backdoor 11.
> - Agent-native flags = skills reading ~/.claude, MCP config, agent memory. Classic static/AV tools don't look for these.
> Limitation: rule-based, so a floor; semantic study (Liu et al. 2026, arXiv:2601.10338) puts it at 26.1%. Methodology + reproducible numbers: agentskillshub.top/blog/securing-117k-ai-skills/
> Interested in how others handle false positives on curl|sh inside fenced code blocks.

### r/ClaudeAI — friendly to Claude/MCP tooling; CLI mention OK; lead with the relatable finding.
Title: `I scanned every Claude/MCP skill I could find for security red flags — some quietly read your ~/.claude config and agent memory`
Body:
> If you install MCP servers and Claude Code skills, this might help. I security-graded 117k agent skills with a rule-based scanner. The surprise: 87 flagged skills in my sample read your agent's config, 23 read its memory — the agent equivalent of identity theft.
> TL;DR: only ~18% of the catalog is popular enough to have been graded; among graded, 1 in 32 is unsafe; risk is heavily in the low-star long tail.
> Check any repo before installing: `npx @agentskillshub/cli audit owner/repo`. Full data + caveats: agentskillshub.top/blog/securing-117k-ai-skills/
> What config/memory paths do you consider sensitive? Building out the detection list.

### r/LocalLLaMA — large, anti-low-effort-promo; data-led, contribute value.
Title: `Only 17.7% of indexed AI agent skills have ever been security-graded — here's what scanning all 117k turned up`
Body:
> Static security scan over 117,854 open-source agent skills / MCP servers:
> - 17.7% clear 5★ (grading bar); ~97k unaudited.
> - Graded: 85.5% safe, 8.4% flagged, 3.1% unsafe.
> - Unsafe rate: 4.1% (5–20★) → 0.4% (1k★+). Popular ones fine; niche long-tail repo from a search is the risk.
> - New flag class: skills reading agent config (87) and memory (23) files.
> Conservative method (rule-based = floor; semantic study says 26%). Reproducible. Writeup: agentskillshub.top/blog/securing-117k-ai-skills/

### r/mcp — small, exact audience; MCP-framed.
Title: `I security-graded every MCP server I could index (8,970 of them). 3.4% trip unsafe red flags.`
Body: reuse r/ClaudeAI body, swap "Claude/MCP skills" → "MCP servers", lead with the mcp-server category stat (3.4% unsafe, n=8,970).

### r/AI_Agents — agent builders; emphasize the agent-native attack surface.
Title: `The new agent attack surface: skills that read your agent's config and memory files`
Body: reuse r/ClaudeAI body, lead harder on agent config/memory theft.

Posting order (1/day): r/ClaudeAI → r/mcp → r/LocalLLaMA → r/AI_Agents → r/netsec (last; needs the most-polished, product-free version).

---

## 5. GitHub plan  (🟢 = I draft, 🔴 = you publish)

### A. awesome-list PRs — highest ROI, permanent, dev-targeted (1–2 per day, not all at once)
- [ ] 🔴 `punkpeye/awesome-mcp-servers` → Resources/Community section
- [ ] 🔴 `wong2/awesome-mcp-servers` → Resources
- [ ] 🔴 `modelcontextprotocol/servers` (official) → Resources
- [ ] 🔴 `hesreallyhim/awesome-claude-code` → Tooling/Resources
- [ ] 🔴 `e2b-dev/awesome-ai-agents` → Resources/Tools
- [ ] 🔴 `Shubhamsaboo/awesome-llm-apps` → Resources
- For each: read CONTRIBUTING.md, follow format exactly, vary the description (entries drafted below).
- PR title pattern: `Add Agent Skills Hub to Resources` ; PR body: one line "adds a community directory + CLI that security-grades MCP servers/agent skills."

Entries (vary per list):
```
punkpeye:   - [Agent Skills Hub](https://agentskillshub.top) - Searchable directory of 117K+ MCP servers and agent skills, each security-graded and quality-scored — audit any server before you install, from the terminal.
wong2:      - [Agent Skills Hub](https://agentskillshub.top) - Open directory of MCP servers with security grades and quality scores, plus a CLI to search and audit any server.
official:   - [Agent Skills Hub](https://agentskillshub.top) - Community directory that indexes and security-grades MCP servers across GitHub, with a free CLI to vet them before installing.
claude:     - [Agent Skills Hub](https://agentskillshub.top) - Directory of 17K+ Claude Code skills, security-graded and quality-scored; vet skills with `npx @agentskillshub/cli`.
e2b:        - [Agent Skills Hub](https://agentskillshub.top) - Trust layer for AI agent skills and MCP servers: 117K indexed, security-graded, auditable from the CLI before deployment.
llm-apps:   - [Agent Skills Hub](https://agentskillshub.top) - Discover and security-audit open-source agent skills and MCP servers before adding them to your LLM app.
```

### B. Badge growth loop — distributed backlinks (mostly built)
- [x] Badge upgraded to security grade (SAFE/CAUTION/…); one-click copy on each skill page (shipped 2fab373)
- [ ] 🔴 After next deploy, sanity-check a live badge: https://agentskillshub.top/badge/browser-use/browser-use.svg
- [ ] 🔴 Run `ops/badge-outreach.sh` to invite authors of high-grade skills to embed the badge
- [ ] 🟢 (optional) add a "copy badge" CTA to the weekly newsletter

### C. CLI / main repo as an entry point
- [ ] 🔴 CLI repo: add topics (`mcp`, `claude-code`, `ai-agents`, `security`, `cli`), a one-line description, pin it
- [ ] 🔴 Link the security report from the CLI README and the main repo README
- [ ] 🔴 Main repo: add topics + a short "what is this" section so HN/Reddit visitors can star easily

### D. Upstream contribution (credibility + backlink from a 300★ security repo)
- [ ] 🔴 Open a PR/issue on `slowmist/slowmist-agent-security` sharing detection patterns or the dataset findings
- [ ] 🔴 Link back to the report as the data source

---

## Sequencing (so nothing reads as spam)
1. Now: GitHub C (repo polish) — low-risk, anytime.
2. This week: 1–2 awesome-list PRs/day (A).
3. Tue/Wed 7–9am PT: HN.
4. Following days: Reddit, one sub/day, in the order above.
5. After badges redeploy: badge outreach (B) + SlowMist PR (D).
6. PH: decide A (launch the CLI) or skip — not before HN/Reddit have run.
