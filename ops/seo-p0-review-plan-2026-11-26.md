# SEO + GEO P0 Review Plan (`seo-geo-p0-1126`)

- **Ship date:** `2026-11-26` (worktree `seo-geo-p0-1126`)
- **Frozen baseline:** [`ops/gsc/baselines/2026-11-26-p0-seo-geo-baseline.json`](gsc/baselines/2026-11-26-p0-seo-geo-baseline.json)
- **Interactive HTML Hub:** [`ops/seo-p0-review-hub-2026-11-26.html`](seo-p0-review-hub-2026-11-26.html)
- **Checkpoints:** **D+7** (`2026-12-03`) · **D+14** (`2026-12-10`) · **D+28** (`2026-12-24`)

---

## 1. Exact Scope Shipped in This Release

### P0-1: `/best/*` Intent-Matched Conversion Strip & Funnel Tracking
- **Files:** `frontend/scripts/scenario-cta.mjs`, `frontend/scripts/scenario-cta.test.mjs`, `frontend/scripts/generate-scenario-pages.mjs`, `frontend/public/best-pages.css`
- **What changed:**
  - Added bilingual, intent-matched conversion strip above Skill Cards on `/best/<slug>/`:
    - Security / Dev-Governance slugs (`code-review`, `secret-detection`, `authentication`, `claude-code-hooks`, `ai-reverse-engineering`, `refactoring`, `debugging`, `test-generation`, `api-testing`, `cli-tools`, `git-tools`): primary CTA `/ci-gate/?from=best-<slug>`, secondary `/analyzer/?from=best-<slug>`, inline link `/pro/?from=best-<slug>`.
    - All other `/best/*` slugs: primary CTA `/pro/?from=best-<slug>`, secondary `/analyzer/?from=best-<slug>`.
  - Instrumented GA4 + PostHog click events: `best_pro_cta_click`, `best_cigate_cta_click`, `best_analyzer_cta_click`.
- **Hypothesis:** `/best/*` drives `74.8%` of GSC clicks (`6,381 / 8,530`) and `14,015+` GA4 human sessions on `/best/claude-video-skills/` alone, yet previously produced only `12` `pro_upgrade_viewed` and `1` `pro_checkout_click` over 28 days because `/best/*` had zero links to `/pro/` or `/ci-gate/`.

### P0-2: `/skill/*` Audit-Verdict Meta Descriptions & Title Hygiene
- **Files:** `frontend/src/lib/skillMeta.mjs`, `frontend/src/lib/skillMeta.d.mts`, `frontend/scripts/generate-skill-pages.mjs`, `frontend/src/pages/SkillDetailPage.tsx`, `frontend/scripts/skill-title.test.mjs`
- **What changed:**
  - Fixed mid-compound Latin word truncation (`AI-looking` → clean word boundary via `WORD_JOINER` / `splitsLatinWord`).
  - Replaced raw `git clone` / install-command-heavy `/skill/*` meta descriptions with verdict-led copy (`[SAFE · 92/100 · 44-rule audit] <clean description>. Setup & alternatives.`) kept strictly within `DESCRIPTION_LIMIT = 155` chars and display width.
  - Both static HTML (`generate-skill-pages.mjs`, preserving `isGone` deleted-repo logic) and hydrated React (`SkillDetailPage.tsx`) emit the exact same title and meta description.
- **Hypothesis:** `/skill/*` pages generate `190,475` impressions at avg pos `7.4` with only `0.97%` CTR (dragging US CTR down to `0.95%`). Leading snippets with our differentiated security grade + 44-rule audit verdict raises SERP CTR without touching rankings.

### P0-3: Surgical Scenario Data & GEO FAQ Upgrades
- **Files:** `frontend/scripts/scenario-keywords.json`, `frontend/scripts/scenario-zh.json`
- **What changed:**
  1. **`skill-management-tools`** (only declining page: `36 → 24` clicks `-33%`; Pos `2.5` for `skills.rest alternatives` and Pos `7.7` for `qaskills.sh alternatives` with `0` clicks):
     - `serp_subject` → `"Claude Skill Managers & Alternatives"` → `<title>`: `"Best Claude Skill Managers & Alternatives (2026): 16 Tested"` (`59/60` chars).
     - Updated EN & ZH descriptions to explicitly reference `skills.rest` and `qaskills.sh` open-source alternatives.
     - Added bilingual `extra_faq` directly answering alternatives to `skills.rest` and `qaskills.sh` (grounded in `luongnv89/asm`, `runkids/skillshare`, `shanliuling/skills-link`, `xingkongliang/skills-manager`, and Agent Skills Hub's 282,000+ graded directory).
  2. **`seo-tools`** (`1,174` impr across `mcp + seo` queries at wPos `43.1`, Pos `45–55` for `best seo mcp server(s)`):
     - `serp_subject` → `"SEO MCP Servers & Claude SEO Skills"` → `<title>`: `"Best SEO MCP Servers & Claude SEO Skills (2026): 13 Tested"` (`58/60` chars).
     - Updated ZH title `t` → `"SEO MCP Server 与 Claude SEO Skill"`.
     - Added bilingual `extra_faq` answering `"What is the best SEO MCP server for Claude Code in 2026?"` (grounded in `AminForou/mcp-gsc`, `saurabhsharma2u/search-console-mcp`, `ahonn/mcp-server-gsc`, `aaron-he-zhu/aaron-marketing-skills`, and `AgriciDaniel/claude-seo`).
  3. **`refactoring`** (`19,220` impr, `2` clicks, `0.01%` CTR — bleeding generic `.net refactoring software` impressions):
     - Set `serp_subject` → `"AI Code Refactoring Skills for Claude"` → `<title>`: `"Best AI Code Refactoring Skills for Claude (2026): 10 Graded"` (`60/60` chars).
     - Narrowed EN & ZH titles/descriptions to Claude Code / Codex / AI coding agent refactoring skills.
  4. **`claude-video-skills` ↔ `animation-skills`** (`1,265` combined impr split across both pages for `claude animation skill(s)`):
     - Added mutual `see_also` disambiguation chips linking `claude-video-skills → animation-skills` (`Pure UI / motion / Lottie animation skills →`) and `animation-skills → claude-video-skills` (`Video editing & Remotion pipelines →`).
  5. **`ppt-presentation` & `code-review`** (GEO ChatGPT/Claude breakthrough):
     - Added bilingual `extra_faq` on `ppt-presentation` answering `"Which Codex PPT skill is best for PowerPoint decks in 2026?"` grounded verbatim in the `2026-10-07` 32-skill test (`hugohe3/ppt-master`, `zarazhangrui/frontend-slides`, `op7418/guizang-ppt-skill`, `ningzimu/codex-ppt-skill`, `ningzimu/image-to-editable-ppt-skill`).
     - Added bilingual `extra_faq` on `code-review` answering `"What is the best code review skill for Claude Code PRs in 2026?"` grounded verbatim in the `2026-10-10` 16-tool 12-PR test (`awesome-skills/code-review-skill`, `vikingmute/review-forge`, `amElnagdy/guard-skills`, `kenn-io/roborev`, `adamjgmiller/adamsreview`).

---

## 2. Frozen Pre-Change Baseline Summary (`2026-10-28 .. 2026-11-24`)

| Metric | 28d Baseline | 14d Baseline (`11-11..11-24`) | Source |
|---|---:|---:|---|
| GSC Site Clicks / Impr | `8,530` / `464,423` | `5,373` / `287,621` | `sc-domain:agentskillshub.top` |
| GSC Site CTR / wPos | `1.84%` / `7.73` | `1.87%` / `7.64` | GSC |
| GSC US CTR / Pos | `0.95%` (`657c / 68,908i`) / `9.2` | — | GSC country |
| GSC `/skill/*` CTR / wPos | `0.97%` (`1,839c / 190,475i`) / `7.4` | — | GSC pages |
| GSC `/best/*` CTR / wPos | `2.46%` (`6,381c / 259,153i`) / `8.0` | — | GSC pages |
| `/best/skill-management-tools/` | `24c / 2,352i` (`1.02%`, Pos `10.0`, `-33%`) | — | GSC pages |
| `/best/seo-tools/` (`mcp + seo`) | `7c / 2,819i` (`0c / 1,174i`, wPos `43.1`) | — | GSC query+page |
| `/best/refactoring/` | `2c / 19,220i` (`0.01%`, Pos `8.0`) | — | GSC pages |
| Brand: `agent skills hub` | `48c / 336i` (`14.3%`, Pos `3.0`) | — | GSC queries |
| GA4 Human Sessions / Engaged | `30,496` / `15,456` (`50.7%`) | — | GA4 `485523739` |
| GA4 Funnel (`copy_install` / `audit_run`) | `542` / `303` | — | GA4 events |
| GA4 Monetization (`pro_upgrade_viewed` / `pro_checkout_click`) | `12` / `1` | — | GA4 events |
| GA4 AI Referral Sessions | `161` AI (`223` AI+Bing) | — | GA4 sources |
| GEO Panel (`2026-11-24`) | PPLX `15/40` · ChatGPT `2/40` · Claude `2/10` | — | 130-run AIsa panel |

---

## 3. D+7 Review — `2026-12-03` (Instrumentation + Re-Crawl Verification)

### Commands to Run (from repo root, using backend venv)
```bash
# 1. Verify GA4 new CTA events & funnel lift (7d post: 2026-11-27..2026-12-03)
backend/venv/bin/python3 ops/ga/fetch_ga.py events --days 7
backend/venv/bin/python3 ops/ga/fetch_ga.py pages --days 7

# 2. Spot-check live HTML meta tags & CTA rendering on production
for path in \
  /skill/heydamir/unslop/ \
  /skill/lemomo-ai/lemo-opuscar/ \
  /best/skill-management-tools/ \
  /best/seo-tools/ \
  /best/refactoring/ \
  /best/claude-video-skills/ \
  /best/animation-skills/ \
  /best/ppt-presentation/ \
  /best/code-review/; do
  echo "=== $path ==="
  curl -sS "https://agentskillshub.top${path}" | grep -oE '<title>[^<]+</title>|<meta name="description" content="[^"]+"|data-cta="[^"]+"'
done

# 3. Check 7d GSC sanity (watch for sudden indexing errors or click drops)
backend/venv/bin/python3 ops/gsc/fetch_gsc.py pages --days 7
```
Also run **URL Inspection** in GSC UI on `/skill/heydamir/unslop/`, `/best/skill-management-tools/`, `/best/seo-tools/`, and `/best/ppt-presentation/` to confirm Google has recrawled post-`2026-11-26` HTML.

### Acceptance Gates (D+7)
- **Instrumentation PASS:** All three new GA4 events (`best_pro_cta_click`, `best_cigate_cta_click`, `best_analyzer_cta_click`) fire non-zero in 7-day human traffic.
- **Funnel PASS:** `pro_upgrade_viewed` >= `15` in 7 days (vs `12` in prior **28** days, i.e., `>= 5x` weekly run-rate).
- **Zero-regression PASS:** No `/best/*` or `/skill/*` HTML returns truncated mid-word titles (`> 60` chars) or broken bilingual toggle text; total 7d GSC clicks do not drop `> 15%` week-over-week.
- **Crawl check:** At least 3 of 4 spot-checked URLs show `lastCrawlTime >= 2026-11-26`. If not recrawled by D+7, submit those 4 URLs via GSC URL Inspection ("Request Indexing") and note the crawl lag before D+14 judgment.

---

## 4. D+14 Review — `2026-12-10` (14d Pre vs 14d Post GSC CTR & Ranking Check)

Wait until `2026-12-12` if needed for GSC's 2-day data lag so full `2026-11-27 .. 2026-12-10` (14d post) compares cleanly against `2026-11-11 .. 2026-11-24` (14d pre: `5,373` clicks / `287,621` impr / `1.87%` CTR / `7.64` wPos).

### Commands to Run
```bash
# 1. Full 14-day GSC comparison dump
backend/venv/bin/python3 ops/gsc/fetch_gsc.py compare --days 14
backend/venv/bin/python3 ops/gsc/fetch_gsc.py dump --days 14

# 2. Target page query checks
backend/venv/bin/python3 ops/gsc/fetch_gsc.py page-queries "/best/skill-management-tools/"
backend/venv/bin/python3 ops/gsc/fetch_gsc.py page-queries "/best/seo-tools/"
backend/venv/bin/python3 ops/gsc/fetch_gsc.py page-queries "/best/refactoring/"
backend/venv/bin/python3 ops/gsc/fetch_gsc.py page-queries "/skill/heydamir/unslop/"

# 3. Check UTM duplicate impressions (baseline: 20 normalized paths, 4,491i on bang-motion UTM variant)
backend/venv/bin/python3 ops/gsc/fetch_gsc.py pages --days 14 | grep -i "utm_" || echo "No UTM URLs in top 500"

# 4. GA4 14d conversion funnel check
backend/venv/bin/python3 ops/ga/fetch_ga.py events --days 14
```

### Acceptance Gates (D+14)
| Check | Pre Baseline | D+14 Target (Green) | Watch / Investigate (Yellow) | Rollback / Fix Trigger (Red) |
|---|---:|---|---|---|
| `/skill/*` CTR | `0.97%` | `>= 1.25%` (`+29%` rel.) | `1.05% – 1.24%` | `< 0.90%` with stable wPos (`<= 8.0`) |
| US Country CTR | `0.95%` | `>= 1.20%` | `1.00% – 1.19%` | `< 0.85%` |
| `/best/skill-management-tools/` | `24c` / 28d (`~12c`/14d) | `>= 18` clicks in 14d & `>= 2` clicks on `skills.rest` / `qaskills.sh` alternatives | `12 – 17` clicks | `< 10` clicks or avg pos worse than `12.0` |
| `/best/seo-tools/` (`mcp + seo` wPos) | `wPos 43.1` (`0c`) | `wPos <= 30.0` (moving up 13+ spots) | `wPos 31 – 40` | `wPos > 48` or `claude seo` clicks drop `> 50%` |
| `/best/refactoring/` | `0.01%` CTR (`19,220i`) | Impr on generic `.net` drops while CTR rises `>= 0.15%` | CTR `0.05% – 0.14%` | Zero clicks & impr collapse with no Claude queries |
| UTM Duplicate Impr | `4,491i` on `bang-motion` UTM | Down `>= 25%` (or flagged for canonical/301 P1 task) | Flat | Rising — promote UTM strip/canonical cleanup to P1 |

---

## 5. D+28 Review — `2026-12-24` (Full Attribution + GEO Panel Re-Run + Go/No-Go)

Run on `2026-12-26` (allowing 2-day GSC lag) for a full 28-day post window (`2026-11-27 .. 2026-12-24`) vs frozen baseline (`2026-10-28 .. 2026-11-24`).

### Commands to Run
```bash
# 1. Full 28d GSC dump & bucket analysis
backend/venv/bin/python3 ops/gsc/fetch_gsc.py dump --days 28
backend/venv/bin/python3 ops/gsc/ctr_buckets.py

# 2. Full 28d GA4 attribution (human sessions, AI referrals, Pro/CI conversions)
backend/venv/bin/python3 ops/ga/fetch_ga.py dump --days 28

# 3. Re-run 40-question / 130-run GEO citation panel (exact same AIsa setup as 2026-11-24)
#    Script: ~/出海/specs/ash-panel-tools/ash_panel.py -> ops/geo/panel/results-2026-12-24.json
python3 ops/geo/panel_score.py

# 4. Compare 28d post against frozen baseline JSON
#    ops/gsc/baselines/2026-11-26-p0-seo-geo-baseline.json
```

### Acceptance Gates (D+28)
1. **SEO CTR & Clicks:**
   - `/skill/*` 28d CTR rises from `0.97%` to **`>= 1.35%`** (worth `+720+` incremental clicks/mo at current impression volume).
   - US 28d CTR rises from `0.95%` to **`>= 1.30%`**.
   - `/best/skill-management-tools/` recovers to **`>= 36` clicks / 28d** (reversing the `-33%` drop).
   - `/best/seo-tools/` breaks into **Top 20 (`wPos <= 20`)** for `best seo mcp server(s)` with **`>= 20` clicks / 28d** (up from `7`).
   - `claude animation skill(s)` cannibalization ratio shifts toward `/best/animation-skills/` (`>= 60%` of combined impressions, up from `36%` baseline `458 / 1,265`).
2. **Monetization & Product Funnel (GA4 28d human):**
   - `best_pro_cta_click` + `best_cigate_cta_click` >= **`150` clicks / 28d** (`~1%` of `/best/*` sessions).
   - `pro_upgrade_viewed` rises from `12` to **`>= 80` / 28d**.
   - `pro_checkout_click` rises from `1` to **`>= 8` / 28d** (and paid Pro/CI conversions tracked in Stripe).
3. **GEO Citation Panel (`2026-12-24` vs `2026-11-24`):**
   - **Perplexity (`sonar`, 40 Qs):** Hold or exceed `site_cited >= 15/40`, `first_pick >= 6/40`.
   - **ChatGPT (`gpt-6`, 40 Qs):** Break out from `site_cited 2/40` to **`>= 5/40`**, with at least 1 new citation among `ppt-presentation`, `code-review`, `claude-video-skills`, `seo-tools`.
   - **Claude (`sonnet-4-5`, 10 Qs):** Break out from `site_cited 2/10` to **`>= 4/10`**.
   - **GA4 AI Referral Sessions:** Grow from `161` / 28d to **`>= 240` / 28d** (`+50%`).

---

## 6. Rollback & Iteration Decision Rules

- **Iterate P0-1 (`scenario-cta.mjs`)** if `best_pro_cta_click` CTR on `/best/*` is `< 0.5%` at D+14: test moving a compact inline CTA into the sticky verdict card or softening copy toward `"Filter by license & zero-flag skills"` rather than removing the strip.
- **Rollback P0-2 (`skillMeta.mjs`)** only if `/skill/*` CTR drops `< 0.85%` at D+14 with stable avg position (`<= 8.0`) AND GSC spot-checks confirm Google is displaying our new `[SAFE · 44-rule audit]` snippet (not rewriting it).
- **Iterate P0-3 (`scenario-meta.mjs`, `scenario-keywords.json`, `scenario-zh.json`)**:
  - If `seo-tools` remains `wPos > 30` for `best seo mcp server` at D+28, spin out a dedicated `/best/seo-mcp-servers/` scenario page (P1) rather than overloading `seo-tools`.
  - If `ppt-presentation` and `code-review` remain `0` on ChatGPT at D+28 despite on-page FAQ upgrades, the bottleneck is off-site Bing/OpenAI authority — prioritize publishing benchmark summary posts on `dev.to` + Zenodo + README tables linking back to `/best/ppt-presentation/` and `/best/code-review/`.
  - If `refactoring` drops below `100` impr/28d with `0` clicks at D+28, mark `"retired": true` (noindex) like the prior 36 retired pages so crawl budget concentrates on converting scenarios.
