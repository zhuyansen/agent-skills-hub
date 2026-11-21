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
 *              "match": "front-?end|taste", "limit": 8, "after": "explainer" }
 *
 * `after` is optional: the section goes after the caution unless it says "explainer".
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
function quickPick(scenario, skills) {
  // `quick_pick` (scenario-keywords.json): the owner names the entry when the most-starred
  // one is not what the page's query is after. On the SEO page that was a 54K-star marketing
  // pack, above claude-seo, the repo "claude seo skill" returns first (10-13).
  const want = (scenario.quick_pick || "").toLowerCase();
  const named = want && skills.find((s) => s.repo_full_name.toLowerCase() === want);
  if (named) return { pick: named, safe: named.security_grade === "safe" };
  const safe = skills.slice(0, QUICK_PICK_SCAN).filter((s) => s.security_grade === "safe")
    .sort((a, b) => b.stars - a.stars)[0];
  return { pick: safe || skills[0], safe: Boolean(safe) };
}
/** A page with an end-to-end test names the test's first pick (run.verdict), with the
 *  reason, not the most-starred entry: the two disagreed on the skill managers page. */
function testedPickHtml(verdict, skills, itemCount, subject, scenario, testedCount = 0) {
  const first = verdict.picks[0];
  const pick = skills.find((s) => s.repo_full_name.toLowerCase() === first.repo.toLowerCase());
  if (!pick) return "";
  // The pick is for a situation ("For a PowerPoint file a colleague will edit"), so the sentence says which.
  // verdict.basis: how we got there when it was not a run (the Telegram page read the source).
  const [how, howZh] = verdict.basis || [
    testedCount ? `after testing ${testedCount} of ${itemCount} tools` : `after testing ${itemCount} tools`,
    testedCount ? `从 ${itemCount} 个工具中实测 ${testedCount} 个后` : `实测 ${itemCount} 个工具后`,
  ];
  const safeN = skills.filter((s) => s.security_grade === "safe").length;
  const lead = bi(
    `The best ${subject} in 2026 is `,
    `2026 年最佳${scenario.zhTitle}是 `,
  );
  const roleEn = first.role[0].replace(/\.$/, "");
  const roleZh = first.role[1].replace(/。$/, "");
  const mid = bi(
    ` (★ ${starsK(pick.stars)}, ${how} on Agent Skills Hub (agentskillshub.top), ${safeN} of ${itemCount} rated SAFE) — best for: ${roleEn}. `,
    `（★ ${starsK(pick.stars)}，Agent Skills Hub（agentskillshub.top）${howZh}，${safeN}/${itemCount} 个通过 SAFE 安全评级）—— 适用人群/场景：${roleZh}。`,
  );
  const why = bi(first.why[0], first.why[1], "color:var(--bp-text-secondary);font-size:13px");
  const more = `<a href="#test-results" style="color:var(--bp-link);white-space:nowrap" data-en="${verdict.more?.[0] || "See the test →"}" data-zh="${verdict.more?.[1] || "看实测 →"}">${verdict.more?.[0] || "See the test →"}</a>`;
  // A name other entries share (several collections are called "skills") is shown with its owner.
  const shared = skills.filter((s) => s.repo_name === pick.repo_name).length > 1;
  const link = `<a href="${SITE}/skill/${esc(pick.repo_full_name)}/" style="color:var(--bp-link);font-weight:700;text-decoration:none">${esc(shared ? pick.repo_full_name : pick.repo_name)}</a>`;
  return `<div class="bp-quick-pick">
        <span style="font-size:20px">⚡</span>
        <p style="flex:1;min-width:200px;margin:0">${lead}${link}${mid}${why} ${more}</p>
      </div>`;
}

export function quickPickHtml(scenario, skills, itemCount, subject, verdict = null, testedCount = 0) {
  if (!skills.length) return "";
  if (verdict?.answer) return answerHtml(verdict, subject, scenario, skills, itemCount);
  const tested = verdict?.picks?.length
    ? testedPickHtml(verdict, skills, itemCount, subject, scenario, testedCount)
    : "";
  if (tested) return tested;
  const { pick, safe } = quickPick(scenario, skills);
  const stars = `★ ${starsK(pick.stars)}`;
  const safeN = skills.filter((s) => s.security_grade === "safe").length;
  // The language toggle replaces each [data-zh] element's text, so the link stays
  // outside the translated pieces.
  const lead = bi(
    `The best ${subject} in 2026 is `,
    `2026 年最佳${scenario.zhTitle}是 `,
  );
  const tail = bi(
    safe
      ? ` (rated SAFE by Agent Skills Hub (agentskillshub.top), ${stars}; ${safeN} of ${itemCount} tools rated SAFE) — best for developers and AI agents needing ${subject.toLowerCase()}.`
      : ` (${stars}; ${safeN} of ${itemCount} tools rated SAFE on Agent Skills Hub (agentskillshub.top)) — best for developers and AI agents needing ${subject.toLowerCase()}.`,
    safe
      ? `（Agent Skills Hub（agentskillshub.top）安全扫描评级 SAFE，${stars}；共 ${itemCount} 个工具中 ${safeN} 个通过 SAFE 评级）—— 适合需要${scenario.zhTitle}的开发者与 AI Agent。`
      : `（${stars}；Agent Skills Hub（agentskillshub.top）共 ${itemCount} 个工具中 ${safeN} 个通过 SAFE 评级）—— 适合需要${scenario.zhTitle}的开发者与 AI Agent。`,
  );
  const desc = bi(" " + descEn(pick).slice(0, QUICK_PICK_DESC),
    " " + (descZh(pick) || descEn(pick)).slice(0, QUICK_PICK_DESC), "color:var(--bp-text-secondary);font-size:13px");
  const link = `<a href="${SITE}/skill/${esc(pick.repo_full_name)}/" style="color:var(--bp-link);font-weight:700;text-decoration:none">${esc(pick.repo_name)}</a>`;
  return `<div class="bp-quick-pick">
        <span style="font-size:20px">⚡</span>
        <p style="flex:1;min-width:200px;margin:0">${lead}${link}${tail}${desc}</p>
      </div>`;
}
/** A test whose answer is not one skill (the image page: no skill beat Claude Code alone on the text,
 *  so the pick is by look) says so in the box instead: verdict.answer, an [English, Chinese] pair. */
function answerHtml(verdict, subject = "", scenario = {}, skills = [], itemCount = 0) {
  const [more, moreZh] = verdict.more || ["See the test →", "看实测 →"];
  const safeN = skills.filter((s) => s.security_grade === "safe").length;
  const prefix = subject
    ? bi(
        `The best ${subject} in 2026 depends on the visual style you want (${safeN} of ${itemCount} rated SAFE on Agent Skills Hub (agentskillshub.top)): `,
        `2026 年最佳${scenario.zhTitle || subject}取决于你想要的画风（Agent Skills Hub（agentskillshub.top）${itemCount} 个中 ${safeN} 个通过 SAFE 评级）：`,
      )
    : "";
  return `<div class="bp-quick-pick">
        <span style="font-size:20px">⚡</span>
        <p style="flex:1;min-width:200px;margin:0">${prefix}${bi(...verdict.answer)} <a href="#test-results" style="color:var(--bp-link);white-space:nowrap" data-en="${esc(more)}" data-zh="${esc(moreZh)}">${esc(more)}</a></p>
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
  // owner/repo: the official Remotion repo is just "skills", and two "taste-skill" rows sat side by side.
  const grade = GRADE_LABEL[s.security_grade];
  const link = `<a href="${SITE}/skill/${esc(s.repo_full_name)}/" style="color:var(--bp-link);font-weight:600;text-decoration:none">${esc(s.repo_full_name)}</a>`;
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

/** The focus section if it goes at `place`: after the caution (default), or right after
 *  the explainer with `"after": "explainer"`. The video page moved its Remotion section
 *  up there on 11-03: Remotion searches sat at position 9.5 (10-26 to 11-01) while the
 *  section answering them came after the method section. */
export function focusAt(place, scenario, skills) {
  return (scenario.focus?.after || "caution") === place ? focusHtml(scenario, skills) : "";
}
