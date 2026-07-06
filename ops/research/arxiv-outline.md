# arXiv Paper Outline — Security Grading of 130K Open-Source AI Agent Skills

> Goal: a short (6–8 page) empirical paper. Highest-authority backlink we can
> earn + the "study, not a tool" positioning that gets cited (feeds brand
> domain authority — the real lever for the brand-word ranking problem).
> Numbers below are live from Supabase (2026-07-06); refresh before submission.

**Title (working):** *The Long Tail Is Unaudited: A Security Survey of 130,000
Open-Source AI Agent Skills and MCP Servers*

**Authors:** Jason Zhu (independent). Consider a co-author with an academic
affiliation for endorsement (arXiv cs.CR needs an endorser for a first
submission — line one up early).

**Category:** cs.CR (primary), cs.SE (cross-list).

## Abstract (draft skeleton)
AI coding agents increasingly install third-party "skills" and MCP servers that
run with the agent's full permissions and credentials. We collect and
security-grade **130,173** such artifacts from GitHub using an 11-category
rule-based scanner (derived from SlowMist's agent-security taxonomy). Of the
**21,582** popular enough to grade (stars ≥ 5), **3.3%** are UNSAFE or REJECT
and **8.8%** carry at least a CAUTION flag. Critically, **83% of the catalog is
UNAUDITED** — the risk concentrates in the long tail that no marketplace surfaces
a trust signal for. We release the full graded dataset and discuss the
implications for agent supply-chain security.

## 1. Introduction
- Skills/MCP = the agent supply chain; install-time trust is unsolved.
- Marketplaces (LobeHub 332K, others) rank by popularity/recency, not safety —
  none ship a per-item security signal (verifiable claim).
- Community demand is real: the #1 most-installed item on one marketplace is a
  community "skill-vetter" (cite). Users are asking for exactly this.
- Contributions: (1) largest security survey of the ecosystem to date, (2) an
  open rule-based grader, (3) a released graded dataset.

## 2. Background & Threat Model
- What a skill / MCP server is; permission + credential model.
- Threat classes: credential exfiltration, obfuscated payload / remote code,
  sandbox escape, prompt injection, supply-chain (typosquat / compromised dep),
  operational (data egress, no audit trail).
- Relation to prior work: Liu et al. 2026 (arXiv:2601.10338, n=31,132 — the
  26.1% vuln stat we already cite); position ours as broader-coverage +
  released dataset.

## 3. Method
- Collection: GitHub search across N query patterns, 6-phase pipeline, refreshed
  every 8h. Dedup by repo_full_name.
- Grading: 11 SlowMist-derived red-flag categories → grade
  (SAFE/CAUTION/UNSAFE/REJECT); UNAUDITED = below the star threshold / no
  signal. Rule definitions in appendix.
- Honesty caveats: rule-based (static), point-in-time, stars≥5 gate. Explicitly
  a floor, not a ceiling — deep per-item audits find more.

## 4. Results (live numbers 2026-07-06 — REFRESH before submit)
- Corpus: 130,173 indexed; 21,582 graded (16.6%).
- Grade distribution: SAFE 19,682 · CAUTION 1,189 · UNSAFE 686 · REJECT 25.
- 711 UNSAFE+REJECT = 3.3% of graded ≈ **1 in 30**.
- 2,287 artifacts carry ≥1 red flag.
- Long-tail finding: 108,591 (83%) UNAUDITED — plot grade-rate vs star bucket.
- Red-flag category breakdown (from security_flags): which flags dominate.
- Optional: correlate grade with stars/category/language (is popularity a proxy
  for safety? hypothesis: weakly).

## 5. Discussion
- The trust gap is a long-tail problem: popularity ranking hides it.
- What a per-install trust signal changes for agent operators.
- Limits of static rules → the case for layered (LLM + dynamic) auditing.

## 6. Release
- Dataset on HuggingFace (see hf-dataset-card.md) + Kaggle mirror.
- Grader rules open on GitHub.
- Link agentskillshub.top as the living, refreshed version.

## Appendix
- The 11 red-flag categories + example matches.
- Reproducibility: query patterns, thresholds, scanner version.

## Submission checklist
- [ ] Refresh all numbers from Supabase the day of submission
- [ ] Line up a cs.CR endorser (first arXiv submission needs one)
- [ ] Dataset live on HF first (paper links it)
- [ ] Format: overleaf, standard arXiv article class, ~6–8 pp
- [ ] After live: pitch The Register / BleepingComputer / kdnuggets with the
      arXiv link (the #1/#2 dofollow media plays from the backlink table)
