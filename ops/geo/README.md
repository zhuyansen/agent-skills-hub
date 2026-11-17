# GEO citation panel — the weekly Measure ritual

Baseline problem this fixes: the Glasser 0/60 citation check (2026-11) left **no repo record**
(only 精读笔记/batches/gefei1.md:852), and the 2026-11-16 Reach check showed the live /best/
set was rebuilt in Nov *after* the last Common Crawl window. A one-off number cannot tell
Cite-layer failure from indexation lag. This panel is the repeatable instrument.

## Files

- `questions.json` — 40 fixed questions: 34 active scenarios (from `frontend/scripts/scenario-keywords.json`,
  `seo_keyword` when set) + 6 brand/entity questions. Regenerate when scenarios change; keep ids stable.
- `panel_score.py` — pure scoring, `--selftest`. Calibers kept separate:
  - **page_cited**: engine cited the exact target page
  - **site_cited**: engine cited any agentskillshub.top URL
  - **named**: answer mentions the brand
  - **first_pick**: our site is the first cited URL (or first brand named when nothing is cited)
- `panel/results-<date>.json` — one row per (engine, question): `{engine, question_id, question,
  answer_text, citations, scores}`. **Commit every run.** The summary markdown is `panel_score.py score <file>`.
- `reach_check.py` — the Reach-layer companion (gates, CC drift, Bing spot check); run after deploys
  and after each new Common Crawl release (~monthly, next window CC-MAIN-2026-47/48).

## Cadence

Weekly, same day. 40 questions × engines below. Record even when the answer is "not cited":
zeros are the signal. Compare week-over-week per caliber, never mix page_cited with named.

## Execution paths (pick one; all record into the same JSON)

1. **Perplexity sonar API** (cleanest: native `citations` array). Needs `PERPLEXITY_API_KEY` in env.
   POST https://api.perplexity.ai/chat/completions, model `sonar`, one question per call;
   map `citations` + answer text into a row, score with `panel_score.score`.
2. **geosearchconsole.co Citation Gap** (`/ai-citation-gap-tool`, prompt + brand → pages AI cites
   for rivals vs you; ChatGPT/Claude/Gemini behind it). Free anonymous quota is small; Google
   sign-in raises it. Browser-run a starter subset, paste results into rows. Their AI Visibility
   tool is crawler reachability, NOT an answer panel — don't confuse the two.
3. **Manual paste**: ask each engine the fixed question in its web UI, save answer + citation links
   into a row. Slowest, zero dependencies, always available.

No path is wired to auto-run here: engine keys are the owner's to supply, and the anonymous
web quota cannot carry 40 questions. The kit makes whichever path chosen repo-recorded.

## Reading the result (2026-11-16 context)

- Reach gates: PASS (GitHub Pages, 6 UAs identical 200, pre-rendered HTML).
- Bing live index: 19/20 CC-missing pages INDEXED; zh twins 6/6 INDEXED; only 3d-mcp absent.
- Common Crawl: Oct window holds the retired scenario set; Nov rebuilds not yet in training lane.
- Therefore a low page_cited rate now points at **Cite-layer selection** (BLUF, citable stats,
  authority/mentions), not at crawl access or Bing freshness. Re-check CC drift monthly;
  re-run this panel weekly; the two together separate the lanes.
