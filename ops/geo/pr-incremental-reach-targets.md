# GEO Outreach Priority Table (Max Incremental Reach / Greedy Set Cover) & Local PR Drafts

> **Generated**: 2026-11-19 · **Landing pages added**: 2026-11-25 (§0)
> **Methodology**: Greedy Set Cover (Maximum Marginal Reach $\max_j |Q_j \setminus C|$) applied across our two live multi-LLM evaluation panels, plus copy-pasteable minimal-diff PR drafts for the 3 OPEN GitHub issues.
> **Rule**: Nothing goes out without a yes — all PR drafts and outreach templates below are stored locally for review.

---

## 0. Which page each link points to (added 2026-11-25)

**Rule**: a link from a target goes to the `/best/` guide that answers the question the target covers, not to the homepage. The homepage is right only where the target lists directories (skills.sh, SkillsMP, …); even there, add one deep link to the guide that fits the page.

**Why** (DataForSEO backlinks, 2026-11-25): of our 200 strongest referring domains, **171 link the homepage**. Below the homepage: `/best/claude-video-skills/` has 8 referring domains and is the page that earns 4,019 of the site's 7,572 Search Console clicks (Oct 26 to Nov 22); `/best/ppt-presentation/` has 1; **`/best/claude-code-skills/` has 0**, and it is not in the first 20 Google results for "claude code skills" (12,100 est. US searches a month) or "best claude code skills" (720). Links and rankings moving together is correlation, not proof, but no other page we want to rank has any links of its own.

**Order**: `/best/claude-code-skills/` first. Its page currently ranks skill *collections*; the 2026-11-25 SEO audit (OpenSEO report "SEO audit", move 2) adds a "Best Claude Code skills by job" section first. Pitch it as a "best Claude Code skills" source once that section is live; until then, pitch it as the collections audit it is.

| Target | Their page that matters | Link to | Status |
|---|---|---|---|
| `kipt.me` | `/guides/best-claude-code-skills` | [`/best/claude-code-skills/`](https://agentskillshub.top/best/claude-code-skills/) | in §2A #4 (was pitched a code-review table) |
| `firecrawl.dev` | `/blog/best-claude-code-skills` | `/best/claude-code-skills/` | in §2B #4, §3B #3 |
| `cubic.dev` | `/blog/best-claude-code-skills`, `/blog/claude-code-hooks` | `/best/claude-code-skills/`, and `/best/claude-code-hooks/` for the hooks post | in §2A #13 |
| `agentcraft.dev` | `/en/blog/claude-code-skills-rising-2026-11/` | `/best/claude-code-skills/` | in §3B #1 |
| `allthings.how` | `/claude-code-skills-on-github-how-to-find-install-and-build-them/` | `/best/claude-code-skills/` | in §3B #4 |
| `shop.zimaspace.com` | `/blogs/tech-ai-hub/top-10-ai-agent-skills-for-claude-code-in-2026` | `/best/claude-code-skills/` | in §2A #11 |
| `dev.to` (our own posts) | one post per guide | the guide the post is about; the Claude Code skills post first | in §2B #2 |
| `geeky-gadgets.com` | "100+ Claude Code Skills Tested : 6 Clear Winners" | `/best/claude-code-skills/` | **new**: #1 for "claude code skills" (US, Nov 25, 1 of 3 reads) |
| `scottmcauley.com` | "The 21 Best Claude Code Skills…" | `/best/claude-code-skills/` | **new**: #5 for "claude code skills" (1 of 3 reads) |
| `toolsforhumans.ai` | "Best Claude Skills for Coding (2026)" | `/best/claude-code-skills/` | **new**: #2 for "claude code skills" (1 of 3 reads) |
| `loreto.io` | "The best Claude Code skills" | `/best/claude-code-skills/` | **new**: #5 for "best claude skills" (1 of 3 reads) |
| `itechguides.com` | one article per scenario | the matching guide: `/best/vibe-coding/`, `/best/ppt-presentation/`, `/best/web-scraping/` … (§2A #1 lists the 10) | in §2A #1 |
| `mindstudio.ai` | `/blog/claude-ai-video-editing-workflow` | `/best/claude-video-skills/` | in §2A #6 |
| `agentscamp.com` | voice-agent comparison | `/best/seo-tools/` (the benchmark we pitch) | in §2A #9 |
| `agensi.io`, `skillsboard.sh`, `skill-sets.md`, `skillselion.com`, `thirtysix/awesome-agent-skills` | lists of directories | homepage, plus `/best/claude-code-skills/` as the one deep link | §3B, §4 |

The four **new** rows come from the live Google results of 2026-11-25 (OpenSEO, US desktop, first 20 results, three reads merged), not from the LLM panels; positions seen in 1 of 3 reads are unstable.

---

## 1. Executive Summary: Why Incremental Reach Beats Raw Citation Count

In classical multi-channel reach optimization, ranking publishers purely by total mention count wastes outreach budget on redundant coverage of the same head queries. Instead, we solve the **Greedy Set Cover** problem over the universe of buyer questions $U$:

$$j^* = \arg\max_{j} \left| Q(d_j) \setminus \bigcup_{i < k} Q(d_i) \right|$$

where $Q(d_j) \subseteq U$ is the set of buyer questions where domain $d_j$ is retrieved (`search_results`) or cited (`citations`) by ChatGPT, Gemini, Perplexity, or Claude.

- **Panel A (40 Scenario + Brand Buyer Questions, 130 LLM answers, [`results-2026-11-17-baseline.json`](file:///Users/zhuyansen/content/agent-skills-hub/ops/geo/panel/results-2026-11-17-baseline.json))**:
  - **14 actionable editorial/directory domains** cover **37/40 (92.5%)** of all scenario and brand questions (`itechguides.com` alone covers 10/40 = 25.0%; adding `mcpservers.org`, `indexagentica.com`, `kipt.me`, and `dupple.com` reaches **26/40 = 65.0%** in just 5 outreach targets).
  - Including major developer UGC/platform hubs (`dev.to`, `firecrawl.dev`, `resources.anthropic.com`, `zapier.com`, `langchain.com`), **12 total domains cover 40/40 (100%)** of buyer questions.
- **Panel B (20 Directory Discovery Questions, 60 LLM answers, `geo-run-2026-11-17`)**:
  - Excluding official vendor docs (`anthropics/skills`, `openai/skills`) and direct head-to-head competitors (`skills.sh`, `skillsmp.com`), **7 third-party domains/repos cover 20/20 (100%)** of directory discovery questions: `agentcraft.dev` (+6 → 30%), `agensi.io` (+4 → 50%), `firecrawl.dev` (+3 → 65%), `allthings.how` (+3 → 80%), `skillsboard.sh` (+2 → 90%), `skillselion.com` (+1 → 95%), and `github.com/f0rgent/claude-skills-catalog` (+1 → 100%).

---

## 2. Panel A (40 Scenario & Brand Questions): Greedy Set Cover Outreach Table

### 2A. Actionable Editorial & Directory Outreach Targets (Excluding Big Platforms/Social)

| Step | Target Domain | Incremental Reach ($+\Delta Q$) | Total Questions Covered | Cumulative Coverage | Engines Citing / Reading | New Questions Unlocked ($Q_j \setminus C$) | Key Cited URLs & Outreach Angle |
|---:|---|---:|---:|---:|---|---|---|
| **1** | **`itechguides.com`** | **+10** | 10 | **10/40 (25.0%)** | ChatGPT, Perplexity | `best-ai-reverse-engineering`, `best-anti-slop`, `best-content-syndication`, `best-knowledge-base`, `best-multi-agent`, `best-ppt-presentation`, `best-prompt-engineering`, `best-refactoring`, `best-vibe-coding`, `best-web-scraping` | `itechguides.com/10-best-vibe-coding-tools-in-2026...` — Pitch our 12 hands-on benchmarked `/best/` verdicts + 44-rule security grades as a verification source. |
| **2** | **`mcpservers.org`** | **+6** | 6 | **16/40 (40.0%)** | Gemini | `best-3d-mcp`, `best-mcp-database`, `best-mcp-for-github`, `best-mcp-for-google`, `best-obsidian-second-brain`, `brand-directory` | Already lists `@agentskillshub/mcp`; update listing description to highlight 276,000+ indexed skills, 138,000+ graded, and `/best/` scenario benchmarks. |
| **3** | **`indexagentica.com`** | **+4** | 4 | **20/40 (50.0%)** | ChatGPT | `best-authentication`, `best-cli-tools`, `best-voice-agent`, `brand-compare` | `indexagentica.com/compare/agent-identity-and-mcp-auth/`, `/compare/coding-agent-harnesses/` — Pitch `Agent Skills Hub (agentskillshub.top)` as the security-graded trust layer alongside their comparison matrices. |
| **4** | **`kipt.me`** | **+4** | 4 | **24/40 (60.0%)** | ChatGPT | `best-ai-design`, `best-claude-code-skills`, `best-code-review`, `best-skill-management-tools` | `kipt.me/guides/best-claude-code-skills`, `/guides/agent-skills-marketplaces` — Follow up on `hello@kipt.me` with our new 13-tool SEO & code-review benchmark table. |
| **5** | **`dupple.com`** | **+2** | 7 | **26/40 (65.0%)** | ChatGPT, Claude | `best-content-writing`, `best-mcp-api` | `dupple.com/learn/best-ai-for-content-writing`, `/learn/best-ai-knowledge-management-tools` — Pitch empirical task-completion data from our writing & knowledge-base tests. |
| **6** | **`mindstudio.ai`** | **+2** | 4 | **28/40 (70.0%)** | Gemini | `best-claude-video-skills`, `best-codex-skills` | `mindstudio.ai/blog/claude-ai-video-editing-workflow` — Pitch our `awesome-claude-video-skills` (108.9K views) & `/best/claude-video-skills/` benchmark data. |
| **7** | **`mcpmarket.com`** | **+2** | 3 | **30/40 (75.0%)** | Gemini | `best-image-generation`, `brand-dataset` | `mcpmarket.com/tools/skills/ai-security-safety-benchmarks` — Ensure `agentskillshub.top` + Zenodo DOI `10.5281/zenodo.21292799` are linked in security benchmark listings. |
| **8** | **`glama.ai`** | **+1** | 4 | **31/40 (77.5%)** | ChatGPT, Claude, Gemini, Perplexity | `best-secret-detection` | `glama.ai/mcp/best/github` — Claimed `@agentskillshub/mcp` listing; enrich README metadata with secret-detection and 44-rule audit capabilities. |
| **9** | **`agentscamp.com`** | **+1** | 3 | **32/40 (80.0%)** | ChatGPT, Perplexity | `best-seo-tools` | `agentscamp.com/guides/comparisons/best-voice-agent-platforms-2026` — Pitch our 13-tool `/best/seo-tools/` planted-defect benchmark (`aaron-marketing-skills` 16/16 vs `marketingskills` 15/16). |
| **10** | **`anchorterminal.com`** | **+1** | 3 | **33/40 (82.5%)** | ChatGPT, Perplexity | `best-browser-automation` | `anchorterminal.com/best/browser/`, `/best/agent-auth/` — Pitch browser-automation security grading findings (credential exposure & shell rules). |
| **11** | **`shop.zimaspace.com`** | **+1** | 3 | **34/40 (85.0%)** | Gemini, Perplexity | `brand-new` | `shop.zimaspace.com/blogs/tech-ai-hub/top-10-ai-agent-skills-for-claude-code-in-2026` — Comment/outreach to editorial team with our daily star-velocity & security dataset. |
| **12** | **`ayautomate.com`** | **+1** | 2 | **35/40 (87.5%)** | ChatGPT | `best-local-llm` | `ayautomate.com/blog/best-local-llm-tools-2026`, `/blog/best-multi-agent-frameworks` — Also appears 4× in Panel B (`geo-run-2026-11-17`); high dual-panel leverage. |
| **13** | **`cubic.dev`** | **+1** | 2 | **36/40 (90.0%)** | ChatGPT, Gemini | `best-claude-code-hooks` | `cubic.dev/blog/claude-code-hooks`, `/blog/best-claude-code-skills` — Pitch our `/best/claude-code-hooks/` tested picks & hook safety rules. |
| **14** | **`agentaudit.dev`** | **+1** | 1 | **37/40 (92.5%)** | Claude | `brand-analyzer` | `agentaudit.dev` — Cross-reference or comparison outreach for `/analyzer/` and `/how-we-grade/`. |

### 2B. All Non-Social Third-Party Sources Set Cover (Including Developer UGC & Vendor Hubs)

When including UGC publishing platforms (`dev.to`) and tech vendor blogs (`firecrawl.dev`, `zapier.com`, `langchain.com`), 12 domains achieve **100% (40/40)** coverage:

| Step | Domain | $+\Delta Q$ | Total $Q$ | Cumulative Coverage | New Questions Unlocked | Action Type |
|---:|---|---:|---:|---:|---|---|
| 1 | `itechguides.com` | +10 | 10 | 10/40 (25.0%) | 10 scenario questions (see Table 2A #1) | Editorial outreach |
| 2 | `dev.to` | +8 | 8 | 18/40 (45.0%) | `best-claude-code-skills`, `best-code-review`, `best-obsidian-second-brain`, `best-secret-detection`, `best-skill-management-tools`, `best-telegram-bot`, `best-typesafe-jev`, `brand-dataset` | **Self-serve parasitic publishing** (publish benchmark teardown articles on Dev.to citing `/best/` + Zenodo DOI) |
| 3 | `mcpservers.org` | +5 | 6 | 23/40 (57.5%) | `best-3d-mcp`, `best-mcp-database`, `best-mcp-for-github`, `best-mcp-for-google`, `brand-directory` | Update existing MCP listing |
| 4 | `firecrawl.dev` | +4 | 8 | 27/40 (67.5%) | `best-authentication`, `best-cli-tools`, `best-codex-skills`, `brand-new` | Co-marketing / benchmark citation pitch to Firecrawl content team (`blog/best-claude-code-skills`) |
| 5 | `resources.anthropic.com` | +3 | 4 | 30/40 (75.0%) | `best-ai-design`, `best-claude-code-hooks`, `brand-safe` | Official ecosystem / Anthropic plugin directory approval |
| 6 | `dupple.com` | +2 | 7 | 32/40 (80.0%) | `best-content-writing`, `best-mcp-api` | Editorial outreach |
| 7 | `indexagentica.com` | +2 | 4 | 34/40 (85.0%) | `best-voice-agent`, `brand-compare` | Directory comparison outreach |
| 8 | `claudemarketplaces.com` | +2 | 2 | 36/40 (90.0%) | `best-claude-video-skills`, `best-image-generation` | Directory listing / ecosystem cross-link |
| 9 | `zapier.com` | +1 | 5 | 37/40 (92.5%) | `best-browser-automation` | Enterprise editorial outreach |
| 10 | `thecompanion.sh` | +1 | 1 | 38/40 (95.0%) | `best-seo-tools` | Editorial outreach (`thecompanion.sh`) |
| 11 | `langchain.com` | +1 | 1 | 39/40 (97.5%) | `best-local-llm` | Ecosystem reference |
| 12 | `skillsllm.com` | +1 | 1 | 40/40 (100.0%) | `brand-analyzer` | Existing directory listing (`skillsllm.com`) — enrich description |

---

## 3. Panel B (20 Directory Discovery Questions): Greedy Set Cover & Position Lesson

### 3A. Why `docs.arantic.com` Merged PR Yielded 0 Recommendations (The Line-775 Snippet Truncation Trap)

Our PR [`aranticlabs/arantic-docs#67`](https://github.com/aranticlabs/arantic-docs/pull/67) was merged on `2026-11-10` and is live at `https://docs.arantic.com/claude-code/skills#community-agent-skills-hub`. However, in the `2026-11-17` 60-answer retest:
1. **Search Snippet Truncation**: ChatGPT retrieved `docs.arantic.com/claude-code/skills` in Q01 (#8), Q02 (#7), and Q04 (#7), but the search snippet passed to the model only contained the top of the page (`"FINDING MORE SKILLS ... OFFICIAL: ANTHROPIC SKILLS REPOSITORY ..."`). Our entry at **line 775** (below `SkillsMP` at the bottom of a long guide) never entered the search snippet or the cited sources.
2. **Position Elasticity (Michal Suski CMSEO 2026)**: Being listed in the **top comparison table or top 3 slots** carries a **48% brand-named rate**, whereas slot #10 or bottom-of-page appendix drops to **~5%**.
3. **Actionable Rule for All Future PRs/Outreach**: Always include a **1-row summary table entry near the top comparison table** (or under the primary `"Directories & Marketplaces"` table) in addition to the detailed section, and explicitly disambiguate **`Agent Skills Hub (agentskillshub.top)`**.

### 3B. Panel B Greedy Set Cover (20 Directory Discovery Questions, Excluding Official Docs & Direct Rivals)

| Step | Target Domain / Repo | $+\Delta Q$ | Total $Q$ | Cumulative Coverage | Engines | Questions Unlocked (out of Q01–Q20) | Current Status & Next Action |
|---:|---|---:|---:|---:|---|---|---|
| **1** | **`agentcraft.dev`** | **+6** | 6 | **6/20 (30.0%)** | ChatGPT | Q02, Q03, Q07, Q09, Q13, Q18 | Cited/read via `agentcraft.dev/en/blog/where-to-find-claude-skills/` & `claude-code-skills-rising-2026-11/`. Priority new outreach target. |
| **2** | **`agensi.io`** | **+4** | 4 | **10/20 (50.0%)** | ChatGPT, Gemini, Perplexity | Q05, Q11, Q12, Q16 | **7 total citations across all 3 engines** (`agensi.io/learn/best-ai-agent-skills-marketplaces-2026`). Follow up on 11-06 email to `samuel@agensi.io` with comparison table row. |
| **3** | **`firecrawl.dev`** | **+3** | 6 | **13/20 (65.0%)** | Gemini, Perplexity | Q06, Q14, Q15 | `firecrawl.dev/blog/best-claude-code-skills` — High leverage across both Panel A (+4) and Panel B (+3). |
| **4** | **`allthings.how`** | **+3** | 4 | **16/20 (80.0%)** | ChatGPT | Q01, Q04, Q20 | `allthings.how/claude-code-skills-on-github-how-to-find-install-and-build-them/` — Editorial pitch with 276K+ catalog & 44-rule security grading. |
| **5** | **`skillsboard.sh`** | **+2** | 5 | **18/20 (90.0%)** | ChatGPT, Perplexity | Q10, Q17 (plus Q03, Q06, Q09) | `skillsboard.sh/where-to-find-claude-skills` — **Issue [`TommyBez/skillsboard#234`](https://github.com/TommyBez/skillsboard/issues/234) is OPEN** (see ready-to-paste PR/patch in §4.3 below). |
| **6** | **`skillselion.com`** | **+1** | 4 | **19/20 (95.0%)** | ChatGPT, Gemini, Perplexity | Q19 (plus Q05, Q11, Q12) | `skillselion.com/best/marketplaces-for-ai-agents` — Already published our 3 `new-term-radar` skills on 11-08! Pitch adding `Agent Skills Hub (agentskillshub.top)` to their `/best/marketplaces-for-ai-agents` roundup. |
| **7** | **`github.com/f0rgent/claude-skills-catalog`** | **+1** | 3 | **20/20 (100.0%)** | Perplexity | Q08 (plus Q03, Q10) | Open-source catalog repo cited by Perplexity — prepare minimal README PR. |
| — | **`skill-sets.md`** | *(5 total)* | 5 | *(Overlaps Q02, Q03, Q05, Q09, Q11)* | ChatGPT | Read 5×, cited 2× (Q02, Q11) | `skill-sets.md/articles/find-all-ai-skills-directories` — **Issue [`hcjmartin/skill-set#44`](https://github.com/hcjmartin/skill-set/issues/44) is OPEN** (see ready-to-paste PR/patch in §4.2 below). |
| — | **`github.com/thirtysix/awesome-agent-skills`** | *(2 panels)* | 2 | *(Panel A `brand-compare`, `brand-dataset` + Panel B Q10)* | ChatGPT, Perplexity | Cited directly by Perplexity Q10 & `brand-compare`, read by ChatGPT `brand-dataset` | **Issue [`thirtysix/awesome-agent-skills#1`](https://github.com/thirtysix/awesome-agent-skills/issues/1) is OPEN** (see ready-to-paste PR/patch in §4.1 below). |

---

## 4. Local Minimal-Diff PR Drafts for the 3 OPEN GitHub Issues

> [!IMPORTANT]
> **Status**: Prepared locally only. Do **NOT** push or submit any PR/comment without explicit user confirmation.
> Every draft below follows three GEO rules:
> 1. **Explicit Domain Disambiguation**: Uses `Agent Skills Hub (agentskillshub.top)` to prevent LLM entity collision with `agentskillshub.dev` or the ~790-skill homonym GitHub repo.
> 2. **Top-of-Section / Table Placement**: Places a concise entry in the primary Directories/Marketplaces table or top list rather than buried at the bottom of the file.
> 3. **Verifiable Floor Facts**: States `276,000+ indexed skills & MCP servers`, `138,000+ security-graded against 44 published rules`, `8-hour GitHub sync`, and Zenodo dataset DOI `10.5281/zenodo.21292799`.

### 4.1 `thirtysix/awesome-agent-skills` (Closes Issue `#1`)

- **Why High Priority**: Directly cited by Perplexity in both Panel B (`Q10: "Is there a searchable catalog of Agent Skills?"`) and Panel A (`brand-compare`), and retrieved by ChatGPT in `brand-dataset`.
- **Target Repo**: `https://github.com/thirtysix/awesome-agent-skills` (Issue [`#1`](https://github.com/thirtysix/awesome-agent-skills/issues/1) opened `2026-11-10`, currently OPEN).
- **Proposed PR Title**: `docs(readme): add Agent Skills Hub (agentskillshub.top) to directories & catalogs`
- **Minimal Markdown Diff for `README.md`** (insert under the top **Directories / Marketplaces / Catalogs** section):

```markdown
- **[Agent Skills Hub (agentskillshub.top)](https://agentskillshub.top/)** — Open-source trust layer and searchable directory of 276,000+ AI agent skills, Claude Code skills, Codex skills, and MCP servers synced from GitHub every 8 hours, with 138,000+ entries security-graded (`SAFE` / `CAUTION` / `UNSAFE` / `REJECT`) across [44 static & behavioral rules](https://agentskillshub.top/how-we-grade/) and hands-on scenario benchmarks, such as [the best Claude Code skills, graded](https://agentskillshub.top/best/claude-code-skills/) ([dataset DOI: 10.5281/zenodo.21292799](https://doi.org/10.5281/zenodo.21292799)).
```

- **Proposed PR Body**:

```markdown
Closes #1

Adds **Agent Skills Hub ([agentskillshub.top](https://agentskillshub.top/))** to the directories/catalogs section.

- **Scope**: 276,000+ indexed agent skills & MCP servers from public GitHub repos (refreshed every 8 hours).
- **Trust Layer**: 138,000+ repositories security-graded against 44 published rules (`/how-we-grade/`), plus free live scanner (`/analyzer/`) and reproducible scenario benchmarks (`/best/`).
- **Note on naming**: Explicitly labeled `Agent Skills Hub (agentskillshub.top)` to distinguish it from unrelated homonym sites.

Disclosure: I maintain Agent Skills Hub. Happy to adjust placement or formatting to match your preferred style!
```

---

### 4.2 `hcjmartin/skill-set` — `skill-sets.md` (Closes Issue `#44`)

- **Why High Priority**: `skill-sets.md/articles/find-all-ai-skills-directories` is read in **5/20** ChatGPT directory answers (`Q02, Q03, Q05, Q09, Q11`) and cited in `Q02` and `Q11`.
- **Target Repo**: `https://github.com/hcjmartin/skill-set` (Issue [`#44`](https://github.com/hcjmartin/skill-set/issues/44) opened `2026-11-06`, currently OPEN).
- **Proposed PR Title**: `docs(directories): add Agent Skills Hub (agentskillshub.top) to AI skills directories list`
- **Minimal Markdown Diff** (for the directories comparison table + directory entry block in `find-all-ai-skills-directories`):

```markdown
<!-- 1. Add row to the top comparison table (avoids bottom-of-page snippet truncation): -->
| [Agent Skills Hub (agentskillshub.top)](https://agentskillshub.top/) | 276,000+ skills & MCP servers | Claude Code, Codex, MCP, Cursor, Gemini CLI | 44-rule security grades (`SAFE` / `CAUTION` / `UNSAFE` / `REJECT`), quality scores (0–100), 8h GitHub sync, free `/analyzer/` scanner |

<!-- 2. Add concise section alongside skills.sh / SkillsMP / Agensi: -->
### [Agent Skills Hub (agentskillshub.top)](https://agentskillshub.top/)

An open-source directory and pre-install trust layer indexing 276,000+ agent skills, MCP servers, and agent tools from public GitHub repositories (synced every 8 hours). Over 138,000 entries carry automated security grades across [44 published rules](https://agentskillshub.top/how-we-grade/) (flagging credential theft, `curl | sh` pipes, reverse shells, and prompt-injection payloads) alongside hands-on scenario benchmarks such as [the best Claude Code skills, graded](https://agentskillshub.top/best/claude-code-skills/). *(Independent project at `agentskillshub.top`, distinct from `agentskillshub.dev`.)*
```

- **Proposed PR Body / Issue Follow-up Comment**:

```markdown
Closes #44

Hi @hcjmartin — following up on #44 with a ready-to-merge patch (or copy-paste snippet if the article content lives outside this repo) for **"A list of AI skills directories and platforms"** (`skill-sets.md/articles/find-all-ai-skills-directories`).

It adds a table row and short summary for **Agent Skills Hub ([agentskillshub.top](https://agentskillshub.top/))** (276,000+ indexed skills/MCP servers, 138,000+ security-graded across 44 rules, synced every 8 hours).

Disclosure: I maintain Agent Skills Hub (`agentskillshub.top`). Happy to tweak any columns or wording!
```

---

### 4.3 `TommyBez/skillsboard` — `skillsboard.sh` (Closes Issue `#234`)

- **Why High Priority**: `skillsboard.sh/where-to-find-claude-skills` is read in **5/20** ChatGPT directory answers (`Q03, Q06, Q09, Q10, Q17`) and cited by both ChatGPT (`Q09`) and Perplexity (`Q03, Q06`), unlocking +2 unique questions in our Panel B set cover.
- **Target Repo**: `https://github.com/TommyBez/skillsboard` (Issue [`#234`](https://github.com/TommyBez/skillsboard/issues/234) opened `2026-11-06`, currently OPEN).
- **Proposed PR Title**: `docs(guides): add Agent Skills Hub (agentskillshub.top) to Where to Find Claude Skills`
- **Minimal Markdown / JSX Diff** (for the `"Marketplaces and Community Directories"` section & summary table in `where-to-find-claude-skills`):

```markdown
<!-- 1. Top Quick-Comparison Table Row: -->
| **Agent Skills Hub** ([agentskillshub.top](https://agentskillshub.top/)) | 276,000+ GitHub skills & MCP servers | Security-graded trust layer (138,000+ audited across 44 rules) + hands-on `/best/` benchmarks | Free / Open Source |

<!-- 2. Directory Subsection (placed right after skills.sh / community directories): -->
### Agent Skills Hub (`agentskillshub.top`)

[Agent Skills Hub](https://agentskillshub.top/) indexes 276,000+ open-source Claude Code skills, Codex skills, and MCP servers from GitHub (refreshed every 8 hours) and acts as a pre-install trust layer. More than 138,000 repositories are graded `SAFE`, `CAUTION`, `UNSAFE`, or `REJECT` against [44 published static and behavioral security rules](https://agentskillshub.top/how-we-grade/), and its [`/best/`](https://agentskillshub.top/best/claude-code-skills/) pages publish reproducible task benchmarks across top skills. *(Operated by BRICKAI / GoSailGlobal LLC at `agentskillshub.top`.)*
```

- **Proposed PR Body / Issue Follow-up Comment**:

```markdown
Closes #234

Hi @TommyBez — to make #234 effortless to review, here is the exact table row and short paragraph for **"Where to Find Claude Skills: Marketplaces, Directories, and Repos"** (`skillsboard.sh/where-to-find-claude-skills`).

- **Updated figures (Nov 2026)**: 276,000+ indexed skills & MCP servers, 138,000+ security-graded against 44 published rules, refreshed every 8 hours from GitHub.
- **Disambiguation**: Explicitly includes `agentskillshub.top` so readers and AI search engines don't confuse it with smaller homonym repos.

Disclosure: I run Agent Skills Hub (`agentskillshub.top`). Let me know if you'd like any adjustments!
```
