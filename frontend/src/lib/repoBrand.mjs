/**
 * The name people search for a repo whose own name says nothing: "remotion-dev/skills" is
 * searched as "remotion skills", "awslabs/mcp" as "aws mcp".
 *
 * The OpenSEO audit of 2026-11-25 found 118 indexable skill pages for repos named skills,
 * agent-skills, mcp, cli and the like. Their titles read "skills by remotion-dev: Agent
 * Skills", so the brand was missing from the title, the heading and every link to the page
 * ("skills"). The Remotion entry had 5 impressions in 28 days while Google showed the
 * 550-skill video guide for the same searches (6,830 impressions, 1.1% clicked), and another
 * directory's entry for the same repo, titled "Remotion | ClaudeSkills", was #1 for
 * "remotion skill". cb3509f put the name people search first ("unslop by theclaymethod");
 * for these repos that name is the brand.
 *
 * Only owners listed here get a brand: a guessed one ("Remotion-dev Skills") would be worse
 * than today's title. Add an owner when its brand is the name people use for it. A person is
 * listed only when people search their full name (matt pocock skills: 6,600 US searches a
 * month); others are searched by handle ("antfu skills") and keep it.
 */

/** GitHub owner (lowercased) -> the brand people search. */
const OWNER_BRANDS = new Map(Object.entries({
  "amd": "AMD",
  "android": "Android",
  "anthropics": "Anthropic",
  "apify": "Apify",
  "awslabs": "AWS",
  "browserbase": "Browserbase",
  "browsermcp": "Browser MCP",
  "builderio": "Builder.io",
  "callstackincubator": "Callstack",
  "clickhouse": "ClickHouse",
  "cloudflare": "Cloudflare",
  "docker": "Docker",
  "dotnet": ".NET",
  "elastic": "Elastic",
  "expo": "Expo",
  "firebase": "Firebase",
  "firecrawl": "Firecrawl",
  "getsentry": "Sentry",
  "google": "Google",
  "googleworkspace": "Google Workspace",
  "hashicorp": "HashiCorp",
  "heygen-com": "HeyGen",
  "huggingface": "Hugging Face",
  "jina-ai": "Jina AI",
  "laravel": "Laravel",
  "larksuite": "Lark",
  "mattpocock": "Matt Pocock",
  "microsoft": "Microsoft",
  "microsoftdocs": "Microsoft Learn",
  "minimax-ai": "MiniMax",
  "nvidia": "NVIDIA",
  "openai": "OpenAI",
  "remotion-dev": "Remotion",
  "semgrep": "Semgrep",
  "supabase": "Supabase",
  "tanstack": "TanStack",
  "theqtcompanyrnd": "Qt",
  "trailofbits": "Trail of Bits",
  "unity-technologies": "Unity",
  "vercel-labs": "Vercel",
  "wordpress": "WordPress",
}));

/** Repo names that say what kind of thing it is and nothing else -> how the brand's name ends. */
const GENERIC_KINDS = new Map(Object.entries({
  "skills": "Skills",
  "skill": "Skill",
  "agent-skills": "Agent Skills",
  "agent_skills": "Agent Skills",
  "claude-skills": "Claude Skills",
  "claude-code-skills": "Claude Code Skills",
  "codex-skills": "Codex Skills",
  "mcp": "MCP",
  "mcp-server": "MCP Server",
  "mcp-servers": "MCP Servers",
  "cli": "CLI",
  "agent": "Agent",
  "agents": "Agents",
  "tools": "Tools",
  "toolkit": "Toolkit",
}));

/** "Remotion Skills" for remotion-dev/skills, "Browser MCP" for BrowserMCP/mcp; null when the
 *  repo name is not generic or the owner has no listed brand. */
export function brandedName(repoFullName) {
  const parts = String(repoFullName || "").split("/");
  if (parts.length !== 2) return null; // a sub-skill path names the skill, not the repo
  const [owner, repo] = parts;
  const brand = OWNER_BRANDS.get(owner.toLowerCase());
  const kind = GENERIC_KINDS.get(repo.toLowerCase());
  if (!brand || !kind) return null;
  return joinBrandKind(brand, kind);
}

/** "Browser MCP" + "MCP" -> "Browser MCP"; "Browser MCP" + "MCP Server" -> "Browser MCP Server". */
function joinBrandKind(brand, kind) {
  const last = brand.split(" ").at(-1).toLowerCase();
  const kindWords = kind.split(" ");
  if (kindWords[0].toLowerCase() !== last) return `${brand} ${kind}`;
  return [brand, ...kindWords.slice(1)].join(" ");
}

/** What a link or heading calls the repo: its brand when it has one, else its own name.
 *  A sub-skill row carries its parent's full name with its own name ("pptx" under
 *  anthropics/skills): it keeps its own name. */
export function displayName(repoFullName, repoName) {
  const repo = String(repoFullName || "").split("/")[1] || "";
  if (repoName && repoName.toLowerCase() !== repo.toLowerCase()) return repoName;
  return brandedName(repoFullName) || repoName || repo;
}
