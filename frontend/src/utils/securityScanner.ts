/**
 * Browser-side Security Scanner — mirrors backend security_scanner.py
 * Inspired by SlowMist Agent Security Framework (11 red-flag categories).
 * Pure regex, zero external dependencies.
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

const REJECT_PATTERNS: PatternDef[] = [
  [/(?:cat|cp)\s+[^\n]*\.(?:ssh|aws|env)[^\n]*\|\s*(?:curl|nc|wget)/i, "exfil_secrets_combo", "critical", "Exfiltrates secrets via pipe to network tool"],
  [/(?:crontab|bashrc|zshrc)[^\n]*(?:curl|wget|nc)/i, "backdoor_install", "critical", "Installs backdoor via shell startup + remote download"],
];

const HIGH_PATTERNS: PatternDef[] = [
  // 1. Data Exfiltration
  [/curl\s+[^\n]*-d\s+[^\n]*\$\(/i, "data_exfiltration", "high", "Sends local data to external server via curl POST"],
  [/curl\s+[^\n]*\|\s*(ba)?sh/i, "curl_pipe_shell", "high", "Downloads and executes remote script via curl|bash"],
  [/wget\s+[^\n]*\|\s*(ba)?sh/i, "wget_pipe_shell", "high", "Downloads and executes remote script via wget|bash"],
  // 2. Credential Harvest
  [/env\s*\|\s*grep\s+-[iI].*(?:key|token|secret|password)/i, "credential_harvest", "high", "Harvests credentials from environment variables"],
  [/cat\s+[^\n]*\.env\b/i, "env_file_read", "high", "Reads .env files which may contain secrets"],
  // 3. Sensitive Dir Access
  [/(?:cat|cp|mv|rm|read)\s+[^\n]*~\/\.(?:ssh|aws|gnupg|config\/gcloud)/i, "sensitive_dir_access", "high", "Accesses sensitive directories (~/.ssh, ~/.aws)"],
  [/(?:cat|cp|mv|rm|read)\s+[^\n]*\/etc\/(?:shadow|passwd)/i, "etc_sensitive_read", "high", "Reads sensitive system files (/etc/shadow, /etc/passwd)"],
  // 4. Agent Memory Theft
  [/(?:cat|cp|read|curl)[^\n]*(?:MEMORY\.md|USER\.md|SOUL\.md|IDENTITY\.md)/i, "agent_memory_theft", "high", "Accesses agent memory/identity files"],
  [/(?:cat|cp|read)[^\n]*\.(?:claude|openclaw|cursor)\/(?:settings|sessions|memory)/i, "agent_config_theft", "high", "Accesses agent configuration/session files"],
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
  [/(?:systemctl\s+enable|launchd|plist|LoginItems)/i, "service_persistence", "high", "Installs persistent service/daemon"],
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
];

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
const HIGH_NAMES = new Set(HIGH_PATTERNS.map(p => p[1]));
const MED_NAMES = new Set(MED_PATTERNS.map(p => p[1]));

// All patterns indexed by flag name for description lookup
const ALL_PATTERNS = [...REJECT_PATTERNS, ...HIGH_PATTERNS, ...MED_PATTERNS];
const DESC_MAP = new Map(ALL_PATTERNS.map(([, name, sev, desc]) => [name, { severity: sev, description: desc }]));

function isInCodeBlock(text: string, pos: number): boolean {
  const before = text.slice(0, pos);
  return (before.split("```").length - 1) % 2 === 1;
}

/**
 * Scan README content for security issues.
 */
export function scanReadme(
  readme: string,
  author: string,
  stars: number,
  license: string | null,
): ScanResult {
  const flags: string[] = [];
  const text = readme.slice(0, 15000).toLowerCase();
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
    readme,
  };
}
