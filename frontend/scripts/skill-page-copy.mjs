/**
 * Language of a static /skill/ page, and the page's template text in English and Chinese.
 *
 * Most of our Bing impressions come from people in China searching a repository's name,
 * and Bing ranks by location and language. A repository that describes itself in Chinese
 * gets a Chinese page: html lang, headings and template text (owner's decision,
 * 2026-11-02). The URL, <title> and meta description stay as they are. Only the static
 * HTML changes: Bing stores it as served, while Google indexes the React page.
 */
import { esc, CATEGORY_LABELS, CATEGORY_LABELS_ZH } from "./shared-utils.mjs";

const HAN = /[㐀-䶿一-鿿]/g;
const KANA = /[぀-ヿ]/;
const LATIN = /[A-Za-z]/g;
/** "飞书" or "小红书" inside an English sentence is not a Chinese description. */
const MIN_HAN = 4;
/** One Han character carries about as much as three Latin letters. */
const HAN_PER_LATIN = 3;

/** "zh" when the repo's own description is mostly Chinese; kana means Japanese, so "en". */
export function skillPageLang(description) {
  const text = String(description || "");
  if (KANA.test(text)) return "en";
  const han = (text.match(HAN) || []).length;
  const latin = (text.match(LATIN) || []).length;
  return han >= MIN_HAN && han * HAN_PER_LATIN >= latin ? "zh" : "en";
}

/**
 * Red-flag names, [English, Chinese]. §20.0 of Google's rater guidelines says a result
 * that gives "reviews and reputation information" is very helpful for a URL query, while
 * one offering "usage statistics" usually is not. Naming what the scan actually found is
 * review information; a star count is not. The Chinese follows /how-we-grade/.
 */
const FLAG_NAMES = {
  sudo_usage: ["sudo usage", "使用 sudo"],
  service_persistence: ["installs a background service", "安装后台服务"],
  curl_pipe_shell: ["curl | sh from an untrusted host", "从陌生主机 curl | sh"],
  agent_config_theft: ["sends agent config files off the machine", "把 agent 配置文件发出本机"],
  fenced_download_exec: ["install step in a code block runs a script from an untrusted host", "代码块里的安装步骤会运行陌生主机的脚本"],
  tunnel_service: ["opens a tunnel service", "开启隧道服务"],
  eval_usage: ["dynamic eval()", "动态 eval()"],
  sensitive_env_vars: ["reads sensitive env vars", "读取敏感环境变量"],
  agent_memory_theft: ["reads agent memory", "读取 agent 的记忆"],
  env_access: ["environment access", "访问环境变量"],
  subprocess_spawn: ["spawns subprocesses", "启动子进程"],
  cron_persistence: ["installs a cron job", "安装 cron 定时任务"],
  sensitive_dir_access: ["sensitive directory access", "访问敏感目录"],
  docker_privileged: ["privileged Docker", "特权模式 Docker"],
  backdoor_install: ["backdoor install pattern", "后门式安装"],
  chmod_dangerous: ["dangerous chmod", "危险的 chmod"],
  ssl_disabled: ["disables SSL verification", "关闭 SSL 校验"],
  etc_sensitive_read: ["reads /etc secrets", "读取 /etc 下的敏感文件"],
  wget_pipe_shell: ["wget | sh from an untrusted host", "从陌生主机 wget | sh"],
  runtime_install_exec: ["installs at runtime", "运行时安装"],
  powershell_download_exec: ["irm | iex from an untrusted host", "从陌生主机 irm | iex"],
  prompt_injection_covert: ["tells the agent to act covertly", "让 agent 暗中行事"],
  credential_harvest: ["collects credentials from your environment", "从你的环境里收集凭证"],
  exec_import: ["runs code it imports at runtime", "运行时导入并执行代码"],
  base64_exec: ["runs base64-decoded code", "执行 base64 解码出的代码"],
  obfuscated_exec: ["runs obfuscated code", "执行混淆过的代码"],
  hex_encoded_payload: ["hides a payload as hex", "用十六进制藏载荷"],
  fs_root_access: ["reads the root of the filesystem", "读取文件系统根目录"],
  jailbreak_mode: ["jailbreak persona prompt", "越狱人格提示词"],
  tool_priority_manipulation: ["tells the agent to ignore other tools", "让 agent 忽略其他工具"],
  credential_in_chat: ["asks you to paste credentials into chat", "要你把凭证贴进对话"],
  shortener_download: ["downloads via a URL shortener", "通过短链接下载"],
  paste_host_download: ["downloads from a paste host", "从粘贴站下载"],
  leaked_secret: ["hardcoded credential in the README", "README 里写死了凭证"],
  privilege_escalation: ["privilege escalation", "提升权限"],
  reverse_shell: ["reverse shell", "反弹 shell"],
  raw_ip_request: ["hardcoded IP request", "直接请求写死的 IP"],
  exfil_secrets_combo: ["secret-exfiltration combo", "窃取密钥的组合操作"],
  rm_rf_root: ["rm -rf on root paths", "对根路径 rm -rf"],
  dev_tcp: ["/dev/tcp socket", "/dev/tcp 连接"],
  data_exfiltration: ["data exfiltration", "数据外泄"],
  write_etc: ["writes to /etc", "写入 /etc"],
  shell_rc_inject: ["injects into shell rc", "注入 shell 配置文件"],
};

export function flagName(flag, lang) {
  const pair = FLAG_NAMES[flag];
  return pair ? pair[lang === "zh" ? 1 : 0] : flag.replace(/_/g, " ");
}

/** The most flags a verdict names before it says how many more there are. */
const FLAGS_SHOWN = 4;

/** Chinese grade names, as the React page shows them (src/i18n/translations.ts). */
const GRADE_ZH = { safe: "安全", caution: "注意", unsafe: "风险", reject: "已拒绝" };

/** A space where Chinese meets a Latin word: "更多 Claude Skill", "更多教育". */
const lead = (s) => (/^[A-Za-z0-9]/.test(s) ? " " : "") + esc(s);
const trail = (s) => s + (/[A-Za-z0-9]$/.test(s) ? " " : "");

const EN = {
  htmlLang: "en",
  home: "Home",
  goneLabel: "Repository no longer available",
  goneHeading: " — repository deleted, archived audit",
  catLabel: (cat) => CATEGORY_LABELS[cat] || "AI Tool",
  by: (creatorHtml) => `by ${creatorHtml}`,
  lastUpdated: "Last updated: ",
  synced: "Indexed by AgentSkillsHub &middot; Auto-synced every 8h",
  auditLink: (name) => `&#128274; Is ${esc(name)} safe to install? View the security audit &rarr;`,
  featuredIn: "Featured in:",
  verdictTitle: (grade, label, q) => `Security audit verdict: ${esc(label)}${q !== null ? ` · quality ${q}/100` : ""}`,
  flagged: (names, more) => `Flagged: ${names.map(esc).join(", ")}${more ? ` and ${more} more` : ""}.`,
  noneMatched: (rules) => `None of the ${rules} rules matched — no credential harvesting, no data exfiltration, no curl-pipe-shell installer.`,
  rulesLink: (rules) => `${rules} published rules`,
  scanned: (link) => ` Scanned against ${link} built on the SlowMist agent-security taxonomy, refreshed every 8 hours.`,
  fullAudit: "Full audit &rarr;",
  // What the quality number means, shown next to it (backend/app/services/quality_analyzer.py).
  qualityNote: "The quality score combines nine heuristic checks of the repo and its README: completeness, clarity, specificity, examples, structure, agent readiness, step-by-step content, instruction quality and security notes. It rates how well the project explains itself to an agent, not the code.",
  quickFacts: "Quick Facts",
  facts: { stars: "Stars", forks: "Forks", language: "Language", category: "Category", license: "License", quality: "Quality Score", commits: "Total Commits", issues: "Open Issues", updated: "Last Updated", created: "Created", platforms: "Platforms", tokens: "Est. Tokens" },
  about: (name) => `About ${esc(name)}`,
  compatTitle: "Compatible Skills",
  compatIntro: (name) => `These tools work well together with ${esc(name)} for enhanced workflows:`,
  altTitle: (name, n) => `${esc(name)} alternative? Top ${n} similar tools`,
  altIntro: (name, cat, n) => `Looking for a ${esc(name)} alternative? If you're comparing ${esc(name)} with other ${esc(cat.toLowerCase())} tools, these ${n} projects are the closest alternatives on Agent Skills Hub — ranked by topic overlap, star count, and community traction.`,
  byAuthor: (author) => ` by ${esc(author)}`,
  moreCat: (cat) => `More ${esc(cat)} Tools`,
  exploreCat: (cat) => `Explore other popular ${esc(cat.toLowerCase())} tools:`,
  viewAllCat: (cat) => `View all ${esc(cat)} tools →`,
  popularLang: (language) => `Popular ${esc(language)} Agent Tools`,
  viewGithub: "View on GitHub &rarr;",
  viewAlt: (sub) => `View alternative: ${esc(sub)} &rarr;`,
  browseCat: (cat) => `Browse ${esc(cat)} tools`,
  noscript: "Enable JavaScript for the full interactive experience, or browse the content above.",
};

const ZH = {
  htmlLang: "zh-CN",
  home: "首页",
  goneLabel: "仓库已下架",
  goneHeading: "——仓库已删除，这是存档的审计",
  catLabel: (cat) => CATEGORY_LABELS_ZH[cat] || "AI 工具",
  by: (creatorHtml) => `作者 ${creatorHtml}`,
  lastUpdated: "最后更新：",
  synced: "由 Agent Skills Hub 收录 &middot; 每 8 小时同步一次",
  auditLink: (name) => `&#128274; ${esc(name)} 安全吗？看安全审计 &rarr;`,
  featuredIn: "入选精选页：",
  verdictTitle: (grade, label, q) => `安全审计结论：${GRADE_ZH[grade] || esc(label)}${q !== null ? ` · 质量分 ${q}/100` : ""}`,
  flagged: (names, more) => `命中：${names.map(esc).join("、")}${more ? `，另有 ${more} 项` : ""}。`,
  noneMatched: (rules) => `${rules} 条规则都没有命中：没有凭证窃取，没有数据外泄，没有 curl | sh 式安装。`,
  rulesLink: (rules) => `${rules} 条公开规则`,
  scanned: (link) => `按慢雾（SlowMist）agent 安全分类法建立的 ${link}扫描，每 8 小时更新一次。`,
  fullAudit: "完整审计 &rarr;",
  qualityNote: "质量分综合九项启发式检查：完整度、清晰度、具体程度、示例、结构、对 agent 的友好度、分步内容、指令质量和安全提示。它衡量的是项目把自己讲清楚的程度，不是代码质量。",
  quickFacts: "基本信息",
  facts: { stars: "Star 数", forks: "Fork 数", language: "语言", category: "分类", license: "许可证", quality: "质量分", commits: "提交数", issues: "未关闭的 Issue", updated: "最后更新", created: "创建时间", platforms: "支持平台", tokens: "估计 Token 数" },
  about: (name) => `关于 ${esc(name)}`,
  compatTitle: "兼容技能",
  compatIntro: (name) => `和 ${esc(name)} 搭配使用的工具：`,
  altTitle: (name, n) => `${esc(name)} 的替代品：最接近的 ${n} 个工具`,
  altIntro: (name, cat, n) => `想找 ${esc(name)} 的替代品？在 Agent Skills Hub 收录的${trail(lead(cat))}里，下面 ${n} 个项目和它最接近，按话题重合度、星数和社区热度排序。`,
  byAuthor: (author) => ` 作者 ${esc(author)}`,
  moreCat: (cat) => `更多${lead(cat)}`,
  exploreCat: (cat) => `其他热门的${lead(cat)}：`,
  viewAllCat: (cat) => `查看全部${lead(cat)} →`,
  popularLang: (language) => `热门 ${esc(language)} Agent 工具`,
  viewGithub: "在 GitHub 上查看 &rarr;",
  viewAlt: (sub) => `查看替代项目：${esc(sub)} &rarr;`,
  browseCat: (cat) => `浏览${lead(cat)}`,
  noscript: "开启 JavaScript 可以使用完整功能，也可以直接看上面的内容。",
};

/** Template text for a page in `lang` ("en" or "zh"). */
export function skillCopy(lang) {
  return lang === "zh" ? ZH : EN;
}

/** The verdict's finding: the flags it names, or that none of the rules matched. */
export function findingText(c, names, rules) {
  if (!names.length) return c.noneMatched(rules);
  const more = names.length > FLAGS_SHOWN ? names.length - FLAGS_SHOWN : 0;
  return c.flagged(names.slice(0, FLAGS_SHOWN), more);
}
