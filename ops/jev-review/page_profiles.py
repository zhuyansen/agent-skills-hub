"""Review profiles for the scenario pages upgraded on 2026-10-03.

The 10-03 audit found six pages with search impressions but thin content (10 to 30
cards picked by keywords). They move to the model the video and PPT pages use: every
listed repo is read by Jev, judged on topic and quality, and given a type for the
page's filter. scenario_gate.py reads PAGES through profile() and QUERIES; the steps
are the same (see ops/jev-review/upgrade_page.py for the collection).

Each page names:
  subject   the question that decides whether a repo belongs on the page
  types     one question per type; a repo gets the highest (TYPE_MIN or more)
  labels    the filter chips, in display order
  queries   GitHub searches, run in every star band
  strict    pages that came out over 300 cards (owner's call, 10-03): topic 0.8 instead
            of 0.5, and under 50 stars only the high quality tier
  extra     further topic questions a repo must also pass (Codex: made mainly for Codex)
  words     a repo must contain one of these (name, description or topics) to be a
            candidate at all, and one of `also` when the page has it; Jev decides the rest
"""
import re


def _q(question: str, focus: str = "") -> dict:
    instructions = {"question": question, **({"focus": focus} if focus else {})}
    return {"type": "noul", "instructions": instructions}


IS_SOFTWARE = _q("Is `repo` software someone can install or run: a tool, library, app, plugin, skill, bot or server?",
                 "As opposed to a list of links, notes, a write-up, or an empty or placeholder repository.")
AGENT_DRIVEN = _q("Is `repo` meant to be operated by an AI coding agent such as Claude Code or Codex?",
                  "A skill, a plugin, an MCP server, or a toolkit whose instructions are written for the agent.")

QUALITY = {
    "shows_result": _q("Does `repo.readme` show it working: a screenshot, GIF, demo, sample output or a link to one?"),
    "one_command_start": _q("Can a reader start using `repo` from a single install or run command given in the README?"),
    "specific_outcome": _q("Does `repo.readme` state a concrete result the user gets, rather than general capability claims?"),
    "complete_docs": _q("Is `repo.readme` organized and complete: install, usage and at least one worked example?"),
    "novel_angle": _q("Does `repo` do something visibly different from the many similar projects in its space?"),
    "shareable_output": _q("Is `repo` the kind of project people share: a striking demo, a new capability, a clear win?"),
}


def _labels(*rows: tuple[str, str, str, str]) -> list[dict]:
    return [{"id": i, "icon": icon, "en": en, "zh": zh} for i, icon, en, zh in rows]


PAGES = {
    "skill-management-tools": {
        "subject": _q("Is the main purpose of `repo` to manage agent skills: find, install, sync, update, share or "
                      "organize skills or plugins for Claude Code, Codex or other agents?",
                      "A skill manager, installer, registry, marketplace or sync tool. One skill, or a collection "
                      "of skills, is not a manager."),
        "types": {
            "cli": _q("Is `repo` a command-line installer or package manager for agent skills?",
                      "npx or pip tools that add, remove and update skills from a terminal."),
            "sync": _q("Does `repo` keep the same skills in sync across several agents or machines?",
                       "One skill folder shared by Claude Code, Codex, Cursor, Gemini CLI and others."),
            "app": _q("Is `repo` a desktop, web or TUI app for browsing and managing skills visually?"),
            "registry": _q("Is `repo` a registry, marketplace, directory or search engine for finding skills?"),
            "team": _q("Is `repo` built for teams: sharing, versioning, permissions or auditing skills across an organization?"),
            "general": _q("Is `repo` a general agent-configuration toolkit that manages skills along with many other things?",
                          "Managers of whole agent setups: skills, MCP servers, prompts, hooks and settings together."),
        },
        "labels": _labels(("general", "🧱", "All-in-one", "综合管理"), ("cli", "⌨️", "CLI installers", "命令行安装"),
                          ("sync", "🔄", "Sync across agents", "多 Agent 同步"), ("app", "🖥", "Apps & GUIs", "桌面与界面"),
                          ("registry", "🔎", "Registries & marketplaces", "市场与目录"), ("team", "👥", "Teams", "团队管理")),
        "queries": ["skill manager in:name,description", "skills manager in:name,description",
                    "agent skills manager in:name,description", "skills sync claude codex in:name,description",
                    "skill marketplace agent in:name,description", "skill registry agent in:name,description",
                    "skills installer claude in:name,description", "agent skills cli in:name,description"],
        # The owner's fork of iamzhihuix/skills-manage (2,212 stars), deleted from GitHub by 10-03;
        # the fork keeps the project available. Listed by the owner's decision, not by review.
        "owner_admitted": ["zhuyansen/skills-manager"],
        "words": ["skill manager", "skills manager", "manage skills", "managing skills", "skill management",
                  "skills management", "skill marketplace", "skills marketplace", "skill registry", "skills registry",
                  "sync skills", "skills sync", "skill sync", "install skills", "skill installer", "skills installer",
                  "skills cli", "skill hub", "skillhub", "skills hub", "skill store", "skills store", "skill directory",
                  "skills directory", "skill package manager", "skills package"],
    },
    "telegram-bot": {
        "subject": _q("Is `repo` a Telegram bot, or a tool for building or running Telegram bots?",
                      "Telegram is the main interface, not one channel among many in a large platform."),
        "types": {
            "assistant": _q("Is `repo` an AI chat assistant that runs in Telegram (GPT, Claude, Gemini or a local model)?"),
            "remote": _q("Does `repo` let someone control a coding agent or computer from Telegram (Claude Code, Codex, a shell)?"),
            "framework": _q("Is `repo` a library, framework, template or MCP server for building Telegram bots?"),
            "utility": _q("Is `repo` a utility bot: downloads, files, PDFs, translation, group management or notifications?"),
            "fun": _q("Is `repo` a bot for fun or learning: games, quizzes, language practice, companions?"),
            "business": _q("Is `repo` a bot for business: support, sales, payments, trading or monitoring?"),
        },
        "labels": _labels(("assistant", "💬", "AI assistants", "AI 聊天助手"), ("remote", "🛰", "Agent remote control", "远程操控 Agent"),
                          ("framework", "🧱", "Frameworks & MCP", "框架与 MCP"), ("utility", "🧰", "Utility bots", "实用工具"),
                          ("fun", "🎲", "Fun & learning", "娱乐与学习"), ("business", "💼", "Business", "商业与运营")),
        "queries": ["telegram bot ai in:name,description", "telegram bot gpt in:name,description",
                    "telegram claude in:name,description", "telegram bot llm in:name,description",
                    "telegram mcp in:name,description,topics", "claude code telegram in:name,description",
                    "telegram bot open source in:name,description", "telegram bot language learning in:name,description"],
        "words": ["telegram"],
    },
    "browser-automation": {
        "strict": True,
        "subject": _q("Is the main purpose of `repo` to let an AI agent operate a web browser: navigate, click, type, "
                      "fill forms or read pages?",
                      "Browser agents, browser MCP servers, browser skills and the infrastructure under them. A plain "
                      "test runner or a scraper with no AI in it does not count."),
        "types": {
            "agent": _q("Is `repo` a browser agent or agent framework that completes web tasks on its own?",
                        "browser-use, Stagehand, Skyvern-style agents that plan and act in the browser."),
            "mcp": _q("Is `repo` an MCP server that gives an AI assistant control of a browser?"),
            "skill": _q("Is `repo` a skill, plugin or extension that adds browser control to Claude Code, Codex or Cursor?"),
            "infra": _q("Is `repo` browser infrastructure: cloud or headless browsers, sessions, sandboxes or CDP tooling?"),
            "extract": _q("Is `repo` focused on reading the web: extraction, scraping or turning pages into data for an agent?"),
            "testing": _q("Is `repo` focused on testing or QA of web apps with an AI agent?"),
        },
        "labels": _labels(("agent", "🤖", "Browser agents", "浏览器 Agent"), ("mcp", "🔌", "MCP servers", "MCP 服务"),
                          ("skill", "🧩", "Skills & plugins", "Skill 与插件"), ("infra", "☁️", "Browser infrastructure", "浏览器基础设施"),
                          ("extract", "📥", "Extraction", "网页提取"), ("testing", "✅", "Testing & QA", "测试与 QA")),
        "queries": ["browser agent in:name,description", "browser automation ai in:name,description",
                    "browser mcp in:name,description,topics", "playwright mcp in:name,description",
                    "browser use agent in:name,description", "claude browser in:name,description",
                    "computer use browser in:name,description", "chrome devtools mcp in:name,description"],
        "words": ["browser", "playwright", "puppeteer", "chrome", "selenium", "web agent", "cdp"],
    },
    "code-review": {
        "strict": True,
        "subject": _q("Is the main purpose of `repo` to review code with AI: pull requests, diffs, commits or a codebase?",
                      "It reads code and reports problems or suggestions. A linter with no AI, or a general coding "
                      "agent that can also review, does not count."),
        "types": {
            "pr_bot": _q("Is `repo` a bot or CI action that reviews pull requests on GitHub, GitLab or another forge?"),
            "skill": _q("Is `repo` a skill, plugin, subagent or command that adds code review to Claude Code, Codex or Cursor?"),
            "cli": _q("Is `repo` a command-line or local tool that reviews code on the developer's machine?"),
            "security": _q("Is `repo` focused on security review: vulnerabilities, secrets or unsafe code?"),
            "multi": _q("Does `repo` review code with several agents or models that check each other?"),
            "platform": _q("Is `repo` a self-hosted review platform or service with its own interface?"),
        },
        "labels": _labels(("pr_bot", "🔁", "PR bots & CI", "PR 机器人与 CI"), ("skill", "🧩", "Agent skills", "Agent Skill"),
                          ("cli", "⌨️", "Local & CLI", "本地与命令行"), ("security", "🛡", "Security review", "安全审查"),
                          ("multi", "👥", "Multi-agent", "多 Agent 互审"), ("platform", "🏗", "Platforms", "自托管平台")),
        "queries": ["ai code review in:name,description", "code review agent in:name,description",
                    "claude code review in:name,description", "codex code review in:name,description",
                    "pr review llm in:name,description", "code review skill in:name,description,topics",
                    "pull request review ai in:name,description", "code-review topic:code-review"],
        "words": ["review"],
        "also": ["code", "pr ", "pull request", "diff", "commit", "claude", "codex", "agent", "llm", "ai "],
    },
    "ai-design": {
        "strict": True,
        "subject": _q("Is the main purpose of `repo` to help an AI agent produce visual design: UI and UX, frontend "
                      "styling, design systems, graphics or brand visuals?",
                      "Design skills, design MCP servers and design-to-code tools. A UI component library with no "
                      "AI in it, or a general image generator, does not count."),
        "types": {
            "ui": _q("Is `repo` a skill or guide that makes an agent's UI and frontend output look better?",
                     "Design rules, styles, typography and layout guidance for generated interfaces."),
            "system": _q("Is `repo` about design systems: tokens, themes, component specs an agent follows?"),
            "tool_mcp": _q("Does `repo` connect an agent to a design tool such as Figma, Penpot, Sketch or Canva?"),
            "to_code": _q("Does `repo` turn a design, screenshot or mockup into working frontend code?"),
            "graphics": _q("Does `repo` make graphics: posters, social images, logos, icons or brand assets?"),
            "review": _q("Does `repo` review or critique a design: accessibility, consistency or AI-looking output?"),
        },
        "labels": _labels(("ui", "🎨", "UI & frontend style", "UI 与前端美化"), ("system", "📐", "Design systems", "设计系统"),
                          ("tool_mcp", "🔌", "Figma & design tools", "Figma 与设计工具"), ("to_code", "🧱", "Design to code", "设计稿转代码"),
                          ("graphics", "🖼", "Graphics & brand", "海报与品牌"), ("review", "🔍", "Design review", "设计审查")),
        "queries": ["design skill claude in:name,description", "frontend design skill in:name,description",
                    "ui ux skill in:name,description", "ui ux pro max in:name,description",
                    "figma mcp in:name,description,topics", "design system agent in:name,description",
                    "design to code ai in:name,description", "claude design in:name,description"],
        "words": ["design skill", "design system", "ui/ux", "ui ux", "ui-ux", "figma", "frontend design",
                  "front-end design", "web design", "ui design", "design-to-code", "design to code", "penpot",
                  "canva", "poster", "brand", "taste", "design agent", "designer"],
        "also": ["claude", "codex", "agent", "skill", "mcp", "ai ", "llm", "cursor", "gpt"],
    },
    # New page 10-03 (AIsa: claude code hooks 3,600/KD16, subagents 2,010/19, statusline 1,900/14).
    "claude-code-hooks": {
        "strict": True,
        "subject": _q("Is the main purpose of `repo` to provide or manage Claude Code hooks, subagents (custom agents) "
                      "or a statusline?",
                      "Hook scripts and hook frameworks, subagent definitions and collections, statusline scripts, or "
                      "tools that create and manage them. A general Claude Code plugin or skill without these does not count."),
        "types": {
            "hooks": _q("Is `repo` mainly about Claude Code hooks: scripts that run on tool use, prompts, stop or other events?",
                        "Guards, formatters, notifications, logging, safety checks wired to hook events."),
            "subagents": _q("Is `repo` mainly about Claude Code subagents: custom agent definitions with their own prompt and tools?",
                            "Agent files in .claude/agents, collections of specialist agents, orchestration of subagents."),
            "statusline": _q("Is `repo` mainly about the Claude Code statusline: what the status bar at the bottom shows?",
                             "Usage, cost, context, git branch or model shown in the status line."),
            "collection": _q("Is `repo` a large collection that bundles many hooks, subagents, commands or settings together?"),
            "tooling": _q("Is `repo` a tool for creating, installing, testing or managing hooks, subagents or statuslines?"),
        },
        "labels": _labels(("hooks", "🪝", "Hooks", "Hooks 钩子"), ("subagents", "🤖", "Subagents", "Subagents 子代理"),
                          ("statusline", "📊", "Statuslines", "Statusline 状态栏"), ("collection", "📚", "Collections", "合集"),
                          ("tooling", "🛠", "Tooling", "管理与生成工具")),
        "queries": ["claude code hooks in:name,description,topics", "claude hooks in:name,description",
                    "claude code subagents in:name,description", "claude subagents in:name,description,topics",
                    "claude code agents collection in:name,description", "claude code statusline in:name,description",
                    "claude statusline in:name,description,topics", "status line claude code in:name,description"],
        # "agents" alone matched 2,880 catalog repos: every Claude agent project. Name the formats instead.
        "words": [" hooks ", " hook ", "hooks,", "subagent", "sub agent", "statusline", "status line", "statusbar",
                  "status bar", "custom agents", "agent definitions", "claude agents", ".claude agents", "agents collection"],
        "also": ["claude"],
    },
    # Upgraded 10-04 (AIsa: obsidian claude 1,600/mo KD 1). Obsidian only: LLM wikis belong to knowledge-base.
    "obsidian-second-brain": {
        "strict": True,
        "subject": _q("Is the main purpose of `repo` to connect AI agents or LLMs with Obsidian: skills, MCP servers, "
                      "plugins or workflows that read, write or organize an Obsidian vault?",
                      "Obsidian must be central. A general note app, an LLM wiki not built on Obsidian, or a "
                      "second-brain app of its own does not count."),
        "types": {
            "skill": _q("Is `repo` an agent skill or prompt set that teaches Claude Code, Codex or another agent to work in an Obsidian vault?"),
            "mcp": _q("Is `repo` an MCP server or API bridge that gives an AI assistant access to an Obsidian vault?"),
            "plugin": _q("Is `repo` an Obsidian plugin that brings an LLM or agent inside Obsidian itself?"),
            "second_brain": _q("Is `repo` a second-brain or PKM system built on Obsidian that an agent maintains: "
                               "templates, folder structures, daily notes, zettelkasten workflows?"),
            "sync": _q("Is `repo` about getting content into or out of Obsidian with AI: import, capture, publishing or sync?"),
        },
        "labels": _labels(("skill", "🧩", "Agent skills", "Agent Skill"), ("mcp", "🔌", "MCP servers", "MCP 服务"),
                          ("plugin", "🧱", "AI plugins", "AI 插件"), ("second_brain", "🧠", "Second brain workflows", "第二大脑工作流"),
                          ("sync", "🔄", "Import, publish & sync", "导入、发布与同步")),
        "queries": ["obsidian claude in:name,description", "obsidian skill in:name,description,topics",
                    "obsidian mcp in:name,description,topics", "obsidian codex in:name,description",
                    "obsidian ai plugin in:name,description", "obsidian agent in:name,description",
                    "obsidian second brain in:name,description", "claude obsidian vault in:name,description"],
        "words": ["obsidian"],
        "also": ["claude", "codex", "agent", "ai ", "llm", "mcp", "skill", "gpt", "rag", "copilot"],
    },
    # Upgraded 10-04 (AIsa: humanizer skill 1,300/mo KD 7).
    "anti-slop": {
        "subject": _q("Is the main purpose of `repo` to make AI-made output read as if a person made it, or to detect or "
                      "remove AI patterns ('slop') in text, code or design?",
                      "Humanizer skills and prompts, slop detectors and linters, style rules against AI tells. A "
                      "general writing assistant or grammar checker does not count."),
        "types": {
            "writing": _q("Does `repo` rewrite AI-written prose so it reads human: articles, posts, emails?"),
            "detector": _q("Does `repo` detect or score AI writing patterns, like a linter or classifier for slop?"),
            "chinese": _q("Is `repo` focused on Chinese text: removing the AI flavour (去 AI 味) from Chinese writing?"),
            "code": _q("Does `repo` clean AI patterns out of code: comments, over-engineering, generated boilerplate?"),
            "design": _q("Does `repo` steer AI-made UI and visuals away from the generic AI look (design taste)?"),
            "rules": _q("Is `repo` mainly a style guide, word list or set of rules that agents follow to avoid AI tells?"),
        },
        "labels": _labels(("writing", "✍️", "Writing humanizers", "文字去 AI 味"), ("detector", "🔍", "Slop detectors", "AI 味检测"),
                          ("chinese", "🀄", "Chinese text", "中文去 AI 味"), ("code", "🧹", "Code cleanup", "代码去 AI 味"),
                          ("design", "🎨", "UI & design taste", "设计去 AI 味"), ("rules", "📏", "Style rules", "写作规则")),
        "queries": ["humanizer skill in:name,description", "humanizer claude in:name,description",
                    "anti slop in:name,description,topics", "deslop in:name,description",
                    "ai slop detector in:name,description", "humanize ai text in:name,description",
                    "去ai味 in:name,description", "stop slop in:name,description"],
        "words": ["humaniz", "slop", "ai tells", "ai writing patterns", "ai-sounding", "去ai味", "去 ai 味", "ai味", "ai 味",
                  "taste skill"],
    },
    "knowledge-base": {
        "strict": True,
        "subject": _q("Is the main purpose of `repo` to build, maintain or query a knowledge base with an LLM or AI agent: "
                      "an LLM-maintained wiki, a RAG knowledge base, or documents an agent answers questions from?",
                      "The knowledge base is the product. A general chatbot, a vector database library on its own, or "
                      "an agent's short-term memory does not count."),
        "types": {
            "llm_wiki": _q("Does `repo` have an LLM or agent write and maintain a wiki of linked markdown pages (the 'LLM wiki' pattern)?"),
            "rag_platform": _q("Is `repo` a RAG knowledge-base platform with its own interface, like MaxKB, FastGPT or AnythingLLM?"),
            "mcp": _q("Is `repo` an MCP server or agent skill that lets Claude Code, Codex or another agent search a knowledge base?"),
            "docs_qa": _q("Does `repo` answer questions from a specific set of documents: product docs, a codebase, papers or PDFs?"),
            "graph": _q("Does `repo` organize knowledge as a graph of entities and relations (GraphRAG, knowledge graphs)?"),
            "personal": _q("Is `repo` a personal knowledge base: notes, bookmarks, reading or a second brain kept by an AI?"),
        },
        "labels": _labels(("llm_wiki", "📖", "LLM wikis", "LLM Wiki"), ("rag_platform", "🏗", "RAG platforms", "RAG 知识库平台"),
                          ("mcp", "🔌", "MCP & agent skills", "MCP 与 Agent Skill"), ("docs_qa", "📄", "Docs Q&A", "文档问答"),
                          ("graph", "🕸", "Knowledge graphs", "知识图谱"), ("personal", "🧠", "Personal knowledge", "个人知识库")),
        "queries": ["llm wiki in:name,description", "llm-wiki in:name", "knowledge base agent in:name,description",
                    "knowledge base mcp in:name,description,topics", "rag knowledge base in:name,description",
                    "claude knowledge base in:name,description", "agent wiki markdown in:name,description",
                    "second brain llm in:name,description"],
        "words": ["knowledge base", "knowledgebase", "llm wiki", "wiki", " rag ", "rag,", "retrieval augmented",
                  "second brain", "knowledge graph", "graphrag"],
        "also": ["claude", "codex", "agent", "llm", "ai ", "mcp", "skill", "gpt", "rag"],
    },
    "codex-skills": {
        "strict": True,
        # 1,929 repos passed "Codex is a named target": most were skills for every agent that
        # list Codex among several. The page is for what is made for Codex (owner, 10-03).
        "extra": {"codex_first": _q("Is `repo` made mainly for OpenAI Codex: Codex is its primary or first-class target "
                                    "in the name or description, not one of several agents it also supports?")},
        "subject": _q("Is `repo` made for OpenAI Codex: a skill, plugin, subagent, MCP setup or workflow for the Codex "
                      "CLI, app or IDE extension, or a collection or tool for Codex skills?",
                      "Codex must be a named target. A skill written only for Claude Code does not count; one that "
                      "supports both does."),
        "types": {
            "collection": _q("Is `repo` a collection or curated list of many Codex skills or plugins?"),
            "skill": _q("Is `repo` one skill or a small set of skills for a specific task?"),
            "plugin": _q("Is `repo` a Codex plugin, extension or MCP integration that adds new capabilities?"),
            "workflow": _q("Is `repo` a workflow or orchestration layer: subagents, planning, multi-agent or long-running tasks?"),
            "bridge": _q("Does `repo` connect Codex with another agent such as Claude Code, Gemini CLI or Cursor?"),
            "tooling": _q("Is `repo` tooling around Codex: config, usage tracking, session management, installers or UIs?"),
        },
        "labels": _labels(("collection", "📚", "Collections", "合集"), ("skill", "🧩", "Skills", "单个 Skill"),
                          ("plugin", "🔌", "Plugins & MCP", "插件与 MCP"), ("workflow", "🗺", "Workflows & subagents", "工作流与子 Agent"),
                          ("bridge", "🌉", "Bridges to other agents", "跨 Agent 桥接"), ("tooling", "🛠", "Tooling", "周边工具")),
        "queries": ["codex skills in:name,description,topics", "codex skill in:name,description",
                    "awesome codex in:name,description", "codex plugin in:name,description,topics",
                    "codex cli skill in:name,description", "codex subagents in:name,description",
                    "openai codex agent in:name,description", "codex mcp in:name,description"],
        "words": ["codex"],
        "name_desc_only": True,   # "codex" sits in the topics of ~2,000 multi-agent tools
        "also": ["skill", "plugin", "subagent", "sub-agent", "extension", "mcp", "awesome", "workflow", "agents.md"],
    },
}


def is_candidate(slug: str, name: str, description: str, topics: list[str]) -> bool:
    """The page's coarse filter: one of `words` (and one of `also`, when set) in the repo's
    name, description and topics. Topics are left out for pages that set name_desc_only."""
    page = PAGES[slug]
    text = f"{name} {description}" + ("" if page.get("name_desc_only") else " " + " ".join(topics))
    text = " " + re.sub(r"[-_/]+", " ", text.lower()) + " "   # "skills-hub" must match "skills hub"
    return any(w in text for w in page["words"]) and (not page.get("also") or any(w in text for w in page["also"]))
