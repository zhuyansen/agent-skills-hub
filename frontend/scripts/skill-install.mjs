/**
 * Install commands for a skill page, read from the repository's own README.
 *
 * Skill pages lead with what a repo is, how to install it and what to use
 * instead; the security verdict lives on /audit/ (owner's decision, 2026-10-14).
 * A title that promises "how to install" needs a real command on the page, so
 * the command is taken verbatim from the README's code blocks, never written by
 * us. A README without one gives an empty list and the page says nothing about
 * installing beyond the GitHub link.
 */

// One command per line, the way READMEs write them. Order does not matter: the
// first matching line in the README wins, which is the one its author put first.
const INSTALL_LINE = new RegExp(
  "^(?:\\$\\s*)?(?:" +
    [
      "npx\\s+\\S", "npm\\s+(?:i|install)\\s", "pnpm\\s+(?:add|dlx)\\s", "yarn\\s+(?:global\\s+)?add\\s", "bunx?\\s+(?:add\\s)?\\S",
      "pipx?\\s+install\\s", "uv\\s+(?:tool\\s+install|pip\\s+install|add)\\s", "uvx\\s+\\S",
      "brew\\s+install\\s", "cargo\\s+install\\s", "go\\s+install\\s", "gem\\s+install\\s",
      "docker\\s+(?:run|pull|compose\\s+up)\\s", "claude\\s+(?:mcp|plugin)\\s+(?:add|install)\\s",
      "/plugin\\s+(?:install|marketplace\\s+add)\\s", "codex\\s+mcp\\s+add\\s", "git\\s+clone\\s",
    ].join("|") +
    ")",
  "i",
);
const MAX_COMMANDS = 2;
const MAX_LENGTH = 160;

/** The README's fenced code blocks, in order. */
function codeBlocks(readme) {
  return [...(readme || "").matchAll(/```[^\n]*\n([\s\S]*?)```/g)].map((m) => m[1]);
}

// Template text a reader would have to replace: not a command we can show as-is.
const PLACEHOLDER = /YOUR[_-]?USER|YOUR[_-]|<your|<username|<repo|\[your|example\.com|xxx|\/path\/to\/|\/USER\//i;
// A clone from a host the reader cannot reach (a company's internal Git) is not an install step.
const PUBLIC_GIT = /git\s+clone\s+(?:--\S+\s+)*(?:https?:\/\/)?(?:www\.)?(?:github\.com|gitlab\.com|codeberg\.org|bitbucket\.org)\//i;

/** Every install line in the README, verbatim and in order, without a leading "$ ". */
function candidates(readme) {
  const lines = codeBlocks(readme).flatMap((b) => b.split("\n")).map((l) => l.trim().replace(/^\$\s*/, ""));
  return [...new Set(lines)].filter((l) => INSTALL_LINE.test(l) && l.length <= MAX_LENGTH && !PLACEHOLDER.test(l)
    && !l.endsWith("\\") && (!/^git\s+clone\b/i.test(l) || PUBLIC_GIT.test(l)));
}

/**
 * Up to MAX_COMMANDS install lines that name the repo, in the README's order. A line
 * that does not name it installs something else (`pip install -r requirements.txt`,
 * `uv pip install httpx`, `pip install uv`): on 122 reverse-engineering READMEs those
 * were the weak samples, so they are left out and such a page shows no install step.
 */
export function installCommands(readme, repoName = "") {
  const name = repoName.toLowerCase().replace(/[^a-z0-9]+/g, "");
  if (name.length < 3) return [];
  const mentions = (l) => l.toLowerCase().replace(/[^a-z0-9]+/g, "").includes(name);
  return candidates(readme).filter(mentions).slice(0, MAX_COMMANDS);
}

const escHtml = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/** "How to install" section, or "" when the README gave no command. */
export function installSectionHtml(repoName, commands, auditUrl) {
  if (!commands.length) return "";
  const check = auditUrl
    ? ` Check <a href="${escHtml(auditUrl)}" style="color:#4f46e5">the security audit</a> before running it.`
    : "";
  return `<section style="margin:20px 0">
        <h2 style="font-size:18px;color:#1e293b;margin-bottom:8px">How to install ${escHtml(repoName)}</h2>
        <pre style="background:#0f172a;color:#e2e8f0;padding:12px 14px;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.6"><code>${commands.map(escHtml).join("\n")}</code></pre>
        <p style="color:#64748b;font-size:13px;margin:6px 0 0">Taken from the project's README on GitHub.${check}</p>
      </section>`;
}
