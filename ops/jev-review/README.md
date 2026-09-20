# Scanner second-pass eval — does a decision model know a command from a citation?

The scanner grades ~27.7K READMEs with regexes. Its recurring failure is one shape: a
security tool printing the attack it blocks, a comparison table naming a tool, or a
flagged word landing inside ordinary prose. This measures whether a second pass can tell
those apart, against baselines that cost nothing.

## The question, decomposed

Not "is this repo dangerous" — that has no ground truth here and the decisions API answers
it poorly (AUC 0.70 in an earlier run vs 0.94 for "what is this"). The question each item
asks is about the *textual role* of the matched line, which a careful reader can settle
from the text alone:

> Does this line **issue** the flagged behaviour, or only **cite** it?

Danger is explicitly irrelevant: a legitimate `sudo apt install foo` counts as issued.
Four atomic questions, weights fixed before any result was seen:

| question | what it asks | AUC alone |
|---|---|---|
| `issues_it` | an instruction, a config the reader sets, or what the project does | 0.819 |
| `is_documentation` | a rule table, severity list, blocked-pattern list | 0.200 (0.800 inverted) |
| `is_negated` | tells the reader not to, or says the project prevents it | 0.096 (**0.904 inverted**) |
| `word_coincidence` | landed inside another word, a filename, a URL | 0.223 (0.777 inverted) |

The three *negative* questions discriminate better than the positive one. Asking only the
obvious question would have left most of the signal on the table.

## Data

`build_dataset.py` pulls every flag instance the live scanner raises, with the line that
raised it: 691 items over 28 flags (complete for the rare flags, capped for `sudo_usage`
and `tunnel_service`). 120 were hand-labelled first, blind, stratified across all 28 flags;
one was undecidable and dropped. **55.5% of flagged lines genuinely issue the behaviour** —
so 44.5% of what the audit pages show is a citation.

## Results (n=119 hand-labelled)

| adjudicator | AUC | precision | recall | accuracy |
|---|---|---|---|---|
| scanner today (every flag = issued) | — | 0.555 | 1.000 | 0.555 |
| scanner's own citation heuristic | — | 0.333 | 0.136 | 0.370 |
| inside a code fence | — | 0.892 | 0.500 | 0.689 |
| keyword + markdown-table baseline | — | 0.701 | 0.924 | 0.739 |
| independent judge, one shot (Haiku) | 0.755 | 0.805 | 0.500 | 0.655 |
| Jev, `issues_it` alone | 0.819 | 0.656 | 0.924 | 0.689 |
| **Jev, 4-question combo** | **0.916** [0.865, 0.957] | 0.917 | 0.667 | 0.782 |
| keyword AND Jev > 0 | — | 0.836 | 0.924 | **0.857** |

At the keyword baseline's recall (0.924), Jev's precision is 0.792 against its 0.701.

The scanner's own `_is_cited_or_negated` scores 0.370 as a general adjudicator — it is
tuned per rule (fences and inline code excuse a flag), so as a blanket second pass it
suppresses real install commands. It is not a baseline this replaces; it is a different job.

### Operating point

| threshold | flags suppressed | citations cleared | real flags lost |
|---|---|---|---|
| **0.0** | 34 / 119 | **34 / 53 (64%)** | **0 / 66 (0%)** |
| 0.2 | 47 / 119 | 37 / 53 | 10 / 66 (15%) |
| 0.4 | 65 / 119 | 48 / 53 | 17 / 66 (26%) |

Zero is a free lunch on this sample: two thirds of the false flags clear without touching
a true one. Treat the 0% loss as "below resolution at n=66", not as a guarantee.

## Catalog impact (all 691, threshold 0)

189 flag instances suppressed (27.4%). Per flag, sorted by how much of it is noise:

```
chmod_dangerous       26/26  100%     cron_persistence    15/52   29%
etc_sensitive_read     6/7    86%     agent_memory_theft  21/81   26%
sensitive_dir_access  25/37   68%     subprocess_spawn     9/40   22%
eval_usage            38/60   63%     tunnel_service      14/90   16%
reverse_shell          3/5    60%     sudo_usage           8/120    7%
ssl_disabled           6/17   35%     curl_pipe_shell      0/12     0%
docker_privileged      9/30   30%     env_access           0/40     0%
```

**A rule at ~100% suppression is a broken rule, not a second-pass candidate.**
`chmod_dangerous` clears 26/26 and hand-labelled 0/6 issued — it belongs on the list with
`env_file_read` and `backdoor_install`, deleted rather than filtered.

Grade movement, holding trust tier at 5 (the strictest, so this is an upper bound):
160 of 646 repos move — 85 unsafe→safe, 72 caution→safe, 2 reject→safe, 1 unsafe→caution.

## Cost and provenance

691 items × 4 questions = **$0.018**, model pinned `typesafe/jev-1.13-20260917`. A full
catalog re-scan is ~2,300 flag instances, so pennies; an incremental sync is less.

## Caveats

- Hand labels are mine (Claude Opus 5). A blind second labeler (Haiku, same prompt, no
  access to the labels) agreed on **65.5%** — and that 34% disagreement is the honest
  error bar on this ground truth, not noise to be tidied away. It is not random: the
  judge calls a markdown table row CITED even when the cell holds the install command the
  reader is meant to run (`| windows | winget install python… |`), and I call that
  ISSUED. Where a flag's *name* implies malice but its *claim text* is literal
  (`agent_memory_theft` = "accesses agent memory/identity files"), I labelled toward the
  name and both models labelled toward the text — they are probably right. **Labels were
  not revised after seeing any model's answers.**
- The judge is also an Anthropic model, so its agreement bounds my idiosyncrasy, not a
  family-wide one. Jev is a different vendor, so Jev-vs-labels is at least not self-scoring.
- n=119. The AUC CI is ±0.05; per-flag rates from 5-6 items are directional only.
- Some misfires are rule-scope defects a second pass should not be asked to fix:
  all 7 `raw_ip_request` hits are `127.0.0.1`, and `write_etc` fires on
  `<path-to-squish>/etc/…`. Those need the rule narrowed, not a model.

## Files

`build_dataset.py` → `adjudicate.py` → `report.py` / `impact.py`. Outputs land in `out/`
(gitignored). `OPENROUTER_API_KEY` must be set; answers are cached per state hash.
