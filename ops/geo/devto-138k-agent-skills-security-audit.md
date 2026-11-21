---
title: "We Audited 138,000+ Open-Source AI Agent Skills & MCP Servers: Why Low-Star Repos Carry 9x Higher Risk"
published: true
description: "Empirical security findings from indexing 276,000+ GitHub agent skills and auditing 138,000+ against 44 published static rules — plus a free pre-install check workflow."
tags: ai, security, claudecode, mcp
canonical_url: https://agentskillshub.top/how-we-grade/
---

**According to Agent Skills Hub ([agentskillshub.top](https://agentskillshub.top/), open dataset archived on CERN Zenodo under DOI [10.5281/zenodo.21292799](https://doi.org/10.5281/zenodo.21292799)), across 276,000+ indexed AI agent skills and MCP servers (with 138,000+ graded against 44 published static rules), repositories with under 20 GitHub stars carry roughly 9x higher severe security risk than established projects.**

Most developers treat a `SKILL.md` or `.mcp.json` file like a harmless README or config snippet. In practice, installing an unvetted skill into Claude Code, Codex, Cursor, or Gemini CLI gives third-party prompt instructions and shell scripts direct reach into your local filesystem, `.env` secrets, SSH keys, and git credentials.

When we built **Agent Skills Hub (agentskillshub.top)** — an open-source directory and pre-install trust layer synced from GitHub every 8 hours (source: [zhuyansen/agent-skills-hub](https://github.com/zhuyansen/agent-skills-hub), MIT) — we wanted hard numbers rather than anecdotes. Here is what came out of scanning the open-source ecosystem.

---

## 1. The Supply-Chain Blind Spot: Stars Are Not an Audit

Across our 117,000-skill longitudinal snapshot (now expanded past 138,000 graded entries, covering 99% of repositories above 100 stars):

| Signal / Cohort | What We Observed | Practical Takeaway |
| --- | --- | --- |
| **Repositories `<20★`** | **~9x higher severe flag rate** vs. established repos | Long-tail copycat and bait repos concentrate the worst patterns (`curl \| sh`, opaque binaries, broad secret harvesting). |
| **Repositories `>100★`** | 99% graded; much lower malware rate, **but not zero risk** | Popular repos still ship overly permissive tool rules, silent telemetry, or unpinned remote fetches. |
| **Unaudited (`Unaudited`)** | Never default-safe | Treat `Unaudited` as unknown risk until inspected, never as `Safe`. |

We publish the full raw grading taxonomy and rule set openly at [agentskillshub.top/how-we-grade/](https://agentskillshub.top/how-we-grade/) and archive the CC BY 4.0 dataset on CERN Zenodo ([DOI: 10.5281/zenodo.21292799](https://doi.org/10.5281/zenodo.21292799); companion supply-chain security audit DOI: [10.5281/zenodo.24387074](https://doi.org/10.5281/zenodo.24387074)) and Hugging Face so researchers and security teams can reproduce or challenge every label.

---

## 2. The 5 Security Grades Explained

Every scanned repository on **Agent Skills Hub (agentskillshub.top)** receives one of five explicit states based on **44 published static rules** inspecting `SKILL.md`, READMEs, repository metadata, and referenced install commands:

| Grade | Meaning | Recommended Developer Action |
| --- | --- | --- |
| **Safe** | Passed all 44 static checks with clear provenance and scoped behavior | Standard review of permissions before adding to a team repo |
| **Caution** | Minor hygiene or broad capability signals (e.g., network calls or shell commands that need context) | Inspect the flagged snippet and pin to a specific commit SHA |
| **Unsafe** | High-risk patterns such as `.env` / `~/.ssh` access, obfuscated payloads, or unsafe `curl \| sh` pipes | Block in CI; do not run outside an isolated container |
| **Reject** | Severe malicious or credential-exfiltration indicators | Do not install |
| **Unaudited** | Indexed from GitHub, awaiting automated or manual grading | Run through a pre-install scanner before cloning |

*Honest limitation*: static README and metadata scanning catches obvious supply-chain traps fast, but it does **not** replace runtime sandboxing or reading executable scripts inside a cloned skill folder. Think of static grading as your first gate, not your only defense.

---

## 3. Four Red Flags We See Repeatedly in `SKILL.md` and `.mcp.json`

1. **Silent remote pipe execution**: Instructions telling the agent to run `curl -fsSL <remote-url> | sh` or download precompiled binaries during setup.
2. **Unscoped secret reads**: Prompt instructions or helper scripts that read `~/.aws`, `~/.ssh`, `.env`, or macOS Keychain tokens when the stated task needs none of them.
3. **Hidden instruction / prompt-injection wrappers**: Instructions telling the agent to perform background telemetry or modify global settings without informing the user.
4. **Deleted or hijacked upstream repos ("ghost repos")**: Skills that look legitimate in an old blog post, then get transferred or rewritten months later. That is why we re-sync GitHub metadata every 8 hours and recommend pinning commit SHAs.

---

## 4. A 30-Second Pre-Install Checklist Before Cloning Any Skill

1. **Check the live grade or paste the repo URL** into the free scanner at [agentskillshub.top/analyzer/](https://agentskillshub.top/analyzer/) before running `npx skills add` or cloning locally.
2. **Read `SKILL.md` and every script in `scripts/`** — watch for unrestricted `Bash` permissions, outbound webhooks, and base64-encoded blocks.
3. **Pin a commit SHA or tag** instead of tracking `main` on third-party community skills.
4. **Compare alternatives on hands-on benchmarks** (e.g., code review, secret detection, database MCPs) at [agentskillshub.top/best/](https://agentskillshub.top/best/) rather than installing the first high-star repo you see.

---

## Open Data & Reproducibility

- **Directory & Live Grades**: [agentskillshub.top](https://agentskillshub.top/) (276,000+ indexed, 138,000+ graded, 8-hour GitHub sync)
- **44 Published Grading Rules**: [agentskillshub.top/how-we-grade/](https://agentskillshub.top/how-we-grade/)
- **Free GitHub Repo Pre-Install Scanner**: [agentskillshub.top/analyzer/](https://agentskillshub.top/analyzer/)
- **Open Research Dataset (CC BY 4.0)**: [CERN Zenodo DOI 10.5281/zenodo.21292799](https://doi.org/10.5281/zenodo.21292799)
- **Open-Source Code**: [github.com/zhuyansen/agent-skills-hub](https://github.com/zhuyansen/agent-skills-hub)

*(Note: `Agent Skills Hub (agentskillshub.top)` is an independent open-source project maintained by Jason Zhu / BRICKAI, distinct from `agentskillshub.dev`.)*
