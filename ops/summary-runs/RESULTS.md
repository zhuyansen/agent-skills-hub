# Meeting-summary test (第二十四期 AI 总结)

Each tool was cloned and installed from its README in a throwaway sandbox (ops/ppt-runs/sandbox, entrypoint
in/summary.py), then Claude Code (Claude Opus) summarised a made-up product meeting (in/fixtures/会议记录.txt, an
automatic transcript of about 5,000 字, see in/fixtures/README.md) from two requests in the person's words
(in/brief-t1.txt, in/brief-t2.txt; in/prompt.txt). Whenever a build stopped short of a finished summary it got the
reply in in/reply.txt, up to 10 times, within 20 minutes. A tester session with no tool loaded then checked the
document against the checklist in in/test.md, the same for every tool and both requests and fixed before the runs:
six checks scripted in in/kit.py against the answer key in/truth.json, one (invented) read by the tester.
octocat/Hello-World is the control: no tool installed. Usage is every Claude Code session a build started, priced at
API rates (score.py); "× control" divides by the control's usage on the same request.

## t1: 帮我总结一下这个会议记录。

| Tool | ★ | Opened | 字 | ≤800字 | 结论先行 | 决定 | 待办 | 数字 | 没定 | 没编 | Passed | Stops | Build min | Run min | Usage $ | × control | Install + tester $ | Ending |
|---|---:|---|---:|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| octocat/Hello-World | 0 | file | 2282 | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | 5/7 | 0 | 0.8 | 1.6 | 0.23 | 1.0 | 0.34 | finished |
| phuryn/pm-skills | 27762 | file | 2632 | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | 4/7 | 0 | 1.1 | 2.9 | 0.35 | 1.5 | 0.51 | finished |
| github/awesome-copilot | 40913 | file | 2826 | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | 2/7 | 1 | 1.6 | 3.3 | 0.37 | 1.6 | 0.49 | finished |
| composio-community/awesome-codex-skills | 17249 | file | 2636 | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ | 4/7 | 1 | 1.4 | 2.7 | 0.39 | 1.7 | 0.46 | finished |
| genspark-ai/genoffice | 11926 | file | 2363 | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | 5/7 | 1 | 2.1 | 3.5 | 0.52 | 2.3 | 0.44 | finished |
| NousResearch/hermes-agent | 261577 | file | 2781 | ✗ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | 3/7 | 0 | 1.1 | 2.8 | 0.36 | 1.6 | 0.51 | finished |
| steipete/summarize | 6789 | file | 942 | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | 5/7 | 0 | 0.6 | 3.2 | 0.18 | 0.8 | 0.58 | finished |

## t2: 帮我把这个会议记录整理成一份总结，发给没来开会的同事看。全文 800 字以内。第一段先写结论：这次会最后定了什么。然后列出所有拍板的决定，再列出所有待办，每一条写清楚谁负责、哪天之前做完。数字一律照原文写，不要改，也不要自己换算。讨论了但没定下来的事单独列出来，标明“没定”，不能写成已经定了。原文里没有的东西一个字都别编，包括负责人和截止日期。

| Tool | ★ | Opened | 字 | ≤800字 | 结论先行 | 决定 | 待办 | 数字 | 没定 | 没编 | Passed | Stops | Build min | Run min | Usage $ | × control | Install + tester $ | Ending |
|---|---:|---|---:|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| octocat/Hello-World | 0 | file | 631 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 7/7 | 0 | 1.5 | 2.2 | 0.27 | 1.0 | 0.33 | finished |
| phuryn/pm-skills | 27762 | file | 601 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 7/7 | 0 | 0.9 | 2.1 | 0.33 | 1.2 | 0.31 | finished |
| github/awesome-copilot | 40913 | file | 625 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | 6/7 | 1 | 1.4 | 2.6 | 0.38 | 1.4 | 0.32 | finished |
| composio-community/awesome-codex-skills | 17249 | file | 617 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 7/7 | 0 | 1.2 | 2.3 | 0.42 | 1.6 | 0.33 | finished |
| genspark-ai/genoffice | 11926 | file | 648 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | 6/7 | 1 | 1.9 | 2.9 | 0.46 | 1.7 | 0.32 | finished |
| NousResearch/hermes-agent | 261577 | file | 630 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 7/7 | 0 | 1.1 | 2.1 | 0.36 | 1.3 | 0.3 | finished |
| steipete/summarize | 6789 | file | 562 | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | 5/7 | 0 | 1.4 | 3.9 | 0.51 | 1.9 | 0.5 | finished |

## What the scripted checks found

| Brief | Tool | 决定 7 | 待办全对 6 | 没定标对 3 | 原文没有的数字 | 旧数字当现在 | 关键数字留下 10 | 闲聊 | 编的（测试员） |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|
| t1 | octocat/Hello-World | 7 | 6 | 3 | 0 | 0 | 10 | 咖啡机 | 2 |
| t1 | phuryn/pm-skills | 7 | 6 | 3 | 1 | 0 | 10 | 咖啡机 | 4 |
| t1 | github/awesome-copilot | 7 | 6 | 1 | 2 | 0 | 10 | - | 7 |
| t1 | composio-community/awesome-codex-skills | 7 | 6 | 3 | 1 | 0 | 10 | - | 10 |
| t1 | genspark-ai/genoffice | 7 | 6 | 3 | 0 | 0 | 10 | - | 3 |
| t1 | NousResearch/hermes-agent | 7 | 6 | 2 | 0 | 0 | 10 | 咖啡机 | 7 |
| t1 | steipete/summarize | 7 | 6 | 3 | 0 | 0 | 10 | 咖啡机、螺蛳粉 | 0 |
| t2 | octocat/Hello-World | 7 | 6 | 3 | 0 | 0 | 2 | - | 0 |
| t2 | phuryn/pm-skills | 7 | 6 | 3 | 0 | 0 | 2 | - | 0 |
| t2 | github/awesome-copilot | 7 | 6 | 3 | 0 | 0 | 5 | - | 1 |
| t2 | composio-community/awesome-codex-skills | 7 | 6 | 3 | 0 | 0 | 2 | - | 0 |
| t2 | genspark-ai/genoffice | 7 | 6 | 3 | 0 | 0 | 2 | - | 2 |
| t2 | NousResearch/hermes-agent | 7 | 6 | 3 | 0 | 0 | 2 | - | 0 |
| t2 | steipete/summarize | 7 | 6 | 2 | 0 | 0 | 2 | - | 1 |

## Notes

- **t1/phuryn/pm-skills**: the tester's copy of undecided differs from the script's verdict here
- **t1/genspark-ai/genoffice**: the tester's copy of conclusion differs from the script's verdict here
- **t1/NousResearch/hermes-agent**: the tester's copy of numbers differs from the script's verdict here
- **t1/steipete/summarize**: the tester's copy of todos differs from the script's verdict here
- **t1/phuryn/pm-skills** doubt on numbers: Two of the three hits look like misreads. 「4.6」: the record says 「应用商店评分还是 4.6 分」, so the figure is the record's own. The summary only dropped the unit 分. 「20 号」: in 「孙浩说 20 号来不及测完。」 the old date is reported as what was said, not given as the launch date; the same paragraph goes on 「周婷当场决定推迟一周」, and the summary everywhere gives 11 月 27 日 as the launch date. 「约 16 分钟」 is a real hit: it is worked out from 10:00–10:16, and the record never states a duration. So the FAIL stands even if the other two hits are dropped.
- **t1/phuryn/pm-skills** doubt on undecided: Row 14 says 「我们在考虑」, which tells the reader the point is still open. The script's marks include 考虑中 but not 在考虑. Also, the row is the loose ask to reply to users (it is not a statement that WeChat login was decided), and it does not present the point as decided. A reviewer may judge 「在考虑」 to be a not-decided mark.
- **t1/github/awesome-copilot** doubt on conclusion: The script took the 基本信息 list starting '开始时间：10:00（当地时间；记录未注明时区，UTC 时间待定）' as the first block because '开始时间' is not in its meta pattern. Skipping it would not change the verdict: the blocks that follow (参会情况, 议程) contain no decisions either; the first decisions appear only under '## 4. 一句话总结'.
- **t1/github/awesome-copilot** doubt on numbers: Partly misread: '20', '27', '13' come from dates written as '11-20', '11-27', '11-13', which are record dates (11 月 20/27/13 日) in another notation. The 'old figure as current' hit, '20 号来不及' in D3's reason column ('2.0 上线从 11-20 推迟到 11-27'), is given as the old date that was replaced, not as the current one. The remaining hits are real: '约 16 分钟' is worked out from 10:00–10:16, and '最后更新：2026-11-08' is a date the record does not give. So the verdict would stand even without the misreads.
- **t1/github/awesome-copilot** doubt on undecided: U1 and U3 are marked as not decided in '## 8. 暂缓 / 未决事项' ('等拿到平板用户占比，下次周会再讨论', '周婷还没想好，以后再说'). The script fails them because of unmarked mentions elsewhere: the agenda line '其他：安卓平板适配、微信登录、竞品改版', the background bullets under '**8. 其他**', and todo rows A14/A15. Under the checklist's 'wherever one appears' rule, that reading is literal, not a misread. Left for the reviewer.
- **t1/composio-community/awesome-codex-skills** doubt on numbers: No misread. 「11 月 25 日」 really is a date the record never gives: it is the tool's 建议 deadline for 孙浩's regression rounds. The other 建议 dates (11 月 6/10/12/20 日) pass only because those dates appear elsewhere in the record. Check 7 lists them as invented.
- **t1/composio-community/awesome-codex-skills** doubt on undecided: No misread. The 留存拆分 item under 待定问题 is a soft ask, not one of the three open points, and does not affect this check.
- **t1/genspark-ai/genoffice** doubt on conclusion: The script took the metadata table (日期和时间 / 地点 / 参会人 / 记录人 rows) as the opening block. Those rows only give the meeting's date, time, place and people, which the checklist says to skip; the one questionable row is 「记录人 | 待定」. After the table and the heading 「# 摘要」, the first paragraph is 「本次产品周会回顾了上周数据和支付重复扣款事故，并逐项讨论 2.0 版本的上线安排、会员价格、新手引导、推送时间和 11 月投放。会议决定：2.0 推迟到 11 月 27 日上线；会员定价为月卡 12 元、年卡 98 元；采用 3 步新手引导；默认提醒改为晚 8 点……」. Its first 150 字 contain at least 4 decisions (D1, D2, D4, D5). If 记录人 counts as a people line, this check should pass. A reviewer should decide.
- **t1/NousResearch/hermes-agent** doubt on numbers: All 71 'extra' figures are [mm:ss] source timestamps the summary cites (e.g. `[01:23]`, `[05:05]`, `[14:55]`). They are the record's own timestamps [00:01:23] etc. with the hours dropped, not meeting figures. Every one corresponds to a real line in the record. The kit lists no other non-matching figure, so the fail rests only on the timestamps.
- **t1/NousResearch/hermes-agent** doubt on undecided: The unmarked mention in 八 refers to the follow-up of collecting the tablet user share (A14), not to whether tablet adaptation is decided. It does not present the open point as decided. The point itself is marked 暂不定 in 五, and the A14 row says 供下次周会讨论. A reviewer may judge this mention does not need its own 没定 mark.
- **t1/steipete/summarize** doubt on todos: Possible misread: T3's owner and due date are in the same paragraph (item) but in different sentences. 「达人名单和排期要在 11 月 12 日前发到群里。」 has the right date (11 月 12 日) but no owner; 赵敏 is named three sentences earlier, in the sentence the script picked. The script compares sentence by sentence. A reader would most likely take 赵敏 as the owner, but the sentence does not name one, so a reviewer should decide whether this paragraph counts as one item.

## Runs that do not count (redone; their files are in out/aborted/)

- out/aborted/t1-octocat__Hello-World-fixture-v1：第一次对照组（22:14，跑得通，验收全流程正常）。它暴露了两处我方的问题，在任何计分运行之前改掉：① 会议记录里我后来插的几段对话让时间戳重复、倒序，抬头写 10:00–10:44 而逐字稿只到约 20 分钟，AI 在纪要里点出这件事并写了「约 20 分钟」，被数字检查判错，这和工具无关；已把时间戳重排成递增、抬头改为 10:00–10:16。② 「先写结论」的脚本没跳过表头里的「下次周会：…」和「> 依据：…」这种出处说明，判错了开头（测试员在 doubt 里指出）；已按检查表原意补上，test.md 第 2 项的措辞同步写明。对照组在新材料上重跑，计分用重跑的。

## Script fixes made during the runs (the rules unchanged; every run rescored with the fixed script)

- 22:24–22:30，第一个工具（t1 phuryn/pm-skills）跑完后，按测试员 doubt 指出的三处脚本误读修正，规则本身不变，score.py 对所有运行用修正后的脚本重算：① 「4.6（1,284 条评价）」里的 4.6 被当成 4 月 6 日（M.D 后面跟括号就算日期），改为只有括号里是周几才算日期；② 旧数字原来只看所在的一句，「孙浩说 20 号来不及测完。」被判成把旧上线日期当现在（下一句就是「周婷当场决定推迟一周」）：改为看所在的整段、列表项或表格行里有没有新数字，或者旧数字前后 20 个字内有没有「原定、改为、推迟」这类说明（只看整段会把隔几句的无关「降到」也算进去，故限 20 字）；③ 「在考虑」没算作「没定」的标记（「考虑中」算），补上「在考虑、还在考虑、再想想」等同义说法。
- 22:28，第二个工具（t1 github/awesome-copilot）跑完后，按测试员 doubt 再修两处脚本误读：④ 「11-20」「11-27」「11-13」这种带短横的日期被当成单独的 20、27、13（原文里只有「11 月 27 号」这类写法），改为认成日期（「7-9 月」「2-3 天」这种范围不算），答案里所有日期写法同步加上短横；⑤ 「开始时间、结束时间」算会议信息（这条不改变任何结论）。测试员同一次提出的另一处疑问（没定的事在议程、背景里提到时没标「没定」）是检查表原文「出现的地方都要标没定」，不属于误读，不改，留给复核。
- 22:33，第四个工具（t1 genspark-ai/genoffice，交的是 Word）跑完后，按测试员 doubt 再修一处：⑥ 开头的会议信息表第一格写的是「日期和时间」「参会人」「记录人」，脚本只认「日期：」这种带冒号的写法，把整张信息表当成了开头；改为表格行第一格以会议信息词开头就跳过。
- 22:37，第五个工具（t1 NousResearch/hermes-agent）跑完后，按测试员 doubt 再修一处：⑦ 纪要里引用原文时间戳的写法「[01:23]」（省了小时）被当成 71 个原文没有的时间；改为把方括号、反引号里的时间戳当作引用，只要原文真有这个时间点就算对（编出来的时间点照样判错）。同一次 doubt 里的另一处（没定的平板适配在第八部分的跟进事项里没标「没定」）是检查表原文，不改，留给复核。
- 22:40，第六个工具（t1 steipete/summarize，写的是成段文字）跑完后，按测试员 doubt 再修一处：⑧ 待办写在一段话里时，负责人和截止日期常在同一段的前后两句（「赵敏……。达人名单和排期要在 11 月 12 日前发到群里。」），脚本逐句比对，判成没写负责人；检查表原文是「同一行、同一项」，改为一段之内没点名的句子沿用前面最后点到的人。
- 11-08 23:53（第二十五期跑完后补，只改证据图，判定不变）：⑨ 证据图按数字的写法标红，同一个数出现几次就标几次：t1 github/awesome-copilot 和 t1 phuryn/pm-skills 里被挑出的是「约 16 分钟」的 16，图上连「10:16」的 16（copilot 那份还有表里的「A16」）一起标了红。改为每个被挑出的数带上它前后各三个字（表格里再加这一行的第一格），只标这一处（和 writing-runs 同一处改法）；重出了这两张图，其余 12 张本来就只标一处、没重出。改前改后 14 个运行的判定逐项比对完全一样。
