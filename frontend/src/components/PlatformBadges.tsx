interface Props {
  platforms: string; // JSON string
  max?: number;
}

const PLATFORM_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  python: { label: "Python", color: "text-yellow-800", bg: "bg-yellow-50" },
  node: { label: "Node.js", color: "text-green-800", bg: "bg-green-50" },
  go: { label: "Go", color: "text-cyan-800", bg: "bg-cyan-50" },
  rust: { label: "Rust", color: "text-orange-800", bg: "bg-orange-50" },
  docker: { label: "Docker", color: "text-blue-800", bg: "bg-blue-50" },
  cli: { label: "CLI", color: "text-gray-800", bg: "bg-gray-100" },
  claude: { label: "Claude", color: "text-violet-800", bg: "bg-violet-50" },
  codex: { label: "Codex", color: "text-emerald-800", bg: "bg-emerald-50" },
  gemini: { label: "Gemini", color: "text-blue-800", bg: "bg-blue-50" },
  mcp: { label: "MCP", color: "text-indigo-800", bg: "bg-indigo-50" },
  vscode: { label: "VS Code", color: "text-blue-800", bg: "bg-blue-50" },
  browser: { label: "Browser", color: "text-pink-800", bg: "bg-pink-50" },
  java: { label: "Java", color: "text-red-800", bg: "bg-red-50" },
  ruby: { label: "Ruby", color: "text-red-800", bg: "bg-red-50" },
  shell: { label: "Shell", color: "text-gray-800", bg: "bg-gray-100" },
};

export function PlatformBadges({ platforms, max = 4 }: Props) {
  let parsed: string[] = [];
  try {
    parsed = JSON.parse(platforms);
  } catch {
    return null;
  }

  if (parsed.length === 0) return null;

  const shown = parsed.slice(0, max);
  const remaining = parsed.length - max;

  return (
    <div className="flex flex-wrap gap-1">
      {shown.map((p) => {
        const config = PLATFORM_CONFIG[p] || { label: p, color: "text-gray-700", bg: "bg-gray-50" };
        return (
          <span
            key={p}
            className={`inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium rounded ${config.bg} ${config.color}`}
          >
            {config.label}
          </span>
        );
      })}
      {remaining > 0 && (
        <span className="inline-flex items-center px-1.5 py-0.5 text-[10px] text-gray-500 bg-gray-50 rounded">
          +{remaining}
        </span>
      )}
    </div>
  );
}
