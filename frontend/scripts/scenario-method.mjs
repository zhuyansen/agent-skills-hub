/**
 * A scenario page's `method` section (scenario-keywords.json): how we judge the
 * entries, in our own words, with the numbers taken from the page's data at build
 * time. It replaces the templated "complete guide" on pages that have one: that
 * guide says the same thing on every page, which is what a page written by a
 * model looks like. 2026-10-07, first on ppt-presentation.
 *
 *   "method": { "h2", "thesis", "routes": [{ "name", "kinds": [...], "how", "gain", "cost" }],
 *               "gap", "next_stop": [{ "who", "pick" }], "questions": [...], "did": [...],
 *               "not_done": [...], "author": { "name", "role", "about", "x", "github", "reviewed" } }
 * Every text field has a `_zh` twin.
 */
import { esc, biAttrs } from "./shared-utils.mjs";

// Rules a skill trips by how it is installed, not by what it does once running.
const INSTALL_RULES = new Set(["sudo_usage", "curl_pipe_shell", "wget_pipe_shell"]);
const ROUTE_EXAMPLES = 2;

const bi = (o, key) => biAttrs(o[key], o[`${key}_zh`] || o[key]);
const text = (o, key) => esc(o[key]);
const t = (o, key, tag = "p", attrs = "") => `<${tag}${attrs ? ` ${attrs}` : ""} ${bi(o, key)}>${text(o, key)}</${tag}>`;

function flags(s) {
  if (Array.isArray(s.security_flags)) return s.security_flags;
  try { return JSON.parse(s.security_flags || "[]"); } catch { return []; }
}

/** Entries per route and the most-starred ones, from the page's reviewed kinds. */
function routeStats(route, cards, scenarioKinds) {
  const rows = cards.filter((s) => route.kinds.includes(scenarioKinds.of(s)));
  const top = [...rows].sort((a, b) => (b.stars || 0) - (a.stars || 0)).slice(0, ROUTE_EXAMPLES);
  return { count: rows.length, top };
}

function routeRow(route, cards, scenarioKinds) {
  const { count, top } = routeStats(route, cards, scenarioKinds);
  const links = top.map((s) => `<a href="/skill/${esc(s.repo_full_name)}/">${esc(s.repo_name)}</a>`).join(", ");
  return `<tr>
          <td><strong ${bi(route, "name")}>${text(route, "name")}</strong><br><span style="color:var(--bp-text-muted);font-size:12px">${count} · ${links}</span></td>
          <td ${bi(route, "how")}>${text(route, "how")}</td>
          <td ${bi(route, "gain")}>${text(route, "gain")}</td>
          <td ${bi(route, "cost")}>${text(route, "cost")}</td>
        </tr>`;
}

function routesTable(m, cards, scenarioKinds) {
  const head = (en, zh) => `<th ${biAttrs(en, zh)}>${esc(en)}</th>`;
  return `<div class="bp-table-wrap"><table class="bp-table">
        <thead><tr>${head("Route", "路线")}${head("How it works", "怎么做")}${head("What you gain", "强项")}${head("What it costs", "代价")}</tr></thead>
        <tbody>${m.routes.map((r) => routeRow(r, cards, scenarioKinds)).join("")}</tbody>
      </table></div>`;
}

/** The install-safety floor, counted from the page's own security flags. */
function floorLine(cards) {
  const flagged = cards.filter((s) => ["caution", "unsafe"].includes((s.security_grade || "").toLowerCase()));
  const install = flagged.filter((s) => flags(s).length && flags(s).every((f) => INSTALL_RULES.has(f)));
  const en = `The floor is install safety. Of the ${flagged.length} entries on this page flagged CAUTION or UNSAFE, ` +
    `${install.length} are flagged only for how they install (sudo, or a curl | sh installer), not for anything they do while making slides.`;
  const zh = `底线是安装安全。这一页被标为 CAUTION 或 UNSAFE 的 ${flagged.length} 个条目里，` +
    `有 ${install.length} 个只是因为安装方式（sudo，或 curl | sh 安装脚本）被标，不是因为生成幻灯片时的行为。`;
  return `<p ${biAttrs(en, zh)}>${esc(en)}</p>`;
}

function list(items, key, tag = "ul") {
  const marker = tag === "ol" ? "decimal" : "disc";   // the base styles reset list-style
  return `<${tag} style="list-style:${marker};padding-left:22px;margin:8px 0;line-height:1.7">${items.map((i) => t(i, key, "li")).join("")}</${tag}>`;
}

function nextStop(m) {
  const rows = m.next_stop.map((r) => `<tr><td ${bi(r, "who")}>${text(r, "who")}</td><td ${bi(r, "pick")}><strong>${text(r, "pick")}</strong></td></tr>`);
  return `<div class="bp-table-wrap"><table class="bp-table"><tbody>${rows.join("")}</tbody></table></div>`;
}

function authorBox(a) {
  return `<div style="display:flex;gap:12px;align-items:flex-start;margin-top:20px;padding:14px 16px;border:1px solid var(--bp-border);border-radius:10px;background:var(--bp-card-bg)">
        <div style="font-size:13px;line-height:1.6;color:var(--bp-text-secondary)">
          <strong style="color:var(--bp-text)"><a href="${esc(a.about)}">${esc(a.name)}</a></strong>
          · <a href="${esc(a.x)}" rel="noopener">X</a> · <a href="${esc(a.github)}" rel="noopener">GitHub</a><br>
          <span ${bi(a, "role")}>${text(a, "role")}</span><br>
          <span ${biAttrs(`Last reviewed ${a.reviewed}`, `最近审阅 ${a.reviewed}`)}>Last reviewed ${esc(a.reviewed)}</span>
        </div>
      </div>`;
}

const h3 = (en, zh) => `<h3 style="font-size:17px;font-weight:600;margin:24px 0 8px" ${biAttrs(en, zh)}>${esc(en)}</h3>`;

/** The section, or "" when the page has no method or no reviewed kinds to count. */
export function methodHtml(scenario, cards, scenarioKinds) {
  const m = scenario.method;
  if (!m || !scenarioKinds) return "";
  return `<!-- Method -->
      <section class="bp-aeo-section" style="margin:32px 0;padding:24px;background:var(--bp-bg-alt);border-radius:12px;border:1px solid var(--bp-border)">
        ${t(m, "h2", "h2", 'class="bp-section-title" style="font-size:20px;margin-bottom:12px"')}
        ${t(m, "thesis", "p", 'style="font-size:15px;line-height:1.8"')}
        ${h3("Three routes, one gap", "三条路线，一道鸿沟")}
        ${routesTable(m, cards, scenarioKinds)}
        ${t(m, "gap", "p", 'style="line-height:1.8"')}
        ${h3("The next-stop rule: pick by who touches the deck next", "下一站原则：按这个 deck 下一步交给谁来选")}
        ${nextStop(m)}
        ${h3("Four questions we ask of every skill", "每个 skill 我们问四个问题")}
        ${list(m.questions, "q", "ol")}
        ${floorLine(cards)}
        ${h3("What we did, and what we did not", "我们做了什么，没做什么")}
        ${list(m.did, "item")}
        ${list(m.not_done, "item")}
        ${authorBox(m.author)}
      </section>`;
}

/** WebPage JSON-LD naming the author and the review date, or "" without a method. */
export function methodLd(scenario, pageUrl) {
  const a = scenario.method?.author;
  if (!a) return "";
  const person = { "@type": "Person", name: a.name, url: `https://agentskillshub.top${a.about}`, sameAs: [a.x, a.github] };
  const data = { "@context": "https://schema.org", "@type": "WebPage", url: pageUrl, author: person, reviewedBy: person, lastReviewed: a.reviewed };
  return `  <script type="application/ld+json">\n${JSON.stringify(data)}\n  </script>`;
}
