"""One-off: the method blocks for three pages, written before their tests finish (2026-10-11).

  python ops/research/method_blocks_2026_10_11.py

Numbers are from the abstracts re-read at arxiv.org on 2026-10-11 (ops/video-runs/SOURCES.md) and
from the crowding runs in ops/codex-runs (session sizes at 12, 112 and 512 installed skills). Each test's evidence.py later puts its findings on top
(runs_common.update_method) and replaces the "not yet run" line.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEYWORDS = ROOT / "frontend/scripts/scenario-keywords.json"
STANDARD = [("A security grade reads what a repository says and contains; it does not watch the tool run.", "安全评级看的是仓库写了什么、包含什么，不是观察工具运行时的行为。"),
            ("No one pays to be listed or ranked here.", "没有任何条目是付费上榜或付费排名的。")]
SRC = {
    "theorem": ("Ku, Chong, Leung, Shah, Yu and Chen. TheoremExplainAgent: Towards Video-based Multimodal Explanations for LLM Theorem Understanding. ACL 2025 (arXiv 2502.19400).", "https://arxiv.org/abs/2502.19400"),
    "mover": ("Ma and Agrawala. MoVer: Motion Verification for Motion Graphics Animations. ACM Transactions on Graphics, SIGGRAPH 2025 (arXiv 2502.13372).", "https://arxiv.org/abs/2502.13372"),
    "design_video": ("Deganutti, Cao, Seol, Hirsch and Mehta. Evaluating Design Video Generation: Metrics for Compositional Fidelity. ICML 2026 Workshop on Human-AI Co-Creativity (arXiv 2605.16223).", "https://arxiv.org/abs/2605.16223"),
    "code2video": ("Chen, Lin and Shou. Code2Video: A Code-centric Paradigm for Educational Video Generation. arXiv 2510.01174 (2025).", "https://arxiv.org/abs/2510.01174"),
    "skillsbench": ("Li et al. SkillsBench: Benchmarking How Well Agent Skills Work Across Diverse Tasks. arXiv 2602.12670 (v4, 2026).", "https://arxiv.org/abs/2602.12670"),
    "ragmcp": ("Gan and Sun. RAG-MCP: Mitigating Prompt Bloat in LLM Tool Selection via Retrieval-Augmented Generation. arXiv 2505.03275 (2025).", "https://arxiv.org/abs/2505.03275"),
    "wild": ("Liu, Wang, Feng, Zhang, Xu, Deng, Li and Zhang. Agent Skills in the Wild: An Empirical Study of Security Vulnerabilities at Scale. arXiv 2601.10338 (2026).", "https://arxiv.org/abs/2601.10338"),
}


def pair(en: str, zh: str, key: str = "item") -> dict:
    return {key: en, f"{key}_zh": zh}


def route(name, how, gain, cost, kinds=None) -> dict:
    r = {"name": name[0], "name_zh": name[1], "how": how[0], "how_zh": how[1], "gain": gain[0], "gain_zh": gain[1], "cost": cost[0], "cost_zh": cost[1]}
    return {**r, "kinds": kinds} if kinds else r


def author(list_name: str, list_zh: str) -> dict:
    return {"name": "Jason Zhu", "about": "/about/", "x": "https://x.com/GoSailGlobal", "github": "https://github.com/zhuyansen",
            "role": f"Builds and maintains Agent Skills Hub{list_name}; tracking open-source agent skills since 2024; author of the Blue Book of Agent Skills 2026.",
            "role_zh": f"Agent Skills Hub{list_zh}的作者与维护者；2024 年起追踪开源 agent skill；《Agent Skills 蓝皮书 2026》作者。", "reviewed": "2026-10-11"}


def block(h2, thesis, h3_routes, columns, routes, gap, h3_next, next_stop, h3_questions, questions, floor, findings, did, not_done, sources, who) -> dict:
    return {"h2": h2[0], "h2_zh": h2[1], "thesis": thesis[0], "thesis_zh": thesis[1], "h3_routes": list(h3_routes), "columns": [list(c) for c in columns],
            "routes": routes, "gap": gap[0], "gap_zh": gap[1], "h3_next": list(h3_next),
            "next_stop": [{"who": w[0], "who_zh": w[1], "pick": p[0], "pick_zh": p[1]} for w, p in next_stop],
            "h3_questions": list(h3_questions), "questions": [pair(*q, key="q") for q in questions], "floor_activity": list(floor),
            "h3_findings": ["What the research found", "研究发现了什么"], "findings": [pair(*f) for f in findings],
            "did": [pair(*d) for d in did], "not_done": [pair(*n) for n in [not_done, *STANDARD]],
            "sources": [{"label": SRC[s][0], "url": SRC[s][1]} for s in sources], "author": who}


KIND_COLS = (("Kind", "类型"), ("How it works", "怎么做"), ("What you gain", "强项"), ("What to check", "要留意什么"))
CURATION = ("Found the candidates on GitHub (every star count) and in our catalog, then had Jev, TypeSafe's decision model, read each README: is it on topic, is it software an agent can use.",
            "在 GitHub（不限星数）和我们的目录里找候选，再让 TypeSafe 的决策模型 Jev 逐个读 README：是否切题、是不是 agent 能用的软件。")
DAILY = ("Security-graded every repo against 11 red-flag categories, and re-check the list every day: new repos are reviewed, deleted and renamed ones removed.",
         "按 11 类风险给每个仓库做安全评级，并且每天复查：新仓库进审核，删除和改名的移出。")

VIDEO = block(
    ("How we judge Remotion skills and Claude Code video tools: does a file come out, and can you read it",
     "我们怎么评 Remotion skill 和 Claude Code 视频工具：能不能出片，片子上的字读不读得到"),
    ("A video skill for a coding agent does not generate pixels. It has the agent write a program (a Remotion composition, an HTML page, a Lottie file, an ffmpeg command) and render it. That is why it can put exact words on screen at an exact second, which pixel video models still cannot do reliably, and it is also where it fails: the program has to run. The research on code-made video measures the same few things. In TheoremExplainAgent (ACL 2025), the best agent rendered 93.8% of its explainer videos, and most of the videos that rendered still had minor layout problems such as overlapping elements. In MoVer (SIGGRAPH 2025), 58.8% of generated motion graphics matched the request on the first try and 93.6% after up to 50 rounds of automatic correction. So we judge a video skill on what can be checked from the file: it renders, it is the length and size you asked for, every line of your copy can be read, and the picture moves. Whether it looks good is for your eyes; we show the video.",
     "给编码 agent 用的视频 skill 并不生成像素。它让 agent 写一段程序（Remotion 组件、HTML 页面、Lottie 文件、ffmpeg 命令）再渲染出来。所以它能在指定的秒数把指定的字准确放到画面上，这一点像素视频模型至今做不稳；它出问题的地方也在这里：程序得跑得通。研究代码生成视频的论文量的也是这几件事。TheoremExplainAgent（ACL 2025）里，最好的 agent 有 93.8% 的讲解视频能渲染出来，而渲染成功的视频大多仍有元素重叠之类的版面小问题。MoVer（SIGGRAPH 2025）里，生成的动效一次就符合要求的占 58.8%，自动修正最多 50 轮后升到 93.6%。所以我们按能从文件里核对的东西来评视频 skill：能渲染、时长和尺寸符合要求、每一句文案都读得到、画面在动。好不好看交给你的眼睛，我们把成片放出来。"),
    ("Eight kinds of video skill, one pipeline", "八类视频 skill，同一条流水线"), KIND_COLS,
    [route(("Frameworks and toolkits", "框架与工具包"), ("Teach the agent a renderer: Remotion, HyperFrames (HTML to video), or a full production toolkit.", "教 agent 用一种渲染器：Remotion、HyperFrames（HTML 转视频），或一整套制作工具。"),
           ("General: any kind of video the renderer can draw.", "通用：渲染器画得出的都能做。"), ("The agent still has to design the video; expect a first render that needs another pass.", "视频还得 agent 自己设计；第一次渲染多半要再改一轮。"), ["general"]),
     route(("Promos and product demos", "宣传片与产品演示"), ("A fixed recipe for launch videos: scenes, pacing, sometimes music and sound made in code.", "产品发布视频的固定配方：分镜、节奏，有的还用代码做配乐和音效。"),
           ("Fast to a finished promo with a consistent style.", "很快出一条风格统一的宣传片。"), ("The style is the skill's, not yours; check it fits your brand.", "风格是 skill 的，不是你的；先看合不合你的品牌。"), ["promo"]),
     route(("Explainers", "讲解视频"), ("Diagrams, maths and step-by-step animation, often with Manim.", "图示、数学和分步动画，常用 Manim。"),
           ("Clear teaching visuals from a script.", "从脚本直接出清晰的教学画面。"), ("Layout is the weak point in the research: check for overlapping text.", "研究里最弱的一环是版面：留意文字重叠。"), ["explainer"]),
     route(("Motion graphics", "动效"), ("Logo animations, Lottie files, SVG motion, B-roll loops.", "Logo 动画、Lottie 文件、SVG 动效、B-roll 循环。"),
           ("Small reusable pieces for a longer video or a site.", "可复用的小片段，放进长视频或网站。"), ("Timing and direction are what generated motion gets wrong most.", "生成的动效最常错的是时间和方向。"), ["motion"]),
     route(("Editing and shorts", "剪辑与短视频"), ("Work on footage you already have: cut, subtitle, reframe, turn long video into shorts.", "处理你已有的素材：剪、加字幕、改画幅、长视频切短视频。"),
           ("Saves the repetitive hours of editing.", "省掉剪辑里重复的那几个小时。"), ("Needs your footage, and often a speech or vision model with its own key.", "要有你自己的素材，常常还要带密钥的语音或视觉模型。"), ["editing", "shorts"]),
     route(("Stories, animation and music videos", "故事、动画与音乐视频"), ("Storyboards and drawn scenes assembled into a film, some with image or video models.", "分镜和手绘场景拼成短片，有的会调用图像或视频模型。"),
           ("A whole short film from a script.", "从剧本直接出一部短片。"), ("Check whether it needs a paid image or video model.", "先看是否需要付费的图像或视频模型。"), ["story", "music"]),
     route(("Avatars", "数字人"), ("A presenter video through a hosted avatar service.", "通过托管的数字人服务生成主持人视频。"),
           ("A talking presenter without filming.", "不用拍摄就有出镜讲解。"), ("Always needs an account and credits with that service.", "一定需要该服务的账号和额度。"), ["avatar"]),
     route(("Scripts and learning", "脚本与学习"), ("Screenwriting, directing and prompt-writing skills; no rendering.", "编剧、导演和写提示词的 skill；不渲染。"),
           ("Better input for any of the above.", "给上面任何一类提供更好的输入。"), ("Produces text, not a video.", "产出是文字，不是视频。"), ["craft"])],
    ("No peer-reviewed study tests Remotion or HTML-to-video skills themselves. The closest work measures agents writing Manim, SVG and Lottie animation; the one benchmark of HTML and React motion design is a vendor's own. So the checks here borrow those papers' metrics; they are not their findings about these skills.",
     "还没有同行评审的研究直接测 Remotion 或 HTML 转视频的 skill。最接近的工作测的是 agent 写 Manim、SVG 和 Lottie 动画；唯一一个测 HTML 和 React 动效的基准是厂商自己做的。所以这里的检查借用了这些论文的指标，并不是它们对这些 skill 的结论。"),
    ("Pick by what you are making", "按你要做什么来选"),
    [(("A launch or feature promo", "发布或功能宣传片"), ("A promo skill; or a framework if you have your own design", "宣传片类 skill；已有自己的设计就用框架")),
     (("A tutorial or explainer", "教程或讲解"), ("An explainer skill, and check the layout of every scene", "讲解类 skill，并逐个场景检查版面")),
     (("You already have footage", "已经有素材"), ("An editing skill", "剪辑类 skill")),
     (("A logo sting or a loop for a site", "Logo 片头或网站用的循环动画"), ("A motion-graphics skill", "动效类 skill"))],
    ("Four checks on every video", "每条视频查四件事"),
    [("Does it render to a playable file without you fixing the code?", "不用你改代码，能不能渲染出可播放的文件？"),
     ("Is it the length, size and frame rate you asked for?", "时长、尺寸和帧率是不是你要的？"),
     ("Can every line of your copy be read on screen, with nothing added?", "你给的每一句文案都能在画面上读到吗，有没有多加内容？"),
     ("Does the picture actually move, or is it slides with a fade?", "画面是真的在动，还是幻灯片加淡入淡出？")],
    ("while making or rendering video", "制作和渲染视频时的行为"),
    [("Rendering is the first hurdle, and it is mostly cleared: the best agent rendered 93.8% of its videos; the failures were mostly calls to functions that do not exist (TheoremExplainAgent, ACL 2025).",
      "渲染是第一道坎，而且多数能过：最好的 agent 有 93.8% 的视频渲染成功；失败大多是调用了并不存在的函数（TheoremExplainAgent，ACL 2025）。"),
     ("The first render is often not the right one. 58.8% of generated motion graphics met the request with no iteration, 93.6% after automatic checking and up to 50 corrections (MoVer, SIGGRAPH 2025).",
      "第一次渲染往往不对。生成的动效不迭代就符合要求的占 58.8%，经过自动检查和最多 50 次修正后是 93.6%（MoVer，SIGGRAPH 2025）。"),
     ("Layout is where code-made video goes wrong: most videos that rendered still had minor layout issues (TheoremExplainAgent), which is why we read the text off the frames instead of trusting the code.",
      "代码生成的视频错在版面：渲染成功的视频大多仍有版面小问题（TheoremExplainAgent），所以我们从画面帧上读字，不只看代码。"),
     ("Text on screen can be checked from the file: sample frames, read the text, compare with what was asked (Deganutti et al., ICML 2026 workshop). Duration and motion are measured the same way, from the file.",
      "画面上的字可以从文件核对：抽帧、读字、和要求的文案对比（Deganutti 等，ICML 2026 workshop）。时长和运动量也一样，从文件里量。")],
    [CURATION, ("Sorted every entry into one of ten kinds, so you can filter.", "把每个条目归入十类之一，可以筛选。"), DAILY],
    ("We have not yet published an end-to-end run of these skills. The test is running: one 15-second promo brief with fixed on-screen copy, the same for every skill and for Claude Code with no skill, scored on the four checks above.",
     "这些 skill 的端到端实跑还没有发布。实测正在进行：同一条 15 秒宣传片的需求、固定的字幕文案，每个 skill 和不装 skill 的 Claude Code 各做一遍，按上面四项检查评分。"),
    ["theorem", "mover", "design_video", "code2video", "skillsbench"], author(" and the awesome-claude-video-skills list", " 和 awesome-claude-video-skills 合集"))

CODEX = block(
    ("How we judge Codex skills: will Codex reach for it, and what does it cost to keep installed",
     "我们怎么评 Codex skill：Codex 会不会用它，一直装着要付出什么"),
    ("A Codex skill is a folder with a SKILL.md: a name, a description, and instructions Codex reads only when the description matches what you asked. The same format works in Claude Code. So two things decide whether a skill is worth installing. The first is whether the agent reaches for it at the right moment, which depends on its description and on what else is installed beside it. When every tool was put in front of a model at once, it chose the right one 13.62% of the time; retrieving only the relevant ones raised that to 43.13% and cut prompt tokens by more than half (RAG-MCP). The second is whether it helps once loaded: in SkillsBench (87 tasks, run with and without skills) curated skills raised the pass rate from 33.9% to 50.5%, and focused skills of at most three modules beat large bundles. So we judge a Codex skill by its description, its size, and what it needs to run, and we test triggering directly.",
     "Codex skill 是一个带 SKILL.md 的文件夹：一个名字、一段描述，以及只有当描述和你的请求对得上时 Codex 才会去读的说明。同样的格式在 Claude Code 里也能用。所以一个 skill 值不值得装，取决于两件事。第一是 agent 会不会在该用的时候用它，这取决于它的描述，也取决于旁边还装了什么。把所有工具一次性摆给模型时，它选对的概率只有 13.62%；只检索相关的几个，选对率升到 43.13%，提示词 token 减少一半以上（RAG-MCP）。第二是加载之后有没有用：SkillsBench（87 个任务，装和不装 skill 各跑一遍）里，精选 skill 把通过率从 33.9% 提到 50.5%，不超过三个模块的小 skill 胜过大而全的合集。所以我们看 Codex skill 的描述、体量和运行条件，并且直接实测它会不会被触发。"),
    ("Six kinds of Codex skill and tooling", "六类 Codex skill 与周边"), KIND_COLS,
    [route(("Single skills", "单个 Skill"), ("One job in one folder: a deck, an illustration style, a code audit.", "一个文件夹做一件事：做 PPT、一种配图风格、一次代码审计。"),
           ("Small, easy to read before you install, easy to remove.", "体量小，装之前读得完，不用了好删。"), ("Many need an image model or a desktop app; read what it calls.", "不少要用图像模型或桌面应用；先看它会调用什么。"), ["skill"]),
     route(("Collections", "合集"), ("Dozens to hundreds of skills in one repository.", "一个仓库里几十到几百个 skill。"),
           ("One install covers many jobs.", "装一次覆盖很多场景。"), ("Every installed skill's description is loaded each session; install the ones you use.", "每个已装 skill 的描述每次会话都会加载；只装你用的。"), ["collection"]),
     route(("Plugins and MCP servers", "插件与 MCP"), ("Give Codex new tools: a browser, an API, another model.", "给 Codex 新工具：浏览器、API、别的模型。"),
           ("Abilities Codex does not have by itself.", "Codex 自己没有的能力。"), ("Runs code with your permissions; check the grade and what it connects to.", "以你的权限运行代码；先看评级和它连接什么。"), ["plugin"]),
     route(("Workflows and subagents", "工作流与子 Agent"), ("A staged way of working: plan, build, review, often with several agents.", "分阶段的工作方式：计划、实现、审查，常由多个 agent 配合。"),
           ("Structure for long tasks.", "给长任务搭好结构。"), ("Heavier context and more tokens per task.", "上下文更重，每个任务花的 token 更多。"), ["workflow"]),
     route(("Bridges to other agents", "跨 Agent 桥接"), ("Let Codex call Claude Code, Gemini or others, or the reverse.", "让 Codex 调用 Claude Code、Gemini 等，或者反过来。"),
           ("A second opinion from another model.", "来自另一个模型的第二意见。"), ("Two subscriptions or keys, and two bills.", "要两份订阅或密钥，也是两份账单。"), ["bridge"]),
     route(("Tooling", "周边工具"), ("Maintenance, hygiene and setup for Codex itself.", "Codex 自身的维护、清理和配置。"),
           ("Keeps a long-lived setup fast.", "让用了很久的环境保持顺畅。"), ("Touches your Codex state; prefer ones that back up first.", "会动你的 Codex 状态；优先选先备份的。"), ["tooling"])],
    ("The research measures tools and skills in general, mostly on other agents. No published study tests Codex skills specifically, so the questions below are our reading of that research.",
     "这些研究测的是一般意义上的工具和 skill，多数在别的 agent 上。还没有公开研究专门测 Codex skill，所以下面的问题是我们对研究的解读。"),
    ("Pick by how much you want installed", "按你想装多少来选"),
    [(("One job you do often", "一件经常做的事"), ("A single skill for it", "对应的单个 skill")),
     (("Starting from nothing", "从零开始"), ("A few single skills, not a whole collection", "先装几个单个 skill，不要整包合集")),
     (("Long, multi-step work", "多步骤的长任务"), ("A workflow, and accept the token cost", "一套工作流，并接受 token 开销")),
     (("You also use Claude Code", "同时在用 Claude Code"), ("Skills in the shared SKILL.md format; they load in both", "用通用 SKILL.md 格式的 skill，两边都能加载"))],
    ("Four questions we ask of every Codex skill", "每个 Codex skill 我们问四个问题"),
    [("Trigger: does its description say when to use it, in words a user would type?", "触发：它的描述有没有用用户会打出来的话说清楚什么时候用它？"),
     ("Size: is it one focused job, or a bundle?", "体量：是专注做一件事，还是一个大包？"),
     ("Needs: which models, keys or apps must be present for it to run?", "条件：要有哪些模型、密钥或应用它才能跑？"),
     ("Scripts: does it ship code that runs on your machine, and have you read it?", "脚本：它带不带会在你机器上运行的代码，你读过吗？")],
    ("while running a Codex skill", "运行 Codex skill 时的行为"),
    [("More installed is not more capable. With every tool listed, a model chose the right one 13.62% of the time; with retrieval, 43.13%, using less than half the prompt tokens (RAG-MCP, a preprint).",
      "装得多不等于能力强。全部列出时模型选对工具的概率是 13.62%；改用检索后是 43.13%，提示词 token 不到原来的一半（RAG-MCP，预印本）。"),
     ("Skills help when they are curated and small: +16.6 points in pass rate, and skills of at most three modules beat larger bundles (SkillsBench).",
      "精选的小 skill 才有帮助：通过率提高 16.6 个百分点，不超过三个模块的 skill 胜过更大的合集（SkillsBench）。"),
     ("Skills that ship scripts carry more risk: in a sample of skills from public registries, 26.1% had at least one vulnerability, and those with scripts were 2.12 times as likely to (Agent Skills in the Wild, a preprint).",
      "带脚本的 skill 风险更高：一份来自公开市场的样本里，26.1% 的 skill 至少有一个漏洞，带脚本的出问题的概率是不带脚本的 2.12 倍（Agent Skills in the Wild，预印本）。")],
    [CURATION, ("Sorted every entry into one of six kinds, so you can filter.", "把每个条目归入六类之一，可以筛选。"), DAILY],
    ("We have not yet published an end-to-end run of these skills. The test is running: 12 skills installed together, three requests each that should reach the skill and six that should reach none, on Codex and on Claude Code, then again with 100 and 500 other skills installed beside them.",
     "这些 skill 的端到端实跑还没有发布。实测正在进行：12 个 skill 一起装上，每个 3 条应该触发它的请求、另加 6 条不该触发任何 skill 的请求，在 Codex 和 Claude Code 上各跑一遍；然后在旁边再装 100 个和 500 个别的 skill 重跑。"),
    ["ragmcp", "skillsbench", "wild"], author("", ""))

CCS = block(
    ("How we judge Claude Code skills collections: what you get, and what it costs to install all of it",
     "我们怎么评 Claude Code skills 合集：装上得到什么，整包安装要付出什么"),
    (f"Most people meet Claude Code skills through a collection: one repository, hundreds of skills, one install command. The research says to be careful with that. In SkillsBench (87 tasks, run with and without skills) curated skills raised the pass rate from 33.9% to 50.5%, and focused skills of at most three modules beat large bundles. And an agent picks worse when more is put in front of it: with every tool listed, a model chose the right one 13.62% of the time, against 43.13% when only the relevant ones were retrieved (RAG-MCP). Claude Code lists installed skills in every session, but only up to a budget. We measured it: with 12 skills installed a session started at 17,781 tokens, with 112 at 24,499, and with 512 at 25,289. Past roughly a hundred skills the list stops growing because descriptions are dropped: with 512 installed, Claude Code reported about 47 skills still shown with a description and the rest by name alone. So a big collection does not cost you tens of thousands of tokens; it costs your skills their descriptions. We judge a collection by what is inside it, whether its skills follow the format, and how many of them would be left with a name only.",
     f"多数人是通过合集接触 Claude Code skills 的：一个仓库、几百个 skill、一条安装命令。研究提醒要小心。SkillsBench（87 个任务，装和不装 skill 各跑一遍）里，精选 skill 把通过率从 33.9% 提到 50.5%，不超过三个模块的小 skill 胜过大而全的合集。摆在 agent 面前的东西越多，它选得越差：全部列出时模型选对工具的概率是 13.62%，只检索相关的几个时是 43.13%（RAG-MCP）。Claude Code 每次会话都会列出已装的 skill，但有预算上限。我们实测过：装 12 个 skill 时会话起始是 17,781 个 token，装 112 个是 24,499，装 512 个是 25,289。超过大约一百个之后列表不再变长，因为描述被丢掉了：装 512 个时，Claude Code 自己报告只有约 47 个 skill 还带描述，其余只剩名字。所以大合集的代价不是几万 token，而是你的 skill 失去了描述。所以我们看一个合集里面有什么、它的 skill 是否符合格式、装上之后有多少个只剩名字。"),
    ("Four kinds of repository on this page", "这一页上的四类仓库"), KIND_COLS,
    [route(("Link lists", "链接清单"), ("A README of links to skills elsewhere; nothing to install.", "一份指向别处 skill 的链接清单；本身没有可安装的东西。"),
           ("Discovery, and someone else's judgement of what is good.", "发现，以及别人对好坏的判断。"), ("Links go stale; check when it was last updated.", "链接会过期；看看最近什么时候更新过。")),
     route(("Skill collections", "Skill 合集"), ("Tens to hundreds of skills, often with commands and agents, installed together or picked one by one.", "几十到几百个 skill，常附带命令和子 agent，可以整包装也可以挑着装。"),
           ("Breadth: one place for many jobs.", "广度：一个地方覆盖很多场景。"), ("Install hundreds and most are listed by name only; pick, do not install all.", "装上几百个，大多数只按名字列出；挑着装，别整包装。")),
     route(("Official plugins", "官方插件"), ("Anthropic's own plugin directory.", "Anthropic 自己的插件目录。"),
           ("Maintained by the vendor, in the current format.", "由官方维护，格式跟得上。"), ("Smaller than community collections.", "比社区合集小。")),
     route(("Tools around skills", "围绕 skill 的工具"), ("Memory, a status line, a desktop app: they extend Claude Code, they are not skills.", "记忆、状态栏、桌面应用：它们扩展 Claude Code，本身不是 skill。"),
           ("Abilities a skill cannot add.", "skill 加不了的能力。"), ("Hooks and background processes run all the time; check the grade.", "hooks 和后台进程一直在跑；先看评级。"))],
    ("The studies measure skills and tool selection in general, not these collections. The session sizes are our own measurement in Claude Code 2.1.292 on 2026-10-11; the count of skills that kept a description is Claude Code's own report of what it could see, counted by the model, so treat it as approximate.",
     "这些研究测的是一般意义上的 skill 和工具选择，不是这些合集。会话大小是我们 2026-10-11 在 Claude Code 里实测的；「还带描述的 skill 数」是 Claude Code 自己报告它看得到什么，由模型数出来的，只能当近似值。"),
    ("Pick by how you install", "按你的安装方式来选"),
    [(("New to skills", "刚接触 skill"), ("The official plugin directory, a few skills at a time", "官方插件目录，一次装几个")),
     (("You want one domain covered", "想覆盖一个领域"), ("A small, single-topic collection", "小而专的单主题合集")),
     (("You want a big collection", "想用大合集"), ("Install by name from it; never the whole repository", "从里面按名字挑着装；不要整仓库装")),
     (("Looking for ideas", "找灵感"), ("A link list, then read each skill before installing", "先看链接清单，装之前把每个 skill 读一遍"))],
    ("Four questions we ask of every collection", "每个合集我们问四个问题"),
    [("Contents: how many skills are really in it, and how many are copies of each other?", "内容：里面到底有多少个 skill，有多少是互相重复的副本？"),
     ("Format: do the skills have a valid name and description, so an agent can find them?", "格式：skill 有没有合规的名字和描述，agent 才找得到？"),
     ("Crowding: if you install all of it, how many skills are left with a name and no description?", "拥挤：整包装上后，有多少个 skill 只剩名字、没有描述？"),
     ("Scripts: how many of its skills ship code that runs on your machine?", "脚本：有多少个 skill 带着会在你机器上运行的代码？")],
    ("while installing or loading skills", "安装和加载 skill 时的行为"),
    [("Curated beats complete. Curated skills raised the average pass rate by 16.6 points, and skills of at most three modules beat larger bundles (SkillsBench).",
      "精选胜过求全。精选 skill 让平均通过率提高 16.6 个百分点，不超过三个模块的 skill 胜过更大的合集（SkillsBench）。"),
     ("Listing everything costs accuracy: 13.62% correct tool selection with all tools listed, 43.13% with retrieval (RAG-MCP, a preprint).",
      "全部列出会损失准确率：全部列出时工具选对率 13.62%，检索后 43.13%（RAG-MCP，预印本）。"),
     ("Scripts raise the risk: 26.1% of sampled skills had at least one vulnerability, and skills with scripts were 2.12 times as likely to (Agent Skills in the Wild, a preprint).",
      "脚本会提高风险：抽样的 skill 里 26.1% 至少有一个漏洞，带脚本的出问题的概率是不带脚本的 2.12 倍（Agent Skills in the Wild，预印本）。")],
    [("Counted every SKILL.md in each repository on this page and checked it against the Agent Skills format: a name of at most 64 lowercase letters, digits and hyphens, and a description of 1 to 1,024 characters. Nothing was executed.",
      "数了本页每个仓库里的每一个 SKILL.md，并按 Agent Skills 格式检查：名字不超过 64 个小写字母、数字和连字符，描述 1 到 1,024 个字符。没有执行任何东西。"),
     DAILY],
    ("We counted files and measured session size; we did not run the skills, so this says nothing about whether a given skill is any good. With 500 other skills installed, Claude Code still opened the right one of our 12 test skills for 35 of 36 requests, but those 12 have descriptive names; a skill with a vague name and no visible description may fare worse, and we did not test that.",
     "我们数了文件、量了会话大小，但没有运行这些 skill，所以这说明不了某个 skill 好不好用。旁边再装 500 个 skill 时，Claude Code 对 36 条请求里的 35 条仍然打开了我们 12 个测试 skill 中正确的那个，但这 12 个的名字本身就说明了用途；名字含糊又看不到描述的 skill 可能会更差，这一点我们没有测。"),
    ["skillsbench", "ragmcp", "wild"], author("", ""))


def main() -> None:
    pages = json.loads(KEYWORDS.read_text())
    for slug, m in (("claude-video-skills", VIDEO), ("codex-skills", CODEX), ("claude-code-skills", CCS)):
        next(p for p in pages if p["slug"] == slug)["method"] = m
    KEYWORDS.write_text(json.dumps(pages, indent=1, ensure_ascii=False) + "\n")
    print("method blocks written")


if __name__ == "__main__":
    main()
