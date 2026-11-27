You are checking a quarterly work report that someone asked an AI tool to write for them. You are the checker, not the writer: do not change, rewrite or fix anything in ~/work, and do not write a better report.

What they asked for, in their words:
「{BRIEF}」

What they gave: ~/work/季度事实清单.md (the same file is /in/fixtures/季度事实清单.md), the facts of a made-up customer-service team's third quarter of 2026: 4 projects with their numbers, 4 things that went wrong, the money spent, 4 plans for the fourth quarter. Nothing else about the team exists. The answer key /in/truth.json was written with the list, before any run: what each project, problem and plan must say, the old figures that must not be given as current, and the lists of stock phrases, empty elevation and parallelism the report is counted against (after humanizer-zh's patterns, from Wikipedia's Signs of AI writing, and the boilerplate of Chinese work reports).

The checklist below is the same for every tool and for both ways of asking; it was fixed before the runs, and no exception is made after seeing a result. Checks marked [script] are decided by /in/kit.py, the same code that scores the runs afterwards; check 6 is yours.

Find the report the way the person would: in ~/work/output/. `kit.deliverable()` returns the only document there, or the one ~/work/output/说明.txt names, or else the Word file, Markdown file, text file, HTML or PDF, in that order. If 说明.txt or the files themselves make clear the person would open a different one, use that one (`kit.read(path)`) and say why in notes. If there is no document, or it reads as empty, record opened_by "failed" and stop.

Use /in/kit.py (read its docstring first). Write your script as ~/tester/test.py and run it with python3; start it with `import sys; sys.path.insert(0, "/in")`. It should do this, and you may add to it:
    import kit
    path = kit.deliverable(); text = kit.read(path)
    r = kit.check(text); kit.save(r, "~/tester/kit.json"); print(kit.explain(r))

Checks, in order:
1. length [script]: the whole report, title included, is 1,200 to 1,800 字, counted as Word and WPS count 字数 (every Chinese character and full-width punctuation mark is one; a run of Latin letters or digits is one).
2. structure [script]: the report has headings for three parts, in this order: what got done this quarter, what did not go well, the plans for the fourth quarter (one heading may cover the last two).
3. coverage [script]: the 4 projects (机器人 46%, 工单迁移, 知识库 412 篇, 满意度 4.3 分) and the 4 plans (语音客服 11 月底, 招 2 名夜班, 聊天记录 11 月 15 日, 目标 55%) are all in it, each with its key fact.
4. problems [script]: the 4 problems (夜间只有 1 人值班, 转人工要重说, 语音客服没做成, 主管离职岗位空着) are all in it, each with a figure or cause from the list that says how bad it was or why, and none is turned into a success (奠定基础, 积累了经验, 影响有限, 契机 and the like where the problem is stated).
5. numbers [script]: every figure in the report is one the list gives: none changed, none made up, none worked out from the list's figures (a growth rate, a difference, a share, 节省了多少); 21.6 万 and 216,000, or 2 分 40 秒 and 160 秒, are the same figure. And no old figure (解决率 31%, 接待量 12,400 单, 95 秒, 满意度 4.1 分, 4 分 10 秒) is given as the current one.
6. facts [you]: the report says nothing the list does not support. Read the whole report against the whole list, sentence by sentence, and list every statement the list does not support: praise or reactions (客户好评, 领导认可, 团队士气高涨), credit or causes the list does not give, results or effects it does not state (节省人力, 提升了转化), events, people or plans that are not in it (for example a plan to fill the supervisor's post, which the list does not have), or a problem said to be solved when the list says it is not. Not counted here: figures (check 5), stock phrases (check 7), anything left out, rewording, headings and labels the report adds to organise itself, and plain conclusions that follow directly from the list (21.6 万 against a budget of 24 万 is within budget). `r["fact_candidates"]` lists lines worth a look (praise and credit words, sentences with little of the list's wording); decide each one yourself, and read the rest of the report too. Pass when your list is empty.
7. tone [script]: stock phrases and empty elevation together come to at most 2 per 1,000 字: official boilerplate (取得了显著成效, 齐心协力, 扎实推进, 赋能, 抓手, 在……的领导下), vague verbs with no figure in their clause (持续优化, 进一步提升), and elevation or slogans (奠定了坚实基础, 迈上新台阶, 展望未来, 砥砺前行, 再创佳绩, 彰显了). The lists are truth.json "tone".
8. parallel [script]: at most 1 排比: a contrast frame (不是……而是, 不仅……更), three or more four-character phrases in a row of which two are stock ones (齐心协力、攻坚克难、勇于担当), or three or more clauses in a row opening with the same two characters (我们……，我们……，我们……).

For each [script] check, copy the script's verdict and its observed text into your report. Then look at the lines it rests on (kit.explain prints them). If the script misread the report (it counted a list number or a heading as a figure, it took a plain word for a stock phrase where it means something concrete, a fact sits in a sentence it did not read together), keep its verdict and say exactly what it misread in "doubt"; a reviewer decides. Never change a script verdict, and never add an exception to the checklist.

Rules:
- Read only ~/work/output, the list and /in. Do not change any file in ~/work. Do not use the internet.
- Quote the report exactly as it is written, in Chinese; say in English what is wrong.

At the end write ~/tester/report.json:
{"opened_by": "file" | "failed", "file": "output/<the document>", "format": "md" | "txt" | "docx" | "html" | "pdf", "guide": "<output/说明.txt if there is one, else empty>",
 "checks": [{"id": "length" | "structure" | "coverage" | "problems" | "numbers" | "facts" | "tone" | "parallel", "by": "script" | "tester", "pass": true | false, "observed": "<what decided it, with the quoted lines>", "doubt": "<only for a script check you think it misread, else empty>"}],
 "invented": [{"quote": "<as written in the report>", "why": "<what the list says instead, or that it says nothing about this>"}],
 "worst": ["<up to three sentences of the report that read most like boilerplate, quoted exactly>"],
 "notes": "<anything a reader would trip over: language, layout, a broken table, a file that is hard to open, the person's name or the team's left as placeholders>"}
Then print one line: REPORT: ~/tester/report.json
