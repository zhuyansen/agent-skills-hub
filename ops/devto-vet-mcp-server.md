---
title: How to vet an MCP server before you install it (I graded 130,000 to find out)
published: false
description: Installing an MCP server means running a stranger's code with your agent's permissions. Four manual checks that catch most bad ones — and what grading the entire public catalog taught me.
tags: mcp, security, ai, opensource
---

> 发布方法:dev.to → Create Post → 整篇粘贴(含上面的 frontmatter)→ 把 `published: false` 改成 `true` 或直接点 Publish。
> 下面正文共 2 条站链(首页 + 数据集),1 条 CLI npm 链。发完把文章 URL 发回,我记进外链台账。

---

Installing an MCP server is running a stranger's code with your agent's permissions. Your shell, your environment variables, your filesystem — and increasingly your agent's own config and memory.

Discovery is the easy part; there are tens of thousands of servers to pick from. Knowing whether the one you just found is safe to run is not. I spent the last few months building a rule-based scanner and grading the entire public catalog — **130,000+ open-source agent skills and MCP servers** — to figure out what "vetting" actually looks like at scale.

Here's the short version: four manual checks that catch most bad ones, and the data on why you need them.

## Why bother: the risk lives exactly where you least expect it

Three numbers from grading the catalog:

- **83% of the public catalog has never been audited by anyone.** No marketplace flag, no review, nothing.
- Among the ~21,500 repos popular enough to grade, **3.3% are unsafe or worse** — credential harvesting, data exfiltration, `curl | sh` installers.
- The unsafe rate is **~9× higher in the long tail** (3.8% at 5–20 stars) than among popular repos (0.4% at 1,000+ stars).

That last one is the trap. The server you've heard of is almost certainly fine. The danger is the obscure 7-star repo you grab from a search for some niche task — which is exactly the moment a directory is supposed to help you, and usually doesn't.

## Check 1 — Read the tool definitions, not the README

The README tells you what the author wants you to think the server does. The tool definitions tell you what it can actually do.

Open the source and find where tools are registered (in TypeScript servers, look for `server.tool(...)` or the `tools` array; in Python, the `@mcp.tool()` decorators). Ask one question per tool: **does this tool's capability match the server's stated purpose?**

A weather server that registers a `run_shell_command` tool is not a weather server. A "read-only" database inspector that registers `execute_query` with no statement filtering is not read-only. This check takes five minutes and catches the single most common failure mode: capability creep.

## Check 2 — Follow the environment variables

Grep the source for `process.env` (or `os.environ`):

```bash
grep -rn "process.env\|os.environ" src/ | grep -iv "NODE_ENV\|LOG"
```

Two things to look for:

1. **What does it read?** An API key for the service it wraps: fine. `AWS_SECRET_ACCESS_KEY`, `SSH_AUTH_SOCK`, or a loop over all of `process.env`: walk away.
2. **Where does it send them?** Trace every outbound request. If an env var ends up in a request body to a domain that isn't the service the server claims to integrate with, that's exfiltration — I flagged hundreds of these.

## Check 3 — Check the install path for `curl | sh`

If the README's install instructions pipe a remote script into your shell, the author is asking you to run unreviewable code *before* you've even run their reviewable code. Same red flag for `postinstall` scripts in `package.json` that fetch remote payloads.

Prefer servers you can run with a plain `npx <package>` or `uvx <package>` — the code that executes is at least the code that was published.

## Check 4 — Maintenance beats stars

Stars measure marketing. Maintenance measures whether someone will fix the CVE.

Thirty seconds on the repo page: when was the last commit? Do issues get responses? Is there exactly one giant "initial commit"? In the graded data, abandonment correlates with risk far better than star count does — a 40-star repo with weekly commits is a better bet than a 900-star repo untouched for a year.

## Or: let the grading be done before you search

The four checks above are what my scanner automates, at catalog scale. Every entry on [Agent Skills Hub](https://agentskillshub.top) — all 130,000+ — carries a **SAFE / CAUTION / UNSAFE grade plus a quality score**, computed from 35 rule-based flags (the SlowMist agent-security taxonomy, extended), refreshed every 8 hours.

From the terminal, the same grades are one command away:

```bash
npx @agentskillshub/cli search "browser automation" --safe
```

It's free, no login, and the full graded dataset is open (CC-BY-4.0) on [Hugging Face](https://huggingface.co/datasets/jasonzhuyansen/agent-skills-security-grades) if you want to run your own analysis or challenge the methodology — it's rule-based, not perfect, and false-positive reports genuinely improve it.

## The honest caveat

No static scanner catches intent. A grade of SAFE means "no known bad pattern," not "audited line by line." For anything touching production credentials, do checks 1–2 yourself regardless of what any directory says — including mine.

But the baseline matters. Right now the ecosystem's default is that nobody has looked at 83% of what you can install. Five minutes of vetting — yours or automated — beats that default by a lot.
