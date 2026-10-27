You are testing a small web app that someone who cannot code asked an AI tool to build. You are the tester, not the builder: do not open, read or change the app's source files, and do not fix anything in it. Use the app only through a browser, the way a person would. (Reading ~/work/output/START.txt to learn how to start it is fine.)

What they asked for, in their words:
「做一个家庭记账本网页：能记收入和支出（金额、类别、日期、备注），能按月看收入、支出和结余，能看每个类别花了多少（最好有图），可以设每月预算、超了要提醒，还能把记录导出成 Excel 表格。数据存在我电脑上就行。」

How to open it: `file_url()` (from tester_kit) is what double-clicking ~/work/output/index.html opens, or None when there is no index.html. `app_url()` is where to use the app for the checks: the same index.html from a local address (the test browser's storage for file:// pages is unreliable), or, when there is no index.html, the address served by the one command in ~/work/output/START.txt (it starts that command for you). If neither works, the app could not be opened: record that and stop.

Use the helpers in /in/tester_kit.py (read its docstring first): `Browser` starts Chromium, records console errors and requests to outside hosts, saves downloads to ~/tester/downloads and takes screenshots. Write your test as ~/tester/test.py and run it with python3 (start it with `import sys; sys.path.insert(0, "/in")`). Fix your test script as often as you need; never the app. Run all checks in one fresh profile: if you rerun the script from the start, delete ~/tester/profile and ~/tester/downloads first. Today's real date is in October 2026; the app's own default month should be October 2026.

Checks, in order:
1. open: open it the way a person would, with `file_url()` (or `app_url()` when there is no index.html). Pass if the page shows the app (not blank, not an error page). Then use `app_url()`, in the same tab (`page.goto`), for every other check.
2. record: enter one income and three expenses, each with its date, category and amount, and the note where the app has a note field:
   - income 5000, category 工资, 2026-10-01, note 十月工资
   - expense 120, category 餐饮, 2026-10-05, note 午饭
   - expense 30, category 交通, 2026-10-08, note 地铁
   - expense 80, category 餐饮, 2026-10-12, note 晚饭
   Use the app's own categories when it has a fixed list (pick the closest: 工资/薪资/收入 for the income, 餐饮/饮食/吃饭 and 交通/出行 for the expenses). Pass if all four records appear with the right amount, category and date.
3. month: Pass if October 2026 shows income 5000, expenses 230 and balance (结余) 4770.
4. category: Pass if the page shows, for October, 餐饮 200 and 交通 30 (a chart's labels, legend or tooltip, or a table, all count; read the numbers, do not guess them from bar lengths).
5. by-month: enter an expense of 999, category 购物 (or the closest), 2026-09-15. Switch to September 2026: pass if it shows that 999 and September's expenses as 999; then switch back to October 2026: it must still show income 5000, expenses 230, balance 4770.
6. budget: set a monthly budget of 200 for October 2026. October's spending (230) is over it. Pass if the page shows a visible warning that the budget is exceeded (text, a banner, a dialog, or a colour change that comes with words). If the app only has budgets per category, set 餐饮 to 150 instead (its 200 is over it) and say so.
7. export: use the app's export. Pass if a file downloads and it contains all five records (amounts 5000, 120, 30, 80 and 999). An .xlsx or .xls file is what was asked for; a .csv also passes, but say which it was. Read .xlsx with openpyxl (`pip install --user openpyxl` if it is missing).
8. reopen: close the app and open it again with `restart` (it opens the app in a new tab, closes the old tab, then reloads). Pass if all five records are still there and October still shows income 5000, expenses 230, balance 4770.

Rules:
- Enter data the way the page invites you to: its own inputs and buttons. If the page has no way to do something a check needs, the check fails; describe what it offers instead.
- A check passes only on what is visible on the page (or, for export, in the downloaded file). Never read or write localStorage, IndexedDB, cookies or the app's variables to decide or to help a check, and never call the app's own functions.
- Take a screenshot after every check: shots/1-open.png, shots/2-record.png, ... shots/8-reopen.png.
- If a check fails, still try the later ones where that makes sense, and say why it failed.

At the end write ~/tester/report.json:
{"opened_by": "file" | "command" | "failed", "start_command": "<the START.txt command, or empty>", "url": "<what you opened>",
 "checks": [{"id": "open" | "record" | "month" | "category" | "by-month" | "budget" | "export" | "reopen", "pass": true | false, "observed": "<what the page or the file showed, with the numbers>", "shot": "shots/<file>.png"}],
 "export_file": "<downloads/<name>, or empty>",
 "notes": "<anything a person would trip over: language, layout, confusing steps>"}
Then print one line: REPORT: ~/tester/report.json
