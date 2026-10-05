# The PPT page playbook

How `/best/ppt-presentation/` became the site's first search page, step by step, and the
checklist to repeat it on another topic. Written 2026-10-05.

## Where it stands

- GSC, last 3 months: **1,103 clicks, 50,006 impressions, average position 7.5**. About
  two thirds of all the site's search clicks.
- `ppt skills` (KD 39.8, "easy"): **#4**, with DR 12. Above us: two github.com results (a
  platform slot no site can take) and kimi.ai (DR 77). seo.web.cafe's SERP breakdown calls
  the page a "页面派范本": it ranks on the page, not on the domain.
- `codex ppt skill`: **#2**, the site's top click query.
- On Page score (seo.web.cafe): 88 → **93** after the 10-05 fixes.
- GitHub list: zhuyansen/awesome-codex-ppt-skills, updated daily.

## What was done, in order

| When | Move | Why it mattered |
|---|---|---|
| 05-04 | "Tweet → landing alignment" (24ed67e): featured anchors pin the repos a post will name to the top of the page | Visitors from the post land on exactly what it promised. |
| 05-05 | Page created (172f023) | |
| 05-09 | [Post on X](https://x.com/GoSailGlobal/status/2053103395863699594) from @GoSailGlobal (36.7K followers): five AI PPT styles, one open-source skill each, link to the page. 167K views, 971 likes, 248 reposts, 1,302 bookmarks | The page had **zero** search impressions before; the week of the post it had **30,687**. Google found and indexed it that week, and the first queries were the post's: `ppt skills`, `guizang ppt skill`, `github ppt skill`. |
| 06-23 | Retitled `PPT & Presentation Skills` → `AI PPT & Slide Generators` (2a1e59c) | 96% of the site's impressions were "presentation skills", public-speaking intent, 0 clicks. The title now names the tool intent. |
| 07-06 | Found ppt as the #1 topic by clustering GSC impressions by term; checked the catalog for depth before deciding | GSC only shows terms already ranking; the catalog showed a deep category behind them. |
| 07-06 | Decided **not** to open `/best/ppt-skills/` | A second page would split the signals of the one already ranking. |
| 07-13 | Internal links (8245091): homepage hot list, footer, three related pages point at it | `codex ppt skill` 0 → 17 clicks a week, position 9.0 → 5.2 in a week. |
| 07 | Held instead of rewriting when the head term stalled | Movement came from links and time; the weekly review said "hold". |
| 10-03 | Rebuilt the page as a reviewed list: GitHub search in all star bands + catalog, Jev reads every README, 6 types with a filter, Chinese descriptions checked by Jev, title "PPT Skills for Codex & Claude Code" | The page answers "which tool to use", with more entries and less noise than keyword picks. |
| 10-03 | GitHub list awesome-codex-ppt-skills, both ways linked, daily job adds new repos | `PPT skills GitHub` is a related search; the list is a second entry point and a citable source. |
| 10-05 | Title ≤ 60 characters, one GitHub icon per card instead of "View details / GitHub" text, image dimensions, two FAQ entries for its related searches (`extra_faq`) | Every deduction the On Page audit found; the FAQ answers "PPT skills GitHub" and "Guizang PPT skill" directly. |

## The checklist

0. **Launch with a post, not just a page.** Build the page first, pin the repos the post
   names (`featured`), then post on X with the link: a concrete list ("5 styles, one
   open-source skill each") people bookmark. The PPT post's week took the page from zero
   to 30,687 impressions. Bookmarks (1,302) outnumbered likes: write it as a reference.
1. **Pick the topic from data, not from guesses.**
   - GSC: cluster 3 months of queries by term; a topic with impressions at positions 5–15
     is ready to rank. Positions 40+ are an authority problem, not a page problem: skip.
   - AIsa (DataForSEO): volume and KD for the "skill / MCP for X" form of the topic.
     **KD matters more than volume**: the ppt cluster is ~840 searches a month at KD ≤ 5
     and brought 50,000 impressions.
   - The catalog: are there 30+ real tools behind it? A topic of one famous repo is a
     navigational query that GitHub wins.
2. **One page per topic.** If a page already ranks for it, upgrade that page; never open a
   second slug for the same intent.
3. **Title names the tool intent and the agents** ("… Skills for Codex & Claude Code"), at
   most 60 characters (the generator enforces it). Avoid words with a different intent
   ("presentation skills" = public speaking).
4. **Reviewed content, not keyword picks** (`ops/jev-review/page_profiles.py` →
   `upgrade_page.py collect/split/publish`, `scenario_gate.py judge/types`):
   - every listed repo read by Jev: on the subject, is software, README quality;
   - 5–7 types with a filter on the page;
   - under 50 stars only with a README that shows results;
   - over 300 cards: the strict rule (subject ≥ 0.8, high tier under 50 stars).
5. **Answer the SERP's related searches on the page** (`extra_faq`): run seo.web.cafe
   `/serp/?keyword=<head term>&gl=us`, take its "相关搜索", write one FAQ entry per real
   question, naming the actual repos. Also goes into FAQPage data.
6. **GitHub list** for topics people search "on GitHub" (`build_video_list.py`,
   `list_text_pages.py`): same repos, same types, links both ways, joins the daily job.
7. **Internal links**: homepage hot list, footer, and `related` from neighbouring pages.
   **External links**: aim weight-layer links (guest posts, mentions) at the topic page,
   not the homepage; see "Links" below.
8. **Daily upkeep**: the daily job reviews new repos, drops deleted or renamed ones, and
   rebuilds the list; the report lands in issue #26.
9. **Measure, then hold.** Re-audit with seo.web.cafe `/audit/?url=&kw=`; read GSC weekly by
   page and query. Don't rewrite a page that is moving; links and time compound.

## Links: what the PPT page actually stands on

Checked 10-05 (DataForSEO through AIsa): **the PPT page has no referring domains of its
own**. The X post's link goes through t.co and is nofollow. The site has 117 referring
domains, nearly all pointing at the homepage. So the page ranks on its content, the
site's authority and the launch post, not on links to it.

The site's authority came from the two-layer link work in `ops/backlink-todo.md`
(decided 07-23, `ops/research/niko-meeting-2026-07-23.md`):

| Layer | What | Done |
|---|---|---|
| Weight (dofollow from real sites) | Paid guest posts, 1–2 a day at most, each checked for `rel` | 07-16: programminginsider, nerdbot, thedatascientist, techbullion, aijourn — 10 dofollow links. Paid directories with dofollow pages: creati.ai, Toolify, TAAFT, aibase (~$276 in all). |
| Weight (reference sources) | Data that others cite | Zenodo DOI, Kaggle notebook, Dev.to article, Wikidata entity, Hugging Face dataset card. |
| Discovery (crawl and AI grounding, not weight) | Free directories and lists: verify, don't add more | libhunt, AlternativeTo, mcpservers.org, deepwiki; awesome-list PRs (nofollow, for developers and LLM training data). |
| Rejected | Buying PH votes, buying GitHub stars | Breaks the trust-layer brand; the site's own audit flags exactly this. |

Ahrefs DR: 6 (07-10) → 7 (07-16) → 12 (10-05).

**For the next pages, the gap is deep links.** Every weight-layer link so far points at
the homepage. Point the next guest posts and media mentions at the topic pages
(`/best/claude-video-skills/`, `/best/claude-code-hooks/`, …) with topic anchors, and
submit our GitHub lists to the larger awesome lists in their topic (nofollow, but they
bring readers and are what LLMs read).

## Not yet done on the PPT page

- A YouTube video for "ppt skills": two of page 1's ten results are YouTube.
- Fewer words: ~9,000 per page against the audit's 1,200–1,800; would mean fewer cards.

## Repeated so far

Same pipeline, 10-03 to 10-05: video, Jev, skill management, Telegram, design, knowledge
base / LLM wiki, Claude Code hooks, Obsidian, humanizer (all with lists); code review,
browser automation, Codex, database MCP (pages only); image generation in progress. Steps 5
(`extra_faq` from related searches) and 7 (internal links) were added to all reviewed pages
on 10-05 (c1a2436). Step 0, a launch post, has been done for the PPT page only.
