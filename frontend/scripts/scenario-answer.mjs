/**
 * The parts of a scenario page that answer the search directly, above the full list.
 *
 * quickPickHtml: one declarative sentence naming the entry to start with.
 * focusHtml: a page's `focus` section (scenario-keywords.json) for a sub-topic people
 * search by name, e.g. "frontend design skill" on the design page (DataForSEO, 10-06:
 * ~5,000 US searches a month across its variants, KD 2-10). Hand-written paragraphs
 * plus the page's own entries that match `focus.match`, most-starred first:
 *
 *   "focus": { "id": "frontend-design", "h2": "...", "h2_zh": "...",
 *              "paragraphs": ["..."], "paragraphs_zh": ["..."],
 *              "command": "/plugin install ...", "source": {"url": "...", "label": "...", "label_zh": "..."},
 *              "match": "front-?end|taste", "limit": 8 }
 */
import { SITE, esc, starsK } from "./shared-utils.mjs";
import { descZh, descEn } from "./scenario-kinds.mjs";

// The page's answer in one declarative sentence, above everything else in the body.
// AI answers quote the first part of a page and prefer a plain claim ("the best X is Y")
// over a description (Tanya Van Gastel, Shenzhen SEO side event 2026-09: 44% of cited
// text sits in the first 30% of the page). The pick is the most-starred entry rated SAFE
// among the top ones: the order is match score, so the first SAFE one can be a small repo
// (an 856★ starter kit on the video page, above HyperFrames). The sentence never
// recommends a flagged repo; with no SAFE one, the top entry and no safety claim.
const QUICK_PICK_SCAN = 10;
const QUICK_PICK_DESC = 140;
function quickPick(skills) {
  const safe = skills.slice(0, QUICK_PICK_SCAN).filter((s) => s.security_grade === "safe")
    .sort((a, b) => b.stars - a.stars)[0];
  return { pick: safe || skills[0], safe: Boolean(safe) };
}
/** A page with an end-to-end test names the test's first pick (run.verdict), with the
 *  reason, not the most-starred entry: the two disagreed on the skill managers page. */
function testedPickHtml(verdict, skills, itemCount, subject, scenario) {
  const first = verdict.picks[0];
  const pick = skills.find((s) => s.repo_full_name.toLowerCase() === first.repo.toLowerCase());
  if (!pick) return "";
  // The pick is for a situation ("For a PowerPoint file a colleague will edit"), so the sentence says which.
  // verdict.basis: how we got there when it was not a run (the Telegram page read the source).
  const [how, howZh] = verdict.basis || ["after testing them", "实测后"];
  const lead = bi(`Of the ${itemCount} ${subject} here, our pick ${how} is `, `这 ${itemCount} 个${scenario.zhTitle}里，${howZh}的首选是 `);
  const tail = bi(` (★ ${starsK(pick.stars)}). `, `（★ ${starsK(pick.stars)}）。`);
  const why = bi(`${first.role[0]}: ${first.why[0]}`, `${first.role[1]}：${first.why[1]}`, "color:var(--bp-text-secondary);font-size:13px");
  const more = `<a href="#test-results" style="color:var(--bp-link);white-space:nowrap" data-en="${verdict.more?.[0] || "See the test →"}" data-zh="${verdict.more?.[1] || "看实测 →"}">${verdict.more?.[0] || "See the test →"}</a>`;
  const link = `<a href="${SITE}/skill/${esc(pick.repo_full_name)}/" style="color:var(--bp-link);font-weight:700;text-decoration:none">${esc(pick.repo_name)}</a>`;
  return `<div class="bp-quick-pick">
        <span style="font-size:20px">⚡</span>
        <p style="flex:1;min-width:200px;margin:0">${lead}${link}${tail}${why} ${more}</p>
      </div>`;
}

export function quickPickHtml(scenario, skills, itemCount, subject, verdict = null) {
  if (!skills.length) return "";
  const tested = verdict?.picks?.length ? testedPickHtml(verdict, skills, itemCount, subject, scenario) : "";
  if (tested) return tested;
  const { pick, safe } = quickPick(skills);
  const stars = `★ ${starsK(pick.stars)}`;
  // The language toggle replaces each [data-zh] element's text, so the link stays
  // outside the translated pieces.
  const lead = bi(`Of the ${itemCount} ${subject} here, the best one to start with is `,
    `这 ${itemCount} 个${scenario.zhTitle}里，首选 `);
  const tail = bi(safe ? ` (rated SAFE by our security scan, ${stars}).` : ` (${stars}).`,
    safe ? `（安全扫描评级 SAFE，${stars}）。` : `（${stars}）。`);
  const desc = bi(" " + descEn(pick).slice(0, QUICK_PICK_DESC),
    " " + (descZh(pick) || descEn(pick)).slice(0, QUICK_PICK_DESC), "color:var(--bp-text-secondary);font-size:13px");
  const link = `<a href="${SITE}/skill/${esc(pick.repo_full_name)}/" style="color:var(--bp-link);font-weight:700;text-decoration:none">${esc(pick.repo_name)}</a>`;
  return `<div class="bp-quick-pick">
        <span style="font-size:20px">⚡</span>
        <p style="flex:1;min-width:200px;margin:0">${lead}${link}${tail}${desc}</p>
      </div>`;
}
function bi(en, zh, style = "") {
  return `<span${style ? ` style="${style}"` : ""} data-en="${esc(en)}" data-zh="${esc(zh)}">${esc(en)}</span>`;
}

const FOCUS_LIMIT = 8;
const FOCUS_DESC = 140;
const GRADE_LABEL = { safe: "SAFE", caution: "CAUTION", unsafe: "UNSAFE", reject: "REJECT" };
const P_STYLE = "color:var(--bp-text-secondary);line-height:1.8;font-size:15px;margin:0 0 12px";

function focusRow(s) {
  const grade = GRADE_LABEL[s.security_grade];
  const link = `<a href="${SITE}/skill/${esc(s.repo_full_name)}/" style="color:var(--bp-link);font-weight:600;text-decoration:none">${esc(s.repo_name)}</a>`;
  const meta = `<span style="color:var(--bp-text-muted);font-size:13px"> ★ ${starsK(s.stars)}${grade ? ` · ${grade}` : ""}</span>`;
  const desc = bi(" — " + descEn(s).slice(0, FOCUS_DESC), " — " + (descZh(s) || descEn(s)).slice(0, FOCUS_DESC),
    "color:var(--bp-text-secondary);font-size:14px");
  return `<li style="margin:0 0 8px">${link}${meta}${desc}</li>`;
}

function focusSource(f) {
  const src = f.source ? `<a href="${esc(f.source.url)}" target="_blank" rel="noopener" style="color:var(--bp-link)" ` +
    `data-en="${esc(f.source.label)}" data-zh="${esc(f.source.label_zh || f.source.label)}">${esc(f.source.label)}</a>` : "";
  const cmd = f.command ? `<pre style="margin:0 0 12px;padding:10px 12px;border-radius:8px;background:var(--bp-bg);` +
    `border:1px solid var(--bp-border);overflow-x:auto;font-size:13px"><code>${esc(f.command)}</code></pre>` : "";
  return cmd + (src ? `<p style="${P_STYLE}">${src}</p>` : "");
}

export function focusHtml(scenario, skills) {
  const f = scenario.focus;
  if (!f) return "";
  const re = new RegExp(f.match, "i");
  const rows = skills.filter((s) => re.test(`${s.repo_full_name} ${s.description || ""}`))
    .sort((a, b) => b.stars - a.stars).slice(0, f.limit || FOCUS_LIMIT);
  const paras = f.paragraphs.map((p, i) => `<p style="${P_STYLE}" data-en="${esc(p)}" ` +
    `data-zh="${esc((f.paragraphs_zh || [])[i] || p)}">${esc(p)}</p>`).join("\n        ");
  return `<section id="${esc(f.id)}" style="margin:32px 0">
        <h2 class="bp-section-title" data-en="${esc(f.h2)}" data-zh="${esc(f.h2_zh || f.h2)}">${esc(f.h2)}</h2>
        ${paras}
        ${focusSource(f)}
        ${rows.length ? `<ul style="padding-left:20px;margin:8px 0 0">${rows.map(focusRow).join("")}</ul>` : ""}
      </section>`;
}
