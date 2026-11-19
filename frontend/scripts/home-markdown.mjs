/**
 * Build-time helpers for homepage canonical stamping and the Markdown homepage
 * representation (dist/index.md) served to agents that request text/markdown.
 */

const CANONICAL_RE = /<link\s+rel="canonical"/i;

/** Injects the homepage canonical tag into dist/index.html if not already present. */
export function stampHomeCanonical(html, site = "https://agentskillshub.top") {
  if (CANONICAL_RE.test(html)) return html;
  const tag = `    <link rel="canonical" href="${site}/" />\n  </head>`;
  return html.replace(/  <\/head>|<\/head>/i, tag);
}

/** Builds a concise, token-efficient Markdown representation of the homepage. */
export function buildHomeMarkdown({ site, counts, indexCount, generatedDate }) {
  const total = counts?.total ?? "267,000+";
  const graded = counts?.graded ?? "132,000+";
  const over100 = counts?.gradedOver100 ?? "99%";
  const over1000 = counts?.gradedOver1000 ?? "99%";
  const updated = generatedDate || new Date().toISOString().slice(0, 10);

  return [
    "# Agent Skills Hub",
    "",
    `> Security-graded directory of ${total} open-source AI agent skills, Claude Skills, Codex skills, and MCP servers. ${graded} graded across 44 published security rules (${over100} of skills over 100 stars; ${over1000} over 1,000), refreshed from GitHub every 8 hours.`,
    "",
    `- **Canonical URL**: ${site}/`,
    "- **Operator**: BRICKAI (GoSailGlobal LLC), 30 N Gould St, Ste N, Sheridan, WY 82801, USA",
    "- **Founder**: Jason Zhu (@GoSailGlobal)",
    `- **Last Updated**: ${updated}`,
    `- **Offline CLI / MCP Index**: ${indexCount.toLocaleString("en-US")} skills (stars >= 5)`,
    "",
    "## Quick Start for AI Agents",
    "",
    `- **MCP Server**: \`npx -y @agentskillshub/mcp\` (tools: \`search_skills\`, \`audit_skill\`, \`get_skill_install\`, \`pro_search\`)`,
    `- **MCP Server Card**: ${site}/.well-known/mcp/server-card.json`,
    `- **CLI**: \`npx @agentskillshub/cli search <query>\` / \`npx @agentskillshub/cli audit <owner/repo>\``,
    `- **Agent Skill Guide**: ${site}/skill.md`,
    `- **LLMs Index**: ${site}/llms.txt | **Full Corpus**: ${site}/llms-full.txt`,
    `- **Official Machine-Readable Facts**: ${site}/ai-info/`,
    "",
    "## Browse by Category",
    "",
    `- [MCP Servers](${site}/category/mcp-server/) — Model Context Protocol servers for AI agents`,
    `- [Claude Skills](${site}/category/claude-skill/) — Skills and plugins for Anthropic Claude`,
    `- [Codex Skills](${site}/category/codex-skill/) — Skills for OpenAI Codex agents`,
    `- [Agent Tools](${site}/category/agent-tool/) — General-purpose AI agent utilities`,
    `- [AI Skills](${site}/category/ai-skill/) — Cross-platform AI skills and plugins`,
    `- [LLM Plugins](${site}/category/llm-plugin/) — Plugins and extensions for LLMs`,
    "",
    "## Key Pages",
    "",
    `- [Security Analyzer](${site}/analyzer/) — Free live 44-rule security scan of any GitHub repo`,
    `- [How We Grade](${site}/how-we-grade/) — 44 published security rules, 9-dimension quality score, and known limits`,
    `- [Scenario Guides](${site}/best/) — Curated, hands-on tested best-of lists by workflow`,
    `- [Daily New Skills](${site}/daily/) — Top 10 new AI agent skills daily by star velocity`,
    `- [Security Audits](${site}/audit/) — Per-repository "is X safe to install?" pages`,
    `- [Compare Tools](${site}/compare/) — Head-to-head skill and MCP server comparisons`,
    `- [Enterprise & Pro](${site}/enterprise/) — Pro Deep Search ($39/yr), Fast-Track Audit ($49), CI Skill Gate ($29/mo)`,
    "",
    "## Open Dataset & Research",
    "",
    "- **Zenodo Census (CC-BY-4.0)**: https://doi.org/10.5281/zenodo.21292799",
    "- **Hugging Face Mirror**: https://huggingface.co/datasets/jasonzhuyansen/agent-skills-security-grades",
    `- **Blue Book of Agent Skills 2026**: ${site}/book/`,
    "",
    "## Company & Legal",
    "",
    `- [About & Methodology](${site}/about/)`,
    `- [Contact](${site}/contact/) — hello@gosailglobal.com`,
    `- [Privacy Policy](${site}/privacy/)`,
    `- [Terms of Service](${site}/terms/)`,
    "",
  ].join("\n");
}
