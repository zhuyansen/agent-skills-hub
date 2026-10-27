You are testing a small web app that someone who cannot code asked an AI tool to build. You are the tester, not the builder: do not open, read or change the app's source files, and do not fix anything in it. Use the app only through a browser, the way a person would. (Reading ~/work/output/START.txt to learn how to start it is fine.)

What they asked for, in their words:
「帮我做一个记账小网页：每次花钱记一笔（花了多少、买了什么），页面上能看到一共花了多少，关掉浏览器再打开，记录还在。」

How to open it: `file_url()` (from tester_kit) is what double-clicking ~/work/output/index.html opens, or None when there is no index.html. `app_url()` is where to use the app for the checks: the same index.html from a local address (the test browser's storage for file:// pages is unreliable), or, when there is no index.html, the address served by the one command in ~/work/output/START.txt (it starts that command for you). If neither works, the app could not be opened: record that and stop.

Use the helpers in /in/tester_kit.py (read its docstring first): `Browser` starts Chromium, records console errors and requests to outside hosts, and takes screenshots. Write your test as ~/tester/test.py and run it with python3 (start it with `import sys; sys.path.insert(0, "/in")`). Fix your test script as often as you need; never the app. Run all checks in one fresh profile: if you rerun the script from the start, delete ~/tester/profile first.

Checks, in order:
1. open: open it the way a person would, with `file_url()` (or `app_url()` when there is no index.html). Pass if the page shows the app (not blank, not an error page). Then use `app_url()`, in the same tab (`page.goto`), for every other check.
2. add: record one expense: 25 spent on 午饭 (amount 25, item 午饭). Pass if the list shows it with both its amount and its item.
3. total: record 12.5 for 咖啡 and 4 for 地铁. Pass if the total shown on the page is 41.5 (41.50 or ¥41.5 count).
4. reopen: close the app and open it again with `restart` (it opens the app in a new tab, closes the old tab, then reloads). Pass if all three entries are there and the total still shows 41.5.

Rules:
- Enter data the way the page invites you to: its own inputs and buttons (or the Enter key, if that is how it works). If the page has no way to enter an amount and an item, the check fails; describe what it offers instead.
- A check passes only on what is visible on the page. Never read or write localStorage, cookies or the app's variables to decide or to help a check, and never call the app's own functions.
- Take a screenshot after every check: shots/1-open.png, shots/2-add.png, shots/3-total.png, shots/4-reopen.png.
- If a check fails, still try the later ones where that makes sense, and say why it failed.

At the end write ~/tester/report.json:
{"opened_by": "file" | "command" | "failed", "start_command": "<the START.txt command, or empty>", "url": "<what you opened>",
 "checks": [{"id": "open" | "add" | "total" | "reopen", "pass": true | false, "observed": "<what the page showed, with the numbers>", "shot": "shots/<file>.png"}],
 "notes": "<anything a person would trip over: language, layout, confusing steps>"}
Then print one line: REPORT: ~/tester/report.json
