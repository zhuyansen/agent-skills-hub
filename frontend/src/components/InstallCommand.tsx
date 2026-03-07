import { useState } from "react";
import { useI18n } from "../i18n/I18nContext";
import type { Skill } from "../types/skill";

interface Props {
  skill: Skill;
}

function getInstallCommands(skill: Skill): { label: string; command: string; primary?: boolean }[] {
  const commands: { label: string; command: string; primary?: boolean }[] = [];
  const platforms = parsePlatforms(skill.platforms);
  const category = skill.category?.toLowerCase() || "";
  const name = skill.repo_full_name;

  // Claude Code install (for claude-skill, mcp-server categories)
  if (
    category.includes("claude") ||
    category.includes("mcp") ||
    platforms.includes("claude-code") ||
    platforms.includes("mcp")
  ) {
    commands.push({
      label: "Claude Code",
      command: `claude mcp add ${skill.repo_name} -- npx -y @anthropic-ai/mcp-remote@latest https://github.com/${name}`,
      primary: true,
    });
  }

  // npx for Node/TypeScript
  if (skill.language === "TypeScript" || skill.language === "JavaScript" || platforms.includes("node")) {
    commands.push({
      label: "npx",
      command: `npx ${skill.repo_name}`,
    });
  }

  // pip for Python
  if (skill.language === "Python" || platforms.includes("python")) {
    commands.push({
      label: "pip",
      command: `pip install ${skill.repo_name}`,
    });
  }

  // Docker
  if (platforms.includes("docker")) {
    commands.push({
      label: "Docker",
      command: `docker run ghcr.io/${name}`,
    });
  }

  // Always add git clone as fallback
  commands.push({
    label: "Git Clone",
    command: `git clone https://github.com/${name}.git`,
  });

  // Mark first as primary if none set
  if (commands.length > 0 && !commands.some((c) => c.primary)) {
    commands[0].primary = true;
  }

  return commands;
}

function parsePlatforms(platforms: string): string[] {
  try {
    return JSON.parse(platforms || "[]");
  } catch {
    return [];
  }
}

export function InstallCommand({ skill }: Props) {
  const { t } = useI18n();
  const commands = getInstallCommands(skill);
  const [activeIdx, setActiveIdx] = useState(commands.findIndex((c) => c.primary) || 0);
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
                  ? "bg-blue-100 text-blue-700 font-medium"
                  : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
              }`}
            >
              {cmd.label}
            </button>
          ))}
        </div>
      )}

      {/* Command display with copy button */}
      <div className="flex items-center gap-2 bg-gray-900 rounded-lg pl-4 pr-2 py-2.5 group">
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
            <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
