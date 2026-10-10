# Code review test, 2026-10-10

12 pull requests, 8 with a planted defect, 4 clean. See make_fixture.py and score_review.py.

| Tool | ★ | Found | False alarms on clean | Findings per PR | Min | Reviewed by | Missed |
|---|---:|---:|---:|---:|---:|---|---|
| Control: Claude Code, no tool | - | 8/8 | 0 | 1.8 | 1 | Claude Opus 5.5 | - |
| awesome-skills/code-review-skill | 1914 | 8/8 | 0 | 1.8 | 1 | Claude Opus 5.5 | - |
| amElnagdy/guard-skills | 1153 | 8/8 | 0 | 1.4 | 2 | Claude Opus 5.5 | - |
| vikingmute/review-forge | 220 | 8/8 | 0 | 1.3 | 2 | Claude Opus 5.5 | - |
| nathankim0/clean-architecture-skills | 90 | 8/8 | 0 | 2.7 | 2 | Claude Opus 5.5 | - |
| spencermarx/open-code-review | 331 | 8/8 | 0 | 7.2 | 11 | Claude Opus 5.5 | - |
| kenn-io/roborev | 1746 | 8/8 | 0 | 0.9 | 13 | gpt-6-astra | - |
| adamjgmiller/adamsreview | 243 | 7/7 | 0 | 0.5 | 30 | Claude Opus 5.5 | - |
| codexstar69/bug-hunter | 487 | 7/8 | 0 | 0.8 | 3 | Claude Opus 5.5 | pr-12 |
| alibaba/open-code-review | 43912 | 7/8 | 0 | 0.6 | 7 | gpt-6-astra | pr-12 |
| imbue-ai/vet | 519 | 7/8 | 0 | 1.1 | 18 | gpt-6-astra | pr-03 |
| hyhmrright/brooks-lint | 1506 | 5/8 | 0 | 0.9 | 3 | Claude Opus 5.5 | pr-04, pr-10, pr-12 |
| Gentleman-Programming/gentleman-guardian-angel | 1180 | 5/8 | n/a (rules file written for the test) | 6.0 | 9 | gpt-6-astra | pr-01, pr-04, pr-10 |
| getsentry/warden | 414 | 4/8 | 0 | 0.5 | 25 | gpt-6-astra | pr-03, pr-04, pr-10, pr-12 |

Could not run:

- w1ckedxt/cynical-sally: It sends the diff to its own hosted service, which answered Service Unavailable.
- HexmosTech/git-lrc: It sends the diff to a LiveReview server; there is none to review with locally.
- GGGODLIN/claude-pr-review: It reviews pull requests on Bitbucket through the Bitbucket API; it has no way to review a local branch.

Notes:

- Gentleman-Programming/gentleman-guardian-angel: It checks code against a rules file you write. The test repo had none, so the agent wrote one from gga's Python example; its 30 failures on clean pull requests are that file's docstring and type-hint rules, not false alarms.
- alibaba/open-code-review: It skipped the two pull requests that only change tests, so the weakened test went unreviewed.
- adamjgmiller/adamsreview: Hit the 30-minute limit with one pull request unfinished; it found the defect in all seven it finished.
- codexstar69/bug-hunter: Treats test files as context only, by design, so it does not report a weakened test.
- hyhmrright/brooks-lint: Reviews for design decay (coupling, complexity), not security: the logged card token and the weakened test scored 100/100.
- getsentry/warden: Its verification pass threw out candidate findings on the pull requests it missed, the SQL injection among them.
- spencermarx/open-code-review: Several reviewer personas write one report: every defect is in it, among 7 findings per pull request.
- kenn-io/roborev: Runs in the background on every commit; here it reviewed with gpt-6-astra through OpenCode and still found all eight.
