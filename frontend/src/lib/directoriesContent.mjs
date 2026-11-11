/**
 * The text of /agent-skills-directories/, English and Chinese side by side, built from the
 * entries in directoryEntries.mjs. Both renderers read it, through the parts all long-form pages
 * share (proseContent.mjs): the static generator (scripts/generate-directories-page.mjs) and the
 * React page (src/pages/DirectoriesPage.tsx).
 *
 * The rules the owner set for this page: facts only from each site's own pages (see
 * directoryEntries.mjs); no superlatives about anyone, us included; sizes carry their unit and
 * are never ranked; paid placements are stated the same way for everyone, our Enterprise audits
 * included; agentskillshub.dev is named as a different site. Our catalog count is never written
 * here: TOTAL is filled in from the build's count (directoriesText()).
 * scripts/directories-content.test.mjs checks these rules.
 */
import { DIRECTORY_ENTRIES } from "./directoryEntries.mjs";
import { COMPARED_COUNT, DIRECTORIES_HEADLINE, DIRECTORIES_LINK, FACTS_READ_ON } from "./directoriesMeta.mjs";
import { HOW_WE_GRADE_PATH, RULE_COUNT } from "./howWeGradeMeta.mjs";
import { pick } from "./proseContent.mjs";

/** Where our catalog count goes in the text; directoriesText() puts the build's count there. */
export const TOTAL = "{total}";
/** What takes TOTAL's place while the React page has no count yet. */
export const UNKNOWN_TOTAL = "…";

/**
 * Our entry says "About half of them are graded". That holds while the graded share of the
 * catalog stays in this band; scripts/generate-directories-page.mjs warns when the build's
 * counts leave it.
 */
export const ABOUT_HALF = { min: 0.4, max: 0.6 };

const THOUSAND = 1000;

/** 267431 → "267,000+", the way the home page states the count (plusThousands in scripts/home-counts.mjs). */
export function countText(n) {
  return `${(Math.floor(n / THOUSAND) * THOUSAND).toLocaleString("en-US")}+`;
}

/* ── How a fact becomes a line ─────────────────────────────────────────────── */

const LANGS = ["en", "zh"];
/** A Text whose English and Chinese come from `make(lang)`. */
const both = (make) => LANGS.map(make);

const PUNCT = {
  en: { label: ":", gap: " ", stop: ".", join: ", " },
  zh: { label: "：", gap: "", stop: "。", join: "、" },
};

/** Every directory's section states these, in this order. */
const FIELDS = [
  ["runBy", ["Run by", "运营方"]],
  ["lists", ["Lists", "收录"]],
  ["size", ["Stated size", "自报规模"]],
  ["security", ["Security result", "安全结果"]],
  ["ranking", ["Ranking", "排序"]],
  ["listing", ["Listing and paid options", "上架与付费项"]],
  ["agents", ["Agent access", "Agent 接入"]],
  ["openness", ["Openness", "开放程度"]],
  ["updates", ["Updates", "更新"]],
  ["languages", ["Languages", "语言"]],
];
export const FIELD_KEYS = FIELDS.map(([key]) => key);
const LABEL = Object.fromEntries(FIELDS);

/** The comparison table's columns after the directory, from each fact's brief. */
const TABLE_FIELDS = ["lists", "size", "security", "listing", "agents", "openness"];

/**
 * Narrower than this, the table scrolls inside its box, as on phones. On laptop and desktop
 * screens its box widens into the page margins (`wide`), so all seven columns show at once.
 */
const TABLE_MIN_REM = 45;

/** A fact as its section states it: the brief, then the rest. */
function factText(fact, lang) {
  const { stop, gap } = PUNCT[lang];
  const brief = `${pick(fact.brief, lang)}${stop}`;
  return fact.more ? `${brief}${gap}${pick(fact.more, lang)}` : brief;
}

/** "**Label:** text", or "**标签：**text". */
function labelled(label, text, lang) {
  const { label: colon, gap } = PUNCT[lang];
  return `**${pick(label, lang)}${colon}**${gap}${text}`;
}

const fieldItem = (entry, key) => both((lang) => labelled(LABEL[key], factText(entry[key], lang), lang));

const GOOD_FOR = ["Good for", "适合"];
const goodForText = (entry) => both((lang) => labelled(GOOD_FOR, pick(entry.goodFor, lang), lang));

const SOURCES = [`Sources, read ${FACTS_READ_ON}`, `来源（${FACTS_READ_ON} 读取）`];
/** "https://www.skills.sh/docs/api" → "www.skills.sh/docs/api": a source's address as its link text. */
const shortUrl = (url) => url.replace(/^https:\/\//, "").replace(/\/$/, "");

function sourcesText(entry) {
  return both((lang) => {
    const links = entry.sources.map((url) => `[${shortUrl(url)}](${url})`).join(PUNCT[lang].join);
    return labelled(SOURCES, links, lang);
  });
}

/* ── The directories, grouped and ordered ──────────────────────────────────── */

const KINDS = [
  {
    kind: "skills",
    id: "skill-directories",
    title: ["Skill directories", "Skill 目录"],
    intro: ["Directories that list agent skills, often alongside MCP servers and other tools.", "以 agent skill 为主的目录，很多也收录 MCP 服务器和其他工具。"],
  },
  {
    kind: "mcp",
    id: "mcp-server-directories",
    title: ["MCP server directories", "MCP 服务器目录"],
    intro: ["Directories that list MCP servers first.", "以 MCP 服务器为主的目录。"],
  },
  {
    kind: "official",
    id: "official-marketplaces",
    title: ["Official marketplaces", "官方市场"],
    intro: ["Marketplaces run by the maker of an agent platform, for that platform.", "由 agent 平台自己运营、服务自家平台的市场。"],
  },
];
const KIND_ORDER = KINDS.map(({ kind }) => kind);

function byKindThenDomain(a, b) {
  const kind = KIND_ORDER.indexOf(a.kind) - KIND_ORDER.indexOf(b.kind);
  if (kind) return kind;
  return a.domain < b.domain ? -1 : 1;
}

/** The entries in page order: skill directories, MCP server directories, official marketplaces, each by domain. */
export const ORDERED_ENTRIES = [...DIRECTORY_ENTRIES].sort(byKindThenDomain);

function entryBlocks(entry) {
  return [
    { type: "h3", id: entry.id, text: entry.heading },
    { type: "ul", items: FIELD_KEYS.map((key) => fieldItem(entry, key)) },
    { type: "p", text: goodForText(entry) },
    { type: "p", text: sourcesText(entry) },
  ];
}

function kindSection({ kind, id, title, intro }) {
  const entries = ORDERED_ENTRIES.filter((entry) => entry.kind === kind);
  return { id, title, blocks: [{ type: "p", text: intro }, ...entries.flatMap(entryBlocks)] };
}

/** A row's first cell: the site's address, linked, over its name when the address is not its name. */
function siteCell(entry) {
  return both((lang) => {
    const link = `[${entry.domain}](${entry.home})`;
    return entry.tag ? `${link}\n${pick(entry.tag, lang)}` : link;
  });
}

const tableRow = (entry) => [siteCell(entry), ...TABLE_FIELDS.map((key) => entry[key].brief)];

const COMPARISON = {
  type: "table",
  label: ["Directories compared", "目录对比"],
  minRem: TABLE_MIN_REM,
  wide: true,
  head: [["Directory", "目录"], ...TABLE_FIELDS.map((key) => LABEL[key])],
  rows: ORDERED_ENTRIES.map(tableRow),
};

/* ── The rest of the page ──────────────────────────────────────────────────── */

const DISCLOSURE = {
  type: "note",
  title: ["Disclosure", "声明"],
  items: [
    [`Agent Skills Hub (agentskillshub.top) runs this page and is one of the ${COMPARED_COUNT} directories compared.`, `本页由 Agent Skills Hub（agentskillshub.top）制作，它本身也是对比的 ${COMPARED_COUNT} 个目录之一。`],
    [`The facts come from each directory's own pages, read on ${FACTS_READ_ON}. Every row of the table links to the site, and every directory's section links the pages it draws on.`, `所有事实都来自各目录自己的页面，读取于 ${FACTS_READ_ON}。表格每一行都链接到对应网站，每个目录的小节都附上了所依据页面的链接。`],
    ["No one paid to be listed here, or for their place on this page.", "没有任何网站为出现在本页或排在哪个位置付过钱。"],
    ["agentskillshub.top is not agentskillshub.dev. They are different sites; the second also calls itself “Agent Skills Hub”.", "agentskillshub.top 不是 agentskillshub.dev。这是两个不同的网站，后者也自称 “Agent Skills Hub”。"],
  ],
};

const LEAD = [
  DISCLOSURE,
  { type: "p", text: [`In short: Agent Skills Hub is for broad discovery across GitHub, with a first-pass grade from ${RULE_COUNT} published rules on each popular repository. To vet one skill before you install it, look it up where its contents are checked: the skills.sh partner results, ClawHub, Tessl or Skillstore, and Glama for MCP servers.`, `一句话：Agent Skills Hub 适合在整个 GitHub 范围里找工具，每个热门仓库都有按 ${RULE_COUNT} 条公开规则给出的初筛评级。装某个 skill 之前想细查，去会检查其内容的目录：skills.sh 的合作方结果、ClawHub、Tessl 或 Skillstore；MCP 服务器看 Glama。`] },
  { type: "p", text: [`Agent skills and MCP servers are listed on many sites. They differ in what they list, how they count, what their security check reads and what they charge for. This page sets those facts side by side for ${COMPARED_COUNT} directories, taken from each site's own pages.`, `收录 agent skill 和 MCP 服务器的网站很多。它们收录的东西不同，计数方式不同，安全检查读的内容不同，收费的项目也不同。本页根据各站自己的页面，把 ${COMPARED_COUNT} 个目录的这些事实放在一起对比。`] },
  { type: "p", text: ["For each directory we record:", "每个目录我们记录这几项："] },
  { type: "ul", items: [
    ["**What it lists**: skills, MCP servers, plugins or whole GitHub repositories.", "**收录什么**：skill、MCP 服务器、插件，还是整个 GitHub 仓库。"],
    ["**Stated size and its unit.** Each site counts its own unit, so the numbers do not rank the sites.", "**自报规模和单位。**各站数的单位不同，所以这些数字不能用来给网站排高低。"],
    ["**Security result per item**: whether each listing shows one, and what the check reads.", "**逐条安全结果**：每个条目有没有，检查读的是什么。"],
    ["**How items get listed**, paid options included.", "**怎么上架**，包括付费选项。"],
    ["**Agent access**: whether an agent can search it through MCP, a CLI or an API.", "**Agent 接入**：agent 能不能通过 MCP、CLI 或 API 直接搜。"],
    ["**Openness**: open-source code and data licenses.", "**开放程度**：代码是否开源，数据用什么许可。"],
  ] },
  { type: "p", text: [`Agent Skills Hub is a broad index of GitHub repositories: skills, MCP servers and agent tools. Each popular one gets a first-pass security grade from ${RULE_COUNT} published rules that read its README. Several directories below check more of each item than we do, and their sections say how.`, `Agent Skills Hub 是一个覆盖面广的 GitHub 仓库索引，收录 skill、MCP 服务器和 agent 工具。热门仓库都有一个初筛用的安全评级，来自 ${RULE_COUNT} 条读 README 的公开规则。下面有几个目录对每个条目查得比我们更深，各自的小节里写了怎么查。`] },
  { type: "p", text: ["“Not stated” means we did not find it on the pages we read. It does not prove the thing doesn't exist.", "“未说明” 表示我们读过的页面上没找到，不代表一定没有。"] },
];

const SIDE_BY_SIDE = {
  id: "side-by-side",
  title: ["Side by side", "对比一览"],
  blocks: [
    { type: "p", text: ["One row per directory, in the order of the sections below: skill directories, then MCP server directories, then official marketplaces, each group in alphabetical order of domain. Each address links to the site. Sizes are each site's own numbers, in its own unit.", "每行一个目录，顺序和下面各小节一致：先是 skill 目录，再是 MCP 服务器目录，然后是官方市场，每组内按域名字母顺序排列。每个域名都链接到对应网站。规模是各站自报的数字和单位。"] },
    COMPARISON,
  ],
};

const HOW_TO_CHOOSE = {
  id: "how-to-choose",
  title: ["How to choose", "怎么选"],
  blocks: [
    { type: "ul", items: [
      ["**To vet one skill before you install it**, look it up where its contents are checked: the skills.sh partner results, ClawHub, Tessl or Skillstore. For an MCP server, Glama runs it in a sandbox. Then read what it will run on your machine.", "**装某个 skill 之前想细查**，就去会检查其内容的目录查：skills.sh 的合作方结果、ClawHub、Tessl 或 Skillstore。MCP 服务器可以看 Glama 在沙箱里运行的结果。然后还是要自己读一遍它会在你机器上运行什么。"],
      ["**For broad discovery under published rules**, use a wide index such as Agent Skills Hub, and treat its grade as a first pass, not an audit.", "**想按公开规则大范围找工具**，用 Agent Skills Hub 这类覆盖面广的索引，把它的评级当作初筛，而不是审计。"],
      ["**If you use one agent platform**, start with its own marketplace: Anthropic's for Claude, ClawHub for OpenClaw.", "**如果你固定用一个 agent 平台**，先看它自己的市场：Claude 看 Anthropic 的，OpenClaw 看 ClawHub。"],
      ["**If an agent will do the searching**, pick a directory with an MCP server, a CLI or an API, and check whether it needs a key.", "**如果让 agent 去搜**，挑有 MCP 服务器、CLI 或 API 的目录，并看清要不要 key。"],
      ["**Check what payment changes.** Some sites sell boosts, sponsor slots, badges or publishing without review. Read what each one says payment does and doesn't change.", "**看清付费改变了什么。**有的网站出售加权、赞助位、徽章或免审上架。看各站自己怎么说：付费改变什么，不改变什么。"],
      ["**Check the dates.** On some sites, the scan or sync date on a listing is months old.", "**看日期。**有些网站条目上的扫描或同步日期，已经是几个月前的了。"],
    ] },
  ],
};

const SECURITY_ANSWER = [
  ["**skills.sh**: pass, warn or fail from partner scanners (Gen Agent Trust Hub, Socket, Snyk), which check the skill and its contents.", "**skills.sh**：合作扫描方（Gen Agent Trust Hub、Socket、Snyk）给出 pass、warn 或 fail，检查 skill 及其内容。"],
  ["**ClawHub**: an audit status and a risk level for each release, from SkillSpector, A.I.G and ClawScan.", "**ClawHub**：每个版本都有审计状态和风险等级，来自 SkillSpector、A.I.G 和 ClawScan。"],
  ["**Tessl**: a Snyk-powered result on each skill.", "**Tessl**：每个 skill 都有 Snyk 提供的结果。"],
  ["**Skillstore**: deterministic inspection plus semantic review, with extra review for skills that ship scripts.", "**Skillstore**：确定性检查加语义审查，带脚本的 skill 多审一轮。"],
  ["**Skills Directory**: an A to F grade from a static scan of SKILL.md.", "**Skills Directory**：对 SKILL.md 做静态扫描，给 A 到 F。"],
  ["**SkillsLLM**: PASS, WARNING or FAIL from Semgrep, npm audit, pip-audit and prompt-injection checks.", "**SkillsLLM**：用 Semgrep、npm audit、pip-audit 和提示注入检查，给 PASS、WARNING 或 FAIL。"],
  ["**Skillget**: a Pass or Fail audit of health, code and permissions, with no method page.", "**Skillget**：检查健康度、代码和权限，给 Pass 或 Fail，没有方法说明页。"],
  [`**Agent Skills Hub**: Safe, Caution, Unsafe or Reject from ${RULE_COUNT} published rules applied to the first 15,000 characters of the README, without running code. The rules are at [${HOW_WE_GRADE_PATH}](${HOW_WE_GRADE_PATH}).`, `**Agent Skills Hub**：用 ${RULE_COUNT} 条公开规则读 README 的前 15,000 个字符，给出安全、注意、风险或拒绝，不运行代码。规则见[评级方法](${HOW_WE_GRADE_PATH})页。`],
  ["**Glama**: no security grade, but it runs MCP servers in a sandbox and shows “Risky” findings on the listing.", "**Glama**：没有安全等级，但会在沙箱里运行 MCP 服务器，把 “Risky” 的发现显示在条目页上。"],
  ["**Anthropic**: a security scan and a review before listing, with no grade on each item; its docs say “Verification isn't a security audit.”", "**Anthropic**：上架前做安全扫描和审核，条目上没有评级；它的文档自己说，验证不等于安全审计（“Verification isn't a security audit.”）。"],
  ["**Skillselion** and **mcp.so** show results from the partners skills.sh uses. **Claude Marketplaces** shows none, and **agentskillshub.dev** shows letters it calls catalog metadata.", "**Skillselion** 和 **mcp.so** 显示的是 skills.sh 那几家合作方的结果。**Claude Marketplaces** 没有安全结果；**agentskillshub.dev** 的字母等级，它自己说是目录元数据。"],
];

const PAID_ANSWER = [
  ["**Agent Skills Hub**: no paid placement. We sell Enterprise audits on a [separate page](/enterprise/).", "**Agent Skills Hub**：没有付费排位。我们在[另一个页面](/enterprise/)出售企业审计。"],
  ["**Glama**: Boost at $49 a month per listing and sponsored cards at $200 a month per category; it says payment does not affect its scores.", "**Glama**：Boost 每个条目每月 $49，赞助卡片每个分类每月 $200；它说付费不影响评分。"],
  ["**mcp.so**: $39 once to publish without review, with a “Verified” badge and priority placement; sponsor slots at $699 and $1,299 a month.", "**mcp.so**：一次性 $39 免审上线，附 “Verified” 徽章和优先展示；赞助位每月 $699 和 $1,299。"],
  ["**Skills Directory**: Pro at $19 once or $4 a month; sponsor slots at $399 and $999 a month. Prices may differ by country.", "**Skills Directory**：Pro 一次性 $19 或每月 $4；赞助位每月 $399 和 $999。不同国家的价格可能不同。"],
  ["**SkillsLLM**: featured placement at $49 or $99 per 30 days, for listings that pass its scan.", "**SkillsLLM**：推荐位 30 天 $49 或 $99，限扫描通过的条目。"],
  ["**Claude Marketplaces**: $4 for priority review; sponsor slots at $1,000 and $1,200 a month.", "**Claude Marketplaces**：加急审核 $4；赞助位每月 $1,000 和 $1,200。"],
  ["**Skillselion**: sponsored guide slots from $29 a month, which it says do not change search ranking.", "**Skillselion**：赞助位每月 $29 起，它说不影响搜索排名。"],
  ["**Skillstore**: audits for vendors, the first one free; it says paying never buys a passing result.", "**Skillstore**：向厂商出售审计，首次免费；它说付费买不来通过。"],
  ["**agentskillshub.dev**: paid submissions and paid reviews, price not stated.", "**agentskillshub.dev**：有付费提交和付费审核，价格未说明。"],
  ["**Anthropic**: submitting needs a paid Claude plan; no listing fee is stated.", "**Anthropic**：提交需要付费的 Claude 套餐；没说要上架费。"],
  ["**Tessl**: publishing is free; reviews and evals use credits, and the Team plan costs $100 a month.", "**Tessl**：发布免费；审核和评测消耗额度，Team 版每月 $100。"],
  ["**skills.sh**, **ClawHub** and **Skillget**: no paid tier stated.", "**skills.sh**、**ClawHub** 和 **Skillget**：没写付费项。"],
];

const AGENT_ANSWER = [
  ["**No key or token needed**: ClawHub (read API), Skillselion (API and MCP server), Skillstore (MCP server), Tessl (search through its MCP server) and Agent Skills Hub (MCP server and CLI). ClawHub and Tessl also have a CLI.", "**不需要 key 或令牌**：ClawHub（读 API）、Skillselion（API 和 MCP 服务器）、Skillstore（MCP 服务器）、Tessl（通过 MCP 服务器搜索）和 Agent Skills Hub（MCP 服务器和 CLI）。ClawHub 和 Tessl 也有 CLI。"],
  ["**A key or token needed**: Glama (API key, attribution required), Skills Directory (API key, 100 requests a day free; MCP for Pro members) and skills.sh (a Vercel OIDC token).", "**需要 key 或令牌**：Glama（API key，要求注明出处）、Skills Directory（API key，免费每天 100 次；Pro 会员有 MCP）和 skills.sh（Vercel 的 OIDC 令牌）。"],
  ["**A public API and CLI, key not stated**: Skillget, 60 requests per 15 minutes.", "**有公开 API 和 CLI，没说要不要 key**：Skillget，每 15 分钟 60 次。"],
  ["**Other routes**: Anthropic's catalog is a public file on GitHub, and Claude Marketplaces has an llms.txt.", "**其他途径**：Anthropic 的目录是 GitHub 上的一个公开文件；Claude Marketplaces 有 llms.txt。"],
  ["**Not stated**: SkillsLLM, mcp.so and agentskillshub.dev.", "**未说明**：SkillsLLM、mcp.so 和 agentskillshub.dev。"],
];

/** The FAQ question readers ask about size. The answer explains why it has none; the test lets this one line say "largest". */
export const SIZE_QUESTION = ["Which directory is the largest?", "哪个目录最大？"];

const FAQ = {
  id: "faq",
  title: ["FAQ", "常见问题"],
  blocks: [
    { type: "h3", text: ["Which directories check skills for security, and how?", "哪些目录会给 skill 做安全检查，怎么查？"] },
    { type: "ul", items: SECURITY_ANSWER },
    { type: "p", text: ["A README check can cover many repos. A scan of the skill's contents, or a sandbox run, reads more of each one.", "读 README 的检查能覆盖很多仓库；扫描 skill 的内容或在沙箱里运行，对每一个看得更多。"] },
    { type: "h3", text: ["Is agentskillshub.top the same as agentskillshub.dev?", "agentskillshub.top 和 agentskillshub.dev 是同一个网站吗？"] },
    { type: "p", text: ["No. They are two different sites. agentskillshub.top is Agent Skills Hub, which runs this page. agentskillshub.dev is not run by us, though its llms.txt also gives its name as “Agent Skills Hub”. It lists 1,220 entries, and its A–F letters are, in its own words, “catalog metadata, not proof of a completed security audit”.", "不是，这是两个不同的网站。agentskillshub.top 是 Agent Skills Hub，也就是本页的制作方。agentskillshub.dev 不是我们运营的，不过它的 llms.txt 里站名也写作 “Agent Skills Hub”。它收录 1,220 个条目；按它自己的说法，它的 A–F 字母等级只是目录元数据，不代表做过安全审计（“catalog metadata, not proof of a completed security audit”）。"] },
    { type: "h3", text: SIZE_QUESTION },
    { type: "p", text: [`Their numbers can't be ranked, because each site counts something different. Agent Skills Hub counts GitHub repositories (${TOTAL}), general AI tools included. Skills Directory counts skills (717,866 on its home page). Glama counts MCP servers (118,148). Anthropic counts plugins (529). skills.sh shows 1,292,103 with no unit. Several sites also state different numbers on different pages.`, `这些数字没法排高低，因为每个网站数的东西不一样。Agent Skills Hub 数的是 GitHub 仓库（${TOTAL}），包括通用 AI 工具；Skills Directory 数的是 skill（首页写 717,866）；Glama 数的是 MCP 服务器（118,148）；Anthropic 数的是插件（529）；skills.sh 显示 1,292,103，没写单位。还有几个网站在不同页面上写的数字不一样。`] },
    { type: "p", text: ["A count says little about whether a directory has what you need. Search each one for the tool you want and compare what comes back.", "数字大小说明不了一个目录里有没有你要的东西。拿你要找的工具去各站搜一搜，比比搜出来的结果。"] },
    { type: "h3", text: ["Do any of them charge for listings or placement?", "有没有目录对上架或排位收费？"] },
    { type: "ul", items: PAID_ANSWER },
    { type: "h3", text: ["Can AI agents search them through MCP, CLI or API?", "AI agent 能通过 MCP、CLI 或 API 搜索这些目录吗？"] },
    { type: "ul", items: AGENT_ANSWER },
  ],
};

const SMITHERY = [
  "Smithery (smithery.ai) could be read, but its role has changed. Its site says it is “now part of Arcade”, and: “On October 31, 2026, we're shutting down Smithery's connection management services.” Its API, CLI, SDKs and accounts stopped that day, and “Smithery will remain as a public (non-proxied) MCP registry.” Its servers page lists “214 servers”. We left it out of the comparison. Sources: [smithery.ai/future](https://smithery.ai/future), [smithery.ai/servers](https://smithery.ai/servers).",
  "Smithery（smithery.ai）能读取，但它的角色变了。网站上写着它现在是 Arcade 的一部分（“now part of Arcade”），并且从 2026 年 10 月 31 日起关闭连接管理服务（“On October 31, 2026, we're shutting down Smithery's connection management services.”）。它的 API、CLI、SDK 和账号在那天停用，之后只保留一个公开、不经代理的 MCP 注册表（“Smithery will remain as a public (non-proxied) MCP registry.”）。服务器页列出 “214 servers”。我们没把它放进对比。来源：[smithery.ai/future](https://smithery.ai/future)、[smithery.ai/servers](https://smithery.ai/servers)。",
];

const NOT_READ = {
  id: "not-compared",
  title: ["Directories we could not read", "没能读取的目录"],
  blocks: [
    { type: "p", text: [`We could not read these sites automatically on ${FACTS_READ_ON}, so this page makes no claims about them:`, `${FACTS_READ_ON} 我们没能自动读取下面这些网站，所以本页不对它们做任何描述：`] },
    { type: "ul", items: [
      ["SkillsMP (skillsmp.com)", "SkillsMP（skillsmp.com）"],
      ["PulseMCP (pulsemcp.com)", "PulseMCP（pulsemcp.com）"],
      "mcpservers.org",
      "cursor.directory",
      ["LobeHub's site (lobehub.com)", "LobeHub 的网站（lobehub.com）"],
    ] },
    { type: "p", text: SMITHERY },
  ],
};

const SOURCES_SECTION = {
  id: "sources",
  title: ["Sources and last checked", "来源与核对日期"],
  blocks: [
    { type: "ul", items: [
      ["Every fact on this page comes from the directory's own public pages, docs, llms.txt, GitHub repositories or npm packages. Each directory's section links the pages it draws on.", "本页每条事实都来自该目录自己的公开页面、文档、llms.txt、GitHub 仓库或 npm 包。每个目录的小节都附上了所依据页面的链接。"],
      [`Every page was read on ${FACTS_READ_ON}, without signing in. We left out the visitor counts and SEO metrics some sites print about themselves.`, `所有页面都在 ${FACTS_READ_ON} 读取，没有登录。有些网站会公布自己的访问量或 SEO 指标，我们没有收录。`],
      ["Sites change often. If something here is wrong or out of date, open an issue at [github.com/zhuyansen/agent-skills-hub](https://github.com/zhuyansen/agent-skills-hub/issues) with the page that shows it.", "网站变化很快。如果这里有错或者过时，请在 [github.com/zhuyansen/agent-skills-hub](https://github.com/zhuyansen/agent-skills-hub/issues) 开一个 issue，附上能说明问题的页面。"],
    ] },
    { type: "p", text: [`**Last checked:** ${FACTS_READ_ON}.`, `**核对日期：**${FACTS_READ_ON}。`] },
  ],
};

/** The whole page, with TOTAL where our catalog count goes. */
export const DIRECTORIES_TEXT = {
  h1: [DIRECTORIES_HEADLINE.en, DIRECTORIES_HEADLINE.zh],
  updated: ["Last checked: ", "核对日期："],
  crumbs: { home: ["Home", "首页"], here: [DIRECTORIES_LINK.en, DIRECTORIES_LINK.zh] },
  lead: LEAD,
  sections: [SIDE_BY_SIDE, ...KINDS.map(kindSection), HOW_TO_CHOOSE, FAQ, NOT_READ, SOURCES_SECTION],
};

/** `node` with every TOTAL in its strings replaced by `total`. */
function fill(node, total) {
  if (typeof node === "string") return node.replaceAll(TOTAL, total);
  if (Array.isArray(node)) return node.map((child) => fill(child, total));
  if (node === null || typeof node !== "object") return node;
  return Object.fromEntries(Object.entries(node).map(([key, value]) => [key, fill(value, total)]));
}

/** The page's text with our catalog count, as the home page states it ("267,000+"), in TOTAL's place. */
export function directoriesText(total) {
  return fill(DIRECTORIES_TEXT, total);
}
