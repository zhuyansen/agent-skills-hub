# Scoring Algorithm Design Document

## Overview

The scoring engine computes a **0-100 composite quality score** for each Agent Skill repository. The goal is to surface actively maintained, community-validated projects while penalizing abandoned or low-quality repos.

## Raw Metrics

| Symbol | Metric | Source |
|--------|--------|--------|
| S | Stars | `repo.stargazers_count` |
| F | Forks | `repo.forks_count` |
| AF | Author Followers | `owner.followers` |
| IR | Issue Resolution Rate | `closed_issues / total_issues` |
| C | Total Commits | commit count from API |
| D | Days Since Last Commit | `now - pushed_at` |

## Step 1: Min-Max Normalization

For metrics S, F, AF, C — apply Min-Max scaling across the entire dataset:

```
norm(x) = (x - x_min) / (x_max - x_min)
```

When `x_max == x_min`, `norm(x) = 0`. This maps every metric to [0, 1].

**Issue Resolution Rate** is already in [0, 1], so no normalization needed. When a repo has zero total issues, IR defaults to 0.5 (neutral).

## Step 2: Time Decay Penalty (Recency)

A step-function penalty based on time since last commit:

| Days Since Last Commit | Recency Score |
|----------------------|---------------|
| 0-30 | 1.0 |
| 31-90 | 0.9 |
| 91-180 | 0.7 |
| 181-365 | 0.4 |
| >365 | 0.15 |

**Rationale**: A step function maps to how developers intuitively judge project health ("updated this month" vs "dead for over a year"). The severe drop at 6+ months prevents stale projects from dominating rankings.

## Step 3: Weighted Composite Score

```
Score = (0.30 × norm(Stars)
       + 0.15 × norm(Forks)
       + 0.10 × norm(Author_Followers)
       + 0.15 × Issue_Resolution_Rate
       + 0.15 × norm(Commits)
       + 0.15 × Recency) × 100
```

## Weight Rationale

| Metric | Weight | Reasoning |
|--------|--------|-----------|
| Stars | 0.30 | Strongest signal of community interest; most universally available metric |
| Forks | 0.15 | Indicates people building on top of the tool; practical adoption signal |
| Author Followers | 0.10 | Proxy for author credibility, but lower weight because large orgs inflate this |
| Issue Resolution | 0.15 | Maintenance quality signal; shows whether authors respond to community |
| Commits | 0.15 | Development activity depth; consistent effort indicator |
| Recency | 0.15 | Freshness of the project; penalizes abandoned repos |

Total: 1.00

## Expected Behavior

- A recently updated repo with 500 stars, active issue management, and 100+ commits scores **70-90**
- A popular but abandoned repo (1000+ stars, no commits in 2 years) scores **30-50**
- A new repo with few stars but active development scores **20-40**
- A fork with minimal activity scores **5-15**

## Database Table

See `backend/app/models/skill.py` — the `score` column (Float, indexed) stores the computed score. Scores are recalculated after each sync cycle.
