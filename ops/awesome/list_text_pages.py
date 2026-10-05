"""Text of the GitHub lists for the pages upgraded on 2026-10-03 (page_profiles.PAGES).
Each list states its own rule 1 (what the page is about) and shares rules 2-4; keys not
set here come from PPT_TEXT in build_video_list.py."""
from __future__ import annotations

RULES_EN = ["It is software someone can install or run, not a list of links or a placeholder.",
            "It has a README. Without one it cannot be graded.",
            "At 50 stars or more it is listed on topic alone. Under 50 it must also clear a README quality bar "
            "(shows it working, one-command start, a concrete outcome, complete docs), and have 5 stars."]
RULES_ZH = ["它是能安装或运行的软件,不是链接合集或空仓库。",
            "它有 README。没有 README 就没法评级。",
            "50 星及以上只看是否切题;50 星以下还要过 README 质量线(展示效果、一条命令上手、说清产出、文档完整),并且至少 5 星。"]
SIBLINGS = ("[zhuyansen/awesome-claude-video-skills](https://github.com/zhuyansen/awesome-claude-video-skills), "
            "[zhuyansen/awesome-codex-ppt-skills](https://github.com/zhuyansen/awesome-codex-ppt-skills)")


def _text(title: str, pitch: tuple[str, str], rule: tuple[str, str], album: tuple[str, str]) -> dict:
    return {
        "en": {"title": title, "pitch": pitch[0] + " {n} repos, each one read and security-graded by "
                                                   "[Agent Skills Hub]({site}{utm}).",
               "rules": [rule[0], *RULES_EN], "album": album[0],
               "related": [f"{SIBLINGS} — lists built the same way."]},
        "zh": {"title": title, "pitch": pitch[1] + "共 {n} 个仓库,每个都由 [Agent Skills Hub]({site}{utm}) 读过 README 并做了安全评级。",
               "rules": [rule[1], *RULES_ZH], "album": album[1],
               "related": [f"{SIBLINGS} —— 同样做法的合集。"]},
    }


PAGE_LISTS = {
    "skill-management-tools": {
        "repo": "zhuyansen/awesome-agent-skills-managers",
        "text": _text("Awesome Agent Skills Managers",
                      ("Open-source tools to **find, install, sync and organize agent skills** across Claude Code, Codex, "
                       "Cursor and other coding agents: CLI installers, desktop apps, registries, team tools.",
                       "**查找、安装、同步、整理 agent skill** 的开源工具,覆盖 Claude Code、Codex、Cursor 等编程 agent:"
                       "命令行安装器、桌面应用、市场与目录、团队管理。"),
                      ("It manages agent skills or plugins: finds, installs, syncs, updates or shares them. One skill, "
                       "or a collection of skills, is not a manager.",
                       "它管理 agent 的 skill 或插件:查找、安装、同步、更新或分享。单个 skill 或 skill 合集不算管理工具。"),
                      ("What these managers look like", "这些管理工具长什么样")),
        "blurb": {
            "general": ("Managers of whole agent setups: skills, MCP servers, prompts and settings.", "管理整套 agent 配置:skill、MCP、提示词和设置。"),
            "cli": ("Add, remove and update skills from a terminal.", "在终端里添加、删除、更新 skill。"),
            "sync": ("One skill folder shared by several agents or machines.", "一份 skill 在多个 agent、多台机器间同步。"),
            "app": ("Desktop, web and TUI apps to browse and manage skills.", "桌面、网页和终端界面的 skill 管理应用。"),
            "registry": ("Registries, marketplaces and search engines for skills.", "skill 的市场、目录和搜索引擎。"),
            "team": ("Sharing, versioning and permissions across a team.", "团队内的共享、版本和权限管理。"),
        },
    },
    "telegram-bot": {
        "repo": "zhuyansen/awesome-ai-telegram-bots",
        "text": _text("Awesome AI Telegram Bots",
                      ("Open-source **Telegram bots built on AI**: GPT, Claude and local-model assistants, remote control "
                       "for Claude Code and Codex, bot frameworks and MCP servers, utility, learning and business bots.",
                       "**基于 AI 的开源 Telegram 机器人**:GPT、Claude 和本地模型助手,远程操控 Claude Code 和 Codex,"
                       "机器人框架与 MCP,工具、学习和商业机器人。"),
                      ("It is a Telegram bot, or a tool for building or running one; Telegram is its main interface.",
                       "它是 Telegram 机器人,或用来搭建、运行机器人的工具;Telegram 是它的主要界面。"),
                      ("What these bots look like", "这些机器人长什么样")),
        "blurb": {
            "assistant": ("AI chat assistants in Telegram: GPT, Claude, Gemini, local models.", "在 Telegram 里聊天的 AI 助手:GPT、Claude、Gemini、本地模型。"),
            "remote": ("Control Claude Code, Codex or a computer from your phone.", "用手机远程操控 Claude Code、Codex 或电脑。"),
            "framework": ("Libraries, templates and MCP servers for building bots.", "搭建机器人的库、模板和 MCP 服务。"),
            "utility": ("Downloads, files, translation, group management.", "下载、文件、翻译、群管理。"),
            "fun": ("Games, quizzes, language practice and companions.", "游戏、答题、语言练习和陪伴。"),
            "business": ("Support, sales, payments, trading and monitoring.", "客服、销售、支付、交易和监控。"),
        },
    },
    "ai-design": {
        "repo": "zhuyansen/awesome-claude-design-skills",
        "text": _text("Awesome Claude Design Skills",
                      ("Open-source **design skills and tools for Claude Code, Codex and other coding agents**: better UI "
                       "and frontend style, design systems, Figma and design-tool MCP, design to code, graphics and posters.",
                       "给 **Claude Code、Codex 等编程 agent 用的开源设计 skill 和工具**:UI 与前端美化、设计系统、"
                       "Figma 与设计工具 MCP、设计稿转代码、海报与品牌图。"),
                      ("It helps an agent produce visual design: UI and frontend style, design systems, graphics. A "
                       "component library with no AI in it, or a general image generator, does not count.",
                       "它帮 agent 做视觉设计:UI 与前端风格、设计系统、图形。没有 AI 的组件库、通用图片生成器不算。"),
                      ("What these skills make", "这些 skill 能做出什么")),
        "blurb": {
            "ui": ("Rules and styles that make generated interfaces look designed.", "让 agent 生成的界面更有设计感的规则和风格。"),
            "system": ("Tokens, themes and component specs an agent follows.", "agent 遵循的设计令牌、主题和组件规范。"),
            "tool_mcp": ("Figma, Penpot, Canva and other design tools, driven by an agent.", "让 agent 操作 Figma、Penpot、Canva 等设计工具。"),
            "to_code": ("Designs, screenshots and mockups turned into frontend code.", "把设计稿、截图、线框图转成前端代码。"),
            "graphics": ("Posters, social images, logos and brand assets.", "海报、社交配图、Logo 和品牌素材。"),
            "review": ("Design critique: accessibility, consistency, AI-looking output.", "设计审查:无障碍、一致性、AI 味。"),
        },
    },
    "knowledge-base": {
        "repo": "zhuyansen/awesome-llm-wiki",
        "text": _text("Awesome LLM Wiki",
                      ("Open-source tools where **an LLM or agent builds and maintains a knowledge base**: LLM wikis of "
                       "linked markdown pages, RAG knowledge-base platforms, MCP servers and skills, docs Q&A, knowledge "
                       "graphs, personal knowledge.",
                       "**由 LLM 或 agent 搭建和维护知识库**的开源工具:Markdown 互链的 LLM Wiki、RAG 知识库平台、"
                       "MCP 与 skill、文档问答、知识图谱、个人知识库。"),
                      ("The knowledge base is the product: a wiki an LLM maintains, a RAG knowledge base, or documents "
                       "an agent answers from. A general chatbot or a bare vector database does not count.",
                       "知识库本身就是产品:LLM 维护的 wiki、RAG 知识库,或 agent 据以回答的文档。通用聊天机器人、单纯的向量数据库不算。"),
                      ("What these knowledge bases look like", "这些知识库长什么样")),
        "blurb": {
            "llm_wiki": ("An agent writes and keeps a wiki of linked markdown pages.", "由 agent 撰写并维护的 Markdown 互链 wiki。"),
            "rag_platform": ("RAG knowledge-base platforms with their own interface.", "自带界面的 RAG 知识库平台。"),
            "mcp": ("MCP servers and skills that let an agent search a knowledge base.", "让 agent 检索知识库的 MCP 服务和 skill。"),
            "docs_qa": ("Answers from product docs, codebases, papers or PDFs.", "基于产品文档、代码库、论文或 PDF 回答问题。"),
            "graph": ("Knowledge as a graph of entities and relations.", "以实体和关系组织知识的图谱。"),
            "personal": ("Notes, bookmarks and a second brain kept by AI.", "由 AI 维护的笔记、收藏和第二大脑。"),
        },
    },
    "claude-code-hooks": {
        "repo": "zhuyansen/awesome-claude-code-hooks",
        "text": _text("Awesome Claude Code Hooks",
                      ("Open-source **Claude Code hooks, subagents and statuslines**: hook guards and formatters, "
                       "specialist agent collections, usage and context status bars, and the tools that manage them.",
                       "开源的 **Claude Code hooks、subagents 和 statusline**:Hook 守卫与格式化、专家 Agent 合集、"
                       "用量与上下文状态栏,以及管理它们的工具。"),
                      ("It provides or manages Claude Code hooks, subagents or a statusline. A general Claude Code "
                       "plugin or skill without them does not count.",
                       "它提供或管理 Claude Code 的 hooks、subagents 或 statusline。不涉及这三样的一般插件、skill 不算。"),
                      ("What these projects look like", "这些项目长什么样")),
        "blurb": {
            "hooks": ("Scripts that run on tool use, prompts or stop: guards, formatters, notifications.", "在工具调用、提问、结束等事件上运行的脚本:守卫、格式化、通知。"),
            "subagents": ("Specialist agents with their own prompt and tools, and their orchestration.", "带独立提示词和工具的专家 Agent,以及编排方式。"),
            "statusline": ("What the status bar shows: usage, cost, context, git, model.", "状态栏显示的内容:用量、花费、上下文、git、模型。"),
            "collection": ("Large bundles of hooks, agents, commands and settings.", "打包了大量 hooks、agents、命令和配置的合集。"),
            "tooling": ("Create, install, test and manage hooks, subagents and statuslines.", "创建、安装、测试和管理 hooks、subagents、statusline 的工具。"),
        },
    },
    "obsidian-second-brain": {
        "repo": "zhuyansen/awesome-obsidian-ai-skills",
        "text": _text("Awesome Obsidian AI Skills",
                      ("Open-source **Obsidian skills, MCP servers and AI plugins** that let Claude Code, Codex and other "
                       "agents read, write and organize your vault, plus second-brain workflows an agent maintains.",
                       "让 Claude Code、Codex 等 agent **读写和整理 Obsidian 库**的开源 skill、MCP 服务和 AI 插件,"
                       "以及由 agent 维护的第二大脑工作流。"),
                      ("It connects AI agents or LLMs with Obsidian; Obsidian is central. A general note app, an LLM wiki "
                       "not built on Obsidian, or a second-brain app of its own does not count.",
                       "它把 AI agent 或大模型和 Obsidian 连起来,Obsidian 是核心。通用笔记应用、不基于 Obsidian 的 LLM Wiki、"
                       "自成一体的第二大脑应用不算。"),
                      ("What these projects look like", "这些项目长什么样")),
        "blurb": {
            "skill": ("Skills that teach an agent to work in your vault.", "教 agent 在你的 Obsidian 库里干活的 skill。"),
            "mcp": ("MCP servers and bridges that give an assistant your vault.", "让 AI 助手访问 Obsidian 库的 MCP 服务和桥接。"),
            "plugin": ("Obsidian plugins with an LLM or agent inside.", "把大模型或 agent 装进 Obsidian 的插件。"),
            "second_brain": ("Second-brain and PKM systems on Obsidian that an agent keeps.", "基于 Obsidian、由 agent 维护的第二大脑与知识管理体系。"),
            "sync": ("Import, capture, publish and sync with AI.", "借助 AI 导入、收集、发布和同步。"),
        },
    },
    "anti-slop": {
        "repo": "zhuyansen/awesome-humanizer-skills",
        "text": _text("Awesome Humanizer Skills",
                      ("Open-source **humanizer and anti-slop skills**: make AI-written text, code and UI read like a "
                       "person made it, detect AI tells, and keep agents to a house style. English and Chinese.",
                       "开源的 **去 AI 味 / humanizer skill**:让 AI 写的文字、代码和界面读起来像人做的,检测 AI 腔,"
                       "让 agent 守住写作风格。中英文都有。"),
                      ("It makes AI-made output read as if a person made it, or detects or removes AI patterns in text, "
                       "code or design. A general writing assistant or grammar checker does not count.",
                       "它让 AI 的产出读起来像人做的,或者检测、去除文字、代码、设计里的 AI 痕迹。通用写作助手、语法检查器不算。"),
                      ("What these skills do", "这些 skill 能做什么")),
        "blurb": {
            "writing": ("Rewrite AI prose so it reads human.", "把 AI 写的文章、帖子、邮件改得像人写的。"),
            "detector": ("Find and score AI writing patterns.", "找出并给 AI 写作痕迹打分。"),
            "chinese": ("Take the AI flavour out of Chinese writing.", "专门给中文去 AI 味。"),
            "code": ("Clean AI patterns out of code and comments.", "清理代码和注释里的 AI 痕迹。"),
            "design": ("Steer AI-made UI away from the generic AI look.", "让 AI 做的界面摆脱千篇一律的 AI 感。"),
            "rules": ("Style guides and word lists agents follow.", "agent 遵守的写作规范和禁用词表。"),
        },
    },
    "image-generation": {
        "repo": "zhuyansen/awesome-ai-image-skills",
        "text": _text("Awesome AI Image Skills",
                      ("Open-source **image generation skills and MCP servers** for Claude Code, Codex and other agents: "
                       "GPT Image, Nano Banana and Gemini, Flux and Stable Diffusion, image editing, and design assets.",
                       "给 Claude Code、Codex 等 agent 用的开源 **生图 skill 和 MCP 服务**:GPT Image、Nano Banana 与 Gemini、"
                       "Flux 与 Stable Diffusion、图片编辑和设计素材。"),
                      ("It lets an AI agent or assistant generate or edit images through an image model. A prompt list "
                       "with no tool, a model's own training code, or a general chat app does not count.",
                       "它让 AI agent 或助手通过图像模型生成或编辑图片。没有工具的提示词合集、模型本身的训练代码、通用聊天应用不算。"),
                      ("What these skills make", "这些 skill 能做出什么")),
        "blurb": {
            "mcp": ("MCP servers that give an assistant image tools across models.", "给 AI 助手提供生图能力、可接多个模型的 MCP 服务。"),
            "gpt_image": ("Built on OpenAI's GPT Image and DALL-E.", "基于 OpenAI 的 GPT Image 和 DALL-E。"),
            "nano_banana": ("Built on Google's Nano Banana, Gemini and Imagen.", "基于 Google 的 Nano Banana、Gemini 和 Imagen。"),
            "open_models": ("Flux, Stable Diffusion and ComfyUI, often self-hosted.", "Flux、Stable Diffusion、ComfyUI,多可自托管。"),
            "editing": ("Retouching, background removal, upscaling, inpainting.", "修图、抠图、放大、局部重绘。"),
            "design": ("Icons, illustrations, covers, posters and logos.", "图标、插画、封面、海报和 Logo。"),
        },
    },
}
