# Vibe coding test, 2026-10-26 and 27

Each tool was cloned and installed from its README in a throwaway sandbox (ops/ppt-runs/sandbox, entrypoint
in/vibe.py), then Claude Code (Claude Opus 5.5) built two apps with it from requests in the words of someone
who cannot code (in/brief-t1.txt, in/brief-t2.txt; in/prompt.txt). Whenever a build stopped short of a finished
app, it got the reply in in/reply.txt, up to 10 times. Limits: 30 minutes (t1), 45 minutes (t2). A tester session
with no tool loaded opened the app and ran the checks in in/test-t1.md and in/test-t2.md through the browser
helpers in in/tester_kit.py; every screenshot was reviewed, and exported spreadsheets were read back.
octocat/Hello-World is the control: no tool installed. Usage is every Claude Code session a build started,
priced at API rates (score.py); "× control" divides by the control's usage on the same task.

Tester notes: the "open" check uses index.html as a local file (what double-clicking opens); the other checks
use the same file from a local address, and "reopen" closes every tab and opens a new one. The sandbox's test
browser loses localStorage for local files when a script closes it (a plain localStorage page lost its data in
1 to 4 of 8 tries), so the first version of the tester failed apps for the browser's sake; every t1 build was
tested again with the final tester (earlier verdicts in out/t1/*/test-prev-N/, not committed).

## t1: 帮我做一个记账小网页：每次花钱记一笔（花了多少、买了什么），页面上能看到一共花了多少，关掉浏览器再打开，记录还在。

| Tool | ★ | Opened | open | add | total | reopen | Ran | Stops | Build min | Usage $ | × control | Ending |
|---|---:|---|---|---|---|---|---|---:|---:|---:|---:|---|
| octocat/Hello-World | 0 | file | ✓ | ✓ | ✓ | ✓ | yes | 0 | 0.8 | 0.17 | 1.0 | finished |
| obra/superpowers | 305151 | file | ✓ | ✓ | ✓ | ✓ | yes | 3 | 5.8 | 1.93 | 11.4 | finished |
| github/spec-kit | 142899 | file | ✓ | ✓ | ✓ | ✓ | yes | 1 | 4.2 | 1.3 | 7.6 | finished |
| gsd-build/get-shit-done | 64514 | file | ✓ | ✓ | ✓ | ✓ | yes | 1 | 30.0 | 5.28 | 31.1 | out of time |
| eyaltoledano/claude-task-master | 28276 | file | ✓ | ✓ | ✓ | ✓ | yes | 0 | 2.5 | 0.82 | 4.8 | finished |
| SuperClaude-Org/SuperClaude_Framework | 23911 | file | ✓ | ✓ | ✓ | ✓ | yes | 1 | 2.4 | 0.73 | 4.3 | finished |
| coleam00/context-engineering-intro | 13891 | file | ✓ | ✓ | ✓ | ✓ | yes | 0 | 29.7 | 2.06 | 12.1 | finished |
| KhazP/vibe-coding-prompt-template | 3126 | file | ✓ | ✓ | ✓ | ✓ | yes | 0 | 2.7 | 0.88 | 5.2 | finished |
| michaelshimeles/ralphy | 2975 | file | ✓ | ✓ | ✓ | ✓ | yes | 0 | 12.7 | 0.75 | 4.4 | finished |
| asklokesh/loki-mode | 1108 | file | ✓ | ✓ | ✓ | ✓ | yes | 1 | 10.8 | 0.6 | 3.5 | finished |
| botingw/rulebook-ai | 609 | file | ✓ | ✓ | ✓ | ✓ | yes | 1 | 2.0 | 0.55 | 3.2 | finished |
| anombyte93/prd-taskmaster | 587 | file | ✓ | ✗ | ✗ | ✗ | no | 2 | 30.0 | 5.3 | 31.2 | out of time |
| peterfei/ai-agent-team | 443 | file | ✓ | ✓ | ✓ | ✓ | yes | 0 | 13.8 | 1.54 | 9.1 | finished |
| evanklem/evanflow | 418 | file | ✓ | ✓ | ✓ | ✓ | yes | 1 | 2.8 | 0.65 | 3.8 | finished |
| nurettincoban/ai-prd-workflow | 298 | file | ✓ | ✓ | ✓ | ✓ | yes | 4 | 30.0 | 5.58 | 32.8 | out of time |

## t2: 做一个家庭记账本网页：能记收入和支出（金额、类别、日期、备注），能按月看收入、支出和结余，能看每个类别花了多少（最好有图），可以设每月预算、超了要提醒，还能把记录导出成 Excel 表格。数据存在我电脑上就行。

| Tool | ★ | Opened | open | record | month | category | by-month | budget | export | reopen | Ran | Stops | Build min | Usage $ | × control | Ending |
|---|---:|---|---|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---|
| octocat/Hello-World | 0 | file | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | yes | 0 | 4.2 | 1.03 | 1.0 | finished |
| obra/superpowers | 305151 | file | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | yes | 3 | 12.6 | 3.44 | 3.3 | finished |
| github/spec-kit | 142899 | file | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | yes | 1 | 11.3 | 3.18 | 3.1 | finished |
| gsd-build/get-shit-done | 64514 | file | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | no | 1 | 44.2 | 7.23 | 7.0 | out of time |
| eyaltoledano/claude-task-master | 28276 | file | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | yes | 0 | 31.9 | 5.35 | 5.2 | finished |
| SuperClaude-Org/SuperClaude_Framework | 23911 | file | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | yes | 1 | 5.2 | 1.38 | 1.3 | finished |
| coleam00/context-engineering-intro | 13891 | command | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | yes | 0 | 9.4 | 2.37 | 2.3 | finished |
| KhazP/vibe-coding-prompt-template | 3126 | file | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | yes | 0 | 6.6 | 1.99 | 1.9 | finished |
| michaelshimeles/ralphy | 2975 | file | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | yes | 0 | 14.1 | 2.07 | 2.0 | finished |
| asklokesh/loki-mode | 1108 | file | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | yes | 1 | 11.0 | 1.11 | 1.1 | finished |
| botingw/rulebook-ai | 609 | file | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | yes | 1 | 5.8 | 1.46 | 1.4 | finished |
| anombyte93/prd-taskmaster | 587 | file | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ | no | 2 | 45.0 | 7.89 | 7.7 | out of time |
| peterfei/ai-agent-team | 443 | file | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | yes | 0 | 5.0 | 1.51 | 1.5 | finished |
| evanklem/evanflow | 418 | file | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | yes | 3 | 24.7 | 2.82 | 2.7 | finished |
| nurettincoban/ai-prd-workflow | 298 | file | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | no | 2 | 45.0 | 10.56 | 10.3 | out of time |

## Notes from the review

- **t1/anombyte93/prd-taskmaster**: The install session registered its Claude Code plugin but not task-master-ai, which the README also lists, so the Auto-Execute mode was not on offer. The tool recommended its Verified Loop, wrote a PRD of 12 tasks and 24 subtasks for the page, and was still working at the 30-minute limit. The page it had by then sent the form as a page reload and recorded nothing (screenshots agree with the tester).
- **t1/gsd-build/get-shit-done**: After its five questions it was still working at the 30-minute limit, with no closing message; the page in output/ by then passed every check.
- **t1/nurettincoban/ai-prd-workflow**: Stopped four times: its interview, a plan to approve, a question whether to move from localStorage to IndexedDB after its own browser tests saw records go missing, and a second plan. Still working at the 30-minute limit; the page by then passed every check.
- **t2/anombyte93/prd-taskmaster**: Two questions, then its Verified Loop. At the 45-minute limit the page recorded entries and exported them, but its month overview read ¥0.00, the category panel held three empty placeholders and the budget panel said 等待实现 (still to be built). The Mac slept for about 90 minutes during this run; the build's limit counts working time only, so it is shown as 45 minutes, not the 137 the clock recorded.
- **t2/nurettincoban/ai-prd-workflow**: Its interview, then a plan of seven RFCs to approve one by one. At the 45-minute limit the ledger did everything but the budget and the export; its own help text points to backup buttons that are not on the page.
- **t2/coleam00/context-engineering-intro**: Built as a small project with a start script: there is no index.html to double-click, so a person has to run bash output/start.sh first.
- **t2/asklokesh/loki-mode**: Run a second time: during the first, the Mac went to sleep, which cut its install session short and let the run's outer limit expire. That attempt is kept in out-void/ and not counted.
- **t2/gsd-build/get-shit-done**: After seven questions it built in phases. At 44 minutes it had finished its first phase (recording, a list by day, month switching, edit and delete) and stopped to ask for a manual check of it; with under a minute of the 45 left, the run ended there. Monthly totals, the category chart, the budget and the export had not been built (the tester's verdicts agree with the screenshots).
- **t1/coleam00/context-engineering-intro**: Its own browser checks saw records lost on a local file, so it added a small local server (START.txt) and a banner on the page warning against opening it by double-click. That took most of its 29.7 minutes. The page opened by double-click still passed every check.
