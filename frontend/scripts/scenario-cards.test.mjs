import test from "node:test";
import assert from "node:assert/strict";
import {
  INITIAL_CARDS,
  splitScenarioCards,
  serializeOverflowCards,
  moreCardsButtonHtml,
} from "./scenario-cards.mjs";
import { zhTwin } from "./scenario-zh-page.mjs";

const makeSkill = (i) => ({
  repo_name: `tool-${i}`,
  repo_full_name: `org/tool-${i}`,
  author_name: `org`,
  stars: 1000 - i,
  category: "ai-agent",
  description: `Description for tool ${i}`,
  install_commands: i % 2 === 0 ? [`npx tool-${i}`] : [],
});

test("splitScenarioCards keeps all cards when count <= INITIAL_CARDS", () => {
  const cards = Array.from({ length: 12 }, (_, i) => makeSkill(i));
  const { initial, overflow } = splitScenarioCards(cards);
  assert.equal(initial.length, 12);
  assert.equal(overflow.length, 0);
});

test("splitScenarioCards windows large pages to INITIAL_CARDS with exact tail overflow", () => {
  const cards = Array.from({ length: 208 }, (_, i) => makeSkill(i));
  const { initial, overflow } = splitScenarioCards(cards);
  assert.equal(initial.length, INITIAL_CARDS);
  assert.equal(overflow.length, 208 - INITIAL_CARDS);
  assert.equal(initial[0].repo_name, "tool-0");
  assert.equal(overflow[0].repo_name, `tool-${INITIAL_CARDS}`);
});

test("serializeOverflowCards preserves rank offset, kind, install command and run lines", () => {
  const overflow = [makeSkill(20), makeSkill(21)];
  const fakeKinds = {
    kinds: [{ id: "ui", en: "UI Systems", zh: "UI 系统", icon: "🎨" }],
    of: () => "ui",
  };
  const payload = serializeOverflowCards(overflow, {
    startIndex: 20,
    scenarioKinds: fakeKinds,
    twoWeeksAgo: Date.now(),
    runLines: (s) => (s.repo_name === "tool-20" ? '<div class="bp-sc-run">Tested</div>' : ""),
  });
  assert.equal(payload.length, 2);
  assert.equal(payload[0].i, 20);
  assert.equal(payload[0].k, "ui");
  assert.equal(payload[0].ce, "UI Systems");
  assert.equal(payload[0].cz, "UI 系统");
  assert.equal(payload[0].ic, "npx tool-20");
  assert.equal(payload[0].rl, '<div class="bp-sc-run">Tested</div>');
  assert.equal(payload[1].i, 21);
  assert.equal(payload[1].ic, undefined);
  assert.equal(payload[1].rl, undefined);
});

test("moreCardsButtonHtml emits bilingual button that zhTwin rewrites cleanly", () => {
  assert.equal(moreCardsButtonHtml("ai-design", 20, 0), "");
  const btn = moreCardsButtonHtml("ai-design", 208, 188);
  assert.match(btn, /data-more-url="\/best\/ai-design\/more-cards\.json"/);
  assert.match(btn, />Show all 208 tools \(\+188 more\)</);

  const page = `<html lang="en"><head><title>T</title><meta name="description" content="D" /><meta property="og:title" content="T" /><meta property="og:description" content="D" /><meta property="og:url" content="https://agentskillshub.top/best/ai-design/" /><meta name="twitter:title" content="T" /><meta name="twitter:description" content="D" /><link rel="canonical" href="https://agentskillshub.top/best/ai-design/" /></head><body><h1 data-zh="最佳 AI 设计">Best AI Design</h1>${btn}</body></html>`;
  const zh = zhTwin(page, {
    enPath: "/best/ai-design/",
    title: "最佳 AI 设计",
    description: "中文描述",
    twinPaths: new Set(["/best/ai-design/"]),
  });
  assert.match(zh, />展开全部 208 个工具（还有 188 个）</);
  assert.match(zh, /data-more-url="\/best\/ai-design\/more-cards\.json"/);
});
