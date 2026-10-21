import { useState } from "react";
import { useI18n } from "../i18n/I18nContext";
import type { Skill } from "../types/skill";

interface Props {
  skill: Skill;
  /** Install lines taken verbatim from the README, when the page has them. */
  readmeCommands?: string[];
}

export interface InstallOption {
  label: string;
  command: string;
  primary?: boolean;
  fromReadme?: boolean;
}

// What the first word of a README install line says about it, as a tab label.
const LABELS: Record<string, string> = {
  npm: "npm", npx: "npx", pnpm: "pnpm", yarn: "yarn", bun: "bun", bunx: "bunx",
  pip: "pip", pipx: "pipx", uv: "uv", uvx: "uvx", brew: "Homebrew", cargo: "Cargo",
  go: "Go", gem: "gem", docker: "Docker", claude: "Claude Code", "/plugin": "Claude Code",
  codex: "Codex", git: "Git Clone",
};

const labelOf = (command: string) => LABELS[command.split(/\s+/)[0].toLowerCase()] ?? "README";

// The `skills` CLI copies a repository's SKILL.md folders into each agent's skill
// directory, so it works for any repository that holds skills.
const SKILL_AGENTS: [string, string][] = [
  ["claude-code", "Claude Code"],
  ["cursor", "Cursor"],
  ["codex", "Codex"],
  ["opencode", "OpenCode"],
];

/**
 * Install options for a repository: the README's own install lines first (verbatim),
 * then the `skills` CLI for skill repositories, then git clone. Nothing is guessed from
 * the category or the language, the same rule as the static page
 * (scripts/skill-install.mjs). A guessed `npx <repo>` or `pip install <repo>` names a
 * package that may not exist, and the old Claude Code tab handed the GitHub page to
 * mcp-remote as if it were a hosted MCP server, a command that can never run; it was the
 * default on 10,422 of 15,063 skill pages (reported by a maintainer, 2026-10-21).
 */
export function getInstallCommands(
  skill: Skill,
  readmeCommands: string[] = [],
): InstallOption[] {
  const name = skill.repo_full_name;
  const options: InstallOption[] = readmeCommands.map((command) => ({
    label: labelOf(command),
    command,
    fromReadme: true,
  }));
  const taken = (label: string) => options.some((o) => o.label === label);
  if ((skill.category || "").toLowerCase().includes("skill")) {
    for (const [agent, label] of SKILL_AGENTS) {
      if (!taken(label)) options.push({ label, command: `npx skills add ${name} --agent ${agent}` });
    }
  }
  if (!taken("Git Clone")) {
    options.push({ label: "Git Clone", command: `git clone https://github.com/${name}.git` });
  }
  return options.map((o, i) => ({ ...o, primary: i === 0 }));
}

export function InstallCommand({ skill, readmeCommands = [] }: Props) {
  const { t } = useI18n();
  const commands = getInstallCommands(skill, readmeCommands);
  const [activeIdx, setActiveIdx] = useState(0);
  const [copied, setCopied] = useState(false);

  const active = commands[activeIdx];

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(active.command);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
      const textarea = document.createElement("textarea");
      textarea.value = active.command;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="w-full">
      {/* Tab selector for multiple install methods */}
      {commands.length > 1 && (
        <div className="flex items-center gap-1 mb-2">
          {commands.map((cmd, i) => (
            <button
              key={cmd.label}
              onClick={() => setActiveIdx(i)}
              className={`px-2.5 py-1 text-xs rounded-md transition-colors cursor-pointer ${
                i === activeIdx
                  ? "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-medium"
                  : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800"
              }`}
            >
              {cmd.label}
            </button>
          ))}
        </div>
      )}

      {/* Command display with copy button */}
      <div className="flex items-center gap-2 bg-gray-900 dark:bg-gray-950 rounded-lg pl-4 pr-2 py-2.5 group">
        <code className="flex-1 text-sm text-green-400 font-mono truncate select-all">
          {active.command}
        </code>
        <button
          onClick={handleCopy}
          className="shrink-0 w-8 h-8 flex items-center justify-center rounded-md hover:bg-gray-700 transition-colors text-gray-400 hover:text-white cursor-pointer"
          aria-label={t("detail.copyCommand")}
          title={t("detail.copyCommand")}
        >
          {copied ? (
            <svg
              className="w-4 h-4 text-green-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          ) : (
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
          )}
        </button>
      </div>
      {active.fromReadme && (
        <p className="mt-1.5 text-xs text-gray-500 dark:text-gray-400">
          {t("detail.installFromReadme")}
        </p>
      )}
    </div>
  );
}
