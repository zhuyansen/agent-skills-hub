import test from "node:test";
import assert from "node:assert/strict";
import { scenarioCtaHtml, isSecurityCiScenario, SECURITY_CI_SLUGS } from "./scenario-cta.mjs";
import { zhTwin } from "./scenario-zh-page.mjs";

const EXPECTED_SECURITY_SLUGS = [
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
];

const GENERAL_SLUGS = [
  "claude-video-skills",
  "ppt-presentation",
  "animation-skills",
  "image-generation",
  "anti-slop",
  "ai-design",
  "seo-tools",
  "skill-management-tools",
  "codex-skills",
  "telegram-bot",
];

function wrapForTwin(bodyHtml, slug) {
  return `<html lang="en"><head>
<title>Test</title>
<meta name="description" content="Test" />
<meta property="og:title" content="Test" />
<meta property="og:description" content="Test" />
<meta property="og:url" content="https://agentskillshub.top/best/${slug}/" />
<meta name="twitter:title" content="Test" />
<meta name="twitter:description" content="Test" />
<link rel="canonical" href="https://agentskillshub.top/best/${slug}/" />
</head><body>${bodyHtml}</body></html>`;
}

function visibleText(html) {
  const body = html.match(/<body>([\s\S]*)<\/body>/)?.[1] ?? html;
  return body.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

test("isSecurityCiScenario classifies all 11 security/dev-governance slugs and excludes general slugs", () => {
  assert.equal(SECURITY_CI_SLUGS.size, EXPECTED_SECURITY_SLUGS.length);
  for (const slug of EXPECTED_SECURITY_SLUGS) {
    assert.equal(isSecurityCiScenario(slug), true, `expected ${slug} to be security/CI`);
  }
  for (const slug of GENERAL_SLUGS) {
    assert.equal(isSecurityCiScenario(slug), false, `expected ${slug} to be general`);
  }
});

test("security/dev-governance scenarios render /ci-gate/ primary, /analyzer/ secondary, and /pro/ tertiary CTAs", () => {
  const html = scenarioCtaHtml({ slug: "code-review" }, { itemCount: 120, safeN: 95, flaggedN: 25 });
  assert.match(html, /class="bp-intent-cta bp-intent-cta--security"/);
  assert.match(html, /Shipping agent skills in team repos\?/);
  assert.match(html, /25 of 120 tools here triggered security flags/);
  assert.match(
    html,
    /href="\/ci-gate\/\?from=best-code-review"[^>]*data-cta="best_cigate_cta_click"[^>]*data-scenario="code-review"/,
  );
  assert.match(
    html,
    /href="\/analyzer\/\?from=best-code-review"[^>]*data-cta="best_analyzer_cta_click"[^>]*data-scenario="code-review"/,
  );
  assert.match(
    html,
    /href="\/pro\/\?from=best-code-review"[^>]*data-cta="best_pro_cta_click"[^>]*data-scenario="code-review"/,
  );
});

test("security/dev-governance scenarios handle flaggedN === 0 gracefully", () => {
  const html = scenarioCtaHtml({ slug: "refactoring" }, { itemCount: 40, safeN: 40, flaggedN: 0 });
  assert.doesNotMatch(html, /0 of 40/);
  assert.match(html, /Audit all 40 tools here/);
  assert.match(html, /href="\/ci-gate\/\?from=best-refactoring"/);
});

test("general scenarios render /pro/ primary and /analyzer/ secondary CTAs with contextual counts", () => {
  const flaggedHtml = scenarioCtaHtml(
    { slug: "claude-video-skills" },
    { itemCount: 550, safeN: 420, flaggedN: 130 },
  );
  assert.match(flaggedHtml, /130 tools in this list triggered security flags/);
  assert.match(
    flaggedHtml,
    /href="\/pro\/\?from=best-claude-video-skills"[^>]*data-cta="best_pro_cta_click"[^>]*data-scenario="claude-video-skills"/,
  );
  assert.match(
    flaggedHtml,
    /href="\/analyzer\/\?from=best-claude-video-skills"[^>]*data-cta="best_analyzer_cta_click"[^>]*data-scenario="claude-video-skills"/,
  );
  assert.doesNotMatch(flaggedHtml, /\/ci-gate\//);

  const cleanHtml = scenarioCtaHtml(
    { slug: "ppt-presentation" },
    { itemCount: 259, safeN: 259, flaggedN: 0 },
  );
  assert.match(cleanHtml, /Filter all 259 skills by security rule, runtime &amp; maintenance with Pro/);
  assert.match(cleanHtml, /href="\/pro\/\?from=best-ppt-presentation"/);
  assert.match(cleanHtml, /href="\/analyzer\/\?from=best-ppt-presentation"/);
});

test("zhTwin translates both security and general CTAs cleanly into Chinese with zero leftover English prose", () => {
  const cases = [
    { slug: "code-review", counts: { itemCount: 120, safeN: 95, flaggedN: 25 } },
    { slug: "refactoring", counts: { itemCount: 40, safeN: 40, flaggedN: 0 } },
    { slug: "claude-video-skills", counts: { itemCount: 550, safeN: 420, flaggedN: 130 } },
    { slug: "ppt-presentation", counts: { itemCount: 259, safeN: 259, flaggedN: 0 } },
  ];

  const forbiddenEnglish = [
    /Shipping agent skills/i,
    /Block Risky Skills/i,
    /Scan Any Repo/i,
    /Pro Deep Search/i,
    /Try Pro Deep/i,
    /Verify before installing/i,
    /Filter faster/i,
    /Filter all \d+ skills/i,
    /triggered security flags/i,
    /Audit all \d+ tools/i,
  ];

  for (const { slug, counts } of cases) {
    const cta = scenarioCtaHtml({ slug }, counts);
    const twin = zhTwin(wrapForTwin(cta, slug), {
      enPath: `/best/${slug}/`,
      title: "中文标题",
      description: "中文描述",
      twinPaths: new Set(),
    });
    const text = visibleText(twin);

    // Must contain real Chinese copy and preserve all CTA links & tracking attrs.
    assert.match(text, /[\u4e00-\u9fff]{6,}/, `${slug}: expected Chinese text, got "${text}"`);
    assert.match(twin, new RegExp(`data-scenario="${slug}"`));
    assert.match(twin, /data-cta="best_analyzer_cta_click"/);
    assert.match(twin, /data-cta="best_pro_cta_click"/);
    if (isSecurityCiScenario(slug)) {
      assert.match(twin, /data-cta="best_cigate_cta_click"/);
      assert.match(text, /在 CI 中拦截高危 Skill/);
      assert.match(text, /免费扫描任意仓库/);
      assert.match(text, /Pro 深度筛选 \(\$39\/年\)/);
    } else {
      assert.match(text, /解锁 Pro 深度筛选/);
      assert.match(text, /免费扫描任意仓库/);
    }
    for (const bad of forbiddenEnglish) {
      assert.doesNotMatch(text, bad, `${slug}: leftover English matched ${bad} in "${text}"`);
    }
  }
});

test("returns empty string when scenario slug is missing", () => {
  assert.equal(scenarioCtaHtml(null), "");
  assert.equal(scenarioCtaHtml({}), "");
});
