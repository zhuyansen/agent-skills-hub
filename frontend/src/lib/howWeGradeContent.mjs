/**
 * The text of /how-we-grade/, English and Chinese side by side, and the helpers both
 * renderers use: the static generator (scripts/generate-how-we-grade-page.mjs) and the
 * React page (src/pages/HowWeGradePage.tsx). One copy of the text, so the page that
 * crawlers read and the page Google renders say the same thing.
 *
 * Every claim was checked (2026-10-21/22) against backend/app/services/security_scanner.py
 * (rules, tiers, the grade table, what is not counted), grade_refresh.py (when grades are
 * redone), quality_analyzer.py (the weights in the scoring code; the class docstring's are
 * stale), scorer.py (ranking weights) and src/lib/gradeState.ts (why a repo has no grade).
 * Change a number here only after changing it there.
 *
 * Text is `[english, chinese]`, or one string when both languages read the same (grade
 * names, tier numbers, percentages). Inline markup: **bold**, *italic*, `code`,
 * [label](href) and \n for a line break; see inlineTokens().
 */
import { GRADES_ANCHOR, HOW_WE_GRADE_LINK, RULE_COUNT } from "./howWeGradeMeta.mjs";

/**
 * The two sentences about fenced code blocks. Since 2026-10-22 the scanner checks
 * download-and-execute commands inside code blocks too, as the medium-risk
 * fenced_download_exec; every other rule that skips code blocks still does.
 */
export const CODE_BLOCKS = {
  /** Last item of "What we don't count". */
  notCounted: [
    "text inside code blocks for the reject and other high-risk rules and most agent rules, because security tools show the attacks they block there. Download-and-execute commands are the exception: inside a code block they still count, as one medium-risk finding instead of a high-risk one, unless the source is trusted (see the high-risk list) or the line lists what a tool blocks.",
    "代码块里的文字：Reject 级规则、其他高风险规则和大部分针对 agent 的规则都不看代码块，因为安全工具会在代码块里展示它们拦截的攻击。下载即执行的命令是例外：写在代码块里照样计入，但算一条中风险而不是高风险；下载来源可信（见高风险清单），或这一行是在列工具会拦截什么的，不算。",
  ],
  /** Second item of "Known limits". */
  limit: [
    "**Other risky commands inside code blocks are not counted.** A reverse shell or a credential grab shown as a fenced example passes, unless the README also asks for it in its prose. Download-and-execute commands are the exception, and only as medium risk: on its own, a fenced install script from an unknown host makes a tier 5 project Caution and leaves tiers 1 to 4 Safe.",
    "**代码块里的其他高危命令不计入。**以代码块示例形式出现的反弹 shell 或凭证窃取命令能通过，除非 README 的正文里也要求这么做。下载即执行的命令是例外，但只算中风险：单单一条写在代码块里、来自陌生主机的安装脚本，会让第 5 档项目变成 Caution，第 1 到 4 档仍是 Safe。",
  ],
};

/** Tailwind classes shared by both renderers, so the pre-rendered page looks like the React one. */
export const CLASSES = {
  page: "min-h-screen bg-gray-50 dark:bg-gray-950",
  main: "max-w-3xl mx-auto px-4 py-8",
  crumbs: "text-sm text-gray-400 dark:text-gray-500 mb-4",
  crumbLink: "text-indigo-500 hover:text-indigo-600",
  crumbSep: "mx-2",
  crumbHere: "text-gray-600 dark:text-gray-300",
  header: "mb-8 pb-6 border-b border-gray-200 dark:border-gray-700",
  h1: "text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white tracking-tight",
  updated: "mt-3 text-sm text-gray-400 dark:text-gray-500",
  article: "book-prose break-words",
  section: "scroll-mt-24",
  list: "list-disc",
  tableWrap: "overflow-x-auto",
};

// minRem 28: on a 360–430px phone the next column still shows at the edge of the box,
// so it reads as a table that scrolls rather than one that ends (measured 2026-10-22).
// The Chinese grade names go on a second line: "Caution（需注意）" broke inside the bracket.
const GRADES = {
  type: "table",
  label: ["Security grades", "安全评级"],
  minRem: 28,
  head: [["Grade", "等级"], ["What it means", "含义"], ["What to do", "该怎么做"]],
  rows: [
    [
      ["**Safe**", "**Safe**\n安全"],
      ["None of the rules below matched, or only minor ones in a well-established project.", "下面的规则一条都没命中，或者在很成熟的项目里只命中了轻微的规则。"],
      ["Install as you would any open-source tool: still read what it asks for.", "像安装任何开源工具一样安装，但仍要看清它要你做什么。"],
    ],
    [
      ["**Caution**", "**Caution**\n需注意"],
      ["The README asks for something risky: elevated rights, persistence, credentials, opaque downloads. Or a serious pattern turned up in a project whose track record keeps it from Unsafe.", "README 要求做有风险的事：提升权限、常驻后台、提供凭证、下载来源不透明的文件。或者查到了严重的模式，但项目的资历让它没有被评为 Unsafe。"],
      ["Read the flagged lines before installing, and run it somewhere it cannot reach your keys.", "安装前先读被标记的那几行，并在碰不到你密钥的环境里运行。"],
    ],
    [
      ["**Unsafe**", "**Unsafe**\n不安全"],
      ["Serious patterns, such as download-and-execute from an unknown host, a reverse shell or sending credentials off the machine, in a project without the track record to offset them.", "查到严重的模式，比如从陌生主机下载并执行、反弹 shell、把凭证发出本机，而项目没有足以抵消这些的资历。"],
      ["Don't install it on a machine that matters unless you have read every line it runs.", "除非你读过它要运行的每一行，否则别装在重要的机器上。"],
    ],
    [
      ["**Reject**", "**Reject**\n拒收"],
      ["A combination that only makes sense as an attack: piping your secrets to a network tool, or writing a downloaded payload into your shell startup files or cron.", "只有攻击才会这样组合：把你的密钥通过管道交给网络工具，或者把下载来的载荷写进你的 shell 启动文件或 cron。"],
      ["Don't install it.", "别装。"],
    ],
    [
      ["**Unaudited**", "**Unaudited**\n未审核"],
      ["Not graded yet: GitHub has no README for it, or its README has not been fetched or graded yet (the next sync grades it).", "还没有评级：GitHub 上没有它的 README，或者它的 README 还没抓取、还没评级（下一次同步会评）。"],
      ["Treat it as unknown, not as safe.", "当作未知，而不是安全。"],
    ],
  ],
};

const HIGH_RISK = [
  ["*Download and execute from an untrusted host, written in the README's prose:* `curl … | sh`, `wget … | sh`, PowerShell `irm … | iex`. Fetching from the project itself (its GitHub owner, the same repository under another owner after a move or as a fork's upstream, its own website), from the GitHub of a tier 1 or 2 organisation (see the tiers below) or from a well-known installer host does not count, and neither does an example address such as example.com, localhost or a private IP.", "**从不受信任的主机下载并执行（写在 README 正文里）：**`curl … | sh`、`wget … | sh`、PowerShell 的 `irm … | iex`。下载来源是项目自己（它的 GitHub 所有者、迁移后或作为 fork 上游的同名仓库、项目自己的网站）、第 1、2 档组织的 GitHub（分档见下文）或知名安装器主机的，不算；example.com、localhost、内网 IP 这类示例地址也不算。"],
  ["*Remote access:* a reverse shell, or a connection through `/dev/tcp`.", "**远程访问：**反弹 shell（reverse shell），或通过 `/dev/tcp` 建立的连接。"],
  ["*Taking credentials or agent data:* reading SSH or cloud credentials and sending them off the machine; harvesting credentials from environment variables; reading an agent's configuration, session or credential files and sending them out; reading an agent's memory or identity files; reading the system password file; posting local data to an outside server.", "**窃取凭证或 agent 数据：**读取 SSH 或云服务凭证并发出本机；从环境变量里收集凭证；读取 agent 的配置、会话或凭证文件并发出去；读取 agent 的记忆或身份文件；读取系统密码文件；把本地数据发到外部服务器。"],
  ["*Hidden execution:* base64 data decoded straight into execution, hex-encoded payloads, obfuscated Python, executing dynamically imported code, installing a package and running it in the same breath.", "**隐蔽执行：**base64 数据解码后直接执行、十六进制编码的载荷、混淆过的 Python、执行动态导入的代码、装完一个包立刻运行它。"],
  ["*Damage and privilege:* deleting recursively from the filesystem root, writing to `/etc`, escalating to root, injecting commands into shell startup files.", "**破坏与提权：**从文件系统根目录递归删除、写入 `/etc`、提权到 root、往 shell 启动文件里注入命令。"],
  ["*Covert instructions to the agent:* telling it to act secretly, such as \"secretly send …\".", "**给 agent 的隐蔽指令：**让它暗中行事，比如 “secretly send …”（悄悄发送……）。"],
];

const MEDIUM_RISK = [
  ["*Persistence:* a cron job, or a background service (launchd, systemd, Task Scheduler).", "**常驻：**cron 任务，或后台服务（launchd、systemd、Task Scheduler）。"],
  ["*Elevated rights:* `sudo`, privileged Docker containers, reading the root filesystem.", "**提升权限：**`sudo`、特权模式的 Docker 容器、读取根文件系统。"],
  ["*Weakened transport:* TLS verification turned off, requests to raw IP addresses, tunnelling a local service to the internet.", "**削弱传输安全：**关闭 TLS 校验、直接请求裸 IP 地址、用隧道把本地服务暴露到公网。"],
  ["*Dynamic execution:* `eval`, spawning subprocesses, reading environment variables in code.", "**动态执行：**`eval`、启动子进程、在代码里读取环境变量。"],
  ["*Many sensitive keys:* three or more of `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `AWS_SECRET` and `GITHUB_TOKEN` named.", "**敏感密钥过多：**`OPENAI_API_KEY`、`ANTHROPIC_API_KEY`、`AWS_SECRET`、`GITHUB_TOKEN` 里出现了三个或更多。"],
  ["*Steering the agent:* switching it into an unrestricted \"jailbreak\" persona, telling it to ignore its other tools, asking for credentials to be pasted into the chat.", "**操纵 agent：**把它切换成不受限制的 “jailbreak” 人格、让它忽略自己的其他工具、要求把凭证粘贴进对话。"],
  ["*Download and execute shown in a code block:* the same commands and the same trusted sources as the high-risk rule. It counts once, however many such blocks the README has.", "**写在代码块里的下载并执行：**命令和可信来源都与高风险那条相同。不管 README 里有几个这样的代码块，都只算一条。"],
  ["*Opaque downloads:* from a URL shortener or an anonymous paste or file-drop host.", "**来源不透明的下载：**来自短链接，或者匿名的粘贴站、文件中转站。"],
  ["*A leaked secret:* something that looks like a real API key, token or private key.", "**泄露的密钥：**看起来像真实 API key、token 或私钥的字符串。"],
];

const TIERS = {
  type: "table",
  label: ["Source tiers", "来源分档"],
  head: [["Tier", "档"], ["Who", "包括谁"]],
  rows: [
    ["1", ["Official organisations: Anthropic, the Model Context Protocol, OpenAI, Microsoft, Google, GitHub, NVIDIA, Meta, AWS, Azure, LangChain", "官方组织：Anthropic、Model Context Protocol、OpenAI、Microsoft、Google、GitHub、NVIDIA、Meta、AWS、Azure、LangChain"]],
    ["2", ["Known security teams and established projects: SlowMist, Trail of Bits, OpenZeppelin, ConsenSys, Pydantic, Stanford NLP, Salesforce", "知名安全团队和成熟项目：SlowMist、Trail of Bits、OpenZeppelin、ConsenSys、Pydantic、Stanford NLP、Salesforce"]],
    ["3", ["1,000 stars or more, with a license", "1,000 星及以上，且有许可证"]],
    ["4", ["100 stars or more, with a license", "100 星及以上，且有许可证"]],
    ["5", ["Everyone else", "其他所有项目"]],
  ],
};

const DECISION = {
  type: "table",
  label: ["Grade by findings and tier", "按查到的内容和档位定级"],
  minRem: 28,
  head: [["What the rules found", "规则查到了什么"], ["Tiers 1–2", "第 1–2 档"], ["Tier 3", "第 3 档"], ["Tier 4", "第 4 档"], ["Tier 5", "第 5 档"]],
  rows: [
    [["A reject pattern", "一个 Reject 级模式"], "Unsafe", "Reject", "Reject", "Reject"],
    [["Two or more high-risk patterns", "两个及以上高风险模式"], "Caution", "Caution", "Unsafe", "Unsafe"],
    [["One high-risk pattern", "一个高风险模式"], "Caution", "Caution", "Caution", "Unsafe"],
    [["Two or more medium-risk patterns", "两个及以上中风险模式"], "Safe", "Safe", "Caution", "Caution"],
    [["One medium-risk pattern", "一个中风险模式"], "Safe", "Safe", "Safe", "Caution"],
    [["Nothing", "什么都没查到"], "Safe", "Safe", "Safe", "Safe"],
  ],
};

const QUALITY_WEIGHTS = {
  type: "table",
  label: ["Quality score weights", "质量分权重"],
  head: [["Dimension", "维度"], ["Weight", "权重"]],
  rows: [
    [["Agent readiness: install steps, tools, usage, configuration", "Agent 就绪度：安装步骤、工具、用法、配置"], "18%"],
    [["README structure: sections, code examples, navigation", "README 结构：章节、代码示例、导航"], "16%"],
    [["Completeness: README, description, license", "完整度：README、简介、许可证"], "14%"],
    [["Clarity: description, topics, naming", "清晰度：简介、话题标签、命名"], "13%"],
    [["Examples: code examples and activity", "示例：代码示例和活跃度"], "12%"],
    [["Specificity: a clear language, topic and category", "具体性：明确的语言、主题和分类"], "10%"],
    [["Procedural content: step-by-step workflows", "流程内容：分步骤的工作流"], "6%"],
    [["Instruction quality: outputs, constraints, success criteria", "指令质量：输出、约束、成功标准"], "6%"],
    [["Security awareness: permissions, sandboxing, trust boundaries", "安全意识：权限、沙箱、信任边界"], "5%"],
  ],
};

const SECTIONS = [
  {
    id: GRADES_ANCHOR,
    title: ["The grades", "各个等级"],
    blocks: [GRADES],
  },
  {
    id: "what-we-read",
    title: ["What we read", "我们读什么"],
    blocks: [
      { type: "ul", items: [
        ["**The README**, its first 15,000 characters, as GitHub serves it.", "**README**：GitHub 返回的 README 的前 15,000 个字符。"],
        ["**The project's standing**: owner, stars, license and homepage.", "**项目本身的情况**：所有者、星数、许可证和主页。"],
      ] },
      { type: "p", text: ["We do **not** run the code, and we do not read the repository's other files. A grade describes what the README tells you, or your agent, to do.", "我们**不**运行代码，也不读仓库里的其他文件。评级描述的是 README 让你（或你的 agent）去做什么。"] },
      { type: "p", text: ["Grades refresh during the catalog sync, every 8 hours. A repository is graded again when its README, stars, license or homepage change. When we change the rules, the whole catalog is graded again, and every grade is stored with the version of the rules that produced it.", "评级随目录同步刷新，每 8 小时一次。仓库的 README、星数、许可证或主页有变化，就会重新评级。规则一改，整个目录都会重新评级；每个评级都和产生它的那一版规则一起保存。"] },
    ],
  },
  {
    id: "what-we-look-for",
    title: ["What we look for", "我们查什么"],
    blocks: [
      { type: "p", text: [`${RULE_COUNT} rules in three levels.`, `${RULE_COUNT} 条规则，分三级。`] },
      { type: "h3", text: ["Reject (2)", "Reject 级（2 条）"] },
      { type: "ul", items: [
        ["Secrets piped to a network tool.", "把密钥通过管道交给网络工具。"],
        ["A downloaded payload written into a shell startup file or a cron job.", "把下载来的载荷写进 shell 启动文件或 cron 任务。"],
      ] },
      { type: "h3", text: ["High risk (21)", "高风险（21 条）"] },
      { type: "ul", items: HIGH_RISK },
      { type: "h3", text: ["Medium risk (19)", "中风险（19 条）"] },
      { type: "ul", items: MEDIUM_RISK },
    ],
  },
  {
    id: "source-tiers",
    title: ["How the source changes the grade", "来源如何影响评级"],
    blocks: [
      { type: "p", text: ["The same instruction means more from an unknown account than from Anthropic's own repository. Every project falls into one of five tiers:", "同一条指令，出自一个陌生账号，比出自 Anthropic 自己的仓库更值得警惕。每个项目都归入五档之一："] },
      TIERS,
      { type: "p", text: ["What the rules found and the tier set the grade together:", "规则查到的内容和项目所在的档位，一起决定评级："] },
      DECISION,
    ],
  },
  {
    id: "what-we-dont-count",
    title: ["What we don't count", "哪些不算"],
    blocks: [
      { type: "p", text: ["Security tools are the projects most likely to print an attack in their README, as the thing they block. To avoid grading the warning as the threat, we leave out:", "最常在 README 里写出攻击手法的，恰恰是安全工具：那是它们要拦截的东西。为了不把警告当成威胁，下面这些不计入："] },
      { type: "ul", items: [
        ["quoted examples, and matches introduced as an example (\"such as\", \"e.g.\", \"for example\");", "引号里的示例，以及用 “such as”、“e.g.”、“for example” 这类说法引出的匹配；"],
        ["negated advice (\"never paste your API key into a chat\");", "否定式的建议（“never paste your API key into a chat”，即千万别把 API key 粘贴进对话）；"],
        ["table rows, and lines that say what a tool blocks, detects, warns about or scans for, such as a deny list;", "表格行，以及说明工具会拦截、检测、警告或扫描什么的行，比如拒绝清单（deny list）；"],
        ["example addresses as the source of a download-and-execute command: example.com, localhost, a private IP;", "下载即执行命令里的示例地址：example.com、localhost、内网 IP；"],
        CODE_BLOCKS.notCounted,
      ] },
      { type: "p", text: ["Downloads from URL shorteners and paste hosts are an exception too: the opaque host is the whole signal, so only a negation or an explicit example clears them.", "从短链接和粘贴站下载也是例外：来源不透明的主机本身就是全部信号，所以只有否定句或明确的示例能让它不计入。"] },
    ],
  },
  {
    id: "known-limits",
    title: ["Known limits", "已知局限"],
    blocks: [
      { type: "ul", items: [
        ["**It reads the README, not the code.** A script that does something the README never mentions is not caught.", "**它读的是 README，不是代码。**脚本做了 README 里从没提过的事，查不出来。"],
        CODE_BLOCKS.limit,
        ["**Rules miss what they were not written for,** and still flag some honest projects. If you think a grade is wrong, open an issue (link below) with the skill's page.", "**规则会漏掉它们没覆盖到的情况，**也仍会误标一些正当的项目。如果你觉得某个评级错了，请附上这个 skill 的页面开一个 issue（链接见下文）。"],
        ["**Track record softens grades.** A popular, licensed project gets the benefit of the doubt. Popularity is not proof: stars can be bought, and projects change hands.", "**资历会让评级变宽松。**热门、有许可证的项目，存疑时会从宽判定。但热门不是证明：星可以买，项目也会易手。"],
        ["**A grade is not an audit.** For anything that will run on your machine with your keys, read what it runs.", "**评级不是审计。**任何要在你的机器上、拿着你的密钥运行的东西，都要读一读它到底运行什么。"],
      ] },
    ],
  },
  {
    id: "quality-score",
    title: ["The quality score", "质量分"],
    blocks: [
      { type: "p", text: ["Separate from the security grade, each project gets a quality score from 0 to 100: how well its README and metadata prepare a person or an agent to use it. Weights as of October 2026:", "和安全评级分开，每个项目还有一个 0 到 100 的质量分，衡量它的 README 和元数据能不能让人或 agent 顺利用上它。权重（截至 2026 年 10 月）："] },
      QUALITY_WEIGHTS,
      { type: "p", text: ["The weighted total is spread across the 0–100 range with one fixed curve. Without a README, the weight moves to the metadata dimensions.", "加权总分再经过一条固定的曲线，铺开到 0–100 的范围。没有 README 时，权重转到基于元数据的维度上。"] },
    ],
  },
  {
    id: "how-lists-are-ordered",
    title: ["How lists are ordered", "列表怎么排序"],
    blocks: [
      { type: "p", text: ["Rankings use a separate score that blends adoption, upkeep and quality: stars (15%), forks (8%), the author's followers (6%), resolved issues (10%), commits (8%), recency (11%), the quality score above (25%), recent star momentum (7%), size (5%) and a bonus for specialised domains (5%). Star, fork and follower counts are log-scaled, so a few huge projects cannot crowd out the rest.", "排名用的是另一个分数，综合了采用度、维护情况和质量：星数（15%）、fork 数（8%）、作者的关注者数（6%）、已解决的 issue（10%）、提交数（8%）、最近更新（11%）、上面的质量分（25%）、近期涨星势头（7%）、体量（5%），以及细分领域加分（5%）。星数、fork 数和关注者数都取对数，少数超大项目因此挤不掉其他项目。"] },
    ],
  },
  {
    id: "disagree",
    title: ["Disagree with a grade?", "对评级有异议？"],
    blocks: [
      { type: "p", text: ["Open an issue at [github.com/zhuyansen/agent-skills-hub](https://github.com/zhuyansen/agent-skills-hub/issues) with the skill's page and the line you think was misread. Rule changes apply to the whole catalog at once, never to a single project.", "请在 [github.com/zhuyansen/agent-skills-hub](https://github.com/zhuyansen/agent-skills-hub/issues) 开一个 issue，附上这个 skill 的页面，以及你认为被误读的那一行。规则改动一次作用于整个目录，从不只针对某一个项目。"] },
    ],
  },
];

export const HOW_WE_GRADE = {
  h1: ["How we grade skills", "我们怎么给 skill 评级"],
  updated: ["Last updated: ", "最后更新："],
  crumbs: { home: ["Home", "首页"], here: [HOW_WE_GRADE_LINK.en, HOW_WE_GRADE_LINK.zh] },
  lead: [
    { type: "p", text: ["Every skill, MCP server and agent tool on Agent Skills Hub that has a README gets a **security grade**: Safe, Caution, Unsafe or Reject. It answers one question: does the README that a person, or an agent, reads before installing ask for something risky, and how established is the project that asks for it?", "Agent Skills Hub 上每个有 README 的 skill、MCP 服务器和 agent 工具，都有一个**安全评级**：Safe、Caution、Unsafe 或 Reject。它只回答一个问题：人或 agent 在安装前读的那份 README，有没有要求做有风险的事，而提出要求的项目又有多成熟？"] },
    { type: "p", text: ["Grades come from published rules, not from a model's judgement, so the same README always gets the same grade. You can grade any public GitHub repository yourself, free and without signing up, at [agentskillshub.top/analyzer/](/analyzer/).", "评级来自公开的规则，而不是模型的判断，所以同一份 README 总是得到同样的评级。任何公开的 GitHub 仓库，你都可以在 [agentskillshub.top/analyzer/](/analyzer/) 自己评级，免费，也不用注册。"] },
  ],
  sections: SECTIONS,
};

/** The text in `lang`: a pair is [english, chinese], a plain string reads the same in both. */
export function pick(text, lang) {
  if (typeof text === "string") return text;
  return lang === "zh" ? text[1] : text[0];
}

// **bold** | *italic* | `code` | [label](href) | line break — no nesting, which this text never needs.
const INLINE = /\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)|\n/g;

function tokenOf(m) {
  if (m[1] !== undefined) return { kind: "strong", text: m[1] };
  if (m[2] !== undefined) return { kind: "em", text: m[2] };
  if (m[3] !== undefined) return { kind: "code", text: m[3] };
  if (m[4] !== undefined) return { kind: "link", text: m[4], href: m[5] };
  return { kind: "br", text: "" };
}

/** Splits one line of inline markup into plain-text and formatted tokens, in order. */
export function inlineTokens(text) {
  const tokens = [];
  let last = 0;
  for (const m of text.matchAll(INLINE)) {
    if (m.index > last) tokens.push({ kind: "text", text: text.slice(last, m.index) });
    tokens.push(tokenOf(m));
    last = m.index + m[0].length;
  }
  if (last < text.length) tokens.push({ kind: "text", text: text.slice(last) });
  return tokens;
}
