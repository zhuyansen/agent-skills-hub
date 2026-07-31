import { useState } from "react";
import { useI18n } from "../i18n/I18nContext";
import type { Skill } from "../types/skill";

interface Props {
  skill: Skill;
}

const SITE = "https://agentskillshub.top";

function buildBadge(fullName: string): string {
  return `[![Security-graded by Agent Skills Hub](${SITE}/badge/${fullName}.svg)](${SITE}/skill/${fullName}/)`;
}

// Badge + install line as ONE snippet. Distribution insight (2026-07-31): a
// third-party vendor skill (ParkStatic) listed three rival hubs' install
// commands in its README and ours was absent — authors copy whatever the hub
// hands them, and we were only handing out a badge. Shipping the install line
// in the same clipboard payload is the cheapest route into that default list.
// `ash install` is real (CLI v0.4.0) and prints the security grade before the
// install command — that safety step is the reason to prefer it, so the
// snippet says so instead of just being another install line.
function buildSnippet(fullName: string): string {
  return `${buildBadge(fullName)}

\`\`\`bash
# Check the security grade, then install
npx @agentskillshub/cli install ${fullName}
\`\`\``;
}

async function copyText(text: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
  }
}

// Badge SVGs are generated only for the quality catalog (stars >= 5, matches
// generate-badges.mjs) — below that the file doesn't exist, so offering the
// snippet would hand the author a 404.
const MIN_STARS_FOR_BADGE = 5;

export function BadgeEmbed({ skill }: Props) {
  const { lang } = useI18n();
  const isZh = lang === "zh";
  const [copied, setCopied] = useState(false);
  const snippet = buildSnippet(skill.repo_full_name);

  if ((skill.stars || 0) < MIN_STARS_FOR_BADGE) {
    return (
      <p className="text-xs text-gray-400 dark:text-gray-500">
        {isZh
          ? `README 徽章将在仓库达到 ${MIN_STARS_FOR_BADGE}★ 后自动可用(每 8 小时刷新)。`
          : `The README badge unlocks automatically once the repo reaches ${MIN_STARS_FOR_BADGE}★ (refreshed every 8h).`}
      </p>
    );
  }

  const handleCopy = async () => {
    await copyText(snippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-full">
      <div className="flex items-center gap-3 mb-2">
        <img
          src={`${SITE}/badge/${skill.repo_full_name}.svg`}
          alt="Security grade badge"
          height={20}
          className="h-5"
          loading="lazy"
        />
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {isZh
            ? "把安全评级 + 安装命令挂到你的 README"
            : "Add the security grade + install command to your README"}
        </span>
      </div>
      <div className="flex items-start gap-2 bg-gray-900 dark:bg-gray-950 rounded-lg pl-4 pr-2 py-2.5">
        <code className="flex-1 text-xs text-green-400 font-mono whitespace-pre-wrap break-all select-all">
          {snippet}
        </code>
        <button
          onClick={handleCopy}
          className="shrink-0 w-8 h-8 flex items-center justify-center rounded-md hover:bg-gray-700 transition-colors text-gray-400 hover:text-white cursor-pointer"
          aria-label={isZh ? "复制片段" : "Copy snippet"}
          title={isZh ? "复制片段" : "Copy snippet"}
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
    </div>
  );
}
