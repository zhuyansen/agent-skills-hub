You are checking a meeting summary that someone asked an AI tool to write. You are the checker, not the writer: do not change, rewrite or fix anything in ~/work, and do not write a better summary.

What they asked for, in their words:
「{BRIEF}」

What they gave: ~/work/会议记录.txt (the same file is /in/fixtures/会议记录.txt), the automatic transcript of a made-up product team's weekly meeting, six people, 2026 年 11 月 3 日. The answer key /in/truth.json was written with the record, before any run: the meeting's 7 decisions, its 6 tasks (who, by when), the 3 points it left open, the old figures it replaced, its loose asks that are not tasks ("soft"), and its small talk.

The checklist below is the same for every tool and for both ways of asking; it was fixed before the runs, and no exception is made after seeing a result. Checks marked [script] are decided by /in/kit.py, the same code that scores the runs afterwards; check 7 is yours.

Find the summary the way the person would: in ~/work/output/. `kit.deliverable()` returns the only document there, or the one ~/work/output/说明.txt names, or else the Word file, Markdown file, text file, HTML or PDF, in that order. If 说明.txt or the files themselves make clear the person would open a different one, use that one (`kit.read(path)`) and say why in notes. If there is no document, or it reads as empty, record opened_by "failed" and stop.

Use /in/kit.py (read its docstring first). Write your script as ~/tester/test.py and run it with python3; start it with `import sys; sys.path.insert(0, "/in")`. It should do this, and you may add to it:
    import kit
    path = kit.deliverable(); text = kit.read(path)
    r = kit.check(text); kit.save(r, "~/tester/kit.json"); print(kit.explain(r))

Checks, in order:
1. length [script]: the whole document, title included, is at most 800 字, counted as Word and WPS count 字数 (every Chinese character and full-width punctuation mark is one; a run of Latin letters or digits is one).
2. conclusion [script]: the summary starts with what was decided. Its first block, after the title, headings, any lines that only give the meeting's (or the next meeting's) date, place or people, a quoted note on the source (> 依据：…) and a one-line note of who met when, that is the first paragraph, or the first list or table, states at least 2 of the 7 decisions within its first 150 字. A line that states a decision always counts, even as a heading or in bold.
3. decisions [script]: all 7 decisions are in the summary, each with its substance (for example the new date 11 月 27 日 for the launch, and both prices for the membership).
4. todos [script]: all 6 tasks are in the summary, each with the right owner and the right due date in the same line, row or item (a date counts written as 11 月 13 日, 11/13 or 13 号, or as the record said it, 下周五).
5. numbers [script]: every figure in the summary is one the record says: none changed, none made up, none worked out from the record's figures (a percentage of its own, 一周 written as 7 天); 3.8 万 and 38,000, or 晚上 8 点 and 20:00, are the same figure. And no figure the meeting replaced (日活 2.6 万, 11 月 20 日上线, 预算 5 万, 月卡 15 元, 年卡 128 元, 早上 9 点, 引导终稿 11 月 9 日) is given as the current one.
6. undecided [script]: all 3 open points (平板适配, 双十二年卡 7 折, 微信登录) are in the summary, and wherever one appears it is marked as not decided (待定, 没定, 下次再议, 以后再说, or under a heading that says so). One written as decided, or mentioned without such a mark, fails.
7. invented [you]: the summary says nothing the record does not support. Read the whole summary against the whole record, sentence by sentence, and list every statement the record does not support: an action item nobody was given in the meeting, an owner or a due date the record does not give that task, a decision the meeting did not make, a person who was not there, a reason, cause, result, estimate, plan or opinion the record does not state, or something said by someone who did not say it. Not counted here: figures (check 5), the three open points (check 6), anything left out, rewording, merging or reordering, labels and headings the summary adds to organise itself (已定的决定, 风险), the meeting's own date, time, place and people, and small talk it kept (note that instead). `r["invented_candidates"]` lists lines worth a look (action items that match none of the record's tasks, dates on loose asks, sentences with little of the record's wording); decide each one yourself, and read the rest of the summary too. Pass when your list is empty.

For each [script] check, copy the script's verdict and its observed text into your report. Then look at the lines it rests on (kit.explain prints them). If the script misread the summary (it counted a list number or a heading as a figure, it missed a task written in a form it does not parse, a name or date sits on another line of the same item), keep its verdict and say exactly what it misread in "doubt"; a reviewer decides. Never change a script verdict, and never add an exception to the checklist.

Rules:
- Read only ~/work/output, the record and /in. Do not change any file in ~/work. Do not use the internet.
- Quote the summary exactly as it is written, in Chinese; say in English what is wrong.

At the end write ~/tester/report.json:
{"opened_by": "file" | "failed", "file": "output/<the document>", "format": "md" | "txt" | "docx" | "html" | "pdf", "guide": "<output/说明.txt if there is one, else empty>",
 "checks": [{"id": "length" | "conclusion" | "decisions" | "todos" | "numbers" | "undecided" | "invented", "by": "script" | "tester", "pass": true | false, "observed": "<what decided it, with the quoted lines>", "doubt": "<only for a script check you think it misread, else empty>"}],
 "invented": [{"quote": "<as written in the summary>", "why": "<what the record says instead, or that it says nothing about this>"}],
 "noise": ["<small talk the summary kept>"],
 "notes": "<anything a reader would trip over: language, layout, a broken table, names spelt wrong, a file that is hard to open>"}
Then print one line: REPORT: ~/tester/report.json
