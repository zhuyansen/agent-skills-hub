# Scoring Algorithm v3

> Inspired by [SkillsBench](https://arxiv.org/abs/2602.12670) (arXiv:2602.12670)

## Overview

The scoring engine computes a **0-100 composite quality score** combining 10 weighted signals. v3 integrates findings from SkillsBench, which benchmarked 84 tasks across 7 agent-model configurations with 7,308 trajectories.

## Key Changes from v2

| Change | Rationale (Paper Finding) |
|--------|--------------------------|
| README length: optimal range replaces "longer=better" | Finding 6: Comprehensive Skills hurt (-2.9pp), Detailed best (+18.8pp) |
| New: Procedural Content dimension (12%) | Section 2.1: Skills must contain procedural guidance, not just facts |
| New: Instruction Quality dimension (10%) | Section 2.4: Output paths, constraints, success criteria matter |
| New: Domain bonus signal (5%) | Table 4: Healthcare +51.9pp vs Software Eng +4.5pp |
| Quality weight 20% → 25% | Finding 1: Skill quality is the #1 performance predictor |
| Stars weight 18% → 15% | Stars don't correlate well with actual agent performance |

## Quality Dimensions (8)

| Dimension | Weight | Key Signals |
|-----------|--------|-------------|
| Completeness | 12% | README (optimal range), license, description, stars |
| Clarity | 12% | Description quality, topics, naming |
| Specificity | 12% | Language, topic count, category, size |
| Examples | 10% | Code blocks (not just README size), commits |
| README Structure | 15% | Sections, code blocks, optimal length (1-5K best) |
| Agent Readiness | 17% | Install, tools/API, usage, config, compliance |
| **Procedural Content** | **12%** | Step-by-step, numbered lists, sequence words, shell commands |
| **Instruction Quality** | **10%** | Output paths, success criteria, constraints, structured requirements |

## Composite Score (10 signals → 0-100)

| Signal | Weight | Method |
|--------|--------|--------|
| Quality | 25% | 8-dimension aggregate |
| Stars | 15% | log1p normalization |
| Recency | 11% | Exponential decay e^(-0.01d) |
| Issue Resolution | 10% | closed/total, neutral if none |
| Forks | 8% | log1p |
| Commits | 8% | log1p |
| Momentum | 7% | Z-score star growth |
| Author Followers | 6% | log1p |
| Size Bonus | 5% | micro:1.0, small:0.8, medium:0.5, large:0.2 |
| **Domain Bonus** | **5%** | Category + topic specialization |

## README Length Scoring (v3)

Paper Finding 6: "Moderate-length Skills outperform comprehensive ones"

| README Length | Completeness | Structure | Rationale |
|--------------|-------------|-----------|-----------|
| 2K-8K chars | 0.35 (max) | 0.20 (max) | "Detailed": optimal |
| 8K-15K chars | 0.30 | 0.15 | Getting verbose |
| 15K+ chars | 0.25 | 0.05-0.10 | "Comprehensive": diminishing returns |
| 500-2K chars | 0.15 | 0.05 | Too brief |

## Procedural Content Detection

Inspired by SkillsBench Section 2.1 — Skills must provide "procedural content" (how-to, workflows, SOPs).

| Signal | Max Score | What We Detect |
|--------|-----------|---------------|
| Procedure headings | 0.20 | "## Steps", "## Workflow", "## How-to" |
| Numbered steps | 0.25 | "1. Do X", "2. Do Y" patterns |
| Sequence words | 0.15 | "first", "then", "next", "finally" |
| Action verbs | 0.15 | "run", "execute", "configure", "deploy" |
| Procedural description | 0.10 | Description mentions "guide", "workflow", "tutorial" |
| Shell command blocks | 0.15 | ```bash code blocks |

## Domain Bonus

SkillsBench Table 4 shows specialized domains benefit most from Skills:

| Domain | Skills Δ | Our Bonus |
|--------|----------|-----------|
| Healthcare, Medical | +51.9pp | +0.3 topic bonus |
| Manufacturing | +41.9pp | +0.25 topic bonus |
| Cybersecurity | +23.2pp | +0.2 topic bonus |
| Finance | +15.1pp | +0.2 topic bonus |
| Software Engineering | +4.5pp | +0.0 (well-covered) |

Category-level bonuses: `claude-skill` (0.8) > `agent-tool`/`codex-skill` (0.7) > `mcp-server` (0.6) > `ai-skill` (0.6) > `uncategorized` (0.3)
