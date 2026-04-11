import type { Skill } from "../types/skill";

export interface SubcategoryDef {
  id: string;
  labelZh: string;
  labelEn: string;
  keywords: string[];
}

/** Rules per parent category. Order matters — first match wins. */
const SUBCATEGORY_RULES: Record<string, SubcategoryDef[]> = {
  "agent-tool": [
    {
      id: "agent-framework",
      labelZh: "Agent 框架",
      labelEn: "Agent Framework",
      keywords: [
        "framework",
        "sdk",
        "platform",
        "runtime",
        "harness",
        "library",
        "agentic-framework",
      ],
    },
    {
      id: "agent-orchestration",
      labelZh: "多 Agent 编排",
      labelEn: "Orchestration",
      keywords: [
        "orchestrat",
        "multi-agent",
        "crew",
        "swarm",
        "fleet",
        "parallel",
        "squad",
      ],
    },
    {
      id: "local-ai",
      labelZh: "本地 AI",
      labelEn: "Local AI",
      keywords: [
        "local",
        "ollama",
        "llama",
        "self-hosted",
        "on-premise",
        "private",
        "llamafile",
        "gguf",
      ],
    },
    {
      id: "workflow-automation",
      labelZh: "工作流自动化",
      labelEn: "Automation",
      keywords: [
        "automat",
        "n8n",
        "workflow",
        "rpa",
        "no-code",
        "low-code",
        "zapier",
      ],
    },
    {
      id: "search-data",
      labelZh: "搜索 & 数据",
      labelEn: "Search & Data",
      keywords: [
        "search",
        "retrieval",
        "rag",
        "vector",
        "embedding",
        "knowledge",
        "scraper",
        "crawler",
      ],
    },
    {
      id: "coding-agent",
      labelZh: "编程 Agent",
      labelEn: "Coding Agent",
      keywords: [
        "coding",
        "code-agent",
        "developer",
        "ide",
        "copilot",
        "programmer",
        "debug",
        "terminal",
      ],
    },
    {
      id: "memory-context",
      labelZh: "记忆 & 上下文",
      labelEn: "Memory",
      keywords: [
        "memory",
        "context",
        "state",
        "session",
        "history",
        "persist",
        "knowledge-graph",
      ],
    },
    {
      id: "security-infra",
      labelZh: "安全 & 基础设施",
      labelEn: "Security",
      keywords: [
        "security",
        "auth",
        "guard",
        "sandbox",
        "permission",
        "firewall",
        "governance",
        "container",
      ],
    },
  ],
  "mcp-server": [
    {
      id: "mcp-browser",
      labelZh: "浏览器",
      labelEn: "Browser",
      keywords: [
        "browser",
        "playwright",
        "puppeteer",
        "selenium",
        "web-scraping",
        "stealth",
      ],
    },
    {
      id: "mcp-data",
      labelZh: "数据 & 数据库",
      labelEn: "Data & DB",
      keywords: [
        "database",
        "sql",
        "postgres",
        "mysql",
        "mongo",
        "redis",
        "supabase",
        "firebase",
        "excel",
      ],
    },
    {
      id: "mcp-api",
      labelZh: "API 集成",
      labelEn: "API Integration",
      keywords: ["api", "rest", "graphql", "webhook", "integration"],
    },
    {
      id: "mcp-devtools",
      labelZh: "开发工具",
      labelEn: "Dev Tools",
      keywords: ["git", "docker", "kubernetes", "deploy", "cicd", "npm", "pip"],
    },
    {
      id: "mcp-file",
      labelZh: "文件系统",
      labelEn: "File System",
      keywords: ["file", "filesystem", "storage", "s3", "cloud-storage", "ftp"],
    },
    {
      id: "mcp-comms",
      labelZh: "通讯",
      labelEn: "Communication",
      keywords: [
        "slack",
        "discord",
        "telegram",
        "email",
        "chat",
        "teams",
        "wechat",
        "notion",
      ],
    },
  ],
  "claude-skill": [
    {
      id: "skill-coding",
      labelZh: "编程开发",
      labelEn: "Coding",
      keywords: [
        "coding",
        "code",
        "debug",
        "test",
        "tdd",
        "refactor",
        "typescript",
        "python",
        "rust",
      ],
    },
    {
      id: "skill-writing",
      labelZh: "写作创作",
      labelEn: "Writing",
      keywords: [
        "writing",
        "content",
        "blog",
        "article",
        "copywriting",
        "document",
        "docx",
        "pdf",
      ],
    },
    {
      id: "skill-design",
      labelZh: "设计",
      labelEn: "Design",
      keywords: [
        "design",
        "ui",
        "ux",
        "frontend",
        "css",
        "figma",
        "canvas",
        "art",
        "theme",
      ],
    },
    {
      id: "skill-research",
      labelZh: "研究分析",
      labelEn: "Research",
      keywords: [
        "research",
        "analysis",
        "seo",
        "audit",
        "data",
        "report",
        "market",
      ],
    },
    {
      id: "skill-productivity",
      labelZh: "效率工具",
      labelEn: "Productivity",
      keywords: [
        "productivity",
        "workflow",
        "automat",
        "task",
        "todo",
        "schedule",
        "time",
      ],
    },
  ],
  "codex-skill": [
    {
      id: "codex-coding",
      labelZh: "编程开发",
      labelEn: "Coding",
      keywords: [
        "coding",
        "code",
        "debug",
        "test",
        "typescript",
        "python",
        "developer",
      ],
    },
    {
      id: "codex-ops",
      labelZh: "运维 & DevOps",
      labelEn: "DevOps",
      keywords: ["deploy", "docker", "kubernetes", "ci", "infra", "monitor"],
    },
    {
      id: "codex-data",
      labelZh: "数据处理",
      labelEn: "Data",
      keywords: ["data", "etl", "pipeline", "analysis", "database", "sql"],
    },
    {
      id: "codex-client",
      labelZh: "客户端 & GUI",
      labelEn: "Client & GUI",
      keywords: [
        "desktop",
        "gui",
        "client",
        "studio",
        "app",
        "interface",
        "ui",
      ],
    },
    {
      id: "codex-memory",
      labelZh: "记忆 & 上下文",
      labelEn: "Memory",
      keywords: [
        "memory",
        "context",
        "brain",
        "knowledge",
        "persist",
        "session",
      ],
    },
  ],
  "ai-skill": [
    {
      id: "ai-coding",
      labelZh: "编程辅助",
      labelEn: "Coding",
      keywords: [
        "coding",
        "code",
        "debug",
        "test",
        "refactor",
        "developer",
        "programming",
        "terminal",
      ],
    },
    {
      id: "ai-rules",
      labelZh: "规则 & 配置",
      labelEn: "Rules & Config",
      keywords: [
        "rules",
        "rule",
        "config",
        "prompt",
        "template",
        "best practice",
        "convention",
      ],
    },
    {
      id: "ai-productivity",
      labelZh: "效率工具",
      labelEn: "Productivity",
      keywords: [
        "productivity",
        "workflow",
        "automat",
        "task",
        "proxy",
        "launcher",
      ],
    },
    {
      id: "ai-design",
      labelZh: "设计 & UI",
      labelEn: "Design & UI",
      keywords: [
        "design",
        "ui",
        "ux",
        "frontend",
        "css",
        "figma",
        "theme",
        "vibe",
      ],
    },
  ],
};

/**
 * Infer a subcategory from skill metadata.
 * Scans topics, description, and repo name.
 * Returns null if no match.
 */
export function inferSubcategory(skill: Skill): string | null {
  const rules = SUBCATEGORY_RULES[skill.category];
  if (!rules) return null;

  // Build searchable text from available fields
  let topics: string[] = [];
  try {
    topics = JSON.parse(skill.topics || "[]");
  } catch {
    /* ignore */
  }

  const searchable = [skill.repo_full_name, skill.description, ...topics]
    .join(" ")
    .toLowerCase();

  for (const rule of rules) {
    if (rule.keywords.some((kw) => searchable.includes(kw))) {
      return rule.id;
    }
  }
  return null;
}

/** Get available subcategories for a given parent category. */
export function getSubcategoriesForCategory(
  category: string,
): SubcategoryDef[] {
  // Handle comma-separated categories (layer mode)
  const cats = category.split(",");
  const seen = new Set<string>();
  const result: SubcategoryDef[] = [];
  for (const cat of cats) {
    const rules = SUBCATEGORY_RULES[cat.trim()];
    if (rules) {
      for (const r of rules) {
        if (!seen.has(r.id)) {
          seen.add(r.id);
          result.push(r);
        }
      }
    }
  }
  return result;
}
