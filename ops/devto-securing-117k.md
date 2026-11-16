---
title: We security-graded 117,854 AI agent skills. Here's what we found.
published: true
description: Only 17.7% of the catalog is popular enough to be graded, 1 in 32 graded skills is unsafe, and the risk lives in the long tail — plus a new agent-native attack surface.
tags: ai, security, opensource, mcp
canonical_url: https://agentskillshub.top/blog/securing-117k-ai-skills/
---

> **The uncomfortable part isn't the skills that are unsafe. It's how few have been checked at all.**

Installing an AI agent skill or MCP server means handing untrusted code your shell, your environment variables, and increasingly your agent's own config and memory. Discovery is easy — there are tens of thousands to pick from. Knowing whether the one you found is safe to run is not.

So we scanned the whole catalog. Here's the honest picture.

> 📄 This is a cross-post. Canonical version (with charts): **[agentskillshub.top/blog/securing-117k-ai-skills](https://agentskillshub.top/blog/securing-117k-ai-skills/)**

## How we scanned

A rule-based scanner, modeled on [SlowMist's Agent Security Framework](https://github.com/slowmist/slowmist-agent-security) and its 11 red-flag categories. It runs static checks over each skill's README and code, looking for concrete patterns: outbound data exfiltration (`curl -d $(...)`), credential harvesting (`env | grep -i token`), reading `.env` / `.ssh` / `.aws`, `curl | sh` install scripts, privilege escalation, persistence, and secret-exfil combos. Each skill gets a grade — **safe / caution / unsafe / reject** — plus the specific flags it tripped. Skills with no README or too new to fetch stay **unknown**.

This is deliberately a *first* layer: it catches patterns, not intent. At 117K scale, the pattern layer is what makes the catalog auditable at all.

## Finding 1 — 82% of the catalog has never been graded

Of **117,854** indexed skills, only **20,853 (17.7%)** clear 5 stars — the threshold where a skill is popular enough to be worth grading. The other **~97,000 are effectively unaudited.**

"We have 117K skills" is not a feature. The number that matters is how many you can actually trust, and for the long tail the honest answer is: nobody has looked.

## Finding 2 — Among graded skills, 1 in 32 is unsafe or worse

| Grade | Share |
|---|---|
| 🟢 safe | 85.5% |
| 🟡 caution | 5.3% |
| 🔴 unsafe | 3.0% |
| ⛔ reject | 0.1% |
| ⚪ unknown | 6.1% |

**8.4% carry a security concern. 3.1% — about 1 in 32 — are unsafe or reject.** At this catalog's size that's ~650 graded skills you genuinely should not run blind, sitting in the same search results as everything else.

## Finding 3 — Popularity predicts safety. The risk lives in the long tail.

| Stars | Unsafe / reject |
|---|---|
| 5–20★ | 4.1% |
| 20–100★ | 3.7% |
| 100–1,000★ | 0.9% |
| 1,000★+ | 0.4% |

The skill you've *heard of* is almost certainly fine. The danger is the obscure 7-star repo you'd grab from a search for a niche task — exactly the moment a directory is supposed to help, and usually doesn't.

## Finding 4 — The red flags include a new, agent-native attack surface

Most common flags among a sample of 1,000 flagged skills:

| Flag | Count |
|---|---|
| sudo usage | 483 |
| background service install | 152 |
| curl \| shell | 99 |
| **agent config theft** | **87** |
| tunnel service | 66 |
| eval() | 52 |
| sensitive env vars | 34 |
| **agent memory theft** | **23** |
| backdoor install | 11 |

The classic shell risks dominate. But look at `agent config theft` (87) and `agent memory theft` (23): **skills that read your agent's configuration and memory files.** That's not a server exploit — it's a new attack surface that only exists because you're running an agent. Your Claude/MCP config, your stored context, your credentials-by-proxy. The threat model moved, and most directories haven't noticed.

## What to do about it

Check the trust signal *before* you install, from where you already work:

```bash
npx @agentskillshub/cli search "postgres mcp" --safe
npx @agentskillshub/cli audit owner/repo
```

Every result carries its grade and the specific flags it tripped. `--safe` hides anything unaudited or worse.

## The honest caveats (because that's the whole point)

- **Our 3% is a floor, not a ceiling.** Academic deep-analysis ([Liu et al., 2026, arXiv:2601.10338](https://arxiv.org/abs/2601.10338)) puts the agent-skill vulnerability rate at 26.1%, because they analyze semantics, not just patterns. Our rule-based first pass deliberately under-claims. Read 3% as the lower bound of a bigger problem.
- **⚪ unknown is not "probably fine."** It means *no one has checked.* 97K of the catalog is unknown. We label it gray and don't dress it up.
- **All numbers are reproducible.** Every grade is visible on the site and via the CLI. Re-derive them yourself.

A trust layer that only told you the good news wouldn't be one. The most useful thing we can say about 97,000 skills is that we don't yet know — and we'll tell you that to your face.

---

*Full writeup with charts: [We security-graded 117,854 AI agent skills](https://agentskillshub.top/blog/securing-117k-ai-skills/). Check any skill before you install: `npx @agentskillshub/cli audit owner/repo`.*
