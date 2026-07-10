---
# HuggingFace dataset card — paste as README.md of the dataset repo.
# Create at: huggingface.co/new-dataset  →  jasonzhuyansen/agent-skills-security-grades
license: cc-by-4.0
task_categories:
  - tabular-classification
  - text-classification
language:
  - en
tags:
  - security
  - ai-agents
  - mcp
  - claude-skills
  - supply-chain
  - code-security
pretty_name: Agent Skills Security Grades (130K)
size_categories:
  - 100K<n<1M
---

# Agent Skills Security Grades

Security grades and quality scores for **130,173 open-source AI agent skills and
MCP servers** collected from GitHub, from [Agent Skills Hub](https://agentskillshub.top).
Each row is one skill/server with a rule-based security grade
(SAFE / CAUTION / UNSAFE / REJECT / UNAUDITED), red-flag identifiers, and a
0–100 quality score.

## Why this exists

AI coding agents install third-party skills that run with the agent's full
permissions and credentials, but marketplaces rank by popularity, not safety.
Of the 21,582 skills popular enough to grade (stars ≥ 5), **1 in ~30 is UNSAFE
or REJECT** — and **83% of the whole catalog is UNAUDITED**. The risk lives in
the long tail. Read the write-up:
[We security-graded 117,854 AI agent skills](https://agentskillshub.top/blog/securing-117k-ai-skills/).

## Columns

| Column | Type | Description |
|---|---|---|
| `repo_full_name` | str | `owner/repo` |
| `category` | str | mcp-server / claude-skill / codex-skill / agent-tool / … |
| `stars` | int | GitHub stars at snapshot |
| `security_grade` | str | safe / caution / unsafe / reject / unknown |
| `security_flags` | list[str] | matched red-flag ids (e.g. `credential-remote-hosting`) |
| `quality_score` | float | 0–100, doc/structure/maintenance signals |
| `language` | str | primary language |
| `license` | str | SPDX id or null |
| `last_commit_at` | date | recency |

## Grade distribution (snapshot 2026-07-06)

| Grade | Count |
|---|---|
| UNAUDITED (below star gate) | 108,591 |
| SAFE | 19,682 |
| CAUTION | 1,189 |
| UNSAFE | 686 |
| REJECT | 25 |

**The key finding — risk is a long-tail problem.** UNSAFE/REJECT rate by
popularity: 5–20★ = **3.8%**, 20–100★ = 3.7%, 100–1000★ = 0.9%, 1000★+ = **0.4%**.
A ~9× gap between the long tail and the head — and the long tail is exactly where
marketplaces provide no signal.

Most common red-flags: `sudo_usage` (1,146), `service_persistence` (327),
`curl_pipe_shell` (238), `agent_config_theft` (155), `tunnel_service` (137).

## Method & caveats

Rule-based static scan across 11 SlowMist-derived red-flag categories. This is a
**floor, not a ceiling**: static rules on a point-in-time snapshot miss things a
deep per-item audit catches. `UNAUDITED` means *not assessed* (below the stars≥5
gate or no signal) — it does **not** mean "safe". Regenerated every 8 hours on
the live site.

## How to build

```python
from datasets import load_dataset
ds = load_dataset("jasonzhuyansen/agent-skills-security-grades")
```

## Mirrors & DOI

- **Archived snapshot with DOI**: [10.5281/zenodo.21292799](https://doi.org/10.5281/zenodo.21292799) (Zenodo, CSV)
- **Kaggle mirror**: [kaggle.com/datasets/yansenzhu/agent-skills-security-grades](https://www.kaggle.com/datasets/yansenzhu/agent-skills-security-grades)
- **Example analysis notebook**: [Kaggle: 130K Security Grades Analysis](https://www.kaggle.com/code/yansenzhu/ai-agent-skills-130k-security-grades-analysis)

## Citation

```
@misc{zhu2026agentskills,
  title  = {The Long Tail Is Unaudited: A Security Survey of 130,000 Open-Source AI Agent Skills},
  author = {Zhu, Jason},
  year   = {2026},
  doi    = {10.5281/zenodo.21292799},
  note   = {Dataset: huggingface.co/datasets/jasonzhuyansen/agent-skills-security-grades},
  url    = {https://agentskillshub.top}
}
```

License: CC BY 4.0 — attribute Agent Skills Hub (agentskillshub.top).

---

## Export script (run to produce the parquet/csv before upload)

```bash
# backend venv, from repo root:
python ops/research/export_dataset.py   # → ops/research/out/agent-skills-security-grades.parquet
```
