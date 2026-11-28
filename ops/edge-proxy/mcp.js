/**
 * Stateless Remote MCP Streamable HTTP (2025-06-18) endpoint for AgentSkillsHub.
 * Serves POST/GET/OPTIONS on https://agentskillshub.top/mcp using the static
 * catalog at /search-index.json (cached in-isolate and at the Cloudflare edge).
 */

const SITE_URL = "https://agentskillshub.top";
const PROTOCOL_VERSION = "2025-06-18";
const DEFAULT_LIMIT = 10;
const MAX_LIMIT = 25;
const CACHE_TTL_MS = 5 * 60 * 1000;

const SERVER_INFO = {
  name: "agentskillshub",
  title: "Agent Skills Hub MCP Server",
  version: "1.0.0",
};

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Accept, Mcp-Session-Id, MCP-Protocol-Version",
  "Access-Control-Expose-Headers": "Mcp-Session-Id",
};

const GRADE_RANK = {
  safe: 4,
  caution: 3,
  unknown: 2,
  unaudited: 2,
  unsafe: 1,
  reject: 0,
};

export const MCP_TOOLS = [
  {
    name: "search_skills",
    title: "Search Agent Skills",
    description:
      "Search AgentSkillsHub's security-graded directory of AI agent skills, Claude skills, and MCP servers.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Keywords or use case to search for." },
        category: {
          type: "string",
          description: "Optional category such as mcp-server, claude-skill, codex-skill, or agent-tool.",
        },
        min_security: {
          type: "string",
          enum: ["safe", "caution", "unaudited", "unsafe"],
          description: "Minimum acceptable security grade.",
        },
        limit: {
          type: "integer",
          minimum: 1,
          maximum: MAX_LIMIT,
          description: "Maximum number of results to return (default: 10).",
        },
      },
      required: ["query"],
    },
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
  },
  {
    name: "audit_skill",
    title: "Audit Skill Security",
    description:
      "Look up the rule-based security grade (safe, caution, unsafe, reject, or unaudited) and quality score for a GitHub skill repo.",
    inputSchema: {
      type: "object",
      properties: {
        repo: {
          type: "string",
          description: "GitHub repository in 'owner/repo' format or GitHub URL.",
        },
      },
      required: ["repo"],
    },
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
  },
  {
    name: "get_skill_install",
    title: "Get Skill Install Commands",
    description:
      "Return CLI audit and install commands plus safety notes for a GitHub AI agent skill or MCP server.",
    inputSchema: {
      type: "object",
      properties: {
        repo: {
          type: "string",
          description: "GitHub repository in 'owner/repo' format.",
        },
      },
      required: ["repo"],
    },
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false,
    },
  },
];

let cachedSkills = null;
let cacheExpiresAt = 0;

export function resetMcpCacheForTests() {
  cachedSkills = null;
  cacheExpiresAt = 0;
}

async function loadCatalog(origin) {
  const now = Date.now();
  if (cachedSkills && now < cacheExpiresAt) return cachedSkills;
  const indexUrl = `${origin}/search-index.json`;
  const resp = await fetch(indexUrl, {
    headers: { "User-Agent": "agentskillshub-mcp-edge/1.0" },
    cf: { cacheTtl: 600, cacheEverything: true },
  });
  if (!resp.ok) {
    throw new Error(`Failed to load catalog (${resp.status})`);
  }
  const data = await resp.json();
  cachedSkills = Array.isArray(data?.skills) ? data.skills : [];
  cacheExpiresAt = now + CACHE_TTL_MS;
  return cachedSkills;
}

function normalizeRepo(raw) {
  if (typeof raw !== "string") return "";
  return raw
    .trim()
    .replace(/^https?:\/\/github\.com\//i, "")
    .replace(/\.git$/i, "")
    .replace(/^\/+|\/+$/g, "")
    .toLowerCase();
}

function matchesMinGrade(grade, minGrade) {
  if (!minGrade) return true;
  const actual = GRADE_RANK[(grade ?? "unknown").toLowerCase()] ?? 2;
  const required = GRADE_RANK[minGrade.toLowerCase()] ?? 0;
  return actual >= required;
}

function scoreEntry(item, tokens) {
  const haystack = `${item.f} ${item.n} ${item.d ?? ""} ${(item.t ?? []).join(" ")}`.toLowerCase();
  let hits = 0;
  for (const token of tokens) {
    if (haystack.includes(token)) hits += 1;
  }
  if (hits === 0) return 0;
  return hits * 1000 + Math.log10(Math.max(item.s || 0, 1) + 1) * 50 + (item.q ?? 0);
}

function formatSkillSummary(item) {
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

async function executeTool(name, args, origin) {
  switch (name) {
    case "search_skills": {
      const query = typeof args.query === "string" ? args.query.trim().toLowerCase() : "";
      const category = typeof args.category === "string" ? args.category.trim().toLowerCase() : "";
      const minSecurity = typeof args.min_security === "string" ? args.min_security.trim() : "";
      const rawLimit = typeof args.limit === "number" ? Math.trunc(args.limit) : DEFAULT_LIMIT;
      const limit = Math.min(Math.max(rawLimit, 1), MAX_LIMIT);
      const tokens = query.split(/\s+/).filter(Boolean);

      const skills = await loadCatalog(origin);
      const scored = [];
      for (const item of skills) {
        if (category && (item.c ?? "").toLowerCase() !== category) continue;
        if (!matchesMinGrade(item.g, minSecurity)) continue;
        const score = tokens.length ? scoreEntry(item, tokens) : item.s || 0;
        if (score > 0) scored.push({ score, item });
      }
      scored.sort((a, b) => b.score - a.score);
      return {
        ok: true,
        data: {
          query,
          total_matches: scored.length,
          results: scored.slice(0, limit).map(({ item }) => formatSkillSummary(item)),
        },
      };
    }

    case "audit_skill": {
      const repo = normalizeRepo(args.repo);
      if (!repo) return { ok: false, error: "Provide a GitHub repo as 'owner/repo'." };
      const skills = await loadCatalog(origin);
      const match = skills.find((item) => item.f.toLowerCase() === repo);
      if (!match) {
        return {
          ok: true,
          data: {
            repo,
            found: false,
            security_grade: "unaudited",
            analyzer_url: `${SITE_URL}/analyzer/?repo=${encodeURIComponent(repo)}`,
          },
        };
      }
      return {
        ok: true,
        data: {
          repo: match.f,
          found: true,
          security_grade: match.g ?? "unaudited",
          quality_score: match.q ?? null,
          stars: match.s,
          audit_url: `${SITE_URL}/audit/${match.f}/`,
          skill_url: `${SITE_URL}/skill/${match.f}/`,
        },
      };
    }

    case "get_skill_install": {
      const repo = normalizeRepo(args.repo);
      if (!repo) return { ok: false, error: "Provide a GitHub repo as 'owner/repo'." };
      const skills = await loadCatalog(origin);
      const match = skills.find((item) => item.f.toLowerCase() === repo);
      const canonicalRepo = match?.f ?? repo;
      return {
        ok: true,
        data: {
          repo: canonicalRepo,
          security_grade: match?.g ?? "unaudited",
          cli_audit: `npx @agentskillshub/cli audit ${canonicalRepo}`,
          git_clone: `git clone https://github.com/${canonicalRepo}.git`,
          skill_url: `${SITE_URL}/skill/${canonicalRepo}/`,
          safety_note: "Verify the security grade and review SKILL.md or package scripts before installing.",
        },
      };
    }

    default:
      return { ok: false, error: `Unknown tool: ${name}` };
  }
}

async function handleJsonRpc(msg, origin) {
  const id = msg?.id ?? null;
  const method = typeof msg?.method === "string" ? msg.method : "";
  const params = msg?.params && typeof msg.params === "object" ? msg.params : {};

  if (method.startsWith("notifications/")) {
    return null;
  }

  switch (method) {
    case "initialize":
      return {
        jsonrpc: "2.0",
        id,
        result: {
          protocolVersion:
            typeof params.protocolVersion === "string" && params.protocolVersion
              ? params.protocolVersion
              : PROTOCOL_VERSION,
          capabilities: { tools: { listChanged: false } },
          serverInfo: SERVER_INFO,
          instructions:
            "AgentSkillsHub stateless remote MCP server. Use search_skills to discover security-graded AI agent skills and MCP servers, audit_skill to inspect a repo's security grade, and get_skill_install for CLI audit and install commands.",
        },
      };

    case "ping":
      return { jsonrpc: "2.0", id, result: {} };

    case "tools/list":
      return { jsonrpc: "2.0", id, result: { tools: MCP_TOOLS } };

    case "tools/call": {
      const toolName = typeof params.name === "string" ? params.name : "";
      const toolArgs = params.arguments && typeof params.arguments === "object" ? params.arguments : {};
      if (!toolName) {
        return {
          jsonrpc: "2.0",
          id,
          error: { code: -32602, message: "Missing tool name in params.name" },
        };
      }
      try {
        const outcome = await executeTool(toolName, toolArgs, origin);
        if (!outcome.ok) {
          return {
            jsonrpc: "2.0",
            id,
            result: {
              isError: true,
              content: [{ type: "text", text: outcome.error }],
            },
          };
        }
        return {
          jsonrpc: "2.0",
          id,
          result: {
            content: [{ type: "text", text: JSON.stringify(outcome.data, null, 2) }],
            structuredContent: outcome.data,
          },
        };
      } catch (err) {
        return {
          jsonrpc: "2.0",
          id,
          result: {
            isError: true,
            content: [{ type: "text", text: err instanceof Error ? err.message : "Tool execution failed." }],
          },
        };
      }
    }

    default:
      return {
        jsonrpc: "2.0",
        id,
        error: { code: -32601, message: `Method not found: ${method}` },
      };
  }
}

function jsonResp(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ...CORS_HEADERS,
    },
  });
}

export async function handleMcpRequest(request, url) {
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: CORS_HEADERS });
  }

  if (request.method === "GET" || request.method === "HEAD") {
    const info = {
      ...SERVER_INFO,
      protocolVersion: PROTOCOL_VERSION,
      transport: "streamable-http",
      endpoint: `${SITE_URL}/mcp`,
      serverCard: `${SITE_URL}/.well-known/mcp/server-card.json`,
      usage: "Send MCP JSON-RPC 2.0 POST requests (initialize, tools/list, tools/call) to this endpoint.",
      tools: MCP_TOOLS.map((t) => ({ name: t.name, title: t.title })),
    };
    return new Response(request.method === "HEAD" ? null : JSON.stringify(info, null, 2), {
      status: 200,
      headers: { "Content-Type": "application/json; charset=utf-8", ...CORS_HEADERS },
    });
  }

  if (request.method !== "POST") {
    return jsonResp(
      { jsonrpc: "2.0", id: null, error: { code: -32600, message: "Method not allowed; use POST." } },
      405
    );
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return jsonResp(
      { jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error: invalid JSON" } },
      400
    );
  }

  if (Array.isArray(body)) {
    const results = (await Promise.all(body.map((item) => handleJsonRpc(item, url.origin)))).filter(
      (r) => r !== null
    );
    if (results.length === 0) return new Response(null, { status: 202, headers: CORS_HEADERS });
    return jsonResp(results, 200);
  }

  const result = await handleJsonRpc(body, url.origin);
  if (result === null) return new Response(null, { status: 202, headers: CORS_HEADERS });
  return jsonResp(result, 200);
}
