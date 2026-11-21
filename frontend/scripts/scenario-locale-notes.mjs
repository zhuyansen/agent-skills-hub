/**
 * A short section in another language on an English scenario page (`locale_notes` in
 * scenario-keywords.json): a heading, a few paragraphs and questions, under its own lang
 * attribute. Added 2026-11-21 for Indonesian on /best/animation-skills/: 43% of that page's
 * animation searches came from Indonesia, India and Bangladesh, and Indonesian tutorials drove
 * "skill claude animasi" (ops/research/animation-demand). A whole Indonesian page waits on four
 * weeks of Search Console data.
 */
import { esc } from "./shared-utils.mjs";

export function localeNotesHtml(scenario) {
  return (scenario.locale_notes || []).map((n) => `
      <section lang="${esc(n.lang)}" style="margin-top:32px" class="bp-faq">
        <h2 class="bp-section-title" style="font-size:18px">${esc(n.heading)}</h2>
        ${(n.paragraphs || []).map((p) => `<p style="color:var(--bp-text-secondary);line-height:1.6">${esc(p)}</p>`).join("\n        ")}
        ${(n.faq || []).map((f) => `<details style="margin:8px 0;border:1px solid var(--bp-border);border-radius:8px;padding:12px;background:var(--bp-card-bg)">
          <summary style="cursor:pointer;font-weight:500;color:var(--bp-text)">${esc(f.q)}</summary>
          <p style="margin:8px 0 0;color:var(--bp-text-secondary);line-height:1.6">${esc(f.a)}</p>
        </details>`).join("\n        ")}
      </section>`).join("");
}
