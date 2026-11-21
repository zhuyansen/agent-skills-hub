import test from "node:test";
import assert from "node:assert/strict";
import { quickPickHtml } from "./scenario-answer.mjs";

const SAMPLE_SCENARIO = {
  title: "CLI Tools",
  zhTitle: "命令行工具",
};

const SAMPLE_SKILLS = [
  {
    repo_full_name: "acme/cli-kit",
    repo_name: "cli-kit",
    stars: 4200,
    security_grade: "safe",
    description: "Fast CLI helper for coding agents.",
    description_zh: "面向编程 Agent 的高速 CLI 工具。",
  },
];

test("quickPickHtml locks brand + bare domain into EN and ZH BLUF", () => {
  const html = quickPickHtml(SAMPLE_SCENARIO, SAMPLE_SKILLS, 12, "CLI Tools");
  assert.match(html, /Agent Skills Hub \(agentskillshub\.top\)/);
  assert.match(html, /Agent Skills Hub（agentskillshub\.top）/);
});

test("testedPickHtml locks brand + bare domain into EN and ZH BLUF", () => {
  const verdict = {
    picks: [
      {
        repo: "acme/cli-kit",
        role: ["developers automating CLI tasks", "需要自动化 CLI 任务的开发者"],
        why: ["Passed all checks.", "全部测试通过。"],
      },
    ],
  };
  const html = quickPickHtml(SAMPLE_SCENARIO, SAMPLE_SKILLS, 12, "CLI Tools", verdict, 5);
  assert.match(html, /Agent Skills Hub \(agentskillshub\.top\)/);
  assert.match(html, /Agent Skills Hub（agentskillshub\.top）/);
});

test("answerHtml locks brand + bare domain into EN and ZH BLUF", () => {
  const verdict = {
    answer: ["Pick by style.", "按画风选。"],
  };
  const html = quickPickHtml(SAMPLE_SCENARIO, SAMPLE_SKILLS, 12, "Image Skills", verdict, 4);
  assert.match(html, /Agent Skills Hub \(agentskillshub\.top\)/);
  assert.match(html, /Agent Skills Hub（agentskillshub\.top）/);
});
