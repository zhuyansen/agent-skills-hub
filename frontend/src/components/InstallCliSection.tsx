import { useState, type ReactNode } from "react";
import { useI18n } from "../i18n/I18nContext";

// Flip to true once @agentskillshub/cli is published on npm — this swaps the
// displayed command to the clean scoped form and reveals the npm link.
// Published 2026-06-14: https://www.npmjs.com/package/@agentskillshub/cli
const CLI_NPM_PUBLISHED = true;
// Flip to true once @agentskillshub/mcp is published on npm. Until then the
// config points at the GitHub repo (npx can run it directly), so the button
// works the moment the repo is public — before the npm publish lands.
const MCP_NPM_PUBLISHED = false;

const CLI_CMD = CLI_NPM_PUBLISHED
  ? 'npx @agentskillshub/cli search "scrape a website" --safe'
  : 'npx github:zhuyansen/agentskillshub-cli search "scrape a website" --safe';

const MCP_PKG = MCP_NPM_PUBLISHED
  ? "@agentskillshub/mcp"
  : "github:zhuyansen/agentskillshub-mcp";
const MCP_CONFIG = `{
  "mcpServers": {
    "agentskillshub": {
      "command": "npx",
      "args": ["-y", "${MCP_PKG}"]
    }
  }
}`;

const CLI_REPO = "https://github.com/zhuyansen/agentskillshub-cli";
const MCP_REPO = "https://github.com/zhuyansen/agentskillshub-mcp";
const CLI_NPM = "https://www.npmjs.com/package/@agentskillshub/cli";
const MCP_NPM = "https://www.npmjs.com/package/@agentskillshub/mcp";

// LobeHub-style agent onboarding: one prompt the user pastes into their agent;
// the agent reads /skill.md and teaches itself to search/audit/install with
// security grades. The file is served from public/ at the domain root.
const AGENT_PROMPT =
  "Read https://agentskillshub.top/skill.md and follow its instructions — it teaches you to search, audit, and install AI agent skills & MCP servers with a security grade checked BEFORE installing.";

const GH_ICON =
  "M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.043-1.61-4.043-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z";

type Tab = "cli" | "mcp" | "agent";

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard?.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    });
  };
  return (
    <button
      onClick={copy}
      aria-label="Copy to clipboard"
      className="shrink-0 px-2.5 py-1.5 rounded-md text-xs font-medium text-gray-300 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 transition-colors cursor-pointer"
    >
      {copied ? "✓ Copied" : "Copy"}
    </button>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors cursor-pointer ${
        active
          ? "bg-white dark:bg-white/15 text-gray-900 dark:text-white shadow-sm"
          : "text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
      }`}
    >
      {children}
    </button>
  );
}

function SourceLinks({
  repo,
  npmUrl,
  showNpm,
}: {
  repo: string;
  npmUrl: string;
  showNpm: boolean;
}) {
  const { lang } = useI18n();
  const isZh = lang === "zh";
  return (
    <div className="mt-6 flex flex-wrap justify-center items-center gap-x-5 gap-y-2 text-sm">
      <a
        href={repo}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 text-[var(--text-2)] hover:text-[var(--text-1)] font-medium transition-colors"
      >
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
          <path d={GH_ICON} />
        </svg>
        {isZh ? "查看源码" : "View source"}
      </a>
      {showNpm && (
        <a
          href={npmUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 text-[var(--text-2)] hover:text-[var(--text-1)] font-medium transition-colors"
        >
          npm
        </a>
      )}
    </div>
  );
}

export function InstallCliSection() {
  const { lang } = useI18n();
  const isZh = lang === "zh";
  const [tab, setTab] = useState<Tab>("cli");

  return (
    <section className="py-12 mb-8">
      <div className="max-w-3xl mx-auto text-center">
        <div className="eyebrow mb-4">
          {isZh ? "在你的 agent 里用" : "Use it inside your agent"}
        </div>
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white tracking-tight mb-3">
          {isZh ? "一行,装进你的 agent" : "One line, inside your agent"}
        </h2>
        <p className="text-[var(--text-2)] max-w-xl mx-auto mb-7 leading-relaxed">
          {isZh
            ? "搜索、审计、安装 —— 不离开 Claude Code / Cursor。每条结果都带安全等级,本地运行、零后端负载。"
            : "Search, audit, install — without leaving Claude Code or Cursor. Every result is security-graded; runs locally, zero backend load."}
        </p>

        {/* CLI / MCP / Agent toggle */}
        <div className="inline-flex mb-4 p-0.5 rounded-lg border border-gray-200 dark:border-white/10 bg-gray-100 dark:bg-white/5">
          <TabButton active={tab === "cli"} onClick={() => setTab("cli")}>
            {isZh ? "CLI 终端" : "CLI"}
          </TabButton>
          <TabButton active={tab === "mcp"} onClick={() => setTab("mcp")}>
            {isZh ? "MCP 服务器" : "MCP Server"}
          </TabButton>
          <TabButton active={tab === "agent"} onClick={() => setTab("agent")}>
            {isZh ? "🤖 发给你的 Agent" : "🤖 For Agents"}
          </TabButton>
        </div>

        {/* Terminal / config card */}
        <div className="text-left rounded-xl overflow-hidden border border-gray-800 bg-[#0d1117] shadow-lg max-w-2xl mx-auto">
          <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-gray-800">
            <span className="w-3 h-3 rounded-full bg-[#ff5f56]" />
            <span className="w-3 h-3 rounded-full bg-[#ffbd2e]" />
            <span className="w-3 h-3 rounded-full bg-[#27c93f]" />
            <span className="ml-2 text-[11px] text-gray-500 font-mono">
              {tab === "cli"
                ? "ash — AgentSkillsHub CLI"
                : tab === "mcp"
                  ? "mcp config — add to your agent"
                  : "prompt — paste into your agent's chat"}
            </span>
          </div>

          {tab === "cli" && (
            <div className="flex items-center gap-3 px-4 py-4 font-mono text-sm">
              <span className="text-emerald-400 select-none">$</span>
              <code className="flex-1 text-gray-100 overflow-x-auto whitespace-nowrap">
                {CLI_CMD}
              </code>
              <CopyButton text={CLI_CMD} />
            </div>
          )}
          {tab === "mcp" && (
            <div className="relative px-4 py-4 font-mono text-xs sm:text-sm">
              <pre className="text-gray-100 overflow-x-auto whitespace-pre leading-relaxed">
                {MCP_CONFIG}
              </pre>
              <div className="absolute top-3 right-3">
                <CopyButton text={MCP_CONFIG} />
              </div>
            </div>
          )}
          {tab === "agent" && (
            <div className="flex items-start gap-3 px-4 py-4 text-sm">
              <span className="select-none" aria-hidden>
                💬
              </span>
              <p className="flex-1 text-gray-100 leading-relaxed text-left">
                {AGENT_PROMPT}
              </p>
              <CopyButton text={AGENT_PROMPT} />
            </div>
          )}
        </div>

        {/* Per-tab helper line */}
        <p className="mt-4 text-xs text-[var(--text-3)] max-w-xl mx-auto">
          {tab === "cli" &&
            (isZh
              ? "适用于任何终端。首次运行会缓存索引,之后离线可用。"
              : "Works in any terminal. Caches the index on first run, then works offline.")}
          {tab === "mcp" &&
            (isZh
              ? "粘贴进 Claude Code / Cursor / Cline / Cherry Studio 的 MCP 配置,重启客户端即可。无需 API key。"
              : "Paste into your Claude Code / Cursor / Cline / Cherry Studio MCP config and restart the client. No API key needed.")}
          {tab === "agent" &&
            (isZh
              ? "把这句话发给 Claude Code / Cursor / 任何 agent —— 它会自己读 skill.md,学会带安全评级地搜索和安装。"
              : "Paste this into Claude Code / Cursor / any agent — it reads skill.md and teaches itself to search & install with security grades.")}
        </p>

        {tab === "cli" ? (
          <SourceLinks
            repo={CLI_REPO}
            npmUrl={CLI_NPM}
            showNpm={CLI_NPM_PUBLISHED}
          />
        ) : (
          <SourceLinks
            repo={MCP_REPO}
            npmUrl={MCP_NPM}
            showNpm={MCP_NPM_PUBLISHED}
          />
        )}
      </div>
    </section>
  );
}
