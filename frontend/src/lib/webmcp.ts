/**
 * WebMCP (Web Model Context Protocol) tool registration for in-browser AI agents.
 * Registers read-only discovery and security-audit tools against the public static
 * search index (/search-index.json) on page load when the browser exposes
 * navigator.modelContext or document.modelContext.
 */

const SITE_URL = "https://agentskillshub.top";
const INDEX_URL = "/search-index.json";
const DEFAULT_LIMIT = 10;
const MAX_LIMIT = 25;

const GRADE_RANK: Record<string, number> = {
  safe: 4,
  caution: 3,
  unknown: 2,
  unaudited: 2,
  unsafe: 1,
  reject: 0,
};

interface IndexEntry {
  f: string;
  n: string;
  a: string;
  s: number;
  d?: string;
  c?: string;
  p?: string[];
  t?: string[];
  q?: number;
  g?: string;
  k?: number;
}

interface SearchIndexPayload {
  skills?: IndexEntry[];
}

interface ModelContextTool {
  name: string;
  title?: string;
  description: string;
  inputSchema: Record<string, unknown>;
  annotations?: { readOnlyHint?: boolean };
  execute: (input: Record<string, unknown>) => Promise<Record<string, unknown>>;
}

interface ModelContextLike {
  registerTool?: (tool: ModelContextTool) => unknown;
}

type NavigatorWithModelContext = Navigator & { modelContext?: ModelContextLike };
type DocumentWithModelContext = Document & { modelContext?: ModelContextLike };

let cachedSkills: IndexEntry[] | null = null;
let inflightLoad: Promise<IndexEntry[]> | null = null;

async function loadCatalog(): Promise<IndexEntry[]> {
  if (cachedSkills) return cachedSkills;
  if (inflightLoad) return inflightLoad;
  inflightLoad = fetch(INDEX_URL)
    .then(async (res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as SearchIndexPayload;
      cachedSkills = Array.isArray(data.skills) ? data.skills : [];
      return cachedSkills;
    })
    .catch(() => [])
    .finally(() => {
      inflightLoad = null;
    });
  return inflightLoad;
}

function normalizeRepo(raw: unknown): string {
  if (typeof raw !== "string") return "";
  return raw
    .trim()
    .replace(/^https?:\/\/github\.com\//i, "")
    .replace(/\.git$/i, "")
    .replace(/^\/+|\/+$/g, "")
    .toLowerCase();
}

function matchesMinGrade(grade: string | undefined, minGrade: string): boolean {
  if (!minGrade) return true;
  const actual = GRADE_RANK[(grade ?? "unknown").toLowerCase()] ?? 2;
  const required = GRADE_RANK[minGrade.toLowerCase()] ?? 0;
  return actual >= required;
}

function scoreEntry(item: IndexEntry, tokens: string[]): number {
  const haystack = `${item.f} ${item.n} ${item.d ?? ""} ${(item.t ?? []).join(" ")}`.toLowerCase();
  let hits = 0;
  for (const token of tokens) {
    if (haystack.includes(token)) hits += 1;
  }
  if (hits === 0) return 0;
  return hits * 1000 + Math.log10(Math.max(item.s, 1) + 1) * 50 + (item.q ?? 0);
}

function formatSkillSummary(item: IndexEntry): Record<string, unknown> {
  return {
    repo: item.f,
    name: item.n,
    category: item.c ?? "uncategorized",
    stars: item.s,
    quality_score: item.q ?? null,
    security_grade: item.g ?? "unaudited",
    description: item.d ?? "",
    url: `${SITE_URL}/skill/${item.f}/`,
  };
}

async function executeSearchSkills(input: Record<string, unknown>): Promise<Record<string, unknown>> {
  const query = typeof input.query === "string" ? input.query.trim().toLowerCase() : "";
  const category = typeof input.category === "string" ? input.category.trim().toLowerCase() : "";
  const minSecurity = typeof input.min_security === "string" ? input.min_security.trim() : "";
  const rawLimit = typeof input.limit === "number" ? Math.trunc(input.limit) : DEFAULT_LIMIT;
  const limit = Math.min(Math.max(rawLimit, 1), MAX_LIMIT);
  const tokens = query.split(/\s+/).filter(Boolean);
  const skills = await loadCatalog();
  const scored: Array<{ score: number; item: IndexEntry }> = [];
  for (const item of skills) {
    if (category && (item.c ?? "").toLowerCase() !== category) continue;
    if (!matchesMinGrade(item.g, minSecurity)) continue;
    const score = tokens.length ? scoreEntry(item, tokens) : item.s;
    if (score > 0) scored.push({ score, item });
  }
  scored.sort((a, b) => b.score - a.score);
  return {
    query,
    total_matches: scored.length,
    results: scored.slice(0, limit).map(({ item }) => formatSkillSummary(item)),
  };
}

async function executeAuditSkill(input: Record<string, unknown>): Promise<Record<string, unknown>> {
  const repo = normalizeRepo(input.repo);
  if (!repo) return { error: "Provide a GitHub repo as 'owner/repo'." };
  const skills = await loadCatalog();
  const match = skills.find((item) => item.f.toLowerCase() === repo);
  if (!match) {
    return {
      repo,
      found: false,
      security_grade: "unaudited",
      analyzer_url: `${SITE_URL}/analyzer/?repo=${encodeURIComponent(repo)}`,
    };
  }
  return {
    repo: match.f,
    found: true,
    security_grade: match.g ?? "unaudited",
    quality_score: match.q ?? null,
    stars: match.s,
    audit_url: `${SITE_URL}/audit/${match.f}/`,
    skill_url: `${SITE_URL}/skill/${match.f}/`,
  };
}

async function executeGetInstall(input: Record<string, unknown>): Promise<Record<string, unknown>> {
  const repo = normalizeRepo(input.repo);
  if (!repo) return { error: "Provide a GitHub repo as 'owner/repo'." };
  const skills = await loadCatalog();
  const match = skills.find((item) => item.f.toLowerCase() === repo);
  const canonicalRepo = match?.f ?? repo;
  return {
    repo: canonicalRepo,
    security_grade: match?.g ?? "unaudited",
    cli_audit: `npx @agentskillshub/cli audit ${canonicalRepo}`,
    git_clone: `git clone https://github.com/${canonicalRepo}.git`,
    skill_url: `${SITE_URL}/skill/${canonicalRepo}/`,
    safety_note: "Verify the security grade and review SKILL.md or package scripts before installing.",
  };
}

const WEBMCP_TOOLS: ModelContextTool[] = [
    {
      name: "search_skills",
      title: "Search Agent Skills",
      description: "Search AgentSkillsHub's security-graded directory of AI agent skills, Claude skills, and MCP servers.",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", description: "Keywords or use case to search for." },
          category: { type: "string", description: "Optional category such as mcp-server, claude-skill, codex-skill, or agent-tool." },
          min_security: { type: "string", enum: ["safe", "caution", "unaudited", "unsafe"], description: "Minimum acceptable security grade." },
          limit: { type: "integer", minimum: 1, maximum: MAX_LIMIT, description: "Maximum number of results to return." },
        },
        required: ["query"],
      },
      annotations: { readOnlyHint: true },
      execute: executeSearchSkills,
    },
    {
      name: "audit_skill",
      title: "Audit Skill Security",
      description: "Look up the rule-based security grade (safe, caution, unsafe, reject, or unaudited) and quality score for a GitHub skill repo.",
      inputSchema: {
        type: "object",
        properties: {
          repo: { type: "string", description: "GitHub repository in 'owner/repo' format or GitHub URL." },
        },
        required: ["repo"],
      },
      annotations: { readOnlyHint: true },
      execute: executeAuditSkill,
    },
    {
      name: "get_skill_install",
      title: "Get Skill Install Commands",
      description: "Return CLI audit and install commands plus safety notes for a GitHub AI agent skill or MCP server.",
      inputSchema: {
        type: "object",
        properties: {
          repo: { type: "string", description: "GitHub repository in 'owner/repo' format." },
        },
        required: ["repo"],
      },
      annotations: { readOnlyHint: true },
      execute: executeGetInstall,
    },
];

function getModelContexts(): ModelContextLike[] {
  const contexts: ModelContextLike[] = [];
  const navCtx = typeof navigator !== "undefined" ? (navigator as NavigatorWithModelContext).modelContext : undefined;
  const docCtx = typeof document !== "undefined" ? (document as DocumentWithModelContext).modelContext : undefined;
  if (navCtx && typeof navCtx.registerTool === "function") contexts.push(navCtx);
  if (docCtx && docCtx !== navCtx && typeof docCtx.registerTool === "function") contexts.push(docCtx);
  return contexts;
}

function registerOnContext(ctx: ModelContextLike, tools: ModelContextTool[]): void {
  for (const tool of tools) {
    try {
      Promise.resolve(ctx.registerTool?.(tool)).catch(() => {});
    } catch {
      // Ignore duplicate registration or unsupported browser edge cases.
    }
  }
}

let registered = false;

/** Registers AgentSkillsHub WebMCP tools once on page load when supported by the browser. */
export function registerWebMcpTools(): void {
  if (registered) return;
  const contexts = getModelContexts();
  if (contexts.length === 0) return;
  registered = true;
  for (const ctx of contexts) registerOnContext(ctx, WEBMCP_TOOLS);
}
