#!/usr/bin/env python3
"""State of MCP Security 月报生成器 — 每月 10 号随记分板月表跑一次.

产出 ops/monthly/{YYYY-MM}-state-of-mcp-security.md:
数据段(EN, 可直接进 Dev.to/newsletter)+ X thread 中文文案。
数据来源:Supabase skills 表,3 条轻量聚合(串行 + 30s 超时,遵守 DB 纪律)。

用法: cd backend && source venv/bin/activate && python ../ops/monthly_report.py
"""

import json
import os
import sys
from datetime import date, datetime, timezone

import psycopg2
from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(REPO_ROOT, "backend", ".env"))

OUT_DIR = os.path.join(REPO_ROOT, "ops", "monthly")


def query_all(cur):
    cur.execute(
        "SELECT lower(coalesce(security_grade,'unknown')), count(*) FROM skills GROUP BY 1"
    )
    grades = dict(cur.fetchall())

    cur.execute(
        """
        SELECT CASE WHEN stars < 20 THEN '5-20' WHEN stars < 100 THEN '20-100'
                    WHEN stars < 1000 THEN '100-1K' ELSE '1K+' END AS bucket,
               count(*) AS n,
               count(*) FILTER (WHERE lower(security_grade) IN ('unsafe','reject')) AS bad
        FROM skills WHERE stars >= 5
          AND lower(coalesce(security_grade,'')) IN ('safe','caution','unsafe','reject')
        GROUP BY 1
        """
    )
    buckets = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

    cur.execute(
        """
        SELECT flag, count(*) FROM skills,
               LATERAL jsonb_array_elements_text(
                 CASE WHEN jsonb_typeof(security_flags::jsonb)='array'
                      THEN security_flags::jsonb ELSE '[]'::jsonb END) AS flag
        WHERE security_flags IS NOT NULL AND security_flags NOT IN ('', '[]')
        GROUP BY 1 ORDER BY 2 DESC LIMIT 8
        """
    )
    flags = cur.fetchall()
    return grades, buckets, flags


def render(grades, buckets, flags, month: str) -> str:
    total = sum(grades.values())
    graded = sum(v for k, v in grades.items() if k in ("safe", "caution", "unsafe", "reject"))
    bad = grades.get("unsafe", 0) + grades.get("reject", 0)
    unaudited_pct = grades.get("unknown", 0) / total * 100
    bad_pct = bad / graded * 100 if graded else 0

    def rate(bucket):
        n, b = buckets.get(bucket, (0, 0))
        return (b / n * 100) if n else 0.0

    tail, head = rate("5-20"), rate("1K+")
    mult = tail / head if head else 0

    flag_rows = "\n".join(f"| `{f}` | {c:,} |" for f, c in flags)

    return f"""# State of MCP Security — {month}

> Monthly snapshot from [Agent Skills Hub](https://agentskillshub.top)'s security grading
> of the open-source agent-skill / MCP ecosystem. Dataset (CC-BY-4.0):
> [Hugging Face](https://huggingface.co/datasets/jasonzhuyansen/agent-skills-security-grades) ·
> DOI [10.5281/zenodo.21292799](https://doi.org/10.5281/zenodo.21292799)

## Headline numbers

| Metric | Value |
|---|---|
| Indexed skills & MCP servers | **{total:,}** |
| Security-graded (≥5★) | {graded:,} |
| **UNSAFE + REJECT rate (graded)** | **{bad_pct:.1f}%** ({bad:,} repos) |
| **Unaudited share of catalog** | **{unaudited_pct:.1f}%** |
| Long-tail unsafe rate (5-20★) | {tail:.1f}% |
| Popular unsafe rate (1K+★) | {head:.1f}% |
| **Long-tail risk multiplier** | **{mult:.1f}×** |

## Most common red flags

| Flag | Repos |
|---|---|
{flag_rows}

## Method note

Rule-based scanner, 35 patterns in 3 tiers (SlowMist agent-security taxonomy,
extended). Grades: SAFE / CAUTION / UNSAFE / REJECT; repos below 5★ or without
scannable content stay UNAUDITED. This is a first-layer signal, not a line-by-line
audit — treat SAFE as "no known bad pattern."

---

## X thread 文案(中文,复制即发)

1/4
每月安全普查:{month} 的开源 agent skill / MCP 生态

📊 收录 {total:,} 个,其中 {unaudited_pct:.0f}% 完全无人审计
🔴 已分级的 {graded:,} 个里,{bad_pct:.1f}% 是 UNSAFE/REJECT
📈 长尾(5-20★)的危险率是头部(1K+★)的 {mult:.0f} 倍

装一个 MCP server = 用你 agent 的全部权限跑陌生人的代码 👇

2/4
最常见的红旗:
{chr(10).join(f"· {f}({c:,} 个仓库)" for f, c in flags[:5])}

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

**State of MCP Security, {month}**: of {total:,} indexed skills and MCP servers,
{unaudited_pct:.0f}% remain entirely unaudited. Among the {graded:,} graded repos,
{bad_pct:.1f}% grade UNSAFE or REJECT — and the unsafe rate in the 5-20★ long tail
is {mult:.0f}× the rate among 1K+★ repos. Full numbers and the open dataset:
agentskillshub.top

*生成于 {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")} · 数据为当日快照*
"""


def main() -> int:
    month = date.today().strftime("%Y-%m")
    conn = psycopg2.connect(
        os.environ["SUPABASE_DB_URL"],
        connect_timeout=15,
        options="-c statement_timeout=30000",
        keepalives=1,
        keepalives_idle=30,
    )
    cur = conn.cursor()
    grades, buckets, flags = query_all(cur)
    conn.close()

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{month}-state-of-mcp-security.md")
    with open(path, "w") as f:
        f.write(render(grades, buckets, flags, month))
    print(f"written: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
