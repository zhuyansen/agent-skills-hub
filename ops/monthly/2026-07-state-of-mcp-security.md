# State of MCP Security — 2026-07

> Monthly snapshot from [Agent Skills Hub](https://agentskillshub.top)'s security grading
> of the open-source agent-skill / MCP ecosystem. Dataset (CC-BY-4.0):
> [Hugging Face](https://huggingface.co/datasets/jasonzhuyansen/agent-skills-security-grades) ·
> DOI [10.5281/zenodo.21292799](https://doi.org/10.5281/zenodo.21292799)

## Headline numbers

| Metric | Value |
|---|---|
| Indexed skills & MCP servers | **133,832** |
| Security-graded (≥5★) | 21,935 |
| **UNSAFE + REJECT rate (graded)** | **3.3%** (714 repos) |
| **Unaudited share of catalog** | **83.6%** |
| Long-tail unsafe rate (5-20★) | 4.4% |
| Popular unsafe rate (1K+★) | 0.4% |
| **Long-tail risk multiplier** | **10.9×** |

## Most common red flags

| Flag | Repos |
|---|---|
| `sudo_usage` | 1,161 |
| `service_persistence` | 332 |
| `curl_pipe_shell` | 240 |
| `agent_config_theft` | 158 |
| `tunnel_service` | 138 |
| `sensitive_env_vars` | 107 |
| `eval_usage` | 107 |
| `agent_memory_theft` | 67 |

## Method note

Rule-based scanner, 35 patterns in 3 tiers (SlowMist agent-security taxonomy,
extended). Grades: SAFE / CAUTION / UNSAFE / REJECT; repos below 5★ or without
scannable content stay UNAUDITED. This is a first-layer signal, not a line-by-line
audit — treat SAFE as "no known bad pattern."

---

## X thread 文案(中文,复制即发)

1/4
每月安全普查:2026-07 的开源 agent skill / MCP 生态

📊 收录 133,832 个,其中 84% 完全无人审计
🔴 已分级的 21,935 个里,3.3% 是 UNSAFE/REJECT
📈 长尾(5-20★)的危险率是头部(1K+★)的 11 倍

装一个 MCP server = 用你 agent 的全部权限跑陌生人的代码 👇

2/4
最常见的红旗:
· sudo_usage(1,161 个仓库)
· service_persistence(332 个仓库)
· curl_pipe_shell(240 个仓库)
· agent_config_theft(158 个仓库)
· tunnel_service(138 个仓库)

3/4
数据全部开放(CC-BY-4.0):
· HF: huggingface.co/datasets/jasonzhuyansen/agent-skills-security-grades
· DOI: 10.5281/zenodo.21292799
装前先查:agentskillshub.top(免费无登录)

4/4
方法论开源,是规则扫描不是逐行审计 —— SAFE 意思是"没扫到已知坏模式",不是"绝对安全"。
发现误报欢迎来 GitHub 提 issue,每一条都会让下个月的数字更准。

---

## Newsletter 段落(EN,粘进周报即可)

**State of MCP Security, 2026-07**: of 133,832 indexed skills and MCP servers,
84% remain entirely unaudited. Among the 21,935 graded repos,
3.3% grade UNSAFE or REJECT — and the unsafe rate in the 5-20★ long tail
is 11× the rate among 1K+★ repos. Full numbers and the open dataset:
agentskillshub.top

*生成于 2026-07-10 10:22 UTC · 数据为当日快照*
