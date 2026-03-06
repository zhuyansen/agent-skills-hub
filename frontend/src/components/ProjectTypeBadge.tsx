const TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  "agent-framework": { label: "Agent框架", color: "text-purple-700 bg-purple-50 border-purple-200" },
  "mcp-server": { label: "MCP", color: "text-indigo-700 bg-indigo-50 border-indigo-200" },
  "claude-skill": { label: "Claude Skill", color: "text-violet-700 bg-violet-50 border-violet-200" },
  "codex-skill": { label: "Codex Skill", color: "text-emerald-700 bg-emerald-50 border-emerald-200" },
  "agent-tool": { label: "Agent工具", color: "text-blue-700 bg-blue-50 border-blue-200" },
  "llm-plugin": { label: "LLM插件", color: "text-amber-700 bg-amber-50 border-amber-200" },
  "skill": { label: "Skill", color: "text-cyan-700 bg-cyan-50 border-cyan-200" },
  "tool": { label: "Tool", color: "text-gray-600 bg-gray-50 border-gray-200" },
};

interface Props {
  type: string;
}

export function ProjectTypeBadge({ type }: Props) {
  const cfg = TYPE_CONFIG[type] || TYPE_CONFIG["tool"];
  return (
    <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded border ${cfg.color}`}>
      {cfg.label}
    </span>
  );
}
