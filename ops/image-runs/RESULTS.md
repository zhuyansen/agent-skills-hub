# Image generation skills: the same six pictures, 130 skills (2026-11-08)

On the newest models the text is not where skills differ. Claude Code with no skill wrote all six lines and the bag's name correctly, in 5.1 minutes for $0.07 of image calls. 66 skills did as well and none did better. 30 more made all six pictures but broke a rule, most often the format (26 drew the poster square, landscape or 2:3, or the square pictures some other shape) or text on the mascots (8). 31 made no picture: 20 work only with their own service or account, 7 do another job, 2 wait for a person and 2 drew nothing in 20 minutes. By eye, 77 of the 96 complete sets look close to the no-skill set and 19 have a look of their own.

Page: https://agentskillshub.top/best/image-generation/ · Brief: [in/brief.md](in/brief.md) · Runs: run_queue.py → ops/ppt-runs/run.py · Scoring: score_image.py, text_check.py (OCR), text_review.json (by hand) · Tables: summary.py · Page data: evidence.py

## How

On 7 and 8 November 2026 we had 130 image generation skills make the same six pictures in a throwaway sandbox, driven by Claude Code (Claude Opus 5.5): a 3:4 poster for a made-up bakery with six exact lines of English and Chinese text, a square photo of a kraft-paper bag printed with the shop's name, and four square pictures of one mascot in four poses. Every image call went to the newest model of the family the skill asked for (GPT Image 2.6, Nano Banana 2.1 or FLUX 3) through one provider, so the skills compare on their prompts and workflow, not on the model they default to. Claude Code with no skill made the set too. The text was read by OCR, and by hand where OCR stumbled; the formats were measured; a vision model judged whether the four mascots are one character; the look was judged by eye. Each skill ran once, with 20 minutes.

## The model line-up: one poster each, no skill

Each model drew the test's poster once, with no skill, through the same provider; the text was read by OCR and checked by hand. One picture each, and a second try can differ: Nano Banana 2.1 misspelt a Chinese line in an earlier try. The skill test on this page sent every image call to GPT Image 2.6, Nano Banana 2.1 or FLUX 3.

| Model | Lines right (of 6) | Per image | Time | Note |
|---|---|---|---|---|
| Muse | 6 | $0.005 | 53 s |  |
| GPT Image 2 | 6 | $0.009 | 36 s |  |
| GPT Image 2.6 | 6 | $0.009 | 36 s |  |
| Nano Banana 2 | 6 | $0.012 | 14 s |  |
| Nano Banana 2.1 | 6 | $0.012 | 43 s |  |
| Hunyuan Image 3.5 | 6 | $0.019 | 24 s |  |
| Qwen-Image 3 Pro | 6 | $0.029 | 10 s |  |
| Seedream 5 Pro | 6 | $0.029 | 66 s |  |
| FLUX 3 | 6 | $0.038 | 31 s |  |
| Grok Imagine 2 | 6 | $0.048 | 66 s | Only at its own default size |
| Wan 2.7 Image Pro | 6 | $0.054 | 33 s | All six right, plus a line of its own (Est. 2024) |
| Z-Image Turbo | 5 | $0.010 | 7 s | Bristol as Bristel |
| MAI Image 2.6 | 5 | $0.030 | 31 s | 可颂 as 可谅 |
| Nano Banana | 4 | $0.008 | 14 s | Both Chinese lines garbled |
| Nano Banana Pro | 4 | $0.020 | 33 s | Changed the Chinese date and put the last line in English |
| FLUX 2 Pro | 4 | $0.024 | 154 s | Both Chinese lines wrong (周六 as 周云) |
| GPT Image 1 | 4 | $0.200 | 52 s | The price line and the last Chinese line wrong; the dearest per image here |
| Midjourney | - | - | - s | Not offered by the provider we used |
| Imagen 4 | - | - | 18 s | Failed on the day |

## Every skill that made a picture

| Skill | ★ | Result | Text | Format | Look, by eye | Time | Image calls |
|---|---|---|---|---|---|---|---|
| [dacnay816y62-hub/regional-culture-poster](https://github.com/dacnay816y62-hub/regional-culture-poster) | 69 | Followed the brief | 6/6 · bag ✓ | As asked | A look of its own | 3.6 min | 6 · $0.05 |
| [nevertoday/xxd-panel-028](https://github.com/nevertoday/xxd-panel-028) | 72 | Followed the brief | 6/6 · bag ✓ | As asked | A look of its own | 4.6 min | 12 · $0.10 |
| [BIAsia/voxel-icon](https://github.com/BIAsia/voxel-icon) | 103 | Followed the brief | 6/6 · bag ✓ | As asked | A look of its own | 4.7 min | 8 · $0.07 |
| [dacnay816y62-hub/photo-revival](https://github.com/dacnay816y62-hub/photo-revival) | 607 | Followed the brief | 6/6 · bag ✓ | As asked | A look of its own | 6.7 min | 6 · $0.05 |
| [james20141606/sci-figure-workflow](https://github.com/james20141606/sci-figure-workflow) | 41 | Followed the brief | 6/6 · bag ✓ | As asked | A look of its own | 7.8 min | 6 · $0.05 |
| [tmchow/illo-skill](https://github.com/tmchow/illo-skill) | 418 | Followed the brief | 6/6 · bag ✓ | As asked | A look of its own | 9.5 min | 10 · $0.09 |
| [yanliudesign/mono-color-skill](https://github.com/yanliudesign/mono-color-skill) | 3,620 | Followed the brief | 6/6 · bag ✓ | As asked | A look of its own | 10.8 min | 28 · $0.17 |
| [ianlintner/ai-pixel-art-image-generation](https://github.com/ianlintner/ai-pixel-art-image-generation) | 26 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 1.6 min | 6 · $0.05 |
| [Wangnov/gpt-image-2-skill](https://github.com/Wangnov/gpt-image-2-skill) | 146 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 2.0 min | 6 · $0.05 |
| [JongLeePc/gpt-image2-layered-psd](https://github.com/JongLeePc/gpt-image2-layered-psd) | 17 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 2.0 min | 6 · $0.05 |
| [jau123/MeiGen-AI-Design-MCP](https://github.com/jau123/MeiGen-AI-Design-MCP) | 1,800 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 2.1 min | 6 · $0.05 |
| [zhouwei713/gpt-image-2-prompting-skill](https://github.com/zhouwei713/gpt-image-2-prompting-skill) | 56 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 2.2 min | 7 · $0.06 |
| [zvensmoluya/zven-imagegen](https://github.com/zvensmoluya/zven-imagegen) | 9 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 2.2 min | 6 · $0.05 |
| [dshark3y/gpt-image-2-skill](https://github.com/dshark3y/gpt-image-2-skill) | 19 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 2.4 min | 6 · $0.05 |
| [jiangmuran/claude-image](https://github.com/jiangmuran/claude-image) | 88 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 2.5 min | 6 · $0.05 |
| [kismmmnato0933/gpt-image-skills](https://github.com/kismmmnato0933/gpt-image-skills) | 6 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 2.6 min | 6 · $0.05 |
| [skorfmann/nanobanana](https://github.com/skorfmann/nanobanana) | 8 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 2.8 min | 7 · $0.10 |
| [liangdabiao/ecom-details-image](https://github.com/liangdabiao/ecom-details-image) | 1,615 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 2.9 min | 6 · $0.05 |
| [fengfengzhidao/codex-image2-skill](https://github.com/fengfengzhidao/codex-image2-skill) | 155 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 2.9 min | 6 · $0.05 |
| [Sateezg/codex-bridge](https://github.com/Sateezg/codex-bridge) | 244 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 2.9 min | 6 · $0.05 |
| [gnipbao/openai-image-prompt-writer](https://github.com/gnipbao/openai-image-prompt-writer) | 13 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.0 min | 6 · $0.05 |
| [JunSeo99/claude-skill-codex-imagegen](https://github.com/JunSeo99/claude-skill-codex-imagegen) | 22 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.2 min | 7 · $0.06 |
| [techkwon/hermes-codex-image-skill](https://github.com/techkwon/hermes-codex-image-skill) | 6 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.2 min | 7 · $0.06 |
| [dqtx760/deepseek-imagegen](https://github.com/dqtx760/deepseek-imagegen) | 7 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.2 min | 6 · $0.05 |
| [joeseesun/qiaomu-codex-imagegen](https://github.com/joeseesun/qiaomu-codex-imagegen) | 136 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.3 min | 6 · $0.05 |
| [yiyanli123/biorender-mechanism-figures-skill](https://github.com/yiyanli123/biorender-mechanism-figures-skill) | 41 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.3 min | 7 · $0.06 |
| [huysh3/sub2api-gpt-image-2](https://github.com/huysh3/sub2api-gpt-image-2) | 13 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.3 min | 7 · $0.06 |
| [Xuan-BOMS/codex-gpt-image-mcp](https://github.com/Xuan-BOMS/codex-gpt-image-mcp) | 5 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.3 min | 7 · $0.06 |
| [yc-duan/api-image](https://github.com/yc-duan/api-image) | 109 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.4 min | 7 · $0.06 |
| [stevenjinlong/remote-imagegen](https://github.com/stevenjinlong/remote-imagegen) | 24 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.4 min | 7 · $0.06 |
| [missuo/design-bridge](https://github.com/missuo/design-bridge) | 8 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.4 min | 8 · $0.07 |
| [UzenUPoZiTiV4ik/gpt-image-2-skill](https://github.com/UzenUPoZiTiV4ik/gpt-image-2-skill) | 439 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.5 min | 6 · $0.05 |
| [IanShaw027/codex-image](https://github.com/IanShaw027/codex-image) | 32 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.5 min | 7 · $0.06 |
| [mrafaeldie12/nano-banana-pro-mcp](https://github.com/mrafaeldie12/nano-banana-pro-mcp) | 18 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.5 min | 6 · $0.08 |
| [feedtailor/ccskill-nanobanana](https://github.com/feedtailor/ccskill-nanobanana) | 29 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.6 min | 6 · $0.07 |
| [Ibrahim-3d/nano-banana-claude-plugin](https://github.com/Ibrahim-3d/nano-banana-claude-plugin) | 14 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.6 min | 6 · $0.07 |
| [luckyabsoluter/codex-imagegen-free-reference](https://github.com/luckyabsoluter/codex-imagegen-free-reference) | 6 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.7 min | 7 · $0.06 |
| [guinacio/claude-image-gen](https://github.com/guinacio/claude-image-gen) | 80 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 3.8 min | 9 · $0.11 |
| [bushibohai/creating-social-media-visuals](https://github.com/bushibohai/creating-social-media-visuals) | 9 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 4.0 min | 9 · $0.08 |
| [Cuimao777/eterna-image2image-skill](https://github.com/Cuimao777/eterna-image2image-skill) | 185 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 4.1 min | 8 · $0.07 |
| [Xiangyu-CAS/codex-canvas](https://github.com/Xiangyu-CAS/codex-canvas) | 160 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 4.2 min | 8 · $0.07 |
| [jiahuiqu17/paper-signal](https://github.com/jiahuiqu17/paper-signal) | 109 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 4.3 min | 7 · $0.06 |
| [AlekseiUL/gpt-image-2-5-agent-kit](https://github.com/AlekseiUL/gpt-image-2-5-agent-kit) | 25 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 4.4 min | 6 · $0.05 |
| [gpt-img-2/gpt-image-2-ecommerce-skill](https://github.com/gpt-img-2/gpt-image-2-ecommerce-skill) | 13 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 4.4 min | 7 · $0.06 |
| [kingbootoshi/nano-banana-2-skill](https://github.com/kingbootoshi/nano-banana-2-skill) | 417 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 4.5 min | 7 · $0.09 |
| [xianyu110/ecommerce-image-skills](https://github.com/xianyu110/ecommerce-image-skills) | 155 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 4.5 min | 8 · $0.07 |
| [wukongnotnull/image-inspirer](https://github.com/wukongnotnull/image-inspirer) | 41 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 4.5 min | 7 · $0.06 |
| [alchaincyf/huashu-gpt-image](https://github.com/alchaincyf/huashu-gpt-image) | 29 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 4.5 min | 7 · $0.06 |
| [xujie8867/hermes-daily-image-training](https://github.com/xujie8867/hermes-daily-image-training) | 5 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 4.5 min | 7 · $0.06 |
| [qwwiwi/codex-gpt-image-2-subscription](https://github.com/qwwiwi/codex-gpt-image-2-subscription) | 9 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 4.6 min | 7 · $0.06 |
| [dacnay816y62-hub/fantasy-dongfang-jianyuehaibao](https://github.com/dacnay816y62-hub/fantasy-dongfang-jianyuehaibao) | 126 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 4.7 min | 7 · $0.06 |
| [2023Anita/scientific-visual-skills](https://github.com/2023Anita/scientific-visual-skills) | 21 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 4.7 min | 7 · $0.06 |
| [jinshiqwq/image-first-frontend](https://github.com/jinshiqwq/image-first-frontend) | 6 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 5.1 min | 6 · $0.05 |
| [fengyunzaidushi/sub2api-4k-image-generator-ts](https://github.com/fengyunzaidushi/sub2api-4k-image-generator-ts) | 12 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 5.2 min | 10 · $0.09 |
| [nikships/ultimate-image-gen-mcp](https://github.com/nikships/ultimate-image-gen-mcp) | 14 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 5.5 min | 7 · $0.10 |
| [thangphistudent/nano-banana-2-promptor-skill](https://github.com/thangphistudent/nano-banana-2-promptor-skill) | 8 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 5.9 min | 8 · $0.14 |
| [AgriciDaniel/banana-claude](https://github.com/AgriciDaniel/banana-claude) | 1,192 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 6.0 min | 6 · $0.07 |
| [QIYU-JACKMAN/codexQIYU-image-workflow](https://github.com/QIYU-JACKMAN/codexQIYU-image-workflow) | 107 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 6.1 min | 6 · $0.05 |
| [zhongweili/nanobanana-mcp-server](https://github.com/zhongweili/nanobanana-mcp-server) | 403 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 6.4 min | 6 · $0.07 |
| [buluslan/gpt-image2-ecommerce](https://github.com/buluslan/gpt-image2-ecommerce) | 442 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 6.5 min | 7 · $0.06 |
| [dancolta/gen-images-skill](https://github.com/dancolta/gen-images-skill) | 32 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 6.8 min | 7 · $0.09 |
| [Subaru486desuwa/micu-image-mcp](https://github.com/Subaru486desuwa/micu-image-mcp) | 318 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 7.0 min | 6 · $0.05 |
| [YCSE/nanobanana-mcp](https://github.com/YCSE/nanobanana-mcp) | 32 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 7.8 min | 6 · $0.07 |
| [ConechoAI/Nano-Banana-MCP](https://github.com/ConechoAI/Nano-Banana-MCP) | 235 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 8.5 min | 7 · $0.08 |
| [doudou770/flyreq-image-studio](https://github.com/doudou770/flyreq-image-studio) | 169 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 8.9 min | 7 · $0.06 |
| [alchaincyf/huashu-slide-codex](https://github.com/alchaincyf/huashu-slide-codex) | 25 | Followed the brief | 6/6 · bag ✓ | As asked | Close to the no-skill set | 10.1 min | 8 · $0.07 |
| [s1dashu/ip-as-logo-skill](https://github.com/s1dashu/ip-as-logo-skill) | 6,456 | Broke a rule | 0/6 · bag ✗ | Poster 1:1 | A look of its own | 1.5 min | 6 · $0.05 |
| [TaiT-tt/tait-crt-interface-skill](https://github.com/TaiT-tt/tait-crt-interface-skill) | 541 | Broke a rule | 6/6 · bag ✓ | As asked | A look of its own | 2.6 min | 6 · $0.05 |
| [aehyok/generate-article-cover-image](https://github.com/aehyok/generate-article-cover-image) | 16 | Broke a rule | 6/6 · bag ✓ | All six 5:2 | A look of its own | 3.0 min | 6 · $0.05 |
| [chujianyun/awesome-gpt-image2-ppt-skills](https://github.com/chujianyun/awesome-gpt-image2-ppt-skills) | 191 | Broke a rule | 6/6 · bag ✓ | All six 16:9 | A look of its own | 3.1 min | 6 · $0.05 |
| [moonlin1213/muted-zine-poster-v01](https://github.com/moonlin1213/muted-zine-poster-v01) | 90 | Broke a rule | 6/6 · bag ✓ | All six 9:16 | A look of its own | 3.4 min | 7 · $0.06 |
| [chiyolyn/bold-contour-ink-portrait](https://github.com/chiyolyn/bold-contour-ink-portrait) | 9 | Broke a rule | 6/6 · bag ✓ | As asked | A look of its own | 4.5 min | 8 · $0.07 |
| [NimaChu/xhs-imagen](https://github.com/NimaChu/xhs-imagen) | 120 | Broke a rule | 6/6 · bag ✓ | 5 not square | A look of its own | 5.7 min | 7 · $0.06 |
| [helloianneo/ian-xiaohei-scenes](https://github.com/helloianneo/ian-xiaohei-scenes) | 552 | Broke a rule | 2/6 · bag ✓ | All six 16:9 | A look of its own | 6.0 min | 10 · $0.09 |
| [dacnay816y62-hub/fantasy-qiqiguaiguai-skill](https://github.com/dacnay816y62-hub/fantasy-qiqiguaiguai-skill) | 125 | Broke a rule | 6/6 · bag ✓ | 5 not square | A look of its own | 8.0 min | 15 · $0.13 |
| [CaliCastle/skills](https://github.com/CaliCastle/skills) | 97 | Broke a rule | 1/6 · bag ✓ | As asked | A look of its own | 8.1 min | 15 · $0.13 |
| [helloianneo/ian-xiaohei-illustrations](https://github.com/helloianneo/ian-xiaohei-illustrations) | 13,125 | Broke a rule | 6/6 · bag ✓ | All six 16:9 | A look of its own | 12.4 min | 17 · $0.05 |
| [ningzimu/codex-ppt-skill](https://github.com/ningzimu/codex-ppt-skill) | 7,716 | Broke a rule | 6/6 · bag ✓ | All six 16:9 | A look of its own | 20.1 min | 9 · $0.08 |
| [op7418/guizang-material-illustration](https://github.com/op7418/guizang-material-illustration) | 1,243 | Broke a rule | 6/6 · bag ✓ | Poster 1:1 | Close to the no-skill set | 2.6 min | 6 · $0.05 |
| [shixinnt/codex-image-context-runtime](https://github.com/shixinnt/codex-image-context-runtime) | 97 | Broke a rule | 6/6 · bag ✓ | Poster 2:3 | Close to the no-skill set | 3.1 min | 6 · $0.05 |
| [jkalasas/artifex-mcp](https://github.com/jkalasas/artifex-mcp) | 9 | Broke a rule | 6/6 · bag ✓ | Poster 9:16 | Close to the no-skill set | 3.1 min | 6 · $0.05 |
| [minilozio/nano-banana-prompting-skill](https://github.com/minilozio/nano-banana-prompting-skill) | 5 | Broke a rule | 0/6 · bag ✗ | As asked | Close to the no-skill set | 3.3 min | 7 · $0.10 |
| [xiaohuailabs/xiaohu-ip-studio](https://github.com/xiaohuailabs/xiaohu-ip-studio) | 304 | Broke a rule | 6/6 · bag ✓ | Poster 2:3 | Close to the no-skill set | 3.6 min | 7 · $0.06 |
| [zackproser/claude-custom-skills-demo](https://github.com/zackproser/claude-custom-skills-demo) | 7 | Broke a rule | 6/6 · bag ✓ | Poster 1:1 | Close to the no-skill set | 3.7 min | 13 · $0.16 |
| [stevenjinlong/awesome-ppt-skills](https://github.com/stevenjinlong/awesome-ppt-skills) | 74 | Broke a rule | 6/6 · bag ✓ | Poster 1:1 | Close to the no-skill set | 3.8 min | 8 · $0.07 |
| [FA-T-T/codex-skill-academic-slides](https://github.com/FA-T-T/codex-skill-academic-slides) | 8 | Broke a rule | 6/6 · bag ✓ | All six 16:9 | Close to the no-skill set | 4.4 min | 7 · $0.06 |
| [JKc66/custom-icons-skill](https://github.com/JKc66/custom-icons-skill) | 41 | Broke a rule | 6/6 · bag ✓ | Poster 1:1 | Close to the no-skill set | 4.7 min | 7 · $0.06 |
| [dreiachse-cyber/image-cockpit-for-codex-workflows](https://github.com/dreiachse-cyber/image-cockpit-for-codex-workflows) | 296 | Broke a rule | 6/6 · bag ✓ | Poster 2:3 | Close to the no-skill set | 4.9 min | 6 · $0.05 |
| [spartanz51/imagegen-mcp](https://github.com/spartanz51/imagegen-mcp) | 37 | Broke a rule | 6/6 · bag ✓ | Poster 2:3 | Close to the no-skill set | 6.0 min | 6 · $0.05 |
| [chawlaaditya/NanoBananaASO](https://github.com/chawlaaditya/NanoBananaASO) | 61 | Broke a rule | 6/6 · bag ✓ | 5 not square | Close to the no-skill set | 6.8 min | 8 · $0.11 |
| [CLOUDWERX-DEV/gpt-image-1-mcp](https://github.com/CLOUDWERX-DEV/gpt-image-1-mcp) | 18 | Broke a rule | 6/6 · bag ✓ | Poster 2:3 | Close to the no-skill set | 6.8 min | 6 · $0.05 |
| [JuneYaooo/xhs-writer-skill](https://github.com/JuneYaooo/xhs-writer-skill) | 190 | Broke a rule | 4/6 · bag ✓ | All six 2:3 | Close to the no-skill set | 9.0 min | 21 · $0.18 |
| [lansespirit/image-gen-mcp](https://github.com/lansespirit/image-gen-mcp) | 69 | Broke a rule | 6/6 · bag ✓ | Poster 2:3 | Close to the no-skill set | 9.1 min | 14 · $0.12 |
| [qhdrl12/mcp-server-gemini-image-generator](https://github.com/qhdrl12/mcp-server-gemini-image-generator) | 34 | Broke a rule | 0/6 · bag ✗ | Poster 1:1 | Close to the no-skill set | 10.3 min | 23 · $0.28 |
| [kkoppenhaver/cc-nano-banana](https://github.com/kkoppenhaver/cc-nano-banana) | 382 | Broke a rule | 6/6 · bag ✓ | Poster 1:1 | Close to the no-skill set | 17.5 min | 9 · $0.11 |
| [zhouzhq2021/PaperBanana-AIMSLab](https://github.com/zhouzhq2021/PaperBanana-AIMSLab) | 8 | Broke a rule | 6/6 · bag ✓ | Poster 2:3 | Close to the no-skill set | 21.2 min | 48 · $0.41 |
| [llmsresearch/paperbanana](https://github.com/llmsresearch/paperbanana) | 2,471 | Part of the set | - | As asked | - | 20.1 min | 10 · $0.14 |
| [mituan-ai/PaperBanana-CN](https://github.com/mituan-ai/PaperBanana-CN) | 85 | Part of the set | 6/6 · bag ✓ | As asked | - | 20.1 min | 3 · $0.04 |
| [liyue-aigc/female-portrait-director](https://github.com/liyue-aigc/female-portrait-director) | 1,699 | Portrait only | - | - | - | 1.9 min | 1 · $0.01 |

## Made no picture (31)

- [andyluu98/ai-image-gpt-mcp](https://github.com/andyluu98/ai-image-gpt-mcp): Works only with its own service or account: needs a ChatGPT sign-in in a browser; it does not read an API key.
- [AndyShaman/gemini-webapi-mcp](https://github.com/AndyShaman/gemini-webapi-mcp): Works only with its own service or account: needs a signed-in Gemini web session (browser cookies).
- [awei84/antibanana-mcp](https://github.com/awei84/antibanana-mcp): Works only with its own service or account: needs Antigravity credentials.
- [black-forest-labs/flux-mcp](https://github.com/black-forest-labs/flux-mcp): Works only with its own service or account: needs a Black Forest Labs account (the hosted official MCP).
- [BlockRunAI/Claude-Code-GPT-IMAGE2-SeeDance-BlockRun](https://github.com/BlockRunAI/Claude-Code-GPT-IMAGE2-SeeDance-BlockRun): Works only with its own service or account: needs a funded BlockRun wallet (USDC on Base).
- [boteSu/aiChatGptAgent](https://github.com/boteSu/aiChatGptAgent): Works only with its own service or account: needs ChatGPT web accounts, which it offers to mass-register: against OpenAI's terms, so not done.
- [Bria-AI/bria-skill](https://github.com/Bria-AI/bria-skill): Works only with its own service or account: needs a Bria API key.
- [darkamenosa/codex-imagen](https://github.com/darkamenosa/codex-imagen): Works only with its own service or account: needs a ChatGPT or Codex sign-in; it does not take an API key.
- [jomeswang/agnes-ai-skill](https://github.com/jomeswang/agnes-ai-skill): Works only with its own service or account: needs an Agnes API key.
- [kodelyx/flow-agent](https://github.com/kodelyx/flow-agent): Works only with its own service or account: needs a signed-in Google Flow session.
- [koshimazaki/flux-api-control-surface](https://github.com/koshimazaki/flux-api-control-surface): Works only with its own service or account: needs a Black Forest Labs key in the macOS Keychain.
- [luciferfran/nan-mcp-server](https://github.com/luciferfran/nan-mcp-server): Works only with its own service or account: needs a NaN API key.
- [metavolve-labs/studiomcphub](https://github.com/metavolve-labs/studiomcphub): Works only with its own service or account: needs paid credits on its hosted server.
- [ningzimu/codex-gpt-image](https://github.com/ningzimu/codex-gpt-image): Works only with its own service or account: needs a Codex sign-in and says not to use an API key.
- [nopnor/SCOPE](https://github.com/nopnor/SCOPE): Works only with its own service or account: needs a JD Cloud account.
- [runapi-ai/mcp](https://github.com/runapi-ai/mcp): Works only with its own service or account: needs a RunAPI account.
- [SamurAIGPT/Generative-Media-Skills](https://github.com/SamurAIGPT/Generative-Media-Skills): Works only with its own service or account: needs a MuAPI account and key.
- [scenario-labs/skills](https://github.com/scenario-labs/skills): Works only with its own service or account: needs a Scenario account or API key.
- [TamerinTECH/claude-code-generate-images-mcp](https://github.com/TamerinTECH/claude-code-generate-images-mcp): Works only with its own service or account: calls a retired Gemini 2.0 endpoint written into its code, or Azure OpenAI; our sandbox's relay did not serve that endpoint.
- [xinvxueyuan/NovelAI-Image-MCP](https://github.com/xinvxueyuan/NovelAI-Image-MCP): Works only with its own service or account: needs a NovelAI account.
- [Andy20010101/style-prompt-forger-skill](https://github.com/Andy20010101/style-prompt-forger-skill): Does another job, not pictures from a brief: writes reusable style prompts, not pictures.
- [Evianis/travel-photo-abstraction](https://github.com/Evianis/travel-photo-abstraction): Does another job, not pictures from a brief: needs a travel photo to start from.
- [karem505/character-animation-skill](https://github.com/karem505/character-animation-skill): Does another job, not pictures from a brief: animates a character picture you give it.
- [LueXxxxxxx/architecture-image2-diagram-skill](https://github.com/LueXxxxxxx/architecture-image2-diagram-skill): Does another job, not pictures from a brief: draws architecture diagrams only.
- [op7418/guizang-yingzao-skill](https://github.com/op7418/guizang-yingzao-skill): Does another job, not pictures from a brief: covers its own subject only, not ads, products or mascots.
- [ShinChven/nano-banana-skills](https://github.com/ShinChven/nano-banana-skills): Does another job, not pictures from a brief: needs existing pictures of the character; makes a three-view sheet.
- [Vieeeeeee/wibi-style](https://github.com/Vieeeeeee/wibi-style): Does another job, not pictures from a brief: restyles a photo you give it, and its licence is non-commercial only.
- [Gayaya999/ecommerce-detail-page-generator](https://github.com/Gayaya999/ecommerce-detail-page-generator): Waits for a person first: asks for missing shop details before drawing, and makes text-free product shots only.
- [izscc/cc2image](https://github.com/izscc/cc2image): Waits for a person first: must have a person pick a style in a separate plugin first.
- [helloianneo/ian-handdrawn-ppt](https://github.com/helloianneo/ian-handdrawn-ppt): No picture within 20 minutes: a slide-deck workflow: no picture saved in 20 minutes.
- [JuneYaooo/gpt-image2-ppt-skills](https://github.com/JuneYaooo/gpt-image2-ppt-skills): No picture within 20 minutes: a slide-deck workflow: no picture saved in 20 minutes.

## Limits

One run per skill, 20 minutes each; a second run would draw different pictures. Every image call was moved to the newest model of its family, so a skill that pins an older model was not tested on it. The look is our judgement by eye. The mascot verdicts are a vision model's, which gave nearly every set 5 of 5 and counted Zzz sleep marks as text on two sets (overridden by hand, see text_review.json). Skills that need their own service, an account, a photo to start from or a person to answer were stopped, not worked around.
