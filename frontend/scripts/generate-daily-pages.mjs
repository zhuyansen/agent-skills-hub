/**
 * Build-time /daily/{YYYY-MM-DD}/ pages + /daily/ index from the daily-report
 * archive (memory/daily-report-archive.md, git-tracked → available in CI).
 *
 * This is the water-system's ⑥ fresh-water layer: the daily report already
 * runs every day but only ever went to social and evaporated. Landing it as
 * dated, indexable pages gives crawlers a reason to return, gives X posts a
 * page to point at, and (page-foot newsletter) a return-visit hook (⑧).
 *
 * PURE STATIC (no SPA route). Each item links to its /skill/{repo}/ page —
 * outbound internal links that feed the skill catalog. The archive is the
 * source of truth: append a day to it and the next build renders it. No DB.
 */
import { readFileSync, mkdirSync, writeFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { SITE, esc, starsK } from "./shared-utils.mjs";

const ARCHIVE = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "..",
  "memory",
  "daily-report-archive.md",
);

/* ── Parse the archive (tolerant of both historical line formats) ── */
function parseArchive(md) {
  const days = [];
  let cur = null;
  for (const raw of md.split("\n")) {
    const line = raw.trim();
    const dm = line.match(/^##\s+(\d{4}-\d{2}-\d{2})/);
    if (dm) {
      cur = { date: dm[1], items: [], trend: "" };
      days.push(cur);
      continue;
    }
    if (!cur || !line || line.startsWith("---") || line.startsWith("#")) continue;
    if (line.startsWith("（注") || line.startsWith("(注")) continue;
    // The daily-report "🎯 今日趋势" summary line, if the archive carries it —
    // the editorial synthesis that makes a report a report, not just a list.
    if (/^(?:🎯|>?\s*(?:今日)?趋势\s*[:：])/u.test(line) && !/★|⭐|\/day/.test(line)) {
      cur.trend = line
        .replace(/^🎯\s*/u, "")
        .replace(/^>?\s*(?:今日)?趋势\s*[:：]?\s*/u, "")
        .trim();
      continue;
    }
    // Format-agnostic: an item line names an owner/repo and carries a
    // star/velocity marker. Covers "1. repo …（57★ 44/day）" and the older
    // "1️⃣ 🚀 repo — … ⭐524 145/day" alike.
    if (!/★|⭐|\/day/.test(line)) continue;

    const repoM = line.match(/([A-Za-z0-9][\w.-]*\/[A-Za-z0-9][\w.-]*)/);
    if (!repoM) continue;
    const repo = repoM[1];
    const starM = line.match(/(\d[\d,]*)\s*★|⭐\s*(\d[\d,]*)/);
    const stars = starM ? parseInt((starM[1] || starM[2]).replace(/,/g, ""), 10) : 0;
    const velM = line.match(/(\d[\d,]*)\s*\/day/);
    const velocity = velM ? parseInt(velM[1].replace(/,/g, ""), 10) : 0;
    const isNew = line.includes("\u{1F195}"); // 🆕
    const isHot = line.includes("\u{1F680}") || line.includes("\u{1F525}"); // 🚀 🔥

    let desc = "";
    const dash = line.indexOf("—"); // —
    if (dash >= 0) {
      desc = line
        .slice(dash + 1)
        .replace(/[\u{1F195}\u{1F680}\u{1F525}]/gu, "")
        .replace(/[（(][^）)]*[）)]\s*$/g, "")
        .replace(/⭐\s*\d[\d,]*.*$/g, "")
        .replace(/\d[\d,]*\s*★.*$/g, "")
        .trim();
    }
    if (desc) cur.items.push({ repo, desc, stars, velocity, isNew, isHot });
  }
  // Skip thin days (bare "1. repo" stubs in the older archive) — a page needs
  // real content, not a title with two links, or it's thin-content SEO poison.
  const MIN_ITEMS = 5;
  return days.filter((d) => d.items.length >= MIN_ITEMS);
}

/* ── Shared chrome ── */
const HEAD = (title, desc, canonical, ld) => `<!doctype html>
<html lang="en"><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}" />
<link rel="canonical" href="${esc(canonical)}" />
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<meta property="og:title" content="${esc(title)}" />
<meta property="og:description" content="${esc(desc)}" />
<meta property="og:type" content="website" />
<script type="application/ld+json">${ld}</script>
<script type="text/javascript">(function(c,l,a,r,i,t,y){c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);})(window, document, "clarity", "script", "wh16g932g8");</script>
</head><body style="margin:0;font-family:system-ui,-apple-system,sans-serif;color:#1e293b;background:#fff">
<div style="max-width:760px;margin:0 auto;padding:32px 20px">`;

const NEWSLETTER = `
  <section style="margin:36px 0 8px;border:1px solid #e2e8f0;border-radius:12px;padding:20px;background:#f8fafc">
    <h2 style="font-size:16px;margin:0 0 4px">Get this every day</h2>
    <p style="font-size:13px;color:#64748b;margin:0 0 12px">New AI agent skills &amp; MCP servers, security-graded, in your inbox. Free, weekly digest.</p>
    <form onsubmit="return (function(e){e.preventDefault();var em=e.target.querySelector('input').value;if(!em)return false;var b=e.target.querySelector('button');b.textContent='Subscribing…';fetch('https://vknzzecmzsfmohglpfgm.supabase.co/rest/v1/subscribers',{method:'POST',headers:{'Content-Type':'application/json','apikey':'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrbnp6ZWNtenNmbW9oZ2xwZmdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4MDQ3MzIsImV4cCI6MjA4ODM4MDczMn0.zFAGZH-lDcL-GwyMkR-9sSV8pJToVzomsJ_fuXZIoDo','Authorization':'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrbnp6ZWNtenNmbW9oZ2xwZmdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI4MDQ3MzIsImV4cCI6MjA4ODM4MDczMn0.zFAGZH-lDcL-GwyMkR-9sSV8pJToVzomsJ_fuXZIoDo','Prefer':'return=minimal'},body:JSON.stringify({email:em})}).then(function(r){b.textContent=(r.ok||r.status===409)?'Subscribed!':'Try again'}).catch(function(){b.textContent='Try again'});return false})(event)" style="display:flex;gap:8px;max-width:420px">
      <input type="email" required placeholder="you@example.com" style="flex:1;padding:9px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px" />
      <button type="submit" style="padding:9px 18px;border:0;border-radius:8px;background:#4f46e5;color:#fff;font-weight:600;font-size:14px;cursor:pointer">Subscribe</button>
    </form>
  </section>`;

const FOOT = `
  <p style="font-size:12px;color:#94a3b8;margin-top:28px;border-top:1px solid #e2e8f0;padding-top:14px">
    Picks ranked by star velocity from <a href="/" style="color:#4f46e5;text-decoration:none">Agent Skills Hub</a>'s scan of 130,000+ open-source AI agent skills &amp; MCP servers, security-graded &amp; refreshed every 8 hours.
  </p>
</div></body></html>`;

const prettyDate = (d) =>
  new Date(d + "T00:00:00Z").toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  });

/* ── Per-day page ── */
function dayHtml(day, prev, next) {
  const url = `${SITE}/daily/${day.date}/`;
  const title = `New AI Agent Skills — ${day.date} | Agent Skills Hub`;
  const desc = day.trend
    ? `${day.trend} — top ${day.items.length} new AI agent skills & MCP servers on ${day.date}, security-graded.`
    : `Top ${day.items.length} new open-source AI agent skills & MCP servers on ${day.date}, ranked by star velocity: ${day.items.slice(0, 3).map((i) => i.repo.split("/")[1]).join(", ")}. Security-graded.`;
  const ld = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: `New AI agent skills — ${day.date}`,
    itemListElement: day.items.map((it, i) => ({
      "@type": "ListItem",
      position: i + 1,
      url: `${SITE}/skill/${it.repo}/`,
      name: it.repo,
    })),
  });

  const rows = day.items
    .map((it, i) => {
      const badge = it.isHot
        ? `<span style="background:#fef2f2;color:#dc2626;font-size:11px;font-weight:600;padding:1px 7px;border-radius:999px">HOT</span>`
        : it.isNew
          ? `<span style="background:#eef2ff;color:#4f46e5;font-size:11px;font-weight:600;padding:1px 7px;border-radius:999px">NEW</span>`
          : "";
      const vel = it.velocity ? ` · ${it.velocity}★/day` : "";
      return `<li style="margin:0 0 14px;list-style:none">
        <div style="display:flex;align-items:baseline;gap:8px;flex-wrap:wrap">
          <span style="color:#94a3b8;font-size:13px;width:20px;display:inline-block">${i + 1}</span>
          <a href="/skill/${esc(it.repo)}/" style="color:#4f46e5;text-decoration:none;font-weight:600;font-size:15px">${esc(it.repo)}</a>
          ${badge}
          <span style="color:#94a3b8;font-size:12px">★ ${starsK(it.stars)}${vel}</span>
        </div>
        <p style="margin:2px 0 0 28px;color:#475569;font-size:13px;line-height:1.5">${esc(it.desc)}</p>
      </li>`;
    })
    .join("\n");

  const navLink = (d, label) =>
    d
      ? `<a href="/daily/${d.date}/" style="color:#4f46e5;text-decoration:none">${label} ${d.date}</a>`
      : `<span style="color:#cbd5e1">${label}</span>`;

  return (
    HEAD(title, desc, url, ld) +
    `
  <nav style="font-size:13px;color:#64748b;margin-bottom:18px">
    <a href="/" style="color:#4f46e5;text-decoration:none">Home</a> ›
    <a href="/daily/" style="color:#4f46e5;text-decoration:none">Daily</a> ›
    <span>${day.date}</span>
  </nav>
  <h1 style="font-size:25px;margin:0 0 4px">New AI agent skills &amp; MCP servers</h1>
  <p style="color:#64748b;margin:0 0 ${day.trend ? "14" : "24"}px">${prettyDate(day.date)} · top ${day.items.length} by star velocity</p>
  ${day.trend ? `<p style="margin:0 0 24px;padding:12px 16px;background:#f8fafc;border-left:3px solid #4f46e5;border-radius:6px;color:#334155;font-size:14px;line-height:1.6">🎯 ${esc(day.trend)}</p>` : ""}
  <ul style="padding:0;margin:0">${rows}</ul>
  <div style="display:flex;justify-content:space-between;margin:28px 0 0;font-size:13px">
    ${navLink(prev, "‹ Older")}
    <a href="/daily/" style="color:#4f46e5;text-decoration:none">All days</a>
    ${navLink(next, "Newer ›")}
  </div>` +
    NEWSLETTER +
    FOOT
  );
}

/* ── Index page ── */
function indexHtml(days) {
  const url = `${SITE}/daily/`;
  const title = `Daily New AI Agent Skills & MCP Servers | Agent Skills Hub`;
  const desc = `What's new every day in open-source AI agent skills and MCP servers — top picks by star velocity, security-graded. ${days.length} days archived.`;
  const ld = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: "Daily new AI agent skills",
    url,
  });
  const items = days
    .map(
      (d) =>
        `<li style="margin:0 0 8px;list-style:none"><a href="/daily/${d.date}/" style="color:#4f46e5;text-decoration:none;font-weight:600">${d.date}</a> <span style="color:#94a3b8;font-size:13px">— ${d.items.length} picks · ${d.items.slice(0, 2).map((i) => esc(i.repo.split("/")[1])).join(", ")}…</span></li>`,
    )
    .join("\n");
  return (
    HEAD(title, desc, url, ld) +
    `
  <nav style="font-size:13px;color:#64748b;margin-bottom:18px"><a href="/" style="color:#4f46e5;text-decoration:none">Home</a> › <span>Daily</span></nav>
  <h1 style="font-size:26px;margin:0 0 6px">Daily new AI agent skills</h1>
  <p style="color:#64748b;margin:0 0 24px">Fresh open-source AI agent skills &amp; MCP servers every day, ranked by star velocity and security-graded. ${days.length} days archived.</p>
  <ul style="padding:0;margin:0">${items}</ul>` +
    NEWSLETTER +
    FOOT
  );
}

function main() {
  if (!existsSync(ARCHIVE)) {
    console.log("  (no daily-report-archive.md — skipping /daily/)");
    return;
  }
  const days = parseArchive(readFileSync(ARCHIVE, "utf-8")).sort((a, b) =>
    b.date.localeCompare(a.date),
  ); // newest first
  if (!days.length) {
    console.log("  (archive had no parseable days — skipping)");
    return;
  }
  const base = join("dist", "daily");
  mkdirSync(base, { recursive: true });
  writeFileSync(join(base, "index.html"), indexHtml(days));
  // days sorted newest-first; prev = older (index+1), next = newer (index-1)
  days.forEach((day, i) => {
    const dir = join(base, day.date);
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, "index.html"), dayHtml(day, days[i + 1], days[i - 1]));
  });

  const today = new Date().toISOString().slice(0, 10);
  const urls = [`${SITE}/daily/`, ...days.map((d) => `${SITE}/daily/${d.date}/`)]
    .map(
      (u) =>
        `  <url><loc>${u}</loc><lastmod>${today}</lastmod><changefreq>daily</changefreq><priority>0.6</priority></url>`,
    )
    .join("\n");
  writeFileSync(
    "dist/sitemap-daily.xml",
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`,
  );
  console.log(`  ✓ /daily/ index + ${days.length} day pages + sitemap-daily.xml`);
}

main();
