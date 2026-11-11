/**
 * "Tested by Agent Skills Hub" on a skill's own page (/skill/owner/repo/): the end-to-end
 * tests the scenario pages report (scenario-runs.json), shown where people who search a
 * skill by name land. On 2026-11-01 hugohe3/ppt-master, the first pick of the PPT test, had
 * a page Google had discovered but never crawled, while four weeks of searches for "ppt
 * master" (1,172 impressions) landed on the PPT page and 5 of them clicked.
 *
 * The page carries the entries twice: as HTML, for crawlers that do not run scripts, and as
 * <meta name="ash:tested"> for the React page Google renders (src/lib/prerenderedMeta.ts).
 * A run entry with `sub` tested one skill inside the repo, not the repo, so it is left out.
 */
import { existsSync, readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { esc } from "./shared-utils.mjs";
import { allRuns, runBits, seeLabel } from "./scenario-runs.mjs";
import {
  TESTED_TITLE, TESTED_SEE_ALL, TESTED_IMAGE_ALT, testedIntro, testedTop, testedPick, testedResult,
} from "../src/lib/testedCopy.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const SCENARIOS = new Map(JSON.parse(readFileSync(join(HERE, "scenario-keywords.json"), "utf-8")).map((s) => [s.slug, s]));
const ZH = JSON.parse(readFileSync(join(HERE, "scenario-zh.json"), "utf-8"));
const IMAGE = /\.(jpe?g|png|webp)$/i;
const PUBLIC = join(HERE, "..", "public");
const SHEET_SHOT = { w: 1200, h: 675 };   // the PPT test's slide sheets
/** Tests whose result is something to look at: the picture saved beside each tool's result page
 *  (its name with this suffix) and the size the block shows it at. */
const SHOTS = {
  "claude-video-skills": { suffix: ".jpg", w: 640, h: 360 },    // a frame of the film
  "3d-mcp": { suffix: ".webp", w: 640, h: 480 },                // the render (1200x900)
  "anti-slop-ui": { suffix: "-fold.webp", w: 640, h: 400 },     // the redone page's first screen (720x450)
};
const STRIP_SCALE = 2;   // a strip (the image test's six pictures in a row) is saved at twice its listed size
const same = (a, b) => a.toLowerCase() === b.toLowerCase();

function topPlace(scenario, repo) {
  const top = scenario.explainer?.top;
  const place = top ? top.items.findIndex((item) => same(item.repo, repo)) + 1 : 0;
  return place ? { place, title: [top.h2, top.h2_zh || top.h2], ranked: top.numbered !== false } : null;
}

/** What the tool made, to show in the block: { src, w, h }, or null when the test left no picture. */
export function shotFor(key, run, r, exists = existsSync) {
  if (IMAGE.test(r.sheet || "")) return { src: run.dir + r.sheet, ...SHEET_SHOT };
  const rule = SHOTS[key];
  if (rule && r.sheet) {
    const src = run.dir + r.sheet.replace(/\.html$/, rule.suffix);
    return exists(join(PUBLIC, src)) ? { src, w: rule.w, h: rule.h } : null;
  }
  return r.strip ? { src: run.dir + r.strip.src, w: r.strip.w * STRIP_SCALE, h: r.strip.h * STRIP_SCALE } : null;
}

function entry(key, run, repo) {
  const r = run.runs[repo];
  const slug = run.page || key;   // a further test on a page (the anti-slop page's interface test) names its page
  const scenario = SCENARIOS.get(slug) || { title: slug };
  const pick = run.verdict?.picks?.find((p) => same(p.repo, repo));
  return {
    page: `/best/${slug}/#${run.anchor || "test-results"}`,
    pageTitle: [scenario.title, ZH[slug]?.t || scenario.title],
    date: r.date || run.date,   // an entry run after the main test carries its own date
    tested: Object.values(run.runs).filter((x) => x.ran).length,
    bits: runBits(run, r),
    pick: pick ? { role: pick.role, why: pick.why } : null,
    top: topPlace(scenario, repo),
    evidence: { href: run.dir + r.sheet, image: IMAGE.test(r.sheet || ""), shot: shotFor(key, run, r), label: seeLabel(run) },
  };
}

function entriesWhere(repo, keep) {
  return Object.entries(allRuns())
    .filter(([, run]) => run.runs?.[repo]?.ran && keep(run.runs[repo]))
    .map(([key, run]) => entry(key, run, repo));
}

/** The tests this repository ran in, one entry each; [] for the rest. */
export function testedEntries(repo) {
  return entriesWhere(repo, (r) => !r.sub);
}

/** The tests one skill inside a repository ran in (run entries with `sub`), for its own page. */
export function testedSubEntries(repo, slug) {
  return entriesWhere(repo, (r) => r.sub === slug);
}

const P = "margin:0 0 6px;line-height:1.6;font-size:14px;color:#374151";
/** Each copy is an [English, Chinese] pair; `i` picks one (0 or 1). */
const para = (pair, i, style = P) => (pair ? `<p style="${style}">${esc(pair[i])}</p>` : "");

function entryHtml(e, i) {
  const shot = e.evidence.shot;
  const image = shot ? `<a href="${esc(e.evidence.href)}" target="_blank" rel="noopener">`
    + `<img src="${esc(shot.src)}" alt="${esc(TESTED_IMAGE_ALT[i])}" width="${shot.w}" height="${shot.h}" loading="lazy" `
    + `style="display:block;max-width:100%;height:auto;margin:8px 0;border-radius:8px;border:1px solid #e5e7eb"></a>` : "";
  return `<div style="margin:0 0 8px">
        ${para(testedIntro(e), i)}${para(testedTop(e), i, `${P};font-weight:600`)}${para(testedPick(e), i)}${para(testedResult(e), i)}
        ${image}<p style="${P}"><a href="${esc(e.evidence.href)}" target="_blank" rel="noopener">${esc(e.evidence.label[i])}</a>`
    + ` · <a href="${esc(e.page)}">${esc(TESTED_SEE_ALL[i])}</a></p>
      </div>`;
}

/** The static block, in the page's language like the audit verdict above it; "" without entries. */
export function testedHtml(entries, lang = "en") {
  if (!entries.length) return "";
  const i = lang === "zh" ? 1 : 0;
  return `<section style="margin:0 0 16px;padding:14px 16px;border:1px solid #c7d2fe;background:#f5f7ff;border-radius:10px">
        <h2 style="font-size:16px;margin:0 0 8px;color:#1e1b4b">🧪 ${esc(TESTED_TITLE[i])}</h2>
        ${entries.map((e) => entryHtml(e, i)).join("\n        ")}
      </section>`;
}

/** The entries for the React page, as a <meta> in the head; "" without entries. */
export function testedMeta(entries) {
  return entries.length ? `\n  <meta name="ash:tested" content="${esc(JSON.stringify(entries))}" />` : "";
}
