"""One-off: the method block for /best/ai-reverse-engineering/ (2026-10-13).

  python ops/research/method_block_2026_10_13.py

The counts are from the review of that day: ops/jev-review/state/ai-reverse-engineering and
ops/research/ai-reverse-engineering-candidates-2026-10-13.md. Nothing on the page was run.
"""
import json

from method_blocks_2026_10_11 import DAILY, KEYWORDS, KIND_COLS, author, block, route

SLUG = "ai-reverse-engineering"
REVIEWED, WAVE, WAVE_STARRED, CLAIMED, CONFIRMED, LISTED_CASES = 618, 917, 157, 17, 10, 4

ROUTES = [
    route(("Disassembler and decompiler MCP", "反汇编与反编译 MCP"),
          ("A server or plugin that lets the agent drive Ghidra, IDA Pro, Binary Ninja, radare2 or x64dbg: list functions, read decompiled code, rename, comment.",
           "一个服务或插件，让 agent 操作 Ghidra、IDA Pro、Binary Ninja、radare2 或 x64dbg：列函数、读反编译代码、改名、加注释。"),
          ("The agent works inside the tool you already use, on the database you already have.", "agent 就在你已经在用的工具里干活，用的是你现成的分析库。"),
          ("You need the tool itself, and for IDA Pro and Binary Ninja a licence. Check which version the plugin supports.",
           "得先有工具本身，IDA Pro 和 Binary Ninja 还要授权。看清插件支持哪个版本。"), ["mcp"]),
    route(("Mobile app reversing", "移动端逆向"),
          ("jadx, apktool or Frida connected to the agent, for Android, iOS or HarmonyOS apps.", "把 jadx、apktool 或 Frida 接给 agent，面向 Android、iOS 或鸿蒙应用。"),
          ("Reads an APK's code and resources, or hooks a running app.", "能读 APK 的代码和资源，或者挂钩运行中的应用。"),
          ("Frida tools act on a live device. Use a test device, not your own phone.", "Frida 类工具作用于真机。用测试机，别用自己的手机。"), ["mobile"]),
    route(("Web, JS and protocol reversing", "Web、JS 与协议逆向"),
          ("Tools for obfuscated JavaScript, request signing and traffic analysis.", "针对混淆 JavaScript、请求签名和流量分析的工具。"),
          ("Works from a browser, no disassembler needed.", "从浏览器入手，不需要反汇编器。"),
          ("The smallest group here, and a site's terms may forbid what these tools do.", "这一类条目最少；网站的服务条款可能禁止这些操作。"), ["web"]),
    route(("Reverse engineering skills", "逆向 Skill"),
          ("Instructions and workflows that teach the agent how to approach a target and which tool to call.", "教 agent 怎么分析目标、该调用哪个工具的说明与流程。"),
          ("Installs in one step and works with the tools above.", "一步装好，可以和上面的工具配合。"),
          ("A skill is text. What it can do depends on the tools the agent can reach.", "skill 只是文字，能做到什么取决于 agent 够得着哪些工具。"), ["skill"]),
    route(("Reverse-engineered with AI", "AI 逆向出来的项目"),
          ("Programs rebuilt or analysed with REA, where the README says so.", "用 REA 重建或分析出来的程序，README 里写明了这一点。"),
          ("Shows what the approach produces, with the source to read.", "能看到这条路做出来的东西，源码可读。"),
          ("Small and new: three of the four have fewer than ten stars.", "又小又新：四个里有三个不到十星。"), ["case"]),
]

BLOCK = block(
    ("How we chose these AI reverse engineering tools: what the agent is connected to", "我们怎么选这些 AI 逆向工程工具：agent 接的是什么"),
    ("An AI agent does not reverse engineer by itself. It reads what a disassembler, a decompiler or a debugger gives it, so the first question is which of those it is connected to. "
     "The page is grouped by that, and a repository is listed only when reverse engineering with an agent is its main purpose.",
     "AI agent 自己不会逆向。它读的是反汇编器、反编译器或调试器给它的结果，所以第一个问题是它接的是哪一个。本页按这一点分组；一个仓库只有以「用 agent 做逆向」为主要用途才会收录。"),
    ("Five kinds, by what the agent works on", "五种类型，按 agent 处理的对象分"), KIND_COLS, ROUTES,
    ("What none of these changes: you need the right to analyse the target. Unpacking and anti-debugging are ordinary reverse engineering and are listed. "
     "Repositories whose selling point is game cheating or cracking software are not.",
     "这些工具都不改变一件事：你得有权分析那个目标。脱壳和反调试属于正常的逆向，会收录。以游戏作弊或破解软件为卖点的仓库不收录。"),
    ("Pick by what you already have", "按你手头已有的东西选"),
    [(("Ghidra is installed", "已经装了 Ghidra"), ("A Ghidra MCP server, such as LaurieWired/GhidraMCP or bethington/ghidra-mcp", "Ghidra MCP，例如 LaurieWired/GhidraMCP、bethington/ghidra-mcp")),
     (("You have an IDA Pro licence", "有 IDA Pro 授权"), ("mrexodia/ida-pro-mcp", "mrexodia/ida-pro-mcp")),
     (("The target is an Android app", "目标是 Android 应用"), ("zinja-coder/jadx-ai-mcp, or the Android reverse engineering skill", "zinja-coder/jadx-ai-mcp，或 Android 逆向 skill")),
     (("You debug a running Windows program", "要调试运行中的 Windows 程序"), ("duty1g/x64dbg-mcp-server", "duty1g/x64dbg-mcp-server")),
     (("You want to start from the agent, not from a tool", "想从 agent 出发，而不是从某个工具出发"), ("morluto/rea, the official repository", "morluto/rea，官方仓库"))],
    ("Four questions we ask of every repository", "每个仓库我们问四个问题"),
    [("Is reverse engineering with an AI agent its main purpose, or one feature among many?", "用 AI agent 做逆向是它的主要用途，还是众多功能之一？"),
     ("Is it software an agent can use, not a list of links or a write-up?", "它是 agent 能用的软件，而不是链接清单或文章？"),
     ("Is it the original, or a copy of someone else's repository?", "它是原版，还是照搬别人的仓库？"),
     ("Is its selling point analysis, or cheating and cracking?", "它的卖点是分析，还是作弊与破解？")],
    ("while analysing a target", "分析目标时的行为"),
    [(f"The wave around REA is mostly not software. Of {WAVE} repositories that mention it, {WAVE_STARRED} have at least one star; about half of those are unrelated to it.",
      f"围绕 REA 的这一波，大部分不是软件。{WAVE} 个提到它的仓库里，{WAVE_STARRED} 个至少有一颗星；其中约一半其实与它无关。"),
     (f"A model's label is not enough for \"made with REA\". It marked {CLAIMED} repositories as such; reading each README left {CONFIRMED}, and {LISTED_CASES} are listed.",
      f"「用 REA 做的」不能只信模型的判断。模型标了 {CLAIMED} 个，逐个读 README 后剩 {CONFIRMED} 个，收录 {LISTED_CASES} 个。"),
     ("Copies travel with the original. Nine repositories repeat or translate morluto/rea, one with more than 200 stars. They are named in the table below.",
      "原版火了，复制品跟着来。有九个仓库照搬或翻译 morluto/rea，其中一个超过 200 星。它们列在下面的表里。")],
    [(f"Found {REVIEWED} candidates on GitHub (every star count) and in our catalog, then had Jev, TypeSafe's decision model, read each README against the questions above.",
      f"在 GitHub（不限星数）和我们的目录里找到 {REVIEWED} 个候选，再让 TypeSafe 的决策模型 Jev 按上面的问题逐个读 README。"),
     ("Read by hand the README and file list of every repository listed as made with REA, and checked that none ships the original program's files.",
      "凡是列为「用 REA 做的」的仓库，都人工读了 README 和文件列表，并确认没有附带原程序的文件。"),
     ("Compared the README of each suspected copy with the official one.", "把每个疑似复制品的 README 和官方版逐一比对。"), DAILY],
    ("We did not run these tools: nothing here was tested against a binary, and we did not check what the code of the copies does.",
     "我们没有实际运行这些工具：没有拿任何一个去分析二进制，也没有检查复制品的代码做了什么。"),
    [], author(" and its AI reverse engineering list", "及其 AI 逆向工程合集"))
BLOCK["h3_findings"] = ["What the review found", "审核中发现了什么"]
BLOCK["author"]["reviewed"] = "2026-10-13"

pages = json.loads(KEYWORDS.read_text())
next(p for p in pages if p["slug"] == SLUG)["method"] = BLOCK
KEYWORDS.write_text(json.dumps(pages, ensure_ascii=False, indent=1) + "\n")
print("method block written:", SLUG, len(ROUTES), "kinds")
