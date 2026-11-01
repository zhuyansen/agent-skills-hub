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
import { readFileSync } from "fs";
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
const same = (a, b) => a.toLowerCase() === b.toLowerCase();

function topPlace(scenario, repo) {
  const top = scenario.explainer?.top;
  const place = top ? top.items.findIndex((item) => same(item.repo, repo)) + 1 : 0;
  return place ? { place, title: [top.h2, top.h2_zh || top.h2] } : null;
}

function entry(slug, run, repo) {
  const r = run.runs[repo];
  const scenario = SCENARIOS.get(slug) || { title: slug };
  const pick = run.verdict?.picks?.find((p) => same(p.repo, repo));
  return {
    page: `/best/${slug}/#test-results`,
    pageTitle: [scenario.title, ZH[slug]?.t || scenario.title],
    date: run.date,
    tested: Object.values(run.runs).filter((x) => x.ran).length,
    bits: runBits(run, r),
    pick: pick ? { role: pick.role, why: pick.why } : null,
    top: topPlace(scenario, repo),
    evidence: { href: run.dir + r.sheet, image: IMAGE.test(r.sheet || ""), label: seeLabel(run) },
  };
}

/** The tests this repository ran in, one entry each; [] for the rest. */
export function testedEntries(repo) {
  return Object.entries(allRuns())
    .filter(([, run]) => run.runs?.[repo]?.ran && !run.runs[repo].sub)
    .map(([slug, run]) => entry(slug, run, repo));
}

const P = "margin:0 0 6px;line-height:1.6;font-size:14px;color:#374151";
const para = (pair, style = P) => (pair ? `<p style="${style}">${esc(pair[0])}</p>` : "");

function entryHtml(e) {
  const image = e.evidence.image ? `<a href="${esc(e.evidence.href)}" target="_blank" rel="noopener">`
    + `<img src="${esc(e.evidence.href)}" alt="${esc(TESTED_IMAGE_ALT[0])}" width="1200" height="675" loading="lazy" `
    + `style="display:block;max-width:100%;height:auto;margin:8px 0;border-radius:8px;border:1px solid #e5e7eb"></a>` : "";
  return `<div style="margin:0 0 8px">
        ${para(testedIntro(e))}${para(testedTop(e), `${P};font-weight:600`)}${para(testedPick(e))}${para(testedResult(e))}
        ${image}<p style="${P}"><a href="${esc(e.evidence.href)}" target="_blank" rel="noopener">${esc(e.evidence.label[0])}</a>`
    + ` · <a href="${esc(e.page)}">${esc(TESTED_SEE_ALL[0])}</a></p>
      </div>`;
}

/** The static block (English, like the audit verdict above it); "" without entries. */
export function testedHtml(entries) {
  if (!entries.length) return "";
  return `<section style="margin:0 0 16px;padding:14px 16px;border:1px solid #c7d2fe;background:#f5f7ff;border-radius:10px">
        <h2 style="font-size:16px;margin:0 0 8px;color:#1e1b4b">🧪 ${esc(TESTED_TITLE[0])}</h2>
        ${entries.map(entryHtml).join("\n        ")}
      </section>`;
}

/** The entries for the React page, as a <meta> in the head; "" without entries. */
export function testedMeta(entries) {
  return entries.length ? `\n  <meta name="ash:tested" content="${esc(JSON.stringify(entries))}" />` : "";
}
