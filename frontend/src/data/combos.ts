export interface ComboRecipe {
  id: string;
  name: string;
  name_zh: string;
  description: string;
  description_zh: string;
  trigger_keywords: string[];
  skills: string[];
  icon: string;
}

export const COMBO_RECIPES: ComboRecipe[] = [
  {
    id: "claude-code-db",
    name: "Claude Code + Database",
    name_zh: "Claude Code + 数据库工作流",
    description: "Build AI apps with database integration",
    description_zh: "构建带数据库的 AI 应用",
    trigger_keywords: ["claude", "code", "cursor", "copilot", "coding-agent"],
    skills: ["anthropics/claude-code", "supabase/supabase", "modelcontextprotocol/servers"],
    icon: "🔗",
  },
  {
    id: "mcp-stack",
    name: "MCP Full Stack",
    name_zh: "MCP 全家桶",
    description: "Complete MCP server development toolkit",
    description_zh: "MCP 服务器开发全套工具",
    trigger_keywords: ["mcp", "model-context-protocol", "mcp-server"],
    skills: ["modelcontextprotocol/servers", "modelcontextprotocol/inspector", "modelcontextprotocol/create-python-server"],
    icon: "🔌",
  },
  {
    id: "ai-agent-starter",
    name: "AI Agent Starter Kit",
    name_zh: "AI Agent 入门套件",
    description: "Everything to build your first AI agent",
    description_zh: "构建首个 AI Agent 所需一切",
    trigger_keywords: ["agent", "framework", "langchain", "langgraph", "crew", "autogen"],
    skills: ["langchain-ai/langgraph", "crewAIInc/crewAI", "anthropics/claude-code"],
    icon: "🤖",
  },
  {
    id: "rag-pipeline",
    name: "RAG Pipeline",
    name_zh: "RAG 检索增强管线",
    description: "Build retrieval-augmented generation systems",
    description_zh: "构建检索增强生成系统",
    trigger_keywords: ["rag", "retrieval", "vector", "embedding", "knowledge", "search"],
    skills: ["langchain-ai/langchain", "chroma-core/chroma", "qdrant/qdrant"],
    icon: "🔍",
  },
  {
    id: "local-ai",
    name: "Local AI Setup",
    name_zh: "本地 AI 部署方案",
    description: "Run AI models locally without cloud APIs",
    description_zh: "本地运行 AI 模型，无需云 API",
    trigger_keywords: ["ollama", "llama", "local", "self-hosted", "gguf", "mlx"],
    skills: ["ollama/ollama", "ggerganov/llama.cpp", "open-webui/open-webui"],
    icon: "🏠",
  },
  {
    id: "automation-workflow",
    name: "Automation Workflow",
    name_zh: "自动化工作流",
    description: "No-code AI automation pipelines",
    description_zh: "无代码 AI 自动化管线",
    trigger_keywords: ["automat", "workflow", "n8n", "zapier", "no-code", "low-code"],
    skills: ["n8n-io/n8n", "langflow-ai/langflow", "FlowiseAI/Flowise"],
    icon: "⚡",
  },
  {
    id: "security-audit",
    name: "AI Security Toolkit",
    name_zh: "AI 安全审计工具集",
    description: "Secure your AI applications",
    description_zh: "保护你的 AI 应用安全",
    trigger_keywords: ["security", "guard", "safety", "sandbox", "permission", "audit"],
    skills: ["meta-llama/PurpleLlama", "leondz/garak", "NVIDIA/NeMo-Guardrails"],
    icon: "🛡️",
  },
  {
    id: "devtools-stack",
    name: "AI Dev Tools Stack",
    name_zh: "AI 开发工具栈",
    description: "Essential tools for AI-powered development",
    description_zh: "AI 驱动开发的必备工具",
    trigger_keywords: ["dev", "developer", "ide", "editor", "vscode", "terminal"],
    skills: ["anthropics/claude-code", "getcursor/cursor", "continuedev/continue"],
    icon: "🛠️",
  },
];
