# Quarterly-report test (第二十五期 AI 写作)

Each tool was cloned and installed from its README in a throwaway sandbox (ops/ppt-runs/sandbox, entrypoint
in/writing.py), then Claude Code (Claude Opus) wrote a team's third-quarter work report from a made-up fact list
(in/fixtures/季度事实清单.md, see in/fixtures/README.md), from two requests in the person's words (in/brief-t1.txt,
in/brief-t2.txt; in/prompt.txt). Whenever a build stopped short of a finished report it got the reply in
in/reply.txt, up to 10 times, within 30 minutes. A tester session with no tool loaded then checked the document
against the checklist in in/test.md, the same for every tool and both requests and fixed before the runs: seven
checks scripted in in/kit.py against the answer key and tone lists in in/truth.json, one (facts) read by the
tester. octocat/Hello-World is the control: no tool installed. Usage is every Claude Code session a build started,
priced at API rates (score.py); "× control" divides by the control's usage on the same request.

## t1: 帮我写一份季度工作总结。

| Tool | ★ | Opened | 字 | 1200–1800字 | 三块 | 项目计划 | 问题写实 | 数字 | 没编 | 套话≤2/千字 | 排比≤1 | Passed | Stops | Build min | Run min | Usage $ | × control | Install + tester $ | Ending |
|---|---:|---|---:|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| octocat/Hello-World | 0 | file | 1159 | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | 5/8 | 0 | 0.6 | 1.4 | 0.13 | 1.0 | 0.24 | finished |
| anthropics/skills | 188983 | file | 1029 | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | 6/8 | 1 | 0.8 | 1.8 | 0.25 | 1.9 | 0.22 | finished |
| op7418/Humanizer-zh | 22242 | file | 938 | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 7/8 | 0 | 0.8 | 1.8 | 0.42 | 3.2 | 0.25 | finished |
| larashero3-dotcom/lieflat-less-ai-tone | 6829 | file | 781 | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 7/8 | 1 | 1.4 | 2.4 | 0.51 | 3.9 | 0.33 | finished |
| MrGeDiao/shuorenhua | 2532 | file | 920 | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 7/8 | 0 | 0.7 | 2.0 | 0.27 | 2.1 | 0.24 | finished |
| duyunzhoudyz/dyz-gongwen-skills | 438 | file | 1020 | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | 5/8 | 1 | 2.9 | 6.3 | 1.54 | 11.8 | 0.25 | finished |
| Liuxiangjian-ai/official-document-skill | 437 | file | 1064 | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | 6/8 | 0 | 0.6 | 2.1 | 0.29 | 2.2 | 0.38 | finished |

## t2: 帮我写一份第三季度的工作总结，交给部门领导看。只用季度事实清单.md 里的事实和数字，数字照抄，别自己算，清单里没有的东西一句也别补。1500 字左右。分三块写：这个季度做成了什么，哪些没做好，第四季度打算怎么做。说大白话，像当面跟领导汇报一样，别用套话和口号，也别用排比句。没做好的地方要写实：出了什么事、影响多大、为什么，不要轻描淡写，也不要往好里说。

| Tool | ★ | Opened | 字 | 1200–1800字 | 三块 | 项目计划 | 问题写实 | 数字 | 没编 | 套话≤2/千字 | 排比≤1 | Passed | Stops | Build min | Run min | Usage $ | × control | Install + tester $ | Ending |
|---|---:|---|---:|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| octocat/Hello-World | 0 | file | 1246 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 8/8 | 0 | 1.2 | 1.9 | 0.19 | 1.0 | 0.2 | finished |
| anthropics/skills | 188983 | file | 1391 | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | 7/8 | 0 | 1.4 | 2.7 | 0.32 | 1.7 | 0.31 | finished |
| op7418/Humanizer-zh | 22242 | file | 978 | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 7/8 | 0 | 1.1 | 2.0 | 0.4 | 2.1 | 0.25 | finished |
| larashero3-dotcom/lieflat-less-ai-tone | 6829 | file | 1128 | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 7/8 | 1 | 3.4 | 4.5 | 1.08 | 5.7 | 0.35 | finished |
| MrGeDiao/shuorenhua | 2532 | file | 1155 | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 7/8 | 0 | 1.4 | 2.5 | 0.43 | 2.3 | 0.27 | finished |
| duyunzhoudyz/dyz-gongwen-skills | 438 | file | 946 | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 7/8 | 1 | 3.6 | 5.4 | 1.58 | 8.3 | 0.21 | finished |
| Liuxiangjian-ai/official-document-skill | 437 | file | 1323 | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | 7/8 | 0 | 1.6 | 3.2 | 0.43 | 2.3 | 0.32 | finished |

## What the scripted checks found

| Brief | Tool | 字 | 项目计划 8 | 问题写实 4 | 清单没有的数字 | 其中算出来的 | 旧数字当现在 | 套话和拔高 | 每千字 | 排比 | 编的事实（测试员） |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| t1 | octocat/Hello-World | 1159 | 8 | 4 | 9 | 7 | 0 | 0 | 0.0 | 0 | 3 |
| t1 | anthropics/skills | 1029 | 8 | 4 | 2 | 2 | 0 | 0 | 0.0 | 0 | 0 |
| t1 | op7418/Humanizer-zh | 938 | 8 | 4 | 0 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| t1 | larashero3-dotcom/lieflat-less-ai-tone | 781 | 8 | 4 | 0 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| t1 | MrGeDiao/shuorenhua | 920 | 8 | 4 | 0 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| t1 | duyunzhoudyz/dyz-gongwen-skills | 1020 | 8 | 4 | 8 | 8 | 0 | 1 | 1.0 | 0 | 1 |
| t1 | Liuxiangjian-ai/official-document-skill | 1064 | 8 | 4 | 2 | 2 | 0 | 1 | 0.9 | 0 | 0 |
| t2 | octocat/Hello-World | 1246 | 8 | 4 | 0 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| t2 | anthropics/skills | 1391 | 8 | 4 | 0 | 0 | 0 | 0 | 0.0 | 0 | 3 |
| t2 | op7418/Humanizer-zh | 978 | 8 | 4 | 0 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| t2 | larashero3-dotcom/lieflat-less-ai-tone | 1128 | 8 | 4 | 0 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| t2 | MrGeDiao/shuorenhua | 1155 | 8 | 4 | 0 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| t2 | duyunzhoudyz/dyz-gongwen-skills | 946 | 8 | 4 | 0 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| t2 | Liuxiangjian-ai/official-document-skill | 1323 | 8 | 4 | 0 | 0 | 0 | 0 | 0.0 | 0 | 1 |

## Notes

- **t1/anthropics/skills**: the tester's copy of numbers differs from the script's verdict here (the tester ran the script before one of the script fixes listed below; the table uses the fixed script)
- **t1/op7418/Humanizer-zh**: the tester's copy of numbers differs from the script's verdict here (the tester ran the script before one of the script fixes listed below; the table uses the fixed script)
- **t1/octocat/Hello-World** doubt on numbers: Script read correctly on the computed figures (15 个百分点, 43 秒, 0.2 分, 1 分 30 秒, 90%) — all are differences/shares worked out by the report. Its label for 「1 分 30 秒」 is wrong (it is 4 分 10 秒 minus 2 分 40 秒, not a share of the budget), but the verdict is unaffected. The dates 「2026 年 7 月 1 日 – 9 月 30 日」 are just the bounds of the list's 「7–9 月」, arguably not invented figures. The script also missed two derived figures: 「剩下 2.4 万元」 (24 − 21.6; matched only because 培训 2.4 万 is in the list) and 「也就是三分之一」 (27/81).
- **t1/anthropics/skills** doubt on numbers: The script likely misread 「结余 2.4 万元」 (lines 13 and 71) as the list's training cost 2.4 万. In the report it is the budget minus spending (24 − 21.6), a figure worked out from the list, which check 5 does not allow; it only matches by coincidence. 「15.0 万元」 and 「24.0 万元」 are the list's 15 万 and 24 万 written differently, so they are fine.
- **t1/op7418/Humanizer-zh** doubt on numbers: The script misread the cost table. The four flagged figures are cells under the column header 「金额（万元）」: | 机器人供应商 | 15 |, | 外包质检 | 4.2 |, | 培训 | 2.4 |, | 合计 | 21.6 |. With the header's unit they are exactly the list's 「机器人供应商 15 万，外包质检 4.2 万，培训 2.4 万」 and 「实际花了 21.6 万元」 (21.6 also appears as 「实际花费 21.6 万元」 in line 49). '15' is not 46%−31%. The script did not read the unit from the table header together with the cell. All old figures (31%, 12,400 单, 95 秒, 4.1 分, 4 分 10 秒) appear only labelled as earlier values.
- **t1/larashero3-dotcom/lieflat-less-ai-tone** doubt on problems: Not a wrong verdict, but for Q4 the script matched the team section (line 9) rather than problem 4 in section 三 (「9 月 12 日离职的那名客服主管，岗位到现在还空着，招聘也还没开始。」); both are faithful.
- **t1/MrGeDiao/shuorenhua** doubt on coverage: For P2 the script matched the summary sentence in 一、总体情况 (which only names 工单系统迁移) rather than line 27 「8 月底迁完 80%，9 月 26 日全部迁完。」; the key fact is in the report anyway, so the verdict is unaffected.
- **t1/MrGeDiao/shuorenhua** doubt on problems: For Q2 the script quoted the overview line 9 (no figure); the figure and cause are in line 45 「用户得把问题从头再说一遍。9 月转人工后的投诉里，40% 是因为这个。」, so the verdict stands on the right text anyway.
- **t1/duyunzhoudyz/dyz-gongwen-skills** doubt on numbers: Verdict stands; the script also missed one derived share written in Chinese numerals: 「其中夜间27起，占三分之一」 (27/81) is not in the list.
- **t1/duyunzhoudyz/dyz-gongwen-skills** doubt on tone: 「打通」 here means something concrete (carrying the chat record over from bot to human agent, the list's plan 3), not the slogan sense; the true count is likely 0. Verdict is a pass either way.
- **t1/Liuxiangjian-ai/official-document-skill** doubt on coverage: P2 was matched to the intro sentence 「围绕智能客服机器人上线、工单系统迁移…」 rather than to line 19, but line 19 does say 「9月26日全部迁移完毕」, so the verdict stands on the right text anyway.
- **t1/Liuxiangjian-ai/official-document-skill** doubt on problems: Q4 was matched to the 基本情况 paragraph (line 7); the problem section's own line 37 also states it with 「招聘工作尚未启动」.
- **t1/Liuxiangjian-ai/official-document-skill** doubt on numbers: Not a misread of what it flagged, but the script missed a second derived figure written in words: 「其中夜间27起，占三分之一」 (27/81 worked out as a share; the list gives no share). Verdict is fail either way.
- **t1/Liuxiangjian-ai/official-document-skill** doubt on tone: 「打通」 is in 「（三）打通机器人转人工的聊天记录。」 where it means the concrete fix (carry chat history across to the human agent), not an empty verb; the true count is 0.
- **t2/octocat/Hello-World** doubt on structure: The script matched the third part to the bold sub-heading 「语音客服没有按计划上线」 (problem 3) instead of the real heading 「## 三、第四季度打算怎么做」 at line 59. The verdict is still right, because the real heading exists and comes in the right order, but the observed text points at the wrong line.
- **t1/octocat/Hello-World** recorded, not scored: {"em_dash": 0, "bold": 9, "emoji": 0, "inline_header_bullets": 0, "jinxing": 0}
- **t1/anthropics/skills** recorded, not scored: {"em_dash": 0, "bold": 17, "emoji": 0, "inline_header_bullets": 0, "jinxing": 0}
- **t1/op7418/Humanizer-zh** recorded, not scored: {"em_dash": 0, "bold": 0, "emoji": 0, "inline_header_bullets": 0, "jinxing": 0}
- **t1/larashero3-dotcom/lieflat-less-ai-tone** recorded, not scored: {"em_dash": 0, "bold": 0, "emoji": 0, "inline_header_bullets": 0, "jinxing": 0}
- **t1/MrGeDiao/shuorenhua** recorded, not scored: {"em_dash": 0, "bold": 4, "emoji": 0, "inline_header_bullets": 0, "jinxing": 0}
- **t1/duyunzhoudyz/dyz-gongwen-skills** recorded, not scored: {"em_dash": 1, "bold": 0, "emoji": 0, "inline_header_bullets": 0, "jinxing": 0}
- **t1/Liuxiangjian-ai/official-document-skill** recorded, not scored: {"em_dash": 0, "bold": 0, "emoji": 0, "inline_header_bullets": 0, "jinxing": 0}
- **t2/octocat/Hello-World** recorded, not scored: {"em_dash": 0, "bold": 13, "emoji": 0, "inline_header_bullets": 0, "jinxing": 0}
- **t2/anthropics/skills** recorded, not scored: {"em_dash": 0, "bold": 10, "emoji": 0, "inline_header_bullets": 0, "jinxing": 0}
- **t2/op7418/Humanizer-zh** recorded, not scored: {"em_dash": 0, "bold": 0, "emoji": 0, "inline_header_bullets": 0, "jinxing": 0}
- **t2/larashero3-dotcom/lieflat-less-ai-tone** recorded, not scored: {"em_dash": 0, "bold": 0, "emoji": 0, "inline_header_bullets": 0, "jinxing": 0}
- **t2/MrGeDiao/shuorenhua** recorded, not scored: {"em_dash": 0, "bold": 0, "emoji": 0, "inline_header_bullets": 0, "jinxing": 0}
- **t2/duyunzhoudyz/dyz-gongwen-skills** recorded, not scored: {"em_dash": 1, "bold": 0, "emoji": 0, "inline_header_bullets": 0, "jinxing": 0}
- **t2/Liuxiangjian-ai/official-document-skill** recorded, not scored: {"em_dash": 0, "bold": 0, "emoji": 0, "inline_header_bullets": 0, "jinxing": 0}

## Script fixes made during the runs (the rules unchanged; every run rescored with the fixed script)

- 23:04，第一个工具（t1 anthropics/skills）跑完后，按测试员 doubt 修一处：① 「结余 2.4 万元」是 24 万 − 21.6 万算出来的，正是检查表第 5 项点名不许的「节省了多少」，但它和清单里的培训费 2.4 万恰好相等，脚本按数值比对放过了；改为「结余、剩下、节省……」后面跟着的 2.4 万一律算自己算出来的数（truth.json worked_phrases）。同时只改了证据图上的提示文字：「缩短 1 分 30 秒」这类时长只用时长去解释来源（原来误标成 21.6 万占 24 万），不影响判定。
- 23:06，第二个工具（t1 op7418/Humanizer-zh）跑完后，按测试员 doubt 修一处：② 费用表的表头写着「金额（万元）」，格子里只写 15、4.2、2.4、21.6，脚本按没有单位的数比对，判成清单里没有；改为表头括号里写了单位的列，格子里的数按那个单位读（只影响数字检查）。
- 23:20，t1 全部跑完、t2 开跑前，按两个测试员（t1 dyz-gongwen-skills、t1 official-document-skill）的 doubt 修一处：③ 「其中夜间 27 起，占三分之一」是 27 ÷ 81 算出来的占比，正是检查表第 5 项不许的「自己算」，但脚本为了不把「三分钟」读错，故意跳过了「N 分之 M」，漏看了；改为「三分之一」「五分之二」这类分数按百分比读（只影响数字检查，只改 writing-runs 的 textcheck.py，summary-runs 已跑完不动）。t1 有三份写了「三分之一」（对照组、dyz-gongwen-skills、official-document-skill），三份数字检查本来就不过，判定都不变。另有两个测试员说「打通机器人转人工的聊天记录」里的「打通」是实指、不算套话；这条按检查表原文（truth tone 列了「打通」）不改，两份的套话都只算 1 处，判定都是过，不受影响。
- 23:24，t2 对照组跑完后，按测试员 doubt 修一处证据文字：④ 结构检查把「二、哪些没做好」下面的小标题「语音客服没有按计划上线」（含「计划」）当成了第四季度那一块，真正的「三、第四季度打算怎么做」在后面；判定本来就对，只是证据指错了行。改为先在最高一级标题里找三块，找齐了就显示这一级的，找不齐再往下一级放宽，最后一轮仍是原来的全部标题，所以过不过和原来完全一样，只改显示的标题（t1 七份和三份假稿的结构判定都没变）。
- 23:51，全部跑完、出证据图时自己发现、修一处证据图（不是测试员提的，判定不变）：⑤ 证据图按数字的写法去标红，同一个数在文中出现几次就标几次：t1 dyz-gongwen-skills 里「提高 15 个百分点」的 15 被标红时，连「7 月 15 日」「156 篇」「供应商 15 万元」也一起标了，「结余 2.4 万」也连带标了清单里有的「培训 2.4 万」。改为每个被挑出的数带上它前后各三个字（表格里再加这一行的第一格），只标这一处；14 份重新出图后，每份标红的处数都等于挑出的个数。只改 writing-runs 的 kit.py、textcheck.py；summary-runs 的图没有重出。
