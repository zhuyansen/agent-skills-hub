/**
 * Shared gone-repository / community-mirror helpers used by both the static HTML
 * generator (scripts/generate-skill-pages.mjs) and the React SPA
 * (src/pages/SkillDetailPage.tsx, src/components/InstallCommand.tsx).
 *
 * Keeping the logic in one .mjs file ensures crawlers and hydrated visitors see the
 * exact same mirror attribution, install commands, and honesty guarantees.
 */

const GITHUB_SLUG_RE = /^https?:\/\/github\.com\/([A-Za-z0-9._-]+\/[A-Za-z0-9._-]+?)(?:\.git)?\/?$/i;

/** Extract "owner/repo" from a GitHub URL when it points to a different repository
 *  than repoFullName, else null. */
export function retargetedSlug(repoFullName, repoUrl) {
  if (!repoFullName || !repoUrl) return null;
  const match = GITHUB_SLUG_RE.exec(String(repoUrl).trim());
  if (!match) return null;
  const target = match[1];
  if (target.toLowerCase() === String(repoFullName).toLowerCase()) return null;
  return target;
}

/** Classify a retargeted dead-repo URL:
 *  - "mirror": same repository name under another owner (archived community mirror/fork).
 *  - "substitute": different repository name (separate project solving the same problem).
 *  - null: not retargeted. */
export function retargetKind(repoFullName, repoUrl) {
  const target = retargetedSlug(repoFullName, repoUrl);
  if (!target) return null;
  const origName = String(repoFullName).split("/")[1]?.toLowerCase() || "";
  const targetName = target.split("/")[1]?.toLowerCase() || "";
  return origName && origName === targetName ? "mirror" : "substitute";
}

/** Rewrite an install command from the deleted original owner/repo to the live mirror. */
export function rewriteMirrorCommand(command, originalFullName, mirrorFullName) {
  if (!command || !originalFullName || !mirrorFullName) return command;
  const escaped = originalFullName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return command.replace(new RegExp(escaped, "gi"), mirrorFullName);
}

/** Honest, bilingual notice copy for a deleted (404) repository. */
export function goneCopy(repoFullName, repoUrl) {
  const targetSlug = retargetedSlug(repoFullName, repoUrl);
  const kind = retargetKind(repoFullName, repoUrl);

  if (kind === "mirror" && targetSlug) {
    return {
      kind,
      targetSlug,
      headingEn: "Original repository removed (404) — Mirror available",
      headingZh: "原仓库已 404 — 已提供社区镜像备份",
      bodyEn: `— ${repoFullName} returns 404 on GitHub (deleted or author account removed). The GitHub link and install commands below point to our archived fork mirror at ${targetSlug} — a community mirror backup, not the original author's live repo. Review bundled scripts before running.`,
      bodyZh: `—— ${repoFullName} 在 GitHub 上已返回 404（原仓库已删除或作者账号已注销）。下方 GitHub 链接与安装命令已指向归档镜像备份 ${targetSlug}（明确标注为社区镜像，非原作者维护仓库；运行前请自行核对脚本）。`,
    };
  }

  if (kind === "substitute" && targetSlug) {
    return {
      kind,
      targetSlug,
      headingEn: "Repository no longer available",
      headingZh: "仓库已下架",
      bodyEn: `— ${repoFullName} returns 404 on GitHub. It was deleted, or its owner's account was removed. The data below is our last successful snapshot. The GitHub link below points to ${targetSlug}, a SEPARATE project by a different author that solves the same problem — not a continuation of this one.`,
      bodyZh: `—— ${repoFullName} 在 GitHub 上已返回 404，可能是仓库被删除或作者账号已注销。下方数据是我们最后一次成功抓取的快照。下方 GitHub 链接指向 ${targetSlug}，那是另一位作者解决同类问题的独立项目，并非本项目的延续。`,
    };
  }

  return {
    kind: null,
    targetSlug: null,
    headingEn: "Repository no longer available",
    headingZh: "仓库已下架",
    bodyEn: `— ${repoFullName} returns 404 on GitHub. It was deleted, or its owner's account was removed. The data below is our last successful snapshot.`,
    bodyZh: `—— ${repoFullName} 在 GitHub 上已返回 404，可能是仓库被删除或作者账号已注销。下方数据是我们最后一次成功抓取的快照。`,
  };
}

// High-precision topic router for deleted/404 repositories → active /best/<slug>/ guides.
// Ordered from narrow/specific domains to broader ones so 404 search traffic lands on
// the closest actively maintained alternatives without modifying frozen /best/* pages.
const GONE_GUIDE_RULES = [
  ["claude-video-skills", /\b(video|remotion|ffmpeg|jianying|capcut|shorts|reels|tiktok|gtavi|clipping|clip[- ]cutter|editing)\b|剪映|视频剪辑/i],
  ["animation-skills", /\b(animation|motion[- ]graphics|lottie|manim|gsap|anime\.js)\b|动效|动画/i],
  ["ppt-presentation", /\b(ppt|pptx|powerpoint|slide|slides|keynote|marp|deck)\b/i],
  ["ai-design", /\b(design[- ]system|figma|dtcg|ui[- ]design|ux[- ]design|design[- ]extract|tailwindcss|design[- ]token)\b/i],
  ["anti-slop", /\b(anti[- ]slop|humanizer|slop|write like a human|ai[- ]writing)\b/i],
  ["3d-mcp", /\b(blender|unity|godot|unreal|three\.?js|3d[- ]mcp|fbx|gltf)\b/i],
  ["ai-reverse-engineering", /\b(reverse[- ]engineer|ctf|ghidra|ida[- ]pro|radare|binary|decompile|frida|jadx)\b|逆向/i],
  ["browser-automation", /\b(playwright|puppeteer|browser[- ]use|browser[- ]agent|selenium|chrome[- ]devtools|cdp)\b/i],
  ["web-scraping", /\b(scrap(e|er|ing)|crawl(er|ing)|firecrawl|tavily|oxylabs|spider)\b/i],
  ["obsidian-second-brain", /\b(obsidian|second[- ]brain|pkm|zettelkasten|roam[- ]research)\b/i],
  ["knowledge-base", /\b(rag|graph[- ]rag|memory[- ]service|long[- ]term[- ]memory|knowledge[- ]base|vector[- ]db|qdrant|milvus|mem0)\b/i],
  ["mcp-database", /\b(postgres|postgresql|supabase|mysql|sqlite|mongodb|duckdb|clickhouse|database[- ]mcp|sql[- ]mcp)\b/i],
  ["mcp-for-github", /\b(github[- ]mcp|pull[- ]request|pr[- ]review|github[- ]actions)\b/i],
  ["mcp-for-google", /\b(google[- ]workspace|gmail|google[- ]drive|google[- ]calendar|google[- ]sheets|google[- ]docs)\b/i],
  ["secret-detection", /\b(secret|gitleaks|trufflehog|security[- ]scan|pentest|penetration[- ]test(?:ing)?|vulnerability|appsec|audit)\b|渗透|安全扫描/i],
  ["code-review", /\b(code[- ]review|pr[- ]agent|linter|static[- ]analysis)\b/i],
  ["refactoring", /\b(refactor|refactoring|tech[- ]debt|code[- ]cleanup)\b/i],
  ["voice-agent", /\b(voice[- ]agent|tts|stt|whisper|elevenlabs|speech|realtime[- ]audio|livekit)\b/i],
  ["telegram-bot", /\b(telegram|tg[- ]bot)\b/i],
  ["image-generation", /\b(image[- ]gen|flux|stable[- ]diffusion|midjourney|banana|comfyui|nano[- ]banana|dall-?e)\b/i],
  ["seo-tools", /\b(seo|geo|search[- ]console|ahrefs|semrush|keyword[- ]research|backlink)\b/i],
  ["content-writing", /\b(copywriting|blog[- ]post|content[- ]writing|newsletter|technical[- ]writing)\b/i],
  ["summarization", /\b(summariz|youtube[- ]transcript|tldr|digest)\b/i],
  ["multi-agent", /\b(multi[- ]agent|orchestrat|swarm|workforce|crewai|autogen|langgraph|subagent|agent[- ]team)\b/i],
  ["skill-management-tools", /\b(skill[- ]manag|skills[- ]manage|skill[- ]hub|skill[- ]registry|clawhub|plugin[- ]manager)\b/i],
  ["claude-code-hooks", /\b(claude[- ]code[- ]hook|statusline|hook[s]?[- ]for[- ]claude)\b/i],
  ["local-llm", /\b(ollama|llama\.cpp|vllm|lm[- ]studio|local[- ]llm|mlx|gguf)\b/i],
  ["cli-tools", /\b(cli|terminal|tui|shell|tmux|session[- ]log)\b/i],
  ["vibe-coding", /\b(vibe[- ]cod|ai[- ]coding|cursor[- ]rules|windsurf)\b/i],
  ["mcp-api", /\b(mcp|model[- ]context[- ]protocol|api[- ]gateway|proxy|relay)\b/i],
];

const GONE_CATEGORY_FALLBACK = {
  "claude-skill": "claude-code-skills",
  "codex-skill": "codex-skills",
  "mcp-server": "mcp-api",
  "agent-tool": "vibe-coding",
};

// Lightweight built-in titles so React SPA navigation (without static <meta name="ash:best">)
// can still render a rich bilingual guide CTA on any gone repo page.
const GUIDE_TITLES = {
  "claude-video-skills": ["Claude Video Editing & Remotion Skills", "最佳 Claude 视频剪辑与 Remotion Skill"],
  "animation-skills": ["Animation Skills", "动画与动效 Skill"],
  "ppt-presentation": ["PPT Skills for Codex & Claude Code", "PPT 演示生成 Skill"],
  "ai-design": ["AI Design Tools", "AI 设计工具与 Skill"],
  "anti-slop": ["Humanizer & Anti-Slop Skills", "去 AI 味 / 反套话 Skill"],
  "3d-mcp": ["Blender, Unity & Godot MCP", "3D 与游戏引擎 MCP"],
  "ai-reverse-engineering": ["AI Reverse Engineering Tools", "AI 逆向工程工具"],
  "browser-automation": ["browser-use, Playwright MCP & AI Browser Agents", "浏览器自动化与 Playwright MCP"],
  "web-scraping": ["Web Scraping", "网页抓取与爬虫 Skill"],
  "obsidian-second-brain": ["Obsidian for Claude Code & AI Agents", "Obsidian 第二大脑 Skill"],
  "knowledge-base": ["Knowledge Base & RAG", "知识库与长期记忆工具"],
  "mcp-database": ["MCP Database Tools", "数据库 MCP 工具"],
  "mcp-for-github": ["MCP Tools for GitHub", "GitHub MCP 工具"],
  "mcp-for-google": ["MCP Tools for Google Services", "Google 服务 MCP 工具"],
  "secret-detection": ["Secret Detection", "密钥检测与安全审计工具"],
  "code-review": ["Code Review", "AI 代码审查 Skill"],
  "refactoring": ["Code Refactoring", "代码重构 Skill"],
  "voice-agent": ["Voice Agents", "语音 Agent 工具"],
  "telegram-bot": ["Telegram Bot", "Telegram 机器人工具"],
  "image-generation": ["Image Generation", "AI 生图 Skill"],
  "seo-tools": ["Claude SEO Skills & SEO MCP Servers", "Claude SEO 技能与 MCP"],
  "content-writing": ["Content Writing", "内容写作 Skill"],
  "summarization": ["Summarization", "内容总结 Skill"],
  "multi-agent": ["Multi-Agent Orchestration", "多 Agent 编排工具"],
  "skill-management-tools": ["Skill & Agent Management", "Skill 与 Agent 管理工具"],
  "claude-code-hooks": ["Claude Code Hooks, Subagents & Statusline", "Claude Code Hooks 与子代理"],
  "local-llm": ["Local LLM Tools", "本地大模型工具"],
  "cli-tools": ["CLI Tools", "命令行 CLI 工具"],
  "vibe-coding": ["Open-Source Vibe Coding Tools", "开源 Vibe Coding 工具"],
  "mcp-api": ["MCP API Integration", "MCP API 集成工具"],
  "claude-code-skills": ["Claude Code Skills", "Claude Code 精选 Skill"],
  "codex-skills": ["OpenAI Codex Skills", "OpenAI Codex 精选 Skill"],
};

/** Pick the best active /best/<slug>/ guide to recommend on a deleted (404) repo page. */
export function matchGoneGuide(skill, liveBySlug = null) {
  if (!skill) return null;
  const text = `${skill.repo_full_name || ""} ${skill.description || ""} ${skill.topics || ""}`;
  let slug = null;
  for (const [candidate, pattern] of GONE_GUIDE_RULES) {
    if (pattern.test(text)) {
      slug = candidate;
      break;
    }
  }
  if (!slug) {
    slug = GONE_CATEGORY_FALLBACK[skill.category || ""] || "claude-code-skills";
  }
  if (liveBySlug && liveBySlug.has(slug)) {
    return liveBySlug.get(slug);
  }
  const titles = GUIDE_TITLES[slug];
  if (!titles) return null;
  return { slug, title: titles[0], titleZh: titles[1] };
}
