"""One-off: the method block for /best/seo-tools/ (2026-10-17).

  cd ops/research && python method_block_seo_tools_2026_10_17.py

Counts come from the review state (ops/jev-review/state/seo-tools) and the page's
exclude_repos on that day. Nothing on the page was run against a site.
"""
import json

from method_blocks_2026_10_11 import KEYWORDS, KIND_COLS, author, block, route

SLUG = "seo-tools"
REVIEWED, LISTED, COPIES = 651, 247, 20

ROUTES = [
    route(("All-in-one SEO skills", "综合 SEO Skill"),
          ("One skill or agent that runs audits, keyword work, content and technical checks.", "一个 skill 或 agent 包办审计、关键词、内容和技术检查。"),
          ("One install covers most jobs.", "装一个就能做大部分事。"),
          ("Without a data connection it works from what the model remembers, not from your site's numbers.", "不接数据源时，它依据的是模型记得的东西，不是你站的真实数字。"), ["suite"]),
    route(("SEO audit skills", "站点与页面审计"),
          ("Crawls a site or reads a page and lists technical and on-page problems.", "抓取站点或读取页面，列出技术和页面问题。"),
          ("Concrete, checkable findings.", "结论具体，可以逐条核对。"),
          ("A list of problems is not a ranking forecast; whether a fix helps shows in Search Console weeks later.", "问题清单不等于排名预测；改了有没有用，要几周后在 Search Console 里看。"), ["audit"]),
    route(("Keyword research & rank tracking", "关键词与排名研究"),
          ("Finds terms, sizes demand and follows positions.", "找词、估算需求、跟踪排名。"),
          ("Tells you what to build before you build it.", "动手前先知道该做什么。"),
          ("Volumes come from third-party databases and lag by weeks; new terms are often missing.", "搜索量来自第三方数据库，滞后数周；新词常常查不到。"), ["research"]),
    route(("SEO data MCP & monitoring dashboards", "SEO 数据 MCP 与监控面板"),
          ("Gives the agent your Search Console, crawl or SEO-database data.", "把 Search Console、抓取结果或 SEO 数据库的数据交给 agent。"),
          ("Every other kind gets better with real data behind it.", "其他各类工具接上它都会更准。"),
          ("Needs keys or a paid account; check which data each tool sends out.", "需要密钥或付费账号；装前看清它会把哪些数据发出去。"), ["data_mcp"]),
    route(("GEO & AI search visibility", "GEO 与 AI 搜索可见性"),
          ("Tracks and improves how often AI answers mention or cite a site.", "追踪并提高 AI 回答提到或引用你的频率。"),
          ("Covers the traffic that never reaches a search results page.", "覆盖那部分不经过搜索结果页的流量。"),
          ("The youngest kind; measurements differ a lot between tools.", "最新的一类，各工具的测法差别很大。"), ["geo"]),
    route(("SEO content writing", "SEO 内容写作"),
          ("Drafts articles, briefs and on-page copy aimed at a term.", "围绕一个词写文章、大纲和页面文案。"),
          ("Fast first drafts in the right shape.", "很快出结构合适的初稿。"),
          ("Unedited AI copy at scale is what Google's scaled-content rules target.", "未经编辑的批量 AI 文案，正是 Google 规模化内容规则针对的对象。"), ["content"]),
    route(("Link building & backlink audits", "外链建设与外链审计"),
          ("Finds link and PR openings, submits to directories, or checks link sources.", "找外链和媒体机会、提交目录，或检查外链来源。"),
          ("Gets a new site discovered.", "让新站被发现。"),
          ("Directory links help discovery, not authority; paid or manipulative links break Google's spam rules.", "目录外链帮助被发现，不传权重；付费或操纵性外链违反 Google 的垃圾政策。"), ["links"]),
    route(("Marketing skill packs with SEO", "含 SEO 的营销合集"),
          ("A broad marketing collection where SEO is one area.", "SEO 只是其中一部分的综合营销合集。"),
          ("SEO next to copy, ads and analytics in one install.", "SEO、文案、广告、分析一次装齐。"),
          ("SEO depth is usually thinner than in a dedicated skill.", "SEO 部分通常不如专门的 skill 深。"), ["marketing"]),
]

BLOCK = block(
    ("How we chose these Claude SEO skills: what the agent can see", "我们怎么选这些 Claude SEO skill：agent 能看到什么"),
    ("An SEO skill is only as good as the data it reaches. Without a connection it advises from what the model remembers; "
     "connected to Search Console, a crawler or a keyword database, it works from your site's real numbers. "
     "The page is grouped by the job a tool does, and the table says what each kind gains and what it costs.",
     "SEO skill 的上限取决于它能拿到什么数据。不接数据源时，它根据模型记得的东西给建议；接上 Search Console、抓取工具或关键词数据库后，"
     "它依据的是你站的真实数字。本页按工具做的事分组，下表写明每一类的长处和代价。"),
    ("Eight kinds, by the job they do", "八类，按做的事分"), KIND_COLS, ROUTES,
    ("None of these replaces evidence from your own search data: whether a change helped shows in Search Console weeks later. "
     "And none makes bought or manipulated links safe.",
     "这些工具都替代不了你自己搜索数据里的证据：改动有没有用，要几周后在 Search Console 里看。也没有哪个工具能让买来的或操纵性的外链变安全。"),
    ("Pick by what you already have", "按你手头已有的东西选"),
    [(("You want one skill for most jobs", "想装一个包办大部分事"), ("AgriciDaniel/claude-seo", "AgriciDaniel/claude-seo")),
     (("You have Search Console", "已经有 Search Console"), ("A Search Console MCP, such as AminForou/mcp-gsc", "Search Console MCP，例如 AminForou/mcp-gsc")),
     (("You need keyword data without a subscription", "要关键词数据又不想订阅"), ("every-app/open-seo", "every-app/open-seo")),
     (("You care about AI answers", "在意 AI 回答里有没有你"), ("zubair-trabzada/geo-seo-claude", "zubair-trabzada/geo-seo-claude")),
     (("You are about to submit to directories", "准备提交目录站"), ("Check each site first, e.g. with zhuyansen/backlink-guard (ours)", "先逐个检查目标站，例如用 zhuyansen/backlink-guard（我们做的）"))],
    ("Four questions we ask of every repository", "每个仓库我们问四个问题"),
    [("Is SEO its main purpose, done through an agent: a skill, an MCP server or an agent?", "SEO 是它的主要用途吗？是通过 agent 来做的吗（skill、MCP 服务或 agent）？"),
     ("What data does it reach: none, your own site, or a third-party SEO database?", "它能拿到什么数据：没有、你自己的站，还是第三方 SEO 数据库？"),
     ("Is it something you can install and run, not a list of links or a hosted product with no agent interface?", "它是能安装运行的东西，而不是链接清单，或没有 agent 接口的托管产品吗？"),
     ("Is it the original, not a renamed copy of someone else's repository?", "它是原版，而不是改了名的别人的仓库吗？")],
    ("while doing SEO work", "做 SEO 时的行为"),
    [(f"Copies are common in this field: {COPIES} repositories repeated popular skill collections under new names ending in -seo. They are left out.",
      f"这个领域复制品很多：有 {COPIES} 个仓库照搬热门 skill 合集，改名并加上 -seo 后缀，都没有收录。"),
     ("GEO is now the second-largest kind, after all-in-one skills; keyword research tools for agents are still few.",
      "GEO 已是仅次于综合类的第二大类；给 agent 用的关键词研究工具仍然很少。"),
     ("Two tools in the link group are ours (backlink-guard and backlink-spam-list). They are listed by the owner's choice under the same safety grading as every other entry.",
      "外链一类里有两个是我们做的（backlink-guard 和 backlink-spam-list），由站长指定收录，安全评级与其他条目同一标准。")],
    [(f"Found {REVIEWED} candidates on GitHub (every star count) and in our catalog, then had Jev, TypeSafe's decision model, read each README against the questions above; {LISTED} are listed.",
      f"在 GitHub（不限星数）和我们的目录里找到 {REVIEWED} 个候选，再让 TypeSafe 的决策模型 Jev 按上面的问题逐个读 README；收录 {LISTED} 个。"),
     ("Read by hand every repository whose kind changed when the kinds were redrawn on 2026-10-17.", "2026-10-17 重分类时，凡是类型有变动的仓库都人工看过。"),
     ("Security-graded every repo against 11 red-flag categories.", "按 11 类风险给每个仓库做了安全评级。")],
    ("We did not run these tools against a site, so nothing here compares their findings or results.", "我们没有拿这些工具去跑真实站点，所以这里不比较它们的结论和效果。"),
    [], author(" and its Claude SEO list", "及其 Claude SEO 合集"))
BLOCK["h3_findings"] = ["What the review found", "审核中发现了什么"]
BLOCK["author"]["reviewed"] = "2026-10-17"

pages = json.loads(KEYWORDS.read_text())
next(p for p in pages if p["slug"] == SLUG)["method"] = BLOCK
KEYWORDS.write_text(json.dumps(pages, ensure_ascii=False, indent=1) + "\n")
print("method block written:", SLUG)
