/**
 * Browser-side Security Scanner — mirrors backend security_scanner.py
 * Inspired by SlowMist Agent Security Framework (11 red-flag categories), plus
 * agent-era rules and destination-aware pipe-to-shell from the Snyk agent-scan
 * taxonomy. Pure regex, zero external dependencies.
 *
 * The backend scanner is the source of truth — it grades the catalog on every
 * sync. Keep the pattern lists, trust lists and grading here in step with it,
 * or /analyzer/ will contradict the grade printed on the same repo's page.
 */

export interface FlagDetail {
  name: string;
  severity: "critical" | "high" | "medium" | "low";
  description: string;
}

export interface ScanResult {
  grade: "safe" | "caution" | "unsafe" | "reject";
  flags: string[];
  flagDetails: FlagDetail[];
  trustTier: number;
  trustLabel: string;
}

// ══════════════════════════════════════════════════════════════════
// Trust Hierarchy (5 tiers)
// ══════════════════════════════════════════════════════════════════
const TIER1_ORGS = new Set([
  "anthropics", "modelcontextprotocol", "openai", "microsoft", "google",
  "github", "nvidia", "meta", "aws", "azure", "langchain-ai",
]);
const TIER2_ORGS = new Set([
  "slowmist", "trailofbits", "openzeppelin", "consensys",
  "pydantic", "stanfordnlp", "salesforce",
]);

const TRUST_LABELS: Record<number, string> = {
  1: "Official Org",
  2: "Known Security Team",
  3: "High-Star + Licensed",
  4: "Moderate Trust",
  5: "Unknown Source",
};

function getTrustTier(author: string, stars: number, license: string | null): number {
  const a = author.toLowerCase();
  if (TIER1_ORGS.has(a)) return 1;
  if (TIER2_ORGS.has(a)) return 2;
  const hasLicense = !!license;
  if (stars >= 1000 && hasLicense) return 3;
  if (stars >= 100 && hasLicense) return 4;
  return 5;
}

// ══════════════════════════════════════════════════════════════════
// Pattern definitions: [regex, flagName, severity, description]
// ══════════════════════════════════════════════════════════════════
type PatternDef = [RegExp, string, FlagDetail["severity"], string];

// Mirrors _AGENT_SECRET_PATH / _REMOTE_TARGET / _OUTBOUND / _AGENT_CONFIG_THEFT in
// the backend. Composed as strings so the pieces stay diffable against Python;
// no lookbehind anywhere (Vite's default target includes Safari 16.0–16.3).
const AGENT_SECRET_PATH =
  "(?:~?/?\\.(?:claude|openclaw|cursor|codex)(?:\\.json\\b|/(?:settings|sessions|memory|projects|history|\\.?credentials|auth|mcp)\\S*)"
  + "|claude_desktop_config\\.json)";
const REMOTE_TARGET =
  "(?:https?://|\\d{1,3}(?:\\.\\d{1,3}){3}"
  + "|[a-z0-9-]+\\.(?:com|net|org|io|dev|xyz|app|sh|ai|co|me|top|site|online|cloud|ru|cn)\\b)";
// curl's `-F` is left out on purpose: the scan runs on a lowercased README, where
// it collides with `-f` (fail) in `curl -fsSL … -o ~/.claude/settings.json`.
const OUTBOUND =
  "(?:\\|\\s*(?:curl|wget|nc|ncat|netcat|socat|ssh)\\b"
  + "|\\b(?:curl|wget)\\b[^\\n]*(?:https?://|\\s-(?:d|t)\\b|--(?:data(?:-binary)?|form|upload-file))"
  + "|\\b(?:scp|rsync)\\b[^\\n]*\\S+@\\S+:"
  + "|/dev/tcp/"
  + `|\\b(?:send|upload|post|exfiltrate|transmit|forward|submit)(?:s|ed|ing)?\\b[^\\n]{0,60}\\b(?:to|at)\\s+${REMOTE_TARGET})`;
const AGENT_CONFIG_THEFT =
  `\\b(?:cat|cp|read|tar|zip|base64|xxd|type|curl|wget)s?\\b[^\\n]*${AGENT_SECRET_PATH}[^\\n]*${OUTBOUND}`
  + `|\\b(?:curl|wget)\\b[^\\n]*(?:\\s-(?:d|t)\\b|--(?:data(?:-binary)?|form|upload-file))[^\\n]*@?${AGENT_SECRET_PATH}`
  + `|\\b(?:scp|rsync)\\b[^\\n]*${AGENT_SECRET_PATH}[^\\n]*\\S+@\\S+:`;

const REJECT_PATTERNS: PatternDef[] = [
  [/(?:cat|cp)\s+[^\n]*\.(?:ssh|aws|env)[^\n]*\|\s*(?:curl|nc|wget)/i, "exfil_secrets_combo", "critical", "Exfiltrates secrets via pipe to network tool"],
  [/(?:crontab|bashrc|zshrc)[^\n]*(?:curl|wget|nc)/i, "backdoor_install", "critical", "Installs backdoor via shell startup + remote download"],
];

const HIGH_PATTERNS: PatternDef[] = [
  // 1. Data Exfiltration
  [/curl\s+[^\n]*-d\s+[^\n]*\$\(/i, "data_exfiltration", "high", "Sends local data to external server via curl POST"],
  // curl|sh, wget|sh and irm|iex live in PIPE_PATTERNS — they need the destination checked.
  // 2. Credential Harvest
  [/env\s*\|\s*grep\s+-[iI].*(?:key|token|secret|password)/i, "credential_harvest", "high", "Harvests credentials from environment variables"],
  [/cat\s+[^\n]*\.env\b/i, "env_file_read", "high", "Reads .env files which may contain secrets"],
  // 3. Sensitive Dir Access
  [/(?:cat|cp|mv|rm|read)\s+[^\n]*~\/\.(?:ssh|aws|gnupg|config\/gcloud)/i, "sensitive_dir_access", "high", "Accesses sensitive directories (~/.ssh, ~/.aws)"],
  [/(?:cat|cp|mv|rm|read)\s+[^\n]*\/etc\/(?:shadow|passwd)/i, "etc_sensitive_read", "high", "Reads sensitive system files (/etc/shadow, /etc/passwd)"],
  // 4. Agent Memory Theft
  [/(?:cat|cp|read|curl)[^\n]*(?:MEMORY\.md|USER\.md|SOUL\.md|IDENTITY\.md)/i, "agent_memory_theft", "high", "Accesses agent memory/identity files"],
  // Read verb + agent secret path + outbound destination on one line. The bare
  // `cat|cp|read … .claude/settings` form was 168/168 false positives at catalog
  // scale ("mcp" contains "cp"; every Claude Code tool documents settings.json).
  [new RegExp(AGENT_CONFIG_THEFT, "i"), "agent_config_theft", "high", "Reads agent configuration/session/credential files and sends them out"],
  // 5. Dynamic Code Exec
  [/exec\s*\(\s*__import__/i, "exec_import", "high", "Executes dynamically imported Python code"],
  [/base64\s+(-d|--decode)\s*\|/i, "base64_exec", "high", "Decodes and pipes base64 data for execution"],
  // 6. Privilege Escalation
  [/chmod\s+(?:777|[+]s)\b/, "chmod_dangerous", "high", "Sets dangerous file permissions (777 or setuid)"],
  [/>\s*\/etc\//i, "write_etc", "high", "Writes to system /etc/ directory"],
  [/(?:chown\s+root|visudo|\/etc\/sudoers)/i, "privilege_escalation", "high", "Attempts privilege escalation to root"],
  // 7. Persistence
  [/(?:crontab|\/etc\/cron)/i, "cron_persistence", "high", "Installs cron job for persistence"],
  [/>>?\s*~\/\.(?:bashrc|zshrc|profile|bash_profile)/i, "shell_rc_inject", "high", "Injects commands into shell startup files"],
  // service_persistence moved to AGENT_MED_PATTERNS (medium, context-aware): 368/368 false positives as `launchd|plist`.
  // 8. Reverse Shell
  [/(nc|ncat|netcat)\s+-[elp]/i, "reverse_shell", "high", "Opens reverse shell connection"],
  [/\/dev\/tcp\//i, "dev_tcp", "high", "Uses /dev/tcp for network connection"],
  // 9. Destructive
  [/rm\s+-rf\s+\/\s/i, "rm_rf_root", "high", "Recursively deletes from root filesystem"],
  // 10. Obfuscation
  [/python[23]?\s+-c\s+["'].*(?:base64|codecs|rot13).*(?:exec|eval)/i, "obfuscated_exec", "high", "Executes obfuscated/encoded Python code"],
  [/\\x[0-9a-f]{2}\\x[0-9a-f]{2}\\x[0-9a-f]{2}/i, "hex_encoded_payload", "high", "Contains hex-encoded payload"],
  // 11. Supply Chain
  [/(?:npm|pip|gem)\s+install\s+[^\n]*&&\s*(?:node|python|ruby)\s/i, "runtime_install_exec", "high", "Installs and immediately executes package at runtime"],
  // 12. Prompt injection — covert action (Snyk: prompt_injection_skill_instructions)
  [/\bsecretly\s+(?:send|upload|post|exfiltrate|forward|transmit|copy|collect|harvest|steal|install|execute|run)\b/i, "prompt_injection_covert", "high", "Instructs the agent to act covertly (e.g. 'secretly send')"],
];

// Download-and-execute, judged by WHERE it downloads from (Snyk:
// suspicious_download_url). See the backend scanner for the catalog evidence.
const PIPE_PATTERNS: PatternDef[] = [
  [/\bcurl\s+(?:[^\n]*[^\\\n])?\|\s*(?:sudo\s+)?(?:ba|z)?sh\b/gi, "curl_pipe_shell", "high", "Downloads and executes a remote script from an untrusted source via curl|sh"],
  [/\bwget\s+(?:[^\n]*[^\\\n])?\|\s*(?:sudo\s+)?(?:ba|z)?sh\b/gi, "wget_pipe_shell", "high", "Downloads and executes a remote script from an untrusted source via wget|sh"],
  [/\b(?:iex|invoke-expression)\b[^\n]{0,40}\b(?:irm|iwr|invoke-restmethod|invoke-webrequest|downloadstring)\b[^\n)]{0,200}|\b(?:irm|iwr|invoke-restmethod|invoke-webrequest)\b(?:[^\n]{0,159}[^\\\n])?\|\s*(?:iex|invoke-expression)\b/gi, "powershell_download_exec", "high", "Downloads and executes a remote script from an untrusted source via PowerShell (irm|iex)"],
];

const TRUSTED_INSTALLER_HOSTS = new Set([
  "astral.sh", "sh.rustup.rs", "static.rust-lang.org", "bun.sh", "deno.land", "deno.com",
  "get.pnpm.io", "claude.ai", "cursor.com", "cli.kiro.dev", "opencode.ai", "ollama.com",
  "get.docker.com", "install.python-poetry.org", "get.volta.sh", "mise.run", "get.jetify.com",
  "nixos.org", "install.determinate.systems", "pkgx.sh", "starship.rs", "sdk.cloud.google.com",
  "get.scoop.sh", "community.chocolatey.org", "dot.net", "foundry.paradigm.xyz",
  "chatgpt.com", "cli.devin.ai", "junie.jetbrains.com",
  "openclaw.ai", "app.primeintellect.ai", "jimeng.jianying.com",
]);
const TRUSTED_GITHUB_INSTALLER_PREFIXES = ["homebrew/install/", "nvm-sh/nvm/"];
const GITHUB_CONTENT_HOSTS = new Set(["raw.githubusercontent.com", "github.com", "gist.githubusercontent.com"]);
const MULTI_TENANT_SUFFIXES = [
  "github.io", "gitlab.io", "vercel.app", "netlify.app", "pages.dev", "workers.dev",
  "fly.dev", "herokuapp.com", "onrender.com", "railway.app", "glitch.me", "replit.app",
  "web.app", "firebaseapp.com", "azurewebsites.net", "cloudfront.net", "amazonaws.com",
  "surge.sh", "deno.dev", "ngrok-free.app", "trycloudflare.com", "blogspot.com",
];
const URL_IN_COMMAND = /https?:\/\/[^\s`'"|)<>\]]+/g;
const REGISTRABLE_LABELS = 2;
const MIN_OWNER_DOMAIN_MATCH = 5;

// Agent-era medium patterns (Snyk taxonomy). Code spans, quoted examples and
// negated advice are skipped for the text-directive rules.
const AGENT_MED_PATTERNS: PatternDef[] = [
  // prompt_injection_override / _conceal removed — 11 hits, 11 false positives
  // at catalog scale (documented --system-prompt flags, injection guards listing
  // what they detect, a paper title, an anti-sycophancy rule). See the backend.
  [/\b(?:you are now|you're now|from now on,? you are|act as)\s+(?:in\s+)?(?:an?\s+)?(?:dan|jailbreak|jailbroken|god|unrestricted|unfiltered)(?:\s+mode)?\b/gi, "jailbreak_mode", "medium", "Attempts to switch the agent into an unrestricted/jailbreak persona"],
  [/\b(?:ignore|do not use|don't use|never use|avoid using)\s+(?:all\s+|any\s+)?(?:the\s+)?other\s+(?:tools|skills|servers|mcp servers|functions|plugins)\b/gi, "tool_priority_manipulation", "medium", "Pushes the agent to ignore other tools in favour of this one"],
  [/\b(?:paste|enter|type|provide|share|send|give)\s+(?:me\s+)?(?:your|the)\s+(?:api[\s_-]?keys?|access[\s_-]?tokens?|secret[\s_-]?keys?|passwords?|credentials|private[\s_-]?keys?)\s+(?:here|in(?:to)?\s+(?:the\s+|this\s+)?(?:chat|conversation|prompt|message|window))\b/gi, "credential_in_chat", "medium", "Asks for credentials to be pasted into the chat/prompt"],
  [/\b(?:curl|wget|irm|iwr|invoke-webrequest|invoke-restmethod)\b[^\n]{0,60}https?:\/\/(?:bit\.ly|tinyurl\.com|is\.gd|goo\.gl|rb\.gy|cutt\.ly|shorturl\.at|t\.ly|v\.gd)\//gi, "shortener_download", "medium", "Downloads from a URL shortener, which hides the real source"],
  [/\b(?:curl|wget|irm|iwr|invoke-webrequest|invoke-restmethod)\b[^\n]{0,80}(?:pastebin\.com\/raw|transfer\.sh|paste\.ee|hastebin\.com|0x0\.st|temp\.sh|catbox\.moe|anonfiles)/gi, "paste_host_download", "medium", "Downloads from an anonymous paste/file-drop host"],
  // SlowMist 7 (persistence), demoted from HIGH: only the explicit install
  // command, outside code spans. A documented daemon is a capability, not a
  // threat; persistence + remote download is REJECT's backdoor_install.
  [/\b(?:launchctl\s+(?:load|bootstrap|enable|submit)\b|systemctl\s+(?:--user\s+)?enable\b|sc(?:\.exe)?\s+create\b|schtasks(?:\.exe)?\s+\/create\b|reg(?:\.exe)?\s+add\s+[^\n]*\\run\b|(?:cp|mv|tee|>)[ \t]*[^\n]*library\/launch(?:agents|daemons)\/)/gi, "service_persistence", "medium", "Installs a persistent service/daemon (launchd, systemd, Task Scheduler)"],
];
const DESTINATION_FLAGS = new Set(["shortener_download", "paste_host_download"]);
const NEGATION_EXEMPT = new Set<string>();

// Snyk: secret_detection — matched on the ORIGINAL-case README (AKIA… is case-sensitive).
const SECRET_DESC = "Contains what looks like a real hardcoded API key, token or private key";
const SECRET_PATTERNS: PatternDef[] = [
  [/\bsk-ant-(?:api03|admin01)-[A-Za-z0-9_-]{80,}/g, "leaked_secret", "medium", SECRET_DESC],
  [/\bsk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{20,}T3BlbkFJ[A-Za-z0-9_-]{20,}/g, "leaked_secret", "medium", SECRET_DESC],
  [/\bgh[pousr]_[A-Za-z0-9]{36,}/g, "leaked_secret", "medium", SECRET_DESC],
  [/\bAKIA[0-9A-Z]{16}\b/g, "leaked_secret", "medium", SECRET_DESC],
  [/\bxox[baprs]-[0-9A-Za-z-]{20,}/g, "leaked_secret", "medium", SECRET_DESC],
  [/\bAIza[0-9A-Za-z_-]{35}\b/g, "leaked_secret", "medium", SECRET_DESC],
  [/\bsk_live_[0-9A-Za-z]{24,}/g, "leaked_secret", "medium", SECRET_DESC],
  [/-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----\s*[A-Za-z0-9+/=]{60,}/g, "leaked_secret", "medium", SECRET_DESC],
];
const PLACEHOLDER_HINTS = [
  "xxxx", "your", "example", "placeholder", "redacted", "dummy", "sample",
  "fake", "test", "0000", "1234", "abcd", "here", "insert", "replace",
];
const SECRET_PREFIX = /^(?:sk-ant-(?:api03-)?|sk-(?:proj-)?|gh[pousr]_|akia|xox[baprs]-|aiza|sk_live_)/;
const MIN_SECRET_CHAR_VARIETY = 10;
const EXAMPLE_LEADS = /(?:e\.g\.|i\.e\.|such as|for example|for instance|example:|like|attacks?\s+(?:like|such as)|payloads?\s+(?:like|such as)|phrases?\s+(?:like|such as)|detects?|blocks?|prevents?|defends?\s+against)\s*$/;
const QUOTE_CHARS = new Set(['"', "'", "`", "“", "‘", "「", "«"]);
const EXAMPLE_LEAD_WINDOW = 40;
const NEGATION_LEAD = /\b(?:never|not|don't|do not|avoid|must not|should not|shouldn't|won't|cannot|can't|no need to)\s*$/;
const NEGATION_WINDOW = 25;

const MED_PATTERNS: PatternDef[] = [
  [/\bsudo\b/, "sudo_usage", "medium", "Uses sudo for elevated privileges"],
  [/--privileged/i, "docker_privileged", "medium", "Runs Docker in privileged mode"],
  [/fs\.readdir\s*\(\s*['"]\//, "fs_root_access", "medium", "Reads root filesystem directory"],
  [/(OPENAI_API_KEY|ANTHROPIC_API_KEY|AWS_SECRET|GITHUB_TOKEN)/i, "sensitive_env_vars", "medium", "References sensitive API keys/tokens"],
  [/verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['"]?0/i, "ssl_disabled", "medium", "Disables SSL/TLS verification"],
  [/\beval\s*\(/, "eval_usage", "medium", "Uses eval() for dynamic code execution"],
  [/(?:fetch|requests?\.\w+|axios|got|http\.get)\s*\(\s*["']http:\/\/\d+\.\d+\.\d+\.\d+/i, "raw_ip_request", "medium", "Makes HTTP request to raw IP address"],
  [/(?:process\.env|os\.environ|os\.getenv)\s*\[/i, "env_access", "medium", "Accesses environment variables programmatically"],
  [/(?:subprocess\.(?:run|Popen|call)|child_process\.(?:exec|spawn))/i, "subprocess_spawn", "medium", "Spawns subprocesses for command execution"],
  [/(?:ngrok|serveo|localtunnel)/i, "tunnel_service", "medium", "Uses tunneling service"],
];

const REJECT_NAMES = new Set(REJECT_PATTERNS.map(p => p[1]));
const HIGH_NAMES = new Set([...HIGH_PATTERNS, ...PIPE_PATTERNS].map(p => p[1]));
const MED_NAMES = new Set([...MED_PATTERNS, ...AGENT_MED_PATTERNS, ...SECRET_PATTERNS].map(p => p[1]));

// All patterns indexed by flag name for description lookup
const ALL_PATTERNS = [...REJECT_PATTERNS, ...HIGH_PATTERNS, ...PIPE_PATTERNS, ...MED_PATTERNS, ...AGENT_MED_PATTERNS, ...SECRET_PATTERNS];
const DESC_MAP = new Map(ALL_PATTERNS.map(([, name, sev, desc]) => [name, { severity: sev, description: desc }]));

export interface ScanContext {
  /** owner/repo — the skill's own GitHub owner is a trusted install source. */
  repoFullName?: string;
  /** Project homepage — its site is a trusted install source. */
  homepage?: string;
}

function isInCodeBlock(text: string, pos: number): boolean {
  const before = text.slice(0, pos);
  return (before.split("```").length - 1) % 2 === 1;
}

function lineBefore(text: string, pos: number): string {
  return text.slice(text.lastIndexOf("\n", pos - 1) + 1, pos);
}

function isInsideQuoteOrInlineCode(text: string, pos: number): boolean {
  const line = lineBefore(text, pos);
  const count = (s: string) => line.split(s).length - 1;
  return count('"') % 2 === 1 || count("“") > count("”") || count("`") % 2 === 1;
}

function hasExampleLead(text: string, pos: number): boolean {
  const lead = text.slice(Math.max(0, pos - EXAMPLE_LEAD_WINDOW), pos).trimEnd();
  return EXAMPLE_LEADS.test(lead.replace(/["'`“‘「«]+$/, "").trimEnd());
}

function isQuotedExample(text: string, pos: number): boolean {
  const lead = text.slice(Math.max(0, pos - EXAMPLE_LEAD_WINDOW), pos).trimEnd();
  if (QUOTE_CHARS.has(lead.slice(-1))) return true;
  return hasExampleLead(text, pos);
}

function isNegated(text: string, pos: number): boolean {
  return NEGATION_LEAD.test(text.slice(Math.max(0, pos - NEGATION_WINDOW), pos).trimEnd());
}

function isCitedOrNegated(text: string, pos: number, name: string): boolean {
  // Destination flags: the opaque host is the whole signal, so no code span or
  // surrounding quote excuses it (a command in inline code starts right after a
  // backtick). Only an explicit "such as ..." or a negation can clear it.
  if (DESTINATION_FLAGS.has(name)) return hasExampleLead(text, pos) || isNegated(text, pos);
  if (isInCodeBlock(text, pos) || isInsideQuoteOrInlineCode(text, pos)) return true;
  if (isQuotedExample(text, pos)) return true;
  return !NEGATION_EXEMPT.has(name) && isNegated(text, pos);
}

function hostOf(url: string): string {
  try {
    return new URL(url.includes("://") ? url : `https://${url}`).hostname.toLowerCase();
  } catch {
    return "";
  }
}

function registrableDomain(host: string): string {
  return host.split(".").slice(-REGISTRABLE_LABELS).join(".");
}

function sameSite(host: string, homepageHost: string): boolean {
  if (!host || !homepageHost) return false;
  if (MULTI_TENANT_SUFFIXES.some(s => homepageHost === s || homepageHost.endsWith(`.${s}`))) return host === homepageHost;
  return registrableDomain(host) === registrableDomain(homepageHost);
}

function ownerMatchesDomain(owner: string, host: string): boolean {
  const registrable = registrableDomain(host);
  if (MULTI_TENANT_SUFFIXES.includes(registrable)) return false;
  const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, "");
  const o = norm(owner), label = norm(registrable.split(".")[0]);
  if (Math.min(o.length, label.length) < MIN_OWNER_DOMAIN_MATCH) return false;
  return o.startsWith(label) || label.startsWith(o);
}

function isTrustedInstallSource(url: string, ctx: ScanContext): boolean {
  const host = hostOf(url);
  if (TRUSTED_INSTALLER_HOSTS.has(host)) return true;
  const owner = (ctx.repoFullName ?? "").toLowerCase().split("/")[0];
  if (GITHUB_CONTENT_HOSTS.has(host)) {
    let path = "";
    try { path = new URL(url).pathname.toLowerCase().replace(/^\//, ""); } catch { return false; }
    return (!!owner && path.startsWith(`${owner}/`)) || TRUSTED_GITHUB_INSTALLER_PREFIXES.some(p => path.startsWith(p));
  }
  if (owner && (host === `${owner}.github.io` || ownerMatchesDomain(owner, host))) return true;
  return sameSite(host, ctx.homepage ? hostOf(ctx.homepage.trim()) : "");
}

function isMarkdownTableRow(text: string, pos: number): boolean {
  return lineBefore(text, pos).trimStart().startsWith("|");
}

function pipeToShellFlags(text: string, ctx: ScanContext): string[] {
  const found: string[] = [];
  for (const [re, name] of PIPE_PATTERNS) {
    for (const m of text.matchAll(re)) {
      const pos = m.index ?? 0;
      if (isInCodeBlock(text, pos) || isMarkdownTableRow(text, pos)) continue;
      const urls = m[0].match(URL_IN_COMMAND) ?? [];
      if (urls.length === 0 || urls.every(u => isTrustedInstallSource(u, ctx))) continue;
      found.push(name);
      break;
    }
  }
  return found;
}

function agentMediumFlags(text: string): string[] {
  const found: string[] = [];
  for (const [re, name] of AGENT_MED_PATTERNS) {
    for (const m of text.matchAll(re)) {
      if (isCitedOrNegated(text, m.index ?? 0, name)) continue;
      found.push(name);
      break;
    }
  }
  return found;
}

function looksLikeRealSecret(token: string): boolean {
  const lowered = token.toLowerCase();
  if (PLACEHOLDER_HINTS.some(h => lowered.includes(h))) return false;
  return new Set(lowered.replace(SECRET_PREFIX, "")).size >= MIN_SECRET_CHAR_VARIETY;
}

function secretFlags(original: string): string[] {
  for (const [re, name] of SECRET_PATTERNS) {
    for (const m of original.matchAll(re)) {
      if (looksLikeRealSecret(m[0])) return [name];
    }
  }
  return [];
}

/**
 * Scan README content for security issues.
 */
export function scanReadme(
  readme: string,
  author: string,
  stars: number,
  license: string | null,
  context: ScanContext = {},
): ScanResult {
  const flags: string[] = [];
  const original = readme.slice(0, 15000);
  const text = original.toLowerCase();
  const trustTier = getTrustTier(author, stars, license);

  // Check REJECT patterns
  for (const [re, name] of REJECT_PATTERNS) {
    const m = re.exec(text);
    if (m && !isInCodeBlock(text, m.index)) flags.push(name);
  }

  if (flags.some(f => REJECT_NAMES.has(f))) {
    const grade = trustTier <= 2 ? "unsafe" : "reject";
    return _buildResult(grade, flags, trustTier);
  }

  // Check HIGH patterns
  for (const [re, name] of HIGH_PATTERNS) {
    const m = re.exec(text);
    if (m && !isInCodeBlock(text, m.index)) flags.push(name);
  }

  // Check MED patterns
  for (const [re, name] of MED_PATTERNS) {
    const m = re.exec(text);
    if (m) {
      if (name === "sensitive_env_vars") {
        const envCount = new Set(
          readme.match(/(OPENAI_API_KEY|ANTHROPIC_API_KEY|AWS_SECRET|GITHUB_TOKEN)/gi) || []
        ).size;
        if (envCount >= 3) flags.push(name);
      } else {
        flags.push(name);
      }
    }
  }

  // Download-and-execute (destination-aware), agent-era patterns, leaked secrets
  flags.push(...pipeToShellFlags(text, context), ...agentMediumFlags(text), ...secretFlags(original));

  // Grade determination with trust hierarchy
  const highFlags = flags.filter(f => HIGH_NAMES.has(f));
  const medFlags = flags.filter(f => MED_NAMES.has(f));

  let grade: ScanResult["grade"] = "safe";

  if (highFlags.length > 0) {
    if (trustTier <= 3) grade = "caution";
    else if (trustTier === 4 && highFlags.length === 1) grade = "caution";
    else grade = "unsafe";
  } else if (medFlags.length >= 2) {
    grade = trustTier <= 3 ? "safe" : "caution";
  } else if (medFlags.length === 1) {
    grade = trustTier === 5 ? "caution" : "safe";
  }

  return _buildResult(grade, flags, trustTier);
}

function _buildResult(grade: ScanResult["grade"], flags: string[], trustTier: number): ScanResult {
  return {
    grade,
    flags,
    flagDetails: flags.map(f => {
      const info = DESC_MAP.get(f);
      return {
        name: f,
        severity: info?.severity ?? "medium",
        description: info?.description ?? f,
      };
    }),
    trustTier,
    trustLabel: TRUST_LABELS[trustTier] || "Unknown",
  };
}

/**
 * Fetch repo info + README from GitHub public API (unauthenticated, 60 req/hr).
 */
export async function fetchGitHubRepo(fullName: string): Promise<{
  stars: number;
  description: string;
  license: string | null;
  author: string;
  repoUrl: string;
  homepage: string;
  readme: string;
}> {
  const [repoResp, readmeResp] = await Promise.all([
    fetch(`https://api.github.com/repos/${fullName}`, {
      headers: { Accept: "application/vnd.github.v3+json" },
    }),
    fetch(`https://api.github.com/repos/${fullName}/readme`, {
      headers: { Accept: "application/vnd.github.v3.raw" },
    }),
  ]);

  if (!repoResp.ok) {
    if (repoResp.status === 404) throw new Error(`Repository ${fullName} not found`);
    if (repoResp.status === 403) throw new Error("GitHub API rate limit exceeded. Try again later.");
    throw new Error(`GitHub API error: ${repoResp.status}`);
  }

  const repo = await repoResp.json();
  const readme = readmeResp.ok ? await readmeResp.text() : "";

  return {
    stars: repo.stargazers_count || 0,
    description: repo.description || "",
    license: repo.license?.spdx_id || null,
    author: repo.owner?.login || "unknown",
    repoUrl: repo.html_url || `https://github.com/${fullName}`,
    homepage: repo.homepage || "",
    readme,
  };
}
