/**
 * The home page's Chinese twin at /zh/ (2026-11-03), the same pattern as the /best/ twins
 * (scenario-zh-page.mjs): the Chinese text written into the HTML, lang="zh-CN", its own
 * canonical, and hreflang between the twins. The React home page swaps languages in place, so
 * Google only ever read it in English, and Hub had no Chinese URL for a Chinese search to land
 * on. At /zh/ React mounts in Chinese (I18nContext reads the path; Home owns the head tags).
 *
 * Runs after generate-scenario-pages, whose Chinese twins it links by the title in their <h1>,
 * and before generate-sitemap, which lists /zh/ once this file exists.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";
import { CATEGORY_LABELS_ZH, SUPABASE_ANON_KEY, SUPABASE_URL, esc, replaceShellContent } from "./shared-utils.mjs";
import { homeListsHtml } from "./home-lists.mjs";
import { hreflangTags } from "./scenario-zh-page.mjs";
import { ZH_HOME_PATH, ZH_HOME_TITLE as TITLE } from "../src/lib/homeMeta.mjs";

const DIST = "dist";
const ZH_URL = `https://agentskillshub.top${ZH_HOME_PATH}`;
const LIST_COLUMNS = "repo_full_name,description,stars,score,star_momentum,category,topics";
/** Enough rows per list that the NSFW and page filters still leave a full list. */
const LIST_QUERIES = [
  "stars=gte.500&order=star_momentum.desc&limit=200",
  "stars=gte.500&order=score.desc&limit=200",
  ...["mcp-server", "claude-skill", "codex-skill", "agent-tool"].map((c) => `category=eq.${c}&stars=gte.500&order=stars.desc&limit=40`),
];

const description = (total) =>
  `AgentSkillsHub —— Claude Skills 市场：收录 ${total} 个 Claude 技能、MCP 服务器与 Agent 工具，热门的全部做了安全评级，装前先查，每 8 小时刷新。`;

/** The rows the lists are built from: the top of each list, fetched apart. Empty on failure. */
async function listRows() {
  try {
    const pages = await Promise.all(LIST_QUERIES.map(async (q) => {
      const res = await fetch(`${SUPABASE_URL}/rest/v1/skills?select=${LIST_COLUMNS}&${q}`, { headers: { apikey: SUPABASE_ANON_KEY } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    }));
    return [...new Map(pages.flat().map((r) => [r.repo_full_name, r])).values()];
  } catch (e) {
    console.warn(`  home zh: lists skipped (${e.message})`);
    return [];
  }
}

/** The scenarios the English home links, each by its Chinese twin's title; those without a twin are left out. */
function scenarioLinks(enHtml) {
  const slugs = [...enHtml.matchAll(/<li><a href="\/best\/([a-z0-9-]+)\/">/g)].map((m) => m[1]);
  return slugs.flatMap((slug) => {
    const file = join(DIST, "best", slug, "zh", "index.html");
    if (!existsSync(file)) return [];
    const h1 = readFileSync(file, "utf-8").match(/<h1[^>]*>([\s\S]*?)<\/h1>/);
    const title = h1 ? h1[1].replace(/<[^>]+>/g, "").trim() : slug;
    return [`<li><a href="/best/${slug}/zh/">${esc(title)}</a></li>`];
  });
}

const categoryLinks = (enHtml) => [...enHtml.matchAll(/<li><a href="\/category\/([a-z0-9-]+)\/">/g)]
  .map(([, slug]) => `<li><a href="/category/${slug}/">${esc(CATEGORY_LABELS_ZH[slug] ?? slug)}</a></li>`);

function shellHtml(enHtml, total, lists) {
  return `      <header>
        <h1>AgentSkillsHub —— Claude Skills 市场：收录 ${total} 个 Claude 技能、MCP 服务器与 Agent 工具，热门的全部做了安全评级</h1>
        <p>AgentSkillsHub（Agent Skills Hub，agentskillshub.top）是开源的 AI 智能体技能目录，收录 Claude Skills、MCP 服务器、Codex 技能和 Agent 工具，每 8 小时从 GitHub 刷新一次。热门条目都按 <a href="/how-we-grade/">42 条公开规则</a>做了安全评级，装之前先查。</p>
        <nav aria-label="主导航"><ul>
          <li><a href="/" hreflang="en" lang="en">English</a></li>
          <li><a href="/compare/">对比工具</a></li>
          <li><a href="/analyzer/">Skill 安全分析</a></li>
          <li><a href="/stats/zh/">生态数据月报</a></li>
          <li><a href="/about/">关于与方法</a></li>
        </ul></nav>
      </header>
      <main>
        ${lists}
        <section><h2>按分类浏览</h2><ul>${categoryLinks(enHtml).join("")}</ul></section>
        <section><h2>热门场景</h2><p>每个场景页回答「做这件事用哪个工具最好」，按质量评分、安全评级和实测排出短名单。</p><ul>${scenarioLinks(enHtml).join("")}</ul></section>
      </main>
      <footer><p>AgentSkillsHub —— 开源 AI 智能体工具目录，由 Jason Zhu 维护。</p></footer>`;
}

/** The English head turned Chinese: language, title, descriptions, URL, canonical and hreflang. */
function zhHead(html, total) {
  const text = esc(description(total));
  return html
    .replace('<html lang="en">', '<html lang="zh-CN">')
    .replace(/<title>[^<]*<\/title>/, `<title>${TITLE}</title>`)
    .replace(/(<meta (?:name="description"|property="og:description"|name="twitter:description") content=")[^"]*(")/g, `$1${text}$2`)
    .replace(/(<meta (?:property="og:title"|name="twitter:title") content=")[^"]*(")/g, `$1${TITLE}$2`)
    .replace(/(<meta property="og:url" content=")[^"]*(")/, `$1${ZH_URL}$2`)
    .replace("</head>", `  <link rel="canonical" href="${ZH_URL}" />\n  ${hreflangTags("/")}\n</head>`);
}

async function main() {
  const enHtml = readFileSync(join(DIST, "index.html"), "utf-8");
  const total = enHtml.match(/<span data-count="total">([^<]+)<\/span>/)?.[1] ?? "250,000+";
  const lists = homeListsHtml(await listRows(), "zh");
  const html = replaceShellContent(zhHead(enHtml, total), shellHtml(enHtml, total, lists));
  mkdirSync(join(DIST, "zh"), { recursive: true });
  writeFileSync(join(DIST, "zh", "index.html"), html);
  console.log(`✓ /zh/: ${(lists.match(/<li>/g) || []).length} skills listed, ${scenarioLinks(enHtml).length} scenarios linked`);
}

// The twin is an extra page: a failure leaves it out (the sitemap lists /zh/ only when the file
// exists) rather than failing the deploy of everything else.
main().catch((err) => {
  console.error("Failed to generate /zh/, left out of this build:", err);
});
