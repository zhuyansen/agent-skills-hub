/**
 * /stats/ — State of Agent Skills, a monthly page of numbers others can cite (2026-10-19).
 *
 * Why: the official links a competitor earned (claude.com, langchain.com) all point at
 * "the catalog" or "the growing number of skills"; a dated, downloadable source for those
 * numbers is what such writers link to. Not a traffic page: the matching searches are a
 * few dozen a month.
 *
 * Source: public/stats/data/<YYYY-MM>.json, written on the 1st of each month by
 * ops/stats/monthly_snapshot.py (.github/workflows/stats-monthly.yml) and committed, so the
 * history is public in git. Until the first snapshot exists nothing is built.
 *
 * Pages: /stats/ (latest issue) and its Chinese twin /stats/zh/, plus /stats/<period>/ for
 * every issue. The latest issue's permalink is canonical to /stats/; older issues are their
 * own canonical, so a number cited from an issue keeps its URL. Downloads are the snapshot
 * files themselves (Vite copies them to dist/stats/data/), under CC BY 4.0.
 */
import { readFileSync, existsSync, mkdirSync, writeFileSync } from "fs";
import { join } from "path";
import { SITE, esc, biSpan, biAttrs, buildStaticHeader, analyticsTags, extractAssetTags } from "./shared-utils.mjs";
import { withHreflang, zhTwin } from "./scenario-zh-page.mjs";
import { lineChart, barList, dataTable, fmt, pct } from "./stats-charts.mjs";
import { STATS_DATA_DIR, statsPeriods } from "./stats-live.mjs";

const OUT_DIR = join("dist", "stats");
const CSS_VERSION = "20261028";
const LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/";
const HISTORY_URL = "https://github.com/zhuyansen/agent-skills-hub/tree/main/frontend/public/stats/data";
const SCAN_POST = "/blog/securing-117k-ai-skills/";
const MENTION_SHARE = "44.5";   // scanner second pass, 2026-09-20: hits that only mention a pattern
const LEAD_MONTHS = 6;          // recent months the Claude-vs-Codex sentence compares
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const SHORT = MONTHS.map((m) => m.slice(0, 3));

const SERIES = [
  { key: "mcp-server", label: "MCP servers", zh: "MCP 服务器", color: "var(--st-s1)" },
  { key: "claude-skill", label: "Claude skills", zh: "Claude skill", color: "var(--st-s2)" },
  { key: "codex-skill", label: "Codex skills", zh: "Codex skill", color: "var(--st-s3)" },
];
const TYPES = {
  "mcp-server": ["MCP servers", "MCP 服务器"], "claude-skill": ["Claude skills", "Claude skill"],
  "codex-skill": ["Codex skills", "Codex skill"], "agent-tool": ["Agent tools", "Agent 工具"],
  skill: ["Other skills", "其他 skill"], tool: ["Tools", "工具"], "llm-plugin": ["LLM plugins", "LLM 插件"],
  "agent-framework": ["Agent frameworks", "Agent 框架"],
};
const GRADES = [
  { key: "safe", label: "🟢 Safe", zh: "🟢 安全", color: "var(--st-good)" },
  { key: "caution", label: "🟡 Caution", zh: "🟡 需注意", color: "var(--st-warning)" },
  { key: "unsafe", label: "🔴 Unsafe", zh: "🔴 不安全", color: "var(--st-critical)" },
  { key: "reject", label: "⛔ Reject", zh: "⛔ 拒收", color: "var(--st-critical)" },
];
// The scanner's own rule descriptions (backend/app/services/security_scanner.py).
const PATTERNS = {
  sudo_usage: ["Uses sudo for elevated privileges", "用 sudo 提权"],
  tunnel_service: ["Exposes the local network through a tunnel (ngrok and the like)", "用 ngrok 等内网穿透把本机暴露到外网"],
  env_access: ["Reads environment variables in code", "在代码里读取环境变量"],
  cron_persistence: ["Installs a cron job", "安装定时任务（cron）常驻"],
  agent_memory_theft: ["Reads agent memory or identity files", "读取 agent 的记忆或身份文件"],
  subprocess_spawn: ["Spawns subprocesses to run commands", "启动子进程执行命令"],
  sensitive_env_vars: ["References several API keys or tokens", "引用多个 API key 或 token"],
  curl_pipe_shell: ["Pipes a downloaded script into a shell (curl | sh)", "把下载的脚本直接交给 shell 执行（curl | sh）"],
  fenced_download_exec: ["An install step in a code block runs a script from an untrusted host", "代码块里的安装步骤会从不受信任的主机下载并执行脚本"],
  ssl_disabled: ["Turns off TLS certificate checks", "关闭 TLS 证书校验"],
  eval_usage: ["Runs code with eval()", "用 eval() 动态执行代码"],
  docker_privileged: ["Runs Docker in privileged mode", "以特权模式运行 Docker"],
  runtime_install_exec: ["Installs a package and runs it at once", "装完依赖立即执行"],
};
const LICENSES = { "(none)": ["No license", "无许可证"], "(other)": ["Other licenses", "其他许可证"], NOASSERTION: ["Unrecognized license", "无法识别的许可证"] };
const PLATFORMS = { "claude-code": "Claude Code", browser: "Browser", mcp: "MCP", node: "Node.js", cli: "CLI", codex: "Codex", gemini: "Gemini", python: "Python", go: "Go", rust: "Rust", cursor: "Cursor" };
const PLATFORMS_ZH = { browser: "浏览器" };

const monthEn = (p) => `${MONTHS[+p.slice(5) - 1]} ${p.slice(0, 4)}`;
const monthZh = (p) => `${p.slice(0, 4)} 年 ${+p.slice(5)} 月`;
const axisLabel = (m, i) => ({ key: m, en: `${SHORT[+m.slice(5) - 1]}${i === 0 || m.endsWith("-01") ? ` ’${m.slice(2, 4)}` : ""}`, zh: `${+m.slice(5)}月` });
const p = (en, zh, cls = "st-lede") => `<p class="${cls}" ${biAttrs(en, zh)}>${esc(en)}</p>`;
const h2 = (en, zh) => biSpan(en, zh, { tag: "h2", attrs: 'class="bp-section-title"' });
const count = (list, key) => (list.find((r) => r.key === key) || {}).count || 0;

function loadIssues() {
  return statsPeriods().map((period) => JSON.parse(readFileSync(join(STATS_DATA_DIR, `${period}.json`), "utf-8")));
}

function tile(label, zh, value, note, noteZh) {
  return `<div class="st-tile">
      <div class="st-tile-label" ${biAttrs(label, zh)}>${esc(label)}</div>
      <div class="st-tile-value">${esc(value)}</div>
      <div class="st-tile-note" ${biAttrs(note, noteZh)}>${esc(note)}</div>
    </div>`;
}

function headline(d) {
  const { repos, scanned } = d.totals;
  const g = d.security.grades;
  const flagged = (g.caution || 0) + (g.unsafe || 0) + (g.reject || 0);
  const added = d.growth.at(-1)?.total || 0;
  return `<div class="st-tiles">
    ${tile("Repositories indexed", "收录仓库", fmt(repos), "Skill, MCP and agent tool repos on GitHub", "GitHub 上的 skill、MCP 与 agent 工具仓库")}
    ${tile(`Created in ${monthEn(d.period)}`, `${monthZh(d.period)}新建`, fmt(added), "By GitHub creation date", "按 GitHub 创建日期")}
    ${tile("Flagged by the security scan", "安全扫描标记", `${pct(flagged, scanned)}%`, `Of ${fmt(scanned)} audited repos`, `已审 ${fmt(scanned)} 个仓库`)}
    ${tile("No license", "没有许可证", `${pct(count(d.licenses, "(none)"), repos)}%`, "Reuse rights unclear", "能不能复用说不清")}
  </div>`;
}

function leadSentence(growth) {
  const recent = growth.slice(-LEAD_MONTHS);
  const codexLed = recent.filter((g) => g["codex-skill"] > g["claude-skill"]).length;
  const n = recent.length;
  if (!codexLed) return [`Claude skills outnumbered Codex skills among new repositories in each of the last ${n} months.`, `最近 ${n} 个月，每个月新建的 Claude skill 仓库都多于 Codex skill。`];
  if (codexLed === n) return [`Codex skills outnumbered Claude skills among new repositories in each of the last ${n} months.`, `最近 ${n} 个月，每个月新建的 Codex skill 仓库都多于 Claude skill。`];
  return [`Codex skills outnumbered Claude skills among new repositories in ${codexLed} of the last ${n} months.`, `最近 ${n} 个月里，有 ${codexLed} 个月新建的 Codex skill 仓库多于 Claude skill。`];
}

function growthSection(d) {
  const last = d.growth.at(-1) || {};
  const [leadEn, leadZh] = leadSentence(d.growth);
  const months = d.growth.map((g, i) => axisLabel(g.month, i));
  const series = SERIES.map((s) => ({ ...s, values: d.growth.map((g) => g[s.key] || 0) }));
  const rows = d.growth.map((g) => [g.month, g.total, g["mcp-server"], g["claude-skill"], g["codex-skill"], g.other]);
  const en = `${fmt(last.total || 0)} new repositories were created in ${monthEn(d.period)}: ${fmt(last["mcp-server"] || 0)} MCP servers, ${fmt(last["claude-skill"] || 0)} Claude skills and ${fmt(last["codex-skill"] || 0)} Codex skills. ${leadEn}`;
  const zh = `${monthZh(d.period)}新建 ${fmt(last.total || 0)} 个仓库，其中 MCP 服务器 ${fmt(last["mcp-server"] || 0)} 个、Claude skill ${fmt(last["claude-skill"] || 0)} 个、Codex skill ${fmt(last["codex-skill"] || 0)} 个。${leadZh}`;
  return `<section class="st-section">${h2("New repositories per month", "每月新建仓库")}${p(en, zh)}
    ${lineChart(months, series, `New MCP server, Claude skill and Codex skill repositories per month, ${d.growth[0]?.month} to ${d.period}`)}
    ${dataTable([["Month", "月份"], ["All", "全部"], ["MCP servers", "MCP 服务器"], ["Claude skills", "Claude skill"], ["Codex skills", "Codex skill"], ["Other", "其他"]], rows)}
    ${p("By the month each repository was created on GitHub, counting the repositories indexed at snapshot time. Recent months keep filling in as indexing catches up, so every issue keeps its own numbers.", "按仓库在 GitHub 上的创建月份统计，只算快照时已收录的仓库。最近几个月还会随收录补齐，所以每一期都保留自己当时的数。", "st-note")}
  </section>`;
}

/** Known types as rows; anything the classifier names otherwise goes into one "Other" row. */
function typeRows(types) {
  const color = Object.fromEntries(SERIES.map((s) => [s.key, s.color]));
  const known = types.filter((t) => TYPES[t.key]);
  const rest = types.filter((t) => !TYPES[t.key]).reduce((n, t) => n + t.count, 0);
  const rows = known.map((t) => ({ label: TYPES[t.key][0], zh: TYPES[t.key][1], value: t.count, color: color[t.key] || "var(--st-neutral)" }));
  return rest ? [...rows, { label: "Other", zh: "其他", value: rest, color: "var(--st-neutral)" }] : rows;
}

function catalogSection(d) {
  const { repos } = d.totals;
  const rows = typeRows(d.types);
  const skills = count(d.types, "claude-skill") + count(d.types, "codex-skill");
  const en = `${pct(count(d.types, "mcp-server"), repos)}% of the catalog are MCP servers; Claude and Codex skills together make up ${pct(skills, repos)}%.`;
  const zh = `目录里 ${pct(count(d.types, "mcp-server"), repos)}% 是 MCP 服务器，Claude 与 Codex skill 合计占 ${pct(skills, repos)}%。`;
  return `<section class="st-section">${h2("What the catalog holds", "目录里有什么")}${p(en, zh)}${barList(rows, { total: repos })}</section>`;
}

function patternRows(patterns) {
  return patterns.map((r) => {
    const [en, zh] = PATTERNS[r.key] || [r.key, r.key];
    return { label: en, zh, value: r.count };
  });
}

function securitySection(d) {
  const { repos, scanned } = d.totals;
  const g = d.security.grades;
  const flagged = (g.caution || 0) + (g.unsafe || 0) + (g.reject || 0);
  const rows = GRADES.filter((x) => g[x.key]).map((x) => ({ ...x, value: g[x.key] }));
  const en = `${fmt(scanned)} repositories (${pct(scanned, repos)}% of the catalog) have been through the security scan. ${pct(flagged, scanned)}% were graded caution or worse, and ${fmt(g.unsafe || 0)} were graded unsafe. The rest of the catalog is unaudited and is not counted as safe.`;
  const zh = `已有 ${fmt(scanned)} 个仓库（占目录 ${pct(scanned, repos)}%）做过安全扫描，其中 ${pct(flagged, scanned)}% 被评为需注意或更差，${fmt(g.unsafe || 0)} 个被评为不安全。其余仓库还没审，不算作安全。`;
  const caveat = p(`A pattern hit is a lead, not proof: when we reviewed flagged repositories, ${MENTION_SHARE}% of hits were text that mentions a pattern (docs, warnings) rather than code that does it. Grades weigh the hits.`, `命中规则只是线索，不是证据：复核被标记的仓库时，${MENTION_SHARE}% 的命中只是文字提到（文档、警告），不是代码真的这么做。评级会综合权衡这些命中。`, "st-note");
  return `<section class="st-section">${h2("Security scan", "安全扫描")}${p(en, zh)}${barList(rows, { total: scanned })}
    ${biSpan("Most common risky patterns", "最常见的风险模式", { tag: "h3" })}
    ${barList(patternRows(d.security.patterns))}${caveat}
    <p class="st-note"><a href="${SCAN_POST}" ${biAttrs("How the scan works", "扫描是怎么做的")}>How the scan works</a></p>
  </section>`;
}

function licenseSection(d) {
  const { repos } = d.totals;
  const rows = d.licenses.map((l) => {
    const [en, zh] = LICENSES[l.key] || [l.key, l.key];
    return { label: en, zh, value: l.count };
  });
  const en = `${pct(count(d.licenses, "(none)"), repos)}% of repositories carry no license, so whether a company may reuse them is unclear; ${pct(count(d.licenses, "MIT"), repos)}% use MIT.`;
  const zh = `${pct(count(d.licenses, "(none)"), repos)}% 的仓库没有许可证，公司能不能拿来用说不清；${pct(count(d.licenses, "MIT"), repos)}% 用 MIT。`;
  return `<section class="st-section">${h2("Licenses", "许可证")}${p(en, zh)}${barList(rows, { total: repos })}</section>`;
}

function platformSection(d) {
  const rows = d.platforms.map((x) => ({ label: PLATFORMS[x.key] || x.key, zh: PLATFORMS_ZH[x.key] || PLATFORMS[x.key] || x.key, value: x.count }));
  const share = d.cjk_description_share_pct;
  return `<section class="st-section">${h2("Which agents and runtimes they target", "面向哪些 agent 和运行环境")}
    ${p("Read from each repository's README and manifests; one repository can target several.", "从每个仓库的 README 和配置文件里识别，一个仓库可以同时面向多个。")}
    ${barList(rows, { total: d.totals.repos })}
    ${p(`${share}% of repositories describe themselves in Chinese, Japanese or Korean.`, `${share}% 的仓库用中文、日文或韩文写简介。`, "st-note")}
  </section>`;
}

function moverItem(m) {
  const page = existsSync(join("dist", "skill", m.repo, "index.html")) ? `/skill/${m.repo}/` : `https://github.com/${m.repo}`;
  const note = `★ ${fmt(m.stars)} · +${fmt(m.stars_per_day)}/day, week of ${m.week}`;
  const noteZh = `★ ${fmt(m.stars)} · 日均 +${fmt(m.stars_per_day)}，${m.week} 那一周`;
  return `<li><a href="${esc(page)}">${esc(m.repo)}</a><span class="st-note" ${biAttrs(note, noteZh)}>${esc(note)}</span></li>`;
}

function moversSection(d) {
  if (!d.movers.length) return "";
  return `<section class="st-section">${h2(`Fastest-growing in ${monthEn(d.period)}`, `${monthZh(d.period)}增速最快`)}
    ${p("Repositories with the highest average daily star gain in their best week of the month, from our weekly top 20. Known star-farmed copies are left out.", "按当月表现最好的那一周日均新增星数排序，取自我们每周的前 20 名。已知的刷星仓库已排除。")}
    <ol class="st-movers">${d.movers.map(moverItem).join("")}</ol>
  </section>`;
}

function methodSection(d) {
  const items = [
    ["What is counted: public GitHub repositories that hold an agent skill, an MCP server or an agent tool, found by our search queries every 8 hours plus curated additions. Counts are repositories, not files: one repository can hold many SKILL.md files, which is why directories that count files report millions.", "统计什么：GitHub 上包含 agent skill、MCP 服务器或 agent 工具的公开仓库，来自每 8 小时一轮的搜索，加上人工补录。按仓库计数，不按文件：一个仓库可能有很多个 SKILL.md，按文件计数的目录因此会报出几百万。"],
    ["Growth uses the date each repository was created on GitHub, among those indexed at snapshot time; a repository we have not found yet is missing from every month.", "增长按仓库在 GitHub 上的创建日期统计，只算快照时已收录的仓库；还没被我们发现的仓库，在每个月里都不在。"],
    [`Security grades come from a static scan of README, SKILL.md and scripts. ${pct(d.totals.scanned, d.totals.repos)}% of the catalog has been scanned so far.`, `安全评级来自对 README、SKILL.md 和脚本的静态扫描，目前已覆盖目录的 ${pct(d.totals.scanned, d.totals.repos)}%。`],
    ["Types and platforms are inferred from names, topics, READMEs and manifests. They can be wrong for a single repository; the totals are what this page is for.", "类型和平台是从名称、话题标签、README 和配置文件推断的，单个仓库可能判错，这一页看的是总数。"],
    [`Snapshot taken ${d.snapshot_at.replace("T", " ").replace("Z", " UTC")}. A published issue is never changed; corrections go into the next one.`, `快照时间 ${d.snapshot_at.replace("T", " ").replace("Z", " UTC")}。已发布的一期不再修改，更正写进下一期。`],
  ];
  return `<section class="st-section">${h2("Method and limits", "方法与局限")}<ul class="st-method">${items.map(([en, zh]) => `<li ${biAttrs(en, zh)}>${esc(en)}</li>`).join("")}</ul></section>`;
}

function citeSection(d, issues, permalink) {
  const en = `Agent Skills Hub (agentskillshub.top). State of Agent Skills, ${monthEn(d.period)}. ${permalink}`;
  const zh = `Agent Skills Hub（agentskillshub.top），Agent Skills 生态数据月报，${monthZh(d.period)}。${permalink}`;
  const link = (href, label, zhLabel) => `<a href="${esc(href)}" ${biAttrs(label, zhLabel)}>${esc(label)}</a>`;
  const archive = issues.slice().reverse().map((i) => link(`/stats/${i.period}/`, monthEn(i.period), monthZh(i.period))).join("");
  return `<section class="st-section">${h2("Cite and download", "引用与下载")}
    ${p("Free to use, also commercially, with credit and a link: CC BY 4.0.", "可以免费使用，商用也行，只需署名并附上链接：CC BY 4.0。")}
    <div class="st-cite"><code ${biAttrs(en, zh)}>${esc(en)}</code></div>
    <div class="st-links">${link(`/stats/data/${d.period}.json`, "Download JSON", "下载 JSON")}${link(`/stats/data/${d.period}.csv`, "Download CSV", "下载 CSV")}${link(LICENSE_URL, "License: CC BY 4.0", "许可：CC BY 4.0")}${link(HISTORY_URL, "Every snapshot on GitHub", "GitHub 上的全部快照")}</div>
    ${biSpan("Issues", "往期", { tag: "h3" })}
    <div class="st-links">${archive}</div>
  </section>`;
}

function datasetLd(d, permalink) {
  const date = d.snapshot_at.slice(0, 10);
  return JSON.stringify({
    "@context": "https://schema.org",
    "@type": "Dataset",
    name: `State of Agent Skills, ${monthEn(d.period)}`,
    description: `Monthly counts of open-source agent skill, MCP server and agent tool repositories on GitHub indexed by Agent Skills Hub: growth by month, security scan grades, risky patterns, licenses and target platforms. Snapshot of ${date}.`,
    url: permalink,
    license: LICENSE_URL,
    isAccessibleForFree: true,
    creator: { "@type": "Organization", name: "Agent Skills Hub", url: SITE },
    datePublished: date,
    dateModified: date,
    temporalCoverage: `${d.growth[0]?.month || d.period}/${d.period}`,
    keywords: ["agent skills", "MCP servers", "Claude skills", "Codex skills", "AI agent security", "open source licenses"],
    variableMeasured: ["repositories indexed", "new repositories per month", "security grade", "risky pattern hits", "license", "target platform"],
    distribution: ["json", "csv"].map((ext) => ({ "@type": "DataDownload", encodingFormat: ext === "json" ? "application/json" : "text/csv", contentUrl: `${SITE}/stats/data/${d.period}.${ext}` })),
  });
}

function breadcrumbLd() {
  return JSON.stringify({
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: SITE },
      { "@type": "ListItem", position: 2, name: "State of Agent Skills", item: `${SITE}/stats/` },
    ],
  });
}

function head({ title, desc, canonical, ld, cssLinks }) {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${esc(title)}</title>
  <meta name="description" content="${esc(desc)}" />
  <meta property="og:title" content="${esc(title)}" />
  <meta property="og:description" content="${esc(desc)}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="${esc(canonical)}" />
  <meta property="og:image" content="${SITE}/og-image.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="canonical" href="${esc(canonical)}" />
  <script type="application/ld+json">${ld}</script>
  <script type="application/ld+json">${breadcrumbLd()}</script>
  <link rel="stylesheet" href="/best-pages.css?v=${CSS_VERSION}" />
  <link rel="stylesheet" href="/stats-page.css?v=${CSS_VERSION}" />
  ${cssLinks}
  ${analyticsTags()}
</head>`;
}

const titleOf = (d) => `State of Agent Skills, ${monthEn(d.period)} | Agent Skills Hub`;
const descOf = (d) => `Monthly data on ${fmt(d.totals.repos)} open-source agent skill and MCP server repositories: growth, security grades, licenses and platforms. Free to cite and download (CC BY 4.0).`;

function pageHtml(d, issues, { canonical, permalink, cssLinks }) {
  const intro = p("Monthly numbers on the open-source agent skill and MCP server repositories on GitHub that Agent Skills Hub indexes: how fast they grow, how they fare in our security scan, what licenses they carry and which agents they target.", "Agent Skills Hub 收录的 GitHub 开源 agent skill 与 MCP 服务器仓库，每月一期：增长多快、安全扫描结果如何、带什么许可证、面向哪些 agent。");
  const issueLine = p(`${monthEn(d.period)} issue · data as of ${d.snapshot_at.slice(0, 10)}`, `${monthZh(d.period)}号 · 数据截至 ${d.snapshot_at.slice(0, 10)}`, "st-issue");
  return `${head({ title: titleOf(d), desc: descOf(d), canonical, ld: datasetLd(d, permalink), cssLinks })}
<body class="bp-body">
  ${buildStaticHeader({ x: true })}
  <div class="bp-container st-root">
    <nav class="bp-breadcrumb"><a href="/" ${biAttrs("Home", "首页")}>Home</a><span style="margin:0 6px">&gt;</span>${biSpan("State of Agent Skills", "生态数据月报")}</nav>
    <div class="bp-hero">${biSpan("State of Agent Skills", "Agent Skills 生态数据月报", { tag: "h1" })}${issueLine}${intro}</div>
    ${headline(d)}
    ${growthSection(d)}${catalogSection(d)}${securitySection(d)}${licenseSection(d)}${platformSection(d)}${moversSection(d)}${methodSection(d)}${citeSection(d, issues, permalink)}
  </div>
</body>
</html>`;
}

// The scan report people already link to points readers at the newer numbers.
const SCAN_POST_COPIES = [
  { file: join("dist", "blog", "securing-117k-ai-skills", "index.html"), href: "/stats/", text: (d) => `📊 New numbers every month: State of Agent Skills, ${monthEn(d.period)} →` },
  { file: join("dist", "blog", "securing-117k-ai-skills", "zh", "index.html"), href: "/stats/zh/", text: (d) => `📊 每月最新数据：Agent Skills 生态数据月报（${monthZh(d.period)}）→` },
];

/** Adds a link to /stats/ above the scan report's first section heading. */
function linkFromScanPost(d) {
  for (const { file, href, text } of SCAN_POST_COPIES) {
    if (!existsSync(file)) continue;
    const html = readFileSync(file, "utf-8");
    const at = html.indexOf("<h2", html.indexOf('<article class="article-body">'));
    if (at < 0 || html.includes('class="st-latest"')) continue;
    const link = `<p class="st-latest"><a href="${href}">${esc(text(d))}</a></p>\n`;
    writeFileSync(file, html.slice(0, at) + link + html.slice(at));
  }
}

function write(dir, html) {
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "index.html"), html);
}

function main() {
  const issues = loadIssues();
  if (!issues.length) {
    console.log("  (no stats snapshot yet — /stats/ not built)");
    return;
  }
  const { linkTags } = extractAssetTags(readFileSync(join("dist", "index.html"), "utf-8"));
  const cssLinks = linkTags.filter((t) => t.includes("stylesheet")).join("\n  ");
  const latest = issues.at(-1);
  for (const d of issues) {
    const permalink = `${SITE}/stats/${d.period}/`;
    const canonical = d === latest ? `${SITE}/stats/` : permalink;
    write(join(OUT_DIR, d.period), pageHtml(d, issues, { canonical, permalink, cssLinks }));
  }
  const en = withHreflang(pageHtml(latest, issues, { canonical: `${SITE}/stats/`, permalink: `${SITE}/stats/${latest.period}/`, cssLinks }), "/stats/");
  write(OUT_DIR, en);
  const zhDesc = `每月更新：${fmt(latest.totals.repos)} 个开源 agent skill 与 MCP 服务器仓库的增长、安全评级、许可证和平台分布，可免费引用和下载（CC BY 4.0）。`;
  write(join(OUT_DIR, "zh"), zhTwin(en, { enPath: "/stats/", title: `Agent Skills 生态数据月报 · ${monthZh(latest.period)}`, description: zhDesc, twinPaths: new Set(["/stats/"]) }));
  linkFromScanPost(latest);
  console.log(`  ✓ /stats/ (${latest.period}) + /stats/zh/ + ${issues.length} issue page(s)`);
}

main();
