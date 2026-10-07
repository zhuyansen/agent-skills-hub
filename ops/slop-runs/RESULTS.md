## Rewriters

| Skill | ★ | Kind | Files | Deepest layer | Human (1-5) | Structure features removed | Facts | Tells | Em-dashes | Min |
|---|---:|---|---|---|---:|---:|---|---|---|---:|
| seyedehsanhadi/sloptrim | 212 | detector | post_en story_en | phrasing | 4.5 | 0 | 3/3 | 1→1 0→0 | 6→2 2→2 | 1.0 |
| miqdadbadjuber/anti-slop | 4501 | rules | post_en story_en | phrasing | 4.0 | 1 | 3/3 | 1→0 0→0 | 6→0 2→0 | 0.7 |
| eric-tramel/slop-guard | 163 | detector | post_en story_en | phrasing | 4.0 | 0 | 3/3 | 1→0 0→0 | 6→0 2→1 | 1.6 |
| AIScientists-Dev/academic-humanizer | 1781 | rules | post_en story_en | phrasing | 3.5 | 0 | 3/3 | 1→1 0→0 | 6→0 2→0 | 0.8 |
| realrossmanngroup/no_ai_slop_writing_rules | 694 | rules | post_en story_en | phrasing | 3.5 | 0 | 3/3 | 1→1 0→0 | 6→0 2→0 | 0.9 |
| NulightJens/humanizer-stack | 318 | writing | post_en story_en | structure | 3.5 | 1 | 3/3 | 1→0 0→0 | 6→0 2→0 | 1.2 |
| Aboudjem/humanizer-skill | 264 | detector | post_en post_zh story_en | phrasing | 3.3 | 1 | 3/3 3/3 | 1→1 1→0 0→0 | 6→0 0→0 2→0 | 2.3 |
| blader/humanizer | 54072 | writing | post_en post_zh story_en | phrasing | 3.0 | 0 | 3/3 3/3 | 1→0 1→0 0→0 | 6→0 0→0 2→0 | 1.2 |
| op7418/Humanizer-zh | 18940 | chinese | post_zh | phrasing | 3.0 | 0 | 3/3 | 1→0 | 0→0 | 0.5 |
| hardikpandya/stop-slop | 17755 | rules | post_en story_en | phrasing | 3.0 | 1 | 3/3 | 1→0 0→0 | 6→0 2→0 | 0.7 |
| Nanako0129/sepia | 2970 | writing | post_en post_zh story_en | structure | 3.0 | 0 | 3/3 3/3 | 1→1 1→0 0→0 | 6→0 0→0 2→2 | 2.1 |
| Raymondhou0917/speak-human-tw | 1027 | chinese | post_zh | phrasing | 3.0 | 0 | 3/3 | 1→0 | 0→0 | 1.1 |
| OUBIGFA/De-AI-Prompt-Enhancer-Writer-Booster-SKILL | 848 | chinese | post_zh | phrasing | 3.0 | 0 | 3/3 | 1→1 | 0→0 | 0.8 |
| LifelongLazyLearner/qu-ai-wei | 622 | chinese | post_zh | phrasing | 3.0 | 0 | 3/3 | 1→0 | 0→2 | 0.9 |
| harshaneel/humanize | 515 | writing | post_en story_en | phrasing | 3.0 | 1 | 3/3 | 1→0 0→0 | 6→0 2→0 | 0.9 |
| MohamedAbdallah-14/unslop | 153 | writing | post_en story_en | phrasing | 3.0 | 1 | 3/3 | 1→1 0→0 | 6→0 2→0 | 0.9 |
| rudra496/StealthHumanizer | 156 | writing | post_en post_zh story_en | phrasing | 2.3 | 0 | 3/3 3/3 | 1→1 1→1 0→0 | 6→0 0→0 2→0 | 11.1 |
| larashero3-dotcom/lieflat-less-ai-tone | 2303 | chinese | post_zh | phrasing | 2.0 | 0 | 3/3 | 1→1 | 0→0 | 1.1 |
| MrGeDiao/shuorenhua | 1980 | chinese | post_zh | phrasing | 2.0 | 0 | 3/3 | 1→0 | 0→0 | 0.5 |
| devswha/patina | 363 | writing | post_en post_zh | phrasing | 2.0 | 0 | 3/3 3/3 | 1→1 1→0 | 6→4 0→0 | 8.2 |
| DadaNanjesha/AI-Text-Humanizer-App | 435 | writing | post_en story_en | phrasing | 1.0 | 0 | 3/3 | 1→2 0→7 | 6→6 2→2 | 2.5 |

## Detectors

| Skill | ★ | Files | Flags | Surface / Phrasing / Structure |
|---|---:|---|---:|---|
| conorbronsdon/avoid-ai-writing | 4864 | 3 | 7 | 3 / 4 / 0 |
| Aboudjem/humanizer-skill | 264 | 3 | 38 | 14 / 16 / 8 |
| seyedehsanhadi/sloptrim | 212 | 2 | 6 | 5 / 1 / 0 |
| eric-tramel/slop-guard | 163 | 2 | 5 | 1 / 2 / 2 |
| tbhb/vale-ai-tells | 115 | 2 | 22 | 12 / 8 / 2 |

## Not run

- lynote-ai/humanize-text (not run): Needs a Niutrans translation key besides an LLM key, and always outputs English.
- iniwap/AIWriteX (not a fit): A desktop app that writes new articles from trending topics and posts them to WeChat; it cannot rewrite a given file.
- alexgreensh/attention-span (not a fit): Changes how Claude writes its own replies; its skills start only when a person types the command.
