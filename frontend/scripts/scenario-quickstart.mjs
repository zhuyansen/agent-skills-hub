/**
 * The "Quick Start" note on a scenario card whose repository has no install command:
 * the README's install (or usage) section as plain text, plus the first code block in
 * it. Kept out of generate-scenario-pages.mjs so it can be imported without running the
 * generator.
 */
import { stripMarkdown } from "./shared-utils.mjs";

const SECTIONS = [
  /## (?:Installation|Install|Getting Started|Quick Start|Setup)\s*\n([\s\S]*?)(?=\n## |\n$)/i,
  /## (?:Usage|How to Use|Examples?)\s*\n([\s\S]*?)(?=\n## |\n$)/i,
];
const MIN_SECTION_CHARS = 30;
const TEXT_MAX = 300;

/* A fenced block's body as GitHub shows it: no ``` lines, and no indent left from a
 * fence inside a list item. The cards printed the fences until 2026-10-29. */
function fencedBody(body) {
  const lines = body.trimEnd().split("\n");
  const indent = Math.min(...lines.filter((l) => l.trim()).map((l) => l.length - l.trimStart().length));
  return lines.map((l) => l.slice(indent)).join("\n");
}

export function extractQuickStart(readmeContent) {
  if (!readmeContent) return null;
  for (const pat of SECTIONS) {
    const match = readmeContent.match(pat);
    if (match && match[1].trim().length > MIN_SECTION_CHARS) {
      const codeMatch = match[1].match(/```[\w]*\n([\s\S]*?)```/);
      return {
        text: stripMarkdown(match[1]).slice(0, TEXT_MAX),
        code: codeMatch ? fencedBody(codeMatch[1]) : null,
      };
    }
  }
  return null;
}
