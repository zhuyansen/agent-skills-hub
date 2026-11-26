/**
 * Intent-matched conversion strip for /best/<slug>/ pages.
 *
 * /best/* pages drive ~75% of organic search clicks, yet previously had zero links to
 * /pro/ or /ci-gate/ and only a tiny footer link to /analyzer/. This module renders a
 * compact, bilingual CTA bar right above Skill Cards tailored to the visitor's intent:
 *  - Security / Dev-Governance scenarios -> /ci-gate/ primary + /analyzer/ secondary + /pro/ link
 *  - All other scenarios -> /pro/ primary + /analyzer/ secondary
 *
 * Every visible text node carries flat data-en / data-zh attributes (never nested) so
 * scenario-zh-page.mjs's zhTwin() and the runtime language toggle translate it cleanly.
 */
import { esc, biAttrs } from "./shared-utils.mjs";

export const SECURITY_CI_SLUGS = new Set([
  "code-review",
  "secret-detection",
  "authentication",
  "claude-code-hooks",
  "ai-reverse-engineering",
  "refactoring",
  "debugging",
  "test-generation",
  "api-testing",
  "cli-tools",
  "git-tools",
]);

/** True when a /best/<slug>/ page maps to team security / PR governance intent. */
export function isSecurityCiScenario(slug) {
  return SECURITY_CI_SLUGS.has(String(slug || "").trim());
}

/**
 * Renders the intent-matched conversion strip placed above Skill Cards on /best/<slug>/.
 */
export function scenarioCtaHtml(scenario, { itemCount = 0, safeN = 0, flaggedN = 0 } = {}) {
  const slug = String(scenario?.slug || "").trim();
  if (!slug) return "";

  const slugEsc = esc(slug);
  const from = `best-${slugEsc}`;
  const isSecurity = isSecurityCiScenario(slug);

  if (isSecurity) {
    const titleEn = "Shipping agent skills in team repos?";
    const titleZh = "团队仓库接入 Agent Skill？";
    const copyEn =
      flaggedN > 0
        ? `${flaggedN} of ${itemCount} tools here triggered security flags. Gate every PR automatically before risky skills merge.`
        : itemCount > 0
          ? `Audit all ${itemCount} tools here and gate team PRs automatically against published security rules before merging.`
          : "Gate team PRs automatically against published security rules before risky skills merge.";
    const copyZh =
      flaggedN > 0
        ? `本榜 ${itemCount} 个工具中有 ${flaggedN} 个触发了安全告警。在 PR 合并前自动拦截高危 Skill。`
        : itemCount > 0
          ? `本榜共收录 ${itemCount} 个工具，接入 CI 在 PR 合并前按公开安全规则自动审查每个 Agent Skill。`
          : "在 PR 合并前按公开安全规则自动拦截高危 Agent Skill。";

    const ciEn = "Block Risky Skills in CI";
    const ciZh = "在 CI 中拦截高危 Skill";
    const scanEn = "Scan Any Repo Free";
    const scanZh = "免费扫描任意仓库";
    const proEn = "Pro Deep Search ($39/yr)";
    const proZh = "Pro 深度筛选 ($39/年)";

    return `<aside class="bp-intent-cta bp-intent-cta--security" aria-label="Security CI &amp; Pro tools">
        <div class="bp-intent-cta-body">
          <strong class="bp-intent-cta-title" ${biAttrs(titleEn, titleZh)}>${esc(titleEn)}</strong>
          <p class="bp-intent-cta-copy" ${biAttrs(copyEn, copyZh)}>${esc(copyEn)}</p>
        </div>
        <div class="bp-intent-cta-actions">
          <a class="bp-intent-btn bp-intent-btn--primary" href="/ci-gate/?from=${from}" data-cta="best_cigate_cta_click" data-scenario="${slugEsc}" ${biAttrs(ciEn, ciZh)}>${esc(ciEn)}</a>
          <a class="bp-intent-btn bp-intent-btn--secondary" href="/analyzer/?from=${from}" data-cta="best_analyzer_cta_click" data-scenario="${slugEsc}" ${biAttrs(scanEn, scanZh)}>${esc(scanEn)}</a>
          <a class="bp-intent-link" href="/pro/?from=${from}" data-cta="best_pro_cta_click" data-scenario="${slugEsc}" ${biAttrs(proEn, proZh)}>${esc(proEn)}</a>
        </div>
      </aside>`;
  }

  const titleEn =
    flaggedN > 0
      ? "Verify before installing — or filter deeper"
      : "Filter faster or scan before you install";
  const titleZh =
    flaggedN > 0
      ? "安装前先扫一遍，或用 Pro 深度筛选"
      : "更快筛出合适的 Skill，或安装前先扫描";
  const copyEn =
    flaggedN > 0
      ? `${flaggedN} tools in this list triggered security flags — scan before installing, or unlock Pro filters.`
      : itemCount > 0
        ? `Filter all ${itemCount} skills by security rule, runtime & maintenance with Pro, or scan any repo free.`
        : "Filter skills by security rule, runtime & maintenance with Pro, or scan any repo free.";
  const copyZh =
    flaggedN > 0
      ? `本榜有 ${flaggedN} 个工具触发了安全告警——安装前先免费扫描，或用 Pro 按规则与模型深度筛选。`
      : itemCount > 0
        ? `用 Pro 按安全规则、运行时与维护状态深度筛选全部 ${itemCount} 个工具，或免费扫描任意仓库。`
        : "用 Pro 按安全规则、运行时与维护状态深度筛选，或免费扫描任意仓库。";

  const proEn = "Try Pro Deep Search";
  const proZh = "解锁 Pro 深度筛选";
  const scanEn = "Scan Any Repo Free";
  const scanZh = "免费扫描任意仓库";

  return `<aside class="bp-intent-cta" aria-label="Pro search &amp; free security scanner" data-safe-count="${safeN}">
        <div class="bp-intent-cta-body">
          <strong class="bp-intent-cta-title" ${biAttrs(titleEn, titleZh)}>${esc(titleEn)}</strong>
          <p class="bp-intent-cta-copy" ${biAttrs(copyEn, copyZh)}>${esc(copyEn)}</p>
        </div>
        <div class="bp-intent-cta-actions">
          <a class="bp-intent-btn bp-intent-btn--primary" href="/pro/?from=${from}" data-cta="best_pro_cta_click" data-scenario="${slugEsc}" ${biAttrs(proEn, proZh)}>${esc(proEn)}</a>
          <a class="bp-intent-btn bp-intent-btn--secondary" href="/analyzer/?from=${from}" data-cta="best_analyzer_cta_click" data-scenario="${slugEsc}" ${biAttrs(scanEn, scanZh)}>${esc(scanEn)}</a>
        </div>
      </aside>`;
}
