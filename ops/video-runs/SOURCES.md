# Sources for the video test's method (verified at source 2026-10-11)

Read on the arXiv or publisher page through a summarising fetch, except Deganutti et al. 2605.16223, read page by page.
Re-open the source before quoting any number verbatim on the site.

| Source | ID | What it gives this test |
|---|---|---|
| TheoremExplainAgent (Ku et al., ACL 2025) | arXiv 2502.19400 | Render success as the first metric (93.8% for o3-mini, abstract); most videos show minor element-layout issues; automatic metric vs human Spearman from 0.72 (visual relevance) down to 0.14-0.17 (Table 4). |
| Code2Video (Chen et al., 2025) | arXiv 2510.01174 | Code-rendered video beats pixel video models on layout and teaching value (Table 1); people penalise layout errors more than the VLM judge does (Sec. 5.3). Venue unconfirmed. |
| MoVer (Ma and Agrawala, SIGGRAPH 2025) | arXiv 2502.13372 | 58.8% of animations correct with no iteration, 93.6% with up to 50 corrections (abstract): report first try and after retries apart. |
| Evaluating Design Video Generation (Deganutti et al., ICML 2026 workshop) | arXiv 2605.16223 | Text recoverability: OCR on frames at 2 fps, exact match in at least one frame; OCR reads only 0.659 of perfect renders, so calibrate on a known-good render (Sec. 4.5, Table 7). Duration as a metric. |
| Graphic-Design-Bench (Deganutti et al., 2026) | arXiv 2604.04192 | VLMs misjudge duration by about 6 s and classify motion type below 13%: measure duration and motion from the file, not with a model. |
| VBench (Huang et al., 2023) | arXiv 2311.17982 | Motion measured beside consistency: a static video scores well on consistency alone. Venue unconfirmed. |
| SkillsBench (Li et al., 2026, v4) | arXiv 2602.12670 | Same task with and without the skill, deterministic verifiers; curated skills +16.6 points. |
| HeyGen Code2Video Bench (vendor post, 2026-09-18) | heygen.com/research/introducing-code2video-benchmark | Not peer reviewed; the author builds the renderer and the judge. General VLM judges agreed with people 75% of the time (self-reported). |

Checks these support: renders to a playable file; requested duration and resolution met (ffprobe); every required
line of copy readable in at least one sampled frame; something moves (frame difference). "No blank frames" is a
sanity check without a source. A VLM's opinion of quality stays secondary and labelled as such.
