# The Long Tail Is Unaudited: A Security Survey of 130,000 Open-Source AI Agent Skills and MCP Servers

**Jason Zhu** · Independent · agentskillshub.top · [contact]
*Draft 2026-07-06. Live numbers from Supabase — refresh the day of submission.*
*cs.CR (primary), cs.SE (cross-list). Needs a cs.CR endorser for first submission.*

---

## Abstract

AI coding agents (Claude Code, Cursor, OpenAI Codex, and others) increasingly
install third-party "skills" and Model Context Protocol (MCP) servers that
execute with the agent's full permissions and often its credentials. Yet the
marketplaces that distribute these artifacts rank them by popularity and
recency, not safety, and expose no per-item trust signal. We collect
**130,173** open-source agent skills and MCP servers from GitHub and grade them
with an 11-category rule-based scanner derived from an established agent-security
taxonomy. Of the **21,582** artifacts popular enough to grade (stars ≥ 5),
**3.3%** are UNSAFE or REJECT (≈ 1 in 30) and **8.8%** carry at least a CAUTION
flag. Our central finding is distributional: the UNSAFE rate is **3.8% in the
low-star long tail (5–20 stars) versus 0.4% among popular repos (1000+ stars)** —
a ~9× gap — while **83% of the full catalog is UNAUDITED**. Risk concentrates
exactly where popularity ranking hides it and where no marketplace provides a
signal. We release the complete graded dataset and the scanner rules.

## 1. Introduction

An agent skill is a package of instructions, and often code, that teaches an AI
agent to perform a task; an MCP server is a process that exposes tools to an
agent over a standard protocol. Both run inside the trust boundary of the user's
agent: a skill's install script runs on the user's machine, and an MCP server
receives whatever credentials the agent holds. Installing one is a
supply-chain decision, but it is presented to users as a one-click convenience.

The marketplaces that have emerged (one indexes 332K skills; others range from
thousands to millions of monthly visits) rank by stars, installs, or recency.
None, to our knowledge, ships a per-item security grade. That the single
most-installed artifact on one such marketplace is a community-built
"skill-vetter" is direct evidence that users feel this gap and are improvising
around it.

We ask three empirical questions. (Q1) How prevalent are unsafe artifacts across
the open-source agent-skill ecosystem? (Q2) How is that risk distributed with
respect to popularity — does the community's star signal already protect users?
(Q3) What categories of risk dominate? Our contributions:

1. The largest security survey of the agent-skill ecosystem to date: 130,173
   artifacts, refreshed on an 8-hour cycle.
2. An open, rule-based grader over 11 red-flag categories.
3. A released, citable dataset of grades, red-flags, and quality scores.

## 2. Background and Threat Model

**Artifacts.** We consider skills (Claude Skills, Codex skills, and portable
`SKILL.md` variants), MCP servers, and standalone agent tools. All can carry
executable code (install hooks, Python entry points) and all are loaded into a
running agent's context.

**Threat classes.** We group risks into six families, mapped to concrete
red-flags: credential exfiltration (reading `.env`, agent config/memory, tokens),
obfuscated or remote code execution (`curl | sh`, `eval`, base64-decoded exec),
persistence (cron, service installation), tunneling/egress (reverse tunnels,
outbound to non-declared hosts), privilege (unexpected `sudo`), and supply-chain
(typosquatting, compromised or unpinned dependencies).

**Related work.** Agent-skill and MCP security has drawn rapid attention in 2026.
Closest to ours, Liu et al. (arXiv:2601.10338) evaluate 31,132 skills (of 42,447
collected) with the SkillScan framework and report a 26.1% vulnerability rate;
Etteib, Lunghi, and Bissyandé (arXiv:2606.23416) build an attention-based
detector that locates malicious instruction spans in marketplace skills. A
second line targets enforcement and formal guarantees: SkillScope
(arXiv:2605.05868) proposes fine-grained least-privilege enforcement, while a
formal supply-chain analysis (arXiv:2603.00195) and audit-runtime-gap work
(arXiv:2605.05274) model the trust boundary explicitly. A third studies the MCP
protocol itself — threat modeling and tool-poisoning (arXiv:2603.22489) and a
defense-placement taxonomy (arXiv:2604.07551). These contribute detection
methods, enforcement mechanisms, and threat taxonomies. Our contribution is
orthogonal and complementary: the broadest static census of the *published*
ecosystem to date (130,173 artifacts), a *released, citable* graded dataset, and
a distributional finding — unsafe density is ~9× higher in the unranked long tail.
To our knowledge no prior work releases a full graded dataset at this scale. We
further relate to npm/PyPI typosquatting and compromised-dependency studies as
supply-chain analogues.

<!-- PRE-SUBMIT: verify each cited paper's one-line claim against its abstract;
     titles/ids from a 2026-07 arXiv search. Add DOIs/venues if published. -->


## 3. Method

**Collection.** A six-phase pipeline runs every 8 hours: (1) GitHub search across
a fixed set of query patterns for the artifact types; (2) verified-creator repo
fetch; (3) community submissions; (4) owner/metadata enrichment; (5) README
fetch (≤ 50 KB); (6) dedup by `owner/repo` and upsert. This yields 130,173
distinct artifacts.

**Grading.** A static scanner matches each artifact's README, install scripts,
config, and file tree against 11 red-flag categories (Appendix A), producing a
grade: SAFE (no blocking pattern), CAUTION (advisory flags), UNSAFE (a blocking
pattern), or REJECT (multiple/severe). Artifacts below a popularity gate
(stars < 5) or lacking any signal are marked UNAUDITED. We also compute a 0–100
quality score from documentation, structure, and maintenance signals
(orthogonal to security; reported for context).

**Honesty of the instrument.** The scanner is static and point-in-time. It is a
**floor, not a ceiling**: it catches declared patterns, not obfuscated intent or
runtime behavior, and does not execute code. UNAUDITED means *not assessed* — it
must not be read as "safe." A deep, per-item audit (LLM-assisted static review
plus sandboxed execution) is future work.

## 4. Results

*(Live snapshot 2026-07-06 — REFRESH before submission.)*

**Prevalence (Q1).** Of 130,173 indexed, 21,582 are graded (16.6%). Among graded:
SAFE 19,682; CAUTION 1,189; UNSAFE 686; REJECT 25. Thus 711 (3.3%, ≈ 1 in 30) are
UNSAFE or REJECT and 1,900 (8.8%) are CAUTION-or-worse.

**Distribution by popularity (Q2) — the central result.** The UNSAFE/REJECT rate
falls monotonically with popularity:

| Star bucket | n | UNSAFE/REJECT | rate |
|---|---|---|---|
| 5–20 | 10,000 | 375 | **3.8%** |
| 20–100 | 6,631 | 243 | 3.7% |
| 100–1,000 | 4,458 | 42 | 0.9% |
| 1,000+ | 1,447 | 6 | **0.4%** |

Popularity is weakly protective — but the corollary is that **83% of the catalog
(108,591 artifacts) is UNAUDITED**, and the residual unsafe density is ~9× higher
in the low-star tail that no marketplace ranks or flags. The risk is precisely
where users get the least signal.

**Risk categories (Q3).** Among flagged artifacts, the most common red-flags are
unexpected privilege (`sudo`, 1,146), service persistence (327),
`curl | sh` remote execution (238), agent-config theft (155), tunneling (137),
sensitive env-var access (104), and `eval` (102). Credential- and
persistence-oriented flags — the ones that matter most when an artifact runs
with agent credentials — are well represented.

**By category.** UNSAFE rates are comparable across artifact types: MCP servers
3.2%, Claude Skills 3.5%, Codex skills 3.1%, agent tools 2.3% — no single
artifact class is disproportionately dangerous; the problem is ecosystem-wide.

## 5. Discussion

The headline is not "3.3% are unsafe" but *where* the 3.3% lives. Popularity
ranking, the default on every marketplace, systematically routes users toward the
safer head and provides no warning in the long tail where density is 9× higher.
A per-install trust signal — a grade shown before the install command — directly
addresses this, and costs the user nothing to read.

Static grading has clear limits (§3). It motivates layered auditing:
LLM-assisted source review for intent, and sandboxed execution for behavior. We
frame the released dataset as the substrate for that work.

## 6. Availability

- **Dataset:** HuggingFace `agentskillshub/agent-skills-security-grades`
  (CC BY 4.0) + Kaggle mirror.
- **Living version:** agentskillshub.top, regraded every 8 hours.
- **Scanner rules:** open on GitHub (Appendix A).

## Appendix A — Red-flag categories

Extracted from the scanner (`backend/app/services/security_scanner.py`). Flags
are grouped by severity tier; a REJECT-tier flag forces REJECT, a HIGH-tier flag
forces UNSAFE, MEDIUM-tier flags accumulate to CAUTION.

**Remote code execution / exfiltration (HIGH → UNSAFE):**
- `curl_pipe_shell` — downloads and executes a remote script via `curl | (ba)sh`
- `wget_pipe_shell` — same via `wget | bash`
- `data_exfiltration` — sends local data to an external server via `curl` POST
- `exec_import` — executes dynamically imported Python code

**Credential & agent-identity theft (HIGH):**
- `credential_harvest` — harvests credentials from environment variables
- `env_file_read` — reads `.env` files that may hold secrets
- `sensitive_dir_access` — accesses `~/.ssh`, `~/.aws`, `~/.gnupg`
- `etc_sensitive_read` — reads `/etc/shadow`, `/etc/passwd`
- `agent_memory_theft` — reads agent memory/identity files
- `agent_config_theft` — reads agent config/session files

**Privilege & system tampering (MEDIUM → CAUTION):**
- `sudo_usage` — invokes `sudo` (most common flag: 1,146 artifacts)
- `chmod_dangerous` — sets `777`/setuid permissions
- `write_etc` — writes to `/etc/`

**Persistence & egress (MEDIUM):**
- `service_persistence` — installs a service (327)
- `cron_persistence` — installs a cron job
- `tunnel_service` — opens a reverse tunnel (137)

*(Full 43-entry table with regex patterns in the released scanner source; the
list above covers every flag observed in the graded corpus. Verified-org
allowlist entries — anthropics, openai, google, etc. — are used to raise vendor
trust, not as red-flags.)*

## Appendix B — Reproducibility

Query patterns, star gate, scanner version, snapshot date. Dataset schema in the
HF card.

---

### Pre-submission checklist
- [ ] Refresh every number from Supabase on submission day
- [ ] Fill Appendix A from the scanner source
- [ ] Secure a cs.CR endorser
- [ ] Publish the HF dataset first, link it here
- [ ] Overleaf, arXiv article class, ~7 pp
- [ ] Post-publication: pitch The Register / BleepingComputer / kdnuggets with the arXiv link
