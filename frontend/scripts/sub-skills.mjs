/**
 * Sub-skill pages: one page per SKILL.md inside a repository that holds several skills
 * (table sub_skills, filled by backend/sub_skills_collect.py). The catalog is one row per
 * repository, so a skill that lives in a folder of a larger repository had no page and
 * could not rank for its own name (2026-10-31).
 *
 * A new page starts with no click history, so they go out in batches: a page only when its
 * repository's own page may be indexed (MIN_STARS_TO_INDEX) and its SKILL.md says what it
 * does, never for a project's own contributor skills (dot folders) or a second copy of the
 * same SKILL.md, at most PER_REPO_PAGE_CAP per repository, SUB_SKILL_PAGE_CAP in all. Raise
 * the caps once Search Console shows the first batch crawled and earning impressions.
 */
import { SUPABASE_URL, SUPABASE_ANON_KEY, SITE, MIN_STARS_TO_INDEX, esc } from "./shared-utils.mjs";
import {
  subSkillTitle, subSkillDescription, subSkillPath, subSkillUrl, skillMdUrl, githubFolderUrl, subSkillInstall,
} from "../src/lib/subSkillMeta.mjs";
import { HOW_WE_GRADE_PATH } from "../src/lib/howWeGradeMeta.mjs";

export const SUB_SKILL_PAGE_CAP = 200;
export const PER_REPO_PAGE_CAP = 25;
export const MIN_DESCRIPTION_CHARS = 30;
/** Under dist/: the published sub-skill URLs with lastmod, read by generate-sitemap.mjs. */
export const SUB_SKILL_MANIFEST = "sub-skill-pages.json";
const FETCH_PAGE = 1000;
const PARENT_CHUNK = 40;
const LIST_DESCRIPTION_MAX = 140;
const PARENT_LIST_SHOWN = 50;
const SIBLINGS_SHOWN = 20;
const RETRIES = 3;
const HEADERS = { apikey: SUPABASE_ANON_KEY, Authorization: `Bearer ${SUPABASE_ANON_KEY}` };
const SUB_COLUMNS = "id,repo_full_name,path,slug,name,description,body_excerpt,security_grade,blob_sha";
const PARENT_COLUMNS = "repo_full_name,repo_name,stars,repo_status,last_commit_at,author_avatar_url";
const GRADE_LABELS = { safe: "SAFE", caution: "CAUTION", unsafe: "UNSAFE", reject: "REJECT" };

// ── data ──────────────────────────────────────────────────────────────────────────

async function getJson(url) {
  for (let attempt = 1; ; attempt++) {
    const r = await fetch(url, { headers: HEADERS });
    if (r.ok) return r.json();
    if (attempt >= RETRIES) throw new Error(`${r.status} on ${url.split("?")[0]}`);
    await new Promise((res) => setTimeout(res, 1000 * attempt));
  }
}

/** Every sub_skills row, keyset-paged by id. */
export async function fetchSubSkills() {
  const rows = [];
  for (let last = 0; ; ) {
    const page = await getJson(`${SUPABASE_URL}/rest/v1/sub_skills?select=${SUB_COLUMNS}&id=gt.${last}&order=id.asc&limit=${FETCH_PAGE}`);
    rows.push(...page);
    if (page.length < FETCH_PAGE) return rows;
    last = page[page.length - 1].id;
  }
}

/** The parent repositories by name, a few dozen per request: never the whole catalog again. */
export async function fetchParents(names) {
  const parents = new Map();
  for (let i = 0; i < names.length; i += PARENT_CHUNK) {
    const list = names.slice(i, i + PARENT_CHUNK).map((n) => `"${n}"`).join(",");
    const rows = await getJson(`${SUPABASE_URL}/rest/v1/skills?select=${PARENT_COLUMNS}&repo_full_name=in.(${encodeURIComponent(list)})`);
    for (const r of rows) parents.set(r.repo_full_name, r);
  }
  return parents;
}

const keyOf = (s) => `${s.repo_full_name}\u0000${s.slug}`;

/** Skills a project keeps for itself, not for someone outside to install: its contributors'
 *  (.agents/skills/, .claude/skills/: openclaw's QA lanes, n8n's PR checks) and the ones its
 *  own product loads from a monorepo package (n8n's packages/@n8n/instance-ai/skills/). */
const isInternal = (s) => s.path.split("/").some((seg) => seg.startsWith(".") || seg === "packages");

/** The batch that gets pages, most-starred parents first. */
export function selectPublished(subs, parents) {
  const stars = (s) => parents.get(s.repo_full_name)?.stars ?? 0;
  const live = (s) => parents.get(s.repo_full_name)?.repo_status !== "gone";
  const eligible = subs.filter((s) => stars(s) >= MIN_STARS_TO_INDEX && live(s) && !isInternal(s)
    && (s.description || "").length >= MIN_DESCRIPTION_CHARS);
  eligible.sort((a, b) => stars(b) - stars(a) || a.repo_full_name.localeCompare(b.repo_full_name)
    || a.slug.localeCompare(b.slug));
  return capPerRepo(firstCopies(eligible)).slice(0, SUB_SKILL_PAGE_CAP);
}

/** A SKILL.md copied unchanged into another repository (a fork, a collection, the stale row of a
 *  renamed repository) gets one page, in the first repository: the most starred. */
function firstCopies(sorted) {
  const seen = new Set();
  return sorted.filter((s) => {
    if (seen.has(s.blob_sha)) return false;
    seen.add(s.blob_sha);
    return true;
  });
}

function capPerRepo(sorted) {
  const perRepo = new Map();
  return sorted.filter((s) => {
    const n = (perRepo.get(s.repo_full_name) || 0) + 1;
    perRepo.set(s.repo_full_name, n);
    return n <= PER_REPO_PAGE_CAP;
  });
}

function cut(text, max) {
  const chars = Array.from(String(text || ""));
  return chars.length > max ? `${chars.slice(0, max - 1).join("").trim()}…` : chars.join("");
}

/** repo -> its skills for the list on the repository page and sub-skills.json, published ones
 *  first. Only repositories with at least one published page; never contributor skills. */
export function repoLists(subs, published) {
  const pub = new Set(published.map(keyOf));
  const byRepo = new Map();
  for (const s of subs.filter((x) => !isInternal(x))) {
    if (!byRepo.has(s.repo_full_name)) byRepo.set(s.repo_full_name, []);
    byRepo.get(s.repo_full_name).push({ slug: s.slug, name: s.name, path: s.path, grade: s.security_grade,
      description: cut(s.description, LIST_DESCRIPTION_MAX), page: pub.has(keyOf(s)) });
  }
  const lists = new Map();
  for (const [repo, list] of byRepo) {
    if (list.some((x) => x.page)) lists.set(repo, list.sort((a, b) => b.page - a.page || a.name.localeCompare(b.name)));
  }
  return lists;
}

// ── the list on the repository page ──────────────────────────────────────────────

function itemHtml(repo, item) {
  const href = item.page ? subSkillPath(repo, item.slug) : githubFolderUrl(repo, item.path);
  const external = item.page ? "" : ' rel="noopener" target="_blank"';
  return `<li style="font-size:14px;line-height:1.6"><a href="${esc(href)}"${external} style="color:#4f46e5;font-weight:600;text-decoration:none">${esc(item.name)}</a>${item.description ? ` <span style="color:#64748b">${esc(item.description)}</span>` : ""}</li>`;
}

/** "Skills in this repository" for the static repository page. */
export function parentSectionHtml(repo, list) {
  const shown = list.slice(0, PARENT_LIST_SHOWN).map((item) => itemHtml(repo, item)).join("\n          ");
  const more = list.length > PARENT_LIST_SHOWN
    ? `<p style="font-size:13px;color:#64748b;margin:6px 0 0">${list.length - PARENT_LIST_SHOWN} more in <a href="https://github.com/${esc(repo)}" rel="noopener" target="_blank" style="color:#4f46e5">the repository on GitHub</a>.</p>`
    : "";
  return `<section style="margin:20px 0">
        <h2 style="font-size:18px;color:#1e293b;margin-bottom:8px">Skills in this repository (${list.length})</h2>
        <ul style="list-style:none;padding:0;margin:0;display:grid;gap:6px">
          ${shown}
        </ul>
        ${more}
      </section>`;
}

// ── the sub-skill page ───────────────────────────────────────────────────────────

function jsonLd(sub, parent) {
  const repoUrl = `${SITE}/skill/${sub.repo_full_name}/`;
  const crumbs = [["Home", `${SITE}/`], [sub.repo_full_name, repoUrl], [sub.name, subSkillUrl(sub.repo_full_name, sub.slug)]];
  const breadcrumb = { "@context": "https://schema.org", "@type": "BreadcrumbList",
    itemListElement: crumbs.map(([name, item], i) => ({ "@type": "ListItem", position: i + 1, name, item })) };
  const code = { "@context": "https://schema.org", "@type": "SoftwareSourceCode", name: sub.name,
    description: sub.description, codeRepository: githubFolderUrl(sub.repo_full_name, sub.path),
    url: subSkillUrl(sub.repo_full_name, sub.slug), isPartOf: { "@type": "SoftwareSourceCode", name: parent.repo_full_name, url: repoUrl } };
  return [breadcrumb, code].map((o) => `<script type="application/ld+json">${JSON.stringify(o).replace(/</g, "\\u003c")}</script>`).join("\n  ");
}

function socialTags(title, desc, url) {
  return `<meta property="og:title" content="${esc(title)}" />
  <meta property="og:description" content="${esc(desc)}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="${esc(url)}" />
  <meta property="og:site_name" content="Agent Skills Hub" />
  <meta property="og:image" content="${SITE}/og-image.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="${esc(title)}" />
  <meta name="twitter:description" content="${esc(desc)}" />
  <meta name="twitter:site" content="@GoSailGlobal" />`;
}

function headHtml(sub, parent, assetTags) {
  const title = subSkillTitle(sub.repo_full_name, sub.name, sub.description);
  const desc = subSkillDescription(sub.repo_full_name, sub.name, sub.description);
  const url = subSkillUrl(sub.repo_full_name, sub.slug);
  return `<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="referrer" content="strict-origin-when-cross-origin" />
  <title>${esc(title)}</title>
  <meta name="description" content="${esc(desc)}" />
  ${socialTags(title, desc, url)}
  <link rel="canonical" href="${esc(url)}" />
  ${jsonLd(sub, parent)}
  <link rel="preconnect" href="https://vknzzecmzsfmohglpfgm.supabase.co" />
  ${assetTags.scriptTags.join("\n  ")}
  ${assetTags.linkTags.join("\n  ")}
</head>`;
}

function gradeHtml(sub) {
  const label = GRADE_LABELS[sub.security_grade];
  const text = label ? `Security grade of this SKILL.md: <strong>${label}</strong>` : "This SKILL.md has not been graded yet";
  return `<p style="margin:0 0 16px;font-size:14px;color:#475569">${text} · <a href="${HOW_WE_GRADE_PATH}" style="color:#4f46e5;text-decoration:none">how we grade</a></p>`;
}

function installHtml(sub) {
  return `<section style="margin:20px 0">
        <h2 style="font-size:18px;color:#1e293b;margin-bottom:8px">How to install ${esc(sub.name)}</h2>
        <pre style="background:#0f172a;color:#e2e8f0;padding:12px 14px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.6"><code>${esc(subSkillInstall(sub.repo_full_name, sub.name))}</code></pre>
        <p style="color:#64748b;font-size:13px;margin:6px 0 0">The skills CLI copies this one skill into Claude Code (use <code>-a</code> for another agent). Or read <a href="${esc(skillMdUrl(sub.repo_full_name, sub.path))}" rel="noopener" target="_blank" style="color:#4f46e5">its SKILL.md on GitHub</a>.</p>
      </section>`;
}

function excerptHtml(sub) {
  if (!sub.body_excerpt || sub.body_excerpt === sub.description) return "";
  return `<section style="margin:20px 0">
        <h2 style="font-size:18px;color:#1e293b;margin-bottom:8px">What the SKILL.md says</h2>
        <p style="margin:0;font-size:14px;line-height:1.75;color:#334155">${esc(sub.body_excerpt)}</p>
      </section>`;
}

function siblingsHtml(sub, list) {
  const others = list.filter((x) => x.slug !== sub.slug).slice(0, SIBLINGS_SHOWN);
  if (!others.length) return "";
  return `<section style="margin:20px 0">
        <h2 style="font-size:18px;color:#1e293b;margin-bottom:8px">Other skills in ${esc(sub.repo_full_name)}</h2>
        <ul style="list-style:none;padding:0;margin:0;display:grid;gap:6px">
          ${others.map((item) => itemHtml(sub.repo_full_name, item)).join("\n          ")}
        </ul>
      </section>`;
}

function heroHtml(sub, parent) {
  const repoPath = `/skill/${sub.repo_full_name}/`;
  return `<nav style="font-size:13px;color:#64748b;margin-bottom:16px">
        <a href="/" style="color:#4f46e5;text-decoration:none">Home</a><span style="margin:0 6px">&gt;</span>
        <a href="${esc(repoPath)}" style="color:#4f46e5;text-decoration:none">${esc(sub.repo_full_name)}</a><span style="margin:0 6px">&gt;</span>
        <span>${esc(sub.name)}</span>
      </nav>
      <h1 style="font-size:28px;margin:0 0 8px">${esc(sub.name)}</h1>
      <p style="margin:0 0 12px;font-size:14px;color:#64748b">A skill in <a href="${esc(repoPath)}" style="color:#4f46e5;text-decoration:none">${esc(sub.repo_full_name)}</a> · ${Number(parent.stars || 0).toLocaleString("en-US")} stars on GitHub</p>
      <p style="margin:0 0 12px;font-size:16px;line-height:1.7">${esc(sub.description)}</p>`;
}

/** The static page for one sub-skill; React takes over once its bundle loads. */
export function buildSubSkillHtml(sub, parent, list, assetTags) {
  return `<!doctype html>
<html lang="en">
${headHtml(sub, parent, assetTags)}
<body>
  <div id="root">
    <!-- Static SEO content — replaced by React on hydration -->
    <div style="max-width:800px;margin:40px auto;font-family:system-ui,-apple-system,sans-serif;padding:0 20px;color:#1e293b">
      ${heroHtml(sub, parent)}
      ${gradeHtml(sub)}
      ${installHtml(sub)}
      ${excerptHtml(sub)}
      ${siblingsHtml(sub, list)}
    </div>
  </div>
</body>
</html>`;
}
