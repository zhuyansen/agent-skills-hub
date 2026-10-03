"""Text of zhuyansen/awesome-typesafe-jev, the GitHub face of /best/typesafe-jev/ (10-03).
Shapes match VIDEO_TEXT in build_video_list.py; keys not set here are copied from it there."""

JEV_TEXT = {
    "en": {
        "file": "README.md", "other": "[中文](README.zh-CN.md)", "title": "Awesome TypeSafe Jev",
        "pitch": ("Open-source projects built on **TypeSafe Jev**, the decision model: agents and computer use, "
                  "developer tools, SDKs and MCP servers, classification apps, and open replicas. "
                  "{n} repos, each one read and security-graded by [Agent Skills Hub]({site}{utm})."),
        "live": "Live page with filters: **[{page}]({page}{utm})** · refreshed every 8 hours",
        "rules_h": "How a repo gets on the list",
        "rules": ["It uses Jev: it calls the model, wraps it, or reproduces or replaces it. A project that only "
                  "mentions Jev, or a different project that happens to be named Jev, does not count.",
                  "It is software someone can install or run, not a list of links or a placeholder.",
                  "It has a README. Without one it cannot be graded.",
                  "At 50 stars or more it is listed on topic alone. Under 50 it must also reach the top tier of a "
                  "README quality bar (shows it working, one-command start, a concrete outcome, complete docs), "
                  "and have 5 stars."],
        "rules_note": ("The questions are answered by Jev itself reading each README, not by hand. "
                       "A repo near a cut-off can land on either side; open an issue if one is misfiled."),
        "album": "What these projects look like",
        "related": ["[zhuyansen/awesome-claude-video-skills](https://github.com/zhuyansen/awesome-claude-video-skills)"
                    " and [zhuyansen/awesome-codex-ppt-skills](https://github.com/zhuyansen/awesome-codex-ppt-skills)"
                    " — lists built the same way, for skills that make video and slides."],
    },
    "zh": {
        "file": "README.zh-CN.md", "other": "[English](README.md)", "title": "Awesome TypeSafe Jev",
        "pitch": ("基于 **TypeSafe Jev** 决策模型的开源项目:Agent 与电脑操作、开发者工具、SDK 与 MCP、分类与业务应用、"
                  "开源复现。共 {n} 个仓库,每个都由 [Agent Skills Hub]({site}{utm}) 读过 README 并做了安全评级。"),
        "live": "带类型筛选的在线页面:**[{page}]({page}{utm})** · 每 8 小时刷新",
        "rules_h": "什么样的仓库能上榜",
        "rules": ["它用到 Jev:调用、封装,或复现、替代这个模型。只是提到 Jev,或者恰好也叫 Jev 的别的项目,不算。",
                  "它是能安装或运行的软件,不是链接合集或空仓库。",
                  "它有 README。没有 README 就没法评级。",
                  "50 星及以上只看是否切题;50 星以下还要达到 README 质量线的最高档(展示效果、一条命令上手、"
                  "说清产出、文档完整),并且至少 5 星。"],
        "rules_note": "这些问题由 Jev 自己逐个读 README 回答,不是人工挑选。卡在线上的仓库可能判到任一边,归错了请提 issue。",
        "album": "这些项目长什么样",
        "related": ["[zhuyansen/awesome-claude-video-skills](https://github.com/zhuyansen/awesome-claude-video-skills)"
                    " 和 [zhuyansen/awesome-codex-ppt-skills](https://github.com/zhuyansen/awesome-codex-ppt-skills)"
                    " —— 同样做法的视频、PPT skill 合集。"],
    },
}
JEV_BLURB = {
    "general": ("Platforms and harnesses that cover many uses of Jev.", "覆盖多种 Jev 用法的平台和框架。"),
    "replica": ("Open models and servers that reproduce or replace Jev, to self-host.", "复现或替代 Jev 的开源模型和服务,可自托管。"),
    "agent": ("Agents that act: browser and computer use, games, task runners.", "会动手的 Agent:浏览器与电脑操作、游戏、任务执行。"),
    "devtool": ("Coding-agent plugins, code search and review, routing, context compaction.", "编程 Agent 插件、代码搜索与审查、模型路由、上下文压缩。"),
    "sdk": ("Client libraries, MCP servers and local endpoints for calling Jev.", "调用 Jev 的客户端库、MCP 服务和本地接口。"),
    "business": ("Document classification, finance, trading, support triage.", "文档分类、财税、交易、工单分诊。"),
    "consumer": ("Chat assistants, smart input, personal memory.", "聊天助手、智能输入、个人记忆。"),
}
