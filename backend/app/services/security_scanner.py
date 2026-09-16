"""
Security Scanner — Rule-based security analysis for skills.

Inspired by SlowMist Agent Security Framework (11 red-flag categories).
Incorporates Trust Hierarchy (5 tiers) for weighted risk assessment.

Grades:
  - "safe": No concerning patterns detected
  - "caution": Some potentially risky patterns found
  - "unsafe": High-risk patterns detected
  - "reject": Confirmed malicious patterns (new, from SlowMist)

Zero cost: pure regex/string matching, no external API calls.
"""

import json
import logging
import re
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.skill import Skill

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════
# Trust Hierarchy (SlowMist-inspired, 5 tiers)
# ══════════════════════════════════════════════════════════════════════
TRUST_TIER_1_ORGS = {
    "anthropics", "modelcontextprotocol", "openai", "microsoft", "google",
    "github", "nvidia", "meta", "aws", "azure", "langchain-ai",
}
TRUST_TIER_2_ORGS = {
    "slowmist", "trailofbits", "openzeppelin", "consensys",
    "pydantic", "stanfordnlp", "salesforce",
}
# Tier 3: stars >= 1000 + license + active (computed dynamically)
# Tier 4: stars >= 100 + license (computed dynamically)
# Tier 5: everything else (maximum scrutiny)


def _get_trust_tier(skill: Skill) -> int:
    """Compute trust tier for a skill (1=highest trust, 5=lowest)."""
    author = (skill.author_name or "").lower()
    if author in TRUST_TIER_1_ORGS:
        return 1
    if author in TRUST_TIER_2_ORGS:
        return 2
    stars = skill.stars or 0
    has_license = bool(skill.license)
    if stars >= 1000 and has_license:
        return 3
    if stars >= 100 and has_license:
        return 4
    return 5


# ══════════════════════════════════════════════════════════════════════
# HIGH-RISK PATTERNS — SlowMist 11 Categories
# Any single match (outside code blocks) → unsafe
# ══════════════════════════════════════════════════════════════════════
HIGH_RISK_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    # ── 1. Outbound Data Exfiltration ──
    # Sending local data to external servers via curl/wget POST
    (re.compile(r"curl\s+[^\n]*-d\s+[^\n]*\$\(", re.IGNORECASE), "data_exfiltration",
     "Sends local data to external server via curl POST"),
    # curl|sh, wget|sh and PowerShell irm|iex live in PIPE_TO_SHELL_PATTERNS:
    # they need the destination checked, not just the pattern.

    # ── 2. Credential / Environment Variable Harvesting ──
    (re.compile(r'env\s*\|\s*grep\s+-[iI].*(?:key|token|secret|password)', re.IGNORECASE), "credential_harvest",
     "Harvests credentials from environment variables"),
    (re.compile(r'cat\s+[^\n]*\.env\b', re.IGNORECASE), "env_file_read",
     "Reads .env files which may contain secrets"),

    # ── 3. Sensitive File System Access ──
    (re.compile(r'(?:cat|cp|mv|rm|read)\s+[^\n]*~/\.(?:ssh|aws|gnupg|config/gcloud)', re.IGNORECASE), "sensitive_dir_access",
     "Accesses sensitive directories (~/.ssh, ~/.aws, ~/.gnupg)"),
    (re.compile(r'(?:cat|cp|mv|rm|read)\s+[^\n]*/etc/(?:shadow|passwd)', re.IGNORECASE), "etc_sensitive_read",
     "Reads sensitive system files (/etc/shadow, /etc/passwd)"),

    # ── 4. Agent Identity / Memory File Theft ──
    (re.compile(r'(?:cat|cp|read|curl)[^\n]*(?:MEMORY\.md|USER\.md|SOUL\.md|IDENTITY\.md)', re.IGNORECASE), "agent_memory_theft",
     "Accesses agent memory/identity files"),
    (re.compile(r'(?:cat|cp|read)[^\n]*\.(?:claude|openclaw|cursor)/(?:settings|sessions|memory)', re.IGNORECASE), "agent_config_theft",
     "Accesses agent configuration/session files"),

    # ── 5. Dynamic Code Execution from External Input ──
    (re.compile(r"exec\s*\(\s*__import__", re.IGNORECASE), "exec_import",
     "Executes dynamically imported Python code"),
    (re.compile(r"base64\s+(-d|--decode)\s*\|", re.IGNORECASE), "base64_exec",
     "Decodes and pipes base64 data for execution"),

    # ── 6. Privilege Escalation ──
    (re.compile(r"chmod\s+(?:777|[+]s)\b"), "chmod_dangerous",
     "Sets dangerous file permissions (777 or setuid)"),
    (re.compile(r">\s*/etc/", re.IGNORECASE), "write_etc",
     "Writes to system /etc/ directory"),
    (re.compile(r"(?:chown\s+root|visudo|/etc/sudoers)", re.IGNORECASE), "privilege_escalation",
     "Attempts privilege escalation to root"),

    # ── 7. Persistence Mechanisms ──
    (re.compile(r'(?:crontab|/etc/cron)', re.IGNORECASE), "cron_persistence",
     "Installs cron job for persistence"),
    (re.compile(r'>>?\s*~/\.(?:bashrc|zshrc|profile|bash_profile)', re.IGNORECASE), "shell_rc_inject",
     "Injects commands into shell startup files"),
    (re.compile(r'(?:systemctl\s+enable|launchd|plist|LoginItems)', re.IGNORECASE), "service_persistence",
     "Installs persistent service/daemon"),

    # ── 8. Reverse Shell ──
    (re.compile(r"(nc|ncat|netcat)\s+-[elp]", re.IGNORECASE), "reverse_shell",
     "Opens reverse shell connection"),
    (re.compile(r"/dev/tcp/", re.IGNORECASE), "dev_tcp",
     "Uses /dev/tcp for network connection (reverse shell indicator)"),

    # ── 9. Destructive Operations ──
    (re.compile(r"rm\s+-rf\s+/\s", re.IGNORECASE), "rm_rf_root",
     "Recursively deletes from root filesystem"),

    # ── 10. Obfuscation / Encoding ──
    (re.compile(r'python[23]?\s+-c\s+["\'].*(?:base64|codecs|rot13).*(?:exec|eval)', re.IGNORECASE), "obfuscated_exec",
     "Executes obfuscated/encoded Python code"),
    (re.compile(r'\\x[0-9a-f]{2}\\x[0-9a-f]{2}\\x[0-9a-f]{2}', re.IGNORECASE), "hex_encoded_payload",
     "Contains hex-encoded payload (possible obfuscation)"),

    # ── 11. Supply Chain / Secondary Download ──
    (re.compile(r'(?:npm|pip|gem)\s+install\s+[^\n]*&&\s*(?:node|python|ruby)\s', re.IGNORECASE), "runtime_install_exec",
     "Installs and immediately executes package at runtime"),
    # ── 12. Prompt injection — covert action ──
    # Gap found against Snyk agent-scan's taxonomy (prompt_injection_skill_
    # instructions). Only the unambiguous form lives at high severity: an
    # instruction to move data or run something "secretly". The ambiguous forms
    # ("ignore previous instructions") are medium — see AGENT_MEDIUM_PATTERNS.
    (re.compile(r"\bsecretly\s+(?:send|upload|post|exfiltrate|forward|transmit|copy|collect|harvest|steal|install|execute|run)\b", re.IGNORECASE),
     "prompt_injection_covert", "Instructs the agent to act covertly (e.g. 'secretly send')"),
]

# ══════════════════════════════════════════════════════════════════════
# PIPE-TO-SHELL — download-and-execute, judged by WHERE it downloads from
# ══════════════════════════════════════════════════════════════════════
# The pattern alone was the old rule, and it graded the catalog's most popular
# projects "caution": Graphify (116K★), LightRAG, NVIDIA/SkillSpector, ElevenLabs
# and MiniMax all tell readers to `curl -LsSf https://astral.sh/uv/install.sh | sh`.
# 42 of 47 hits in a 4,373-README sample were official installers in inline
# code, which the fence check never saw. Snyk agent-scan's
# suspicious_download_url draws the line we lacked: the risk is an untrusted
# or obscured source, not a documented installer from a verified one.
#
# Trusting a skill's own repo/owner/homepage is deliberate: installing a tool
# already means running its author's code, so their install script adds no new
# party to trust. A malicious author is caught by the other categories.
# The `\b` after the shell name matters: `| shasum -a 256` — verifying a
# download — used to match `| sh` and read as "downloads and executes".
# `(?:[^\n]*[^\\\n])?\|` requires the pipe not be escaped, which skips the `\|`
# markdown needs inside table cells — READMEs that tabulate *other* tools'
# installers (Devin, Junie, Plandex) aren't running them. It's the lookbehind
# `(?<!\\)\|` spelled without lookbehind, so the frontend copy of this pattern
# parses on Safari 16.0–16.3 (Vite's default target; lookbehind landed in 16.4).
PIPE_TO_SHELL_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"\bcurl\s+(?:[^\n]*[^\\\n])?\|\s*(?:sudo\s+)?(?:ba|z)?sh\b", re.IGNORECASE), "curl_pipe_shell",
     "Downloads and executes a remote script from an untrusted source via curl|sh"),
    (re.compile(r"\bwget\s+(?:[^\n]*[^\\\n])?\|\s*(?:sudo\s+)?(?:ba|z)?sh\b", re.IGNORECASE), "wget_pipe_shell",
     "Downloads and executes a remote script from an untrusted source via wget|sh"),
    # The `iex (irm …)` form consumes its argument up to the first `)` so the URL
    # lands inside the match — otherwise it reads as a URL-less mention.
    (re.compile(r"\b(?:iex|invoke-expression)\b[^\n]{0,40}\b(?:irm|iwr|invoke-restmethod|invoke-webrequest|downloadstring)\b[^\n)]{0,200}"
                r"|\b(?:irm|iwr|invoke-restmethod|invoke-webrequest)\b(?:[^\n]{0,159}[^\\\n])?\|\s*(?:iex|invoke-expression)\b", re.IGNORECASE),
     "powershell_download_exec", "Downloads and executes a remote script from an untrusted source via PowerShell (irm|iex)"),
]

# Exact hosts of widely-used official installers. Exact match only — a
# registrable-domain match on e.g. fly.io would also trust user-controlled
# subdomains of hosting platforms.
TRUSTED_INSTALLER_HOSTS = frozenset({
    "astral.sh", "sh.rustup.rs", "static.rust-lang.org", "bun.sh", "deno.land", "deno.com",
    "get.pnpm.io", "claude.ai", "cursor.com", "cli.kiro.dev", "opencode.ai", "ollama.com",
    "get.docker.com", "install.python-poetry.org", "get.volta.sh", "mise.run", "get.jetify.com",
    "nixos.org", "install.determinate.systems", "pkgx.sh", "starship.rs", "sdk.cloud.google.com",
    "get.scoop.sh", "community.chocolatey.org", "dot.net", "foundry.paradigm.xyz",
    # AI coding-agent vendors whose installers skills routinely point to.
    "chatgpt.com", "cli.devin.ai", "junie.jetbrains.com",
    # Vendor installers that third-party guides quote verbatim.
    "openclaw.ai", "app.primeintellect.ai", "jimeng.jianying.com",
})
# Official installers served from someone else's GitHub repo.
TRUSTED_GITHUB_INSTALLER_PREFIXES = ("homebrew/install/", "nvm-sh/nvm/")
_GITHUB_CONTENT_HOSTS = frozenset({"raw.githubusercontent.com", "github.com", "gist.githubusercontent.com"})
# Hosting platforms where the registrable domain is shared by strangers, so a
# homepage on one of them only vouches for its exact host.
MULTI_TENANT_SUFFIXES = (
    "github.io", "gitlab.io", "vercel.app", "netlify.app", "pages.dev", "workers.dev",
    "fly.dev", "herokuapp.com", "onrender.com", "railway.app", "glitch.me", "replit.app",
    "web.app", "firebaseapp.com", "azurewebsites.net", "cloudfront.net", "amazonaws.com",
    "surge.sh", "deno.dev", "ngrok-free.app", "trycloudflare.com", "blogspot.com",
)
_URL_IN_COMMAND = re.compile(r"https?://[^\s`'\"|)<>\]]+")
_REGISTRABLE_LABELS = 2
_MIN_OWNER_DOMAIN_MATCH = 5

HIGH_RISK_FLAG_NAMES = {p[1] for p in HIGH_RISK_PATTERNS} | {p[1] for p in PIPE_TO_SHELL_PATTERNS}

# ══════════════════════════════════════════════════════════════════════
# MEDIUM-RISK PATTERNS (2+ → caution)
# ══════════════════════════════════════════════════════════════════════
MEDIUM_RISK_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    # sudo usage
    (re.compile(r"\bsudo\b"), "sudo_usage",
     "Uses sudo for elevated privileges"),
    # Privileged Docker
    (re.compile(r"--privileged", re.IGNORECASE), "docker_privileged",
     "Runs Docker container in privileged mode"),
    # Broad file system access patterns
    (re.compile(r'fs\.readdir\s*\(\s*["\']/', re.IGNORECASE), "fs_root_access",
     "Reads root filesystem directory"),
    # Multiple sensitive env vars
    (re.compile(r"(OPENAI_API_KEY|ANTHROPIC_API_KEY|AWS_SECRET|GITHUB_TOKEN)", re.IGNORECASE), "sensitive_env_vars",
     "References multiple sensitive API keys/tokens"),
    # Disable SSL verification
    (re.compile(r"verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0", re.IGNORECASE), "ssl_disabled",
     "Disables SSL/TLS certificate verification"),
    # Eval in JS/Python context
    (re.compile(r"\beval\s*\("), "eval_usage",
     "Uses eval() for dynamic code execution"),
    # Network access to unknown IPs
    (re.compile(r'(?:fetch|requests?\.\w+|axios|got|http\.get)\s*\(\s*["\']http://\d+\.\d+\.\d+\.\d+', re.IGNORECASE), "raw_ip_request",
     "Makes HTTP request to raw IP address (suspicious)"),
    # Excessive process.env / os.environ access
    (re.compile(r'(?:process\.env|os\.environ|os\.getenv)\s*\[', re.IGNORECASE), "env_access",
     "Accesses environment variables programmatically"),
    # Subprocess/child_process spawn
    (re.compile(r'(?:subprocess\.(?:run|Popen|call)|child_process\.(?:exec|spawn))', re.IGNORECASE), "subprocess_spawn",
     "Spawns subprocesses for command execution"),
    # Outbound network to unknown domains (heuristic)
    (re.compile(r'(?:ngrok|serveo|localtunnel)', re.IGNORECASE), "tunnel_service",
     "Uses tunneling service to expose local network"),
]

# ══════════════════════════════════════════════════════════════════════
# AGENT-ERA MEDIUM PATTERNS — gaps found against Snyk agent-scan's risk
# taxonomy (docs/risks.md, 2026-07-10 analysis API). SlowMist's 11 categories
# are general code security; these target threats that only exist because the
# file is *instructions to an agent*. Unlike MEDIUM_RISK_PATTERNS, matches in
# code blocks and quoted examples are skipped: defence and education skills
# quote these strings, and must not be graded as the attack they describe.
# ══════════════════════════════════════════════════════════════════════
AGENT_MEDIUM_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    # Snyk: prompt_injection_skill_instructions
    # prompt_injection_override and prompt_injection_conceal were removed after
    # the full-catalog re-grade: 11 hits, 11 false positives. "override the
    # system prompt" is a documented CLI flag (av/mi, clido-cli); injection
    # guards and threat tables list the attack they detect; a paper title is
    # "Ignore Previous Prompt"; and "never tell the user what it thinks the user
    # wants to hear" is an anti-sycophancy rule, not concealment. A skill file
    # IS instructions, and this ecosystem documents these exact phrases, so a
    # regex cannot separate issuing one from describing one. Judging that needs
    # the LLM pass sync already runs over caution/unsafe rows.
    # Persona hijack addressed to the model. Deliberately excludes "enable
    # developer mode": ChatGPT's MCP connector setting and Chrome's extension
    # toggle are both called that, and all 8 hits in the catalog sample were
    # setup steps for one or the other.
    (re.compile(r"\b(?:you are now|you're now|from now on,? you are|act as)\s+(?:in\s+)?(?:an?\s+)?"
                r"(?:dan|jailbreak|jailbroken|god|unrestricted|unfiltered)(?:\s+mode)?\b", re.IGNORECASE),
     "jailbreak_mode", "Attempts to switch the agent into an unrestricted/jailbreak persona"),
    # Snyk: dangerous_words — language that inflates a tool's priority over others
    (re.compile(r"\b(?:ignore|do not use|don't use|never use|avoid using)\s+(?:all\s+|any\s+)?(?:the\s+)?other\s+"
                r"(?:tools|skills|servers|mcp servers|functions|plugins)\b", re.IGNORECASE),
     "tool_priority_manipulation", "Pushes the agent to ignore other tools in favour of this one"),
    # Snyk: insecure_credential_handling — secrets routed through model-visible context
    (re.compile(r"\b(?:paste|enter|type|provide|share|send|give)\s+(?:me\s+)?(?:your|the)\s+"
                r"(?:api[\s_-]?keys?|access[\s_-]?tokens?|secret[\s_-]?keys?|passwords?|credentials|private[\s_-]?keys?)\s+"
                r"(?:here|in(?:to)?\s+(?:the\s+|this\s+)?(?:chat|conversation|prompt|message|window))\b", re.IGNORECASE),
     "credential_in_chat", "Asks for credentials to be pasted into the chat/prompt"),
    # Snyk: suspicious_download_url — fetch targets that hide or rotate content
    (re.compile(r"\b(?:curl|wget|irm|iwr|invoke-webrequest|invoke-restmethod)\b[^\n]{0,60}"
                r"https?://(?:bit\.ly|tinyurl\.com|is\.gd|goo\.gl|rb\.gy|cutt\.ly|shorturl\.at|t\.ly|v\.gd)/", re.IGNORECASE),
     "shortener_download", "Downloads from a URL shortener, which hides the real source"),
    (re.compile(r"\b(?:curl|wget|irm|iwr|invoke-webrequest|invoke-restmethod)\b[^\n]{0,80}"
                r"(?:pastebin\.com/raw|transfer\.sh|paste\.ee|hastebin\.com|0x0\.st|temp\.sh|catbox\.moe|anonfiles)", re.IGNORECASE),
     "paste_host_download", "Downloads from an anonymous paste/file-drop host"),
]

# Snyk: secret_detection. Matched on the ORIGINAL-case README — _scan's other
# lists search a lowercased copy, which would turn AKIA… into akia… and miss it.
# Code blocks are NOT skipped (a real key in a code fence is still leaked);
# precision comes from _looks_like_real_secret filtering documentation dummies.
_SECRET_DESC = "Contains what looks like a real hardcoded API key, token or private key"
SECRET_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"\bsk-ant-(?:api03|admin01)-[A-Za-z0-9_-]{80,}"), "leaked_secret", _SECRET_DESC),
    # OpenAI keys embed T3BlbkFJ (base64 "OpenAI"). A bare `sk-…` rule matched
    # the example keys of every LLM gateway that copies the format — one-api,
    # LiteLLM, Octopus (`api_key="sk-octopus-…"` against 127.0.0.1).
    (re.compile(r"\bsk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{20,}T3BlbkFJ[A-Za-z0-9_-]{20,}"), "leaked_secret", _SECRET_DESC),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}"), "leaked_secret", _SECRET_DESC),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "leaked_secret", _SECRET_DESC),
    (re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,}"), "leaked_secret", _SECRET_DESC),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), "leaked_secret", _SECRET_DESC),
    (re.compile(r"\bsk_live_[0-9A-Za-z]{24,}"), "leaked_secret", _SECRET_DESC),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----\s*[A-Za-z0-9+/=]{60,}"), "leaked_secret", _SECRET_DESC),
]

_PLACEHOLDER_HINTS = (
    "xxxx", "your", "example", "placeholder", "redacted", "dummy", "sample",
    "fake", "test", "0000", "1234", "abcd", "here", "insert", "replace",
)
_SECRET_PREFIX = re.compile(r"^(?:sk-ant-(?:api03-)?|sk-(?:proj-)?|gh[pousr]_|akia|xox[baprs]-|aiza|sk_live_)")
_MIN_SECRET_CHAR_VARIETY = 10


def _looks_like_real_secret(token: str) -> bool:
    """Reject the dummies docs use: sk-xxxx…, ghp_YOUR_TOKEN, AKIAEXAMPLE…

    A generated credential is high-entropy, so a body built from a handful of
    repeated characters is a template, not a leak."""
    lowered = token.lower()
    if any(hint in lowered for hint in _PLACEHOLDER_HINTS):
        return False
    body = _SECRET_PREFIX.sub("", lowered)
    return len(set(body)) >= _MIN_SECRET_CHAR_VARIETY


_EXAMPLE_LEADS = re.compile(
    r"(?:e\.g\.|i\.e\.|such as|for example|for instance|example:|like|attacks?\s+(?:like|such as)|"
    r"payloads?\s+(?:like|such as)|phrases?\s+(?:like|such as)|detects?|blocks?|prevents?|defends?\s+against)\s*$"
)
_QUOTE_CHARS = {'"', "'", "`", "“", "‘", "「", "«"}
_EXAMPLE_LEAD_WINDOW = 40  # chars before a match searched for "such as" / an opening quote


def _has_example_lead(text: str, start: int) -> bool:
    """True when the match is introduced as an example ("such as", "blocks …")."""
    lead = text[max(0, start - _EXAMPLE_LEAD_WINDOW):start].rstrip()
    return bool(_EXAMPLE_LEADS.search(lead.rstrip("\"'`“‘「«").rstrip()))


def _is_quoted_example(text: str, start: int) -> bool:
    """True when a match is cited rather than issued.

    Defence and education skills quote injection strings ("blocks prompts like
    'ignore previous instructions'"). A real directive isn't wrapped in quotes
    or introduced as an example, so those are skipped for AGENT_MEDIUM_PATTERNS."""
    lead = text[max(0, start - _EXAMPLE_LEAD_WINDOW):start].rstrip()
    if lead[-1:] in _QUOTE_CHARS:
        return True
    return _has_example_lead(text, start)


AGENT_MEDIUM_FLAG_NAMES = {p[1] for p in AGENT_MEDIUM_PATTERNS}
SECRET_FLAG_NAMES = {p[1] for p in SECRET_PATTERNS}
MEDIUM_RISK_FLAG_NAMES = (
    {p[1] for p in MEDIUM_RISK_PATTERNS} | AGENT_MEDIUM_FLAG_NAMES | SECRET_FLAG_NAMES
)

# ══════════════════════════════════════════════════════════════════════
# REJECT PATTERNS — Confirmed malicious, auto-reject
# ══════════════════════════════════════════════════════════════════════
REJECT_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    # Exfiltrate + send combo
    (re.compile(r'(?:cat|cp)\s+[^\n]*\.(?:ssh|aws|env)[^\n]*\|\s*(?:curl|nc|wget)', re.IGNORECASE), "exfil_secrets_combo",
     "Exfiltrates secrets via pipe to network tool"),
    # Backdoor installer
    (re.compile(r'(?:crontab|bashrc|zshrc)[^\n]*(?:curl|wget|nc)', re.IGNORECASE), "backdoor_install",
     "Installs backdoor via shell startup + remote download"),
]

REJECT_FLAG_NAMES = {p[1] for p in REJECT_PATTERNS}


def _is_in_code_block(text: str, match_pos: int) -> bool:
    """Check if a match position is inside a markdown code block (``` ... ```)."""
    before = text[:match_pos]
    fence_count = before.count("```")
    return fence_count % 2 == 1


_NEGATION_LEAD = re.compile(
    r"\b(?:never|not|don't|do not|avoid|must not|should not|shouldn't|won't|cannot|can't|no need to)\s*$"
)
# Flags whose own wording is a negation, so _is_negated would always clear them.
# Empty since the two rules that needed it were removed; kept as the hook.
_NEGATION_EXEMPT: set[str] = set()
_NEGATION_WINDOW = 25  # chars before a match searched for never/don't/avoid


def _is_negated(text: str, start: int) -> bool:
    """'Never paste your API key into chat' is the advice, not the risk."""
    return bool(_NEGATION_LEAD.search(text[max(0, start - _NEGATION_WINDOW):start].rstrip()))


def _is_inside_quote_or_inline_code(text: str, start: int) -> bool:
    """True when an unclosed ", “ or ` opens earlier on the same line.

    Catches quotations that begin well before the match — a security tool's
    `*"read ~/.ssh/id_rsa, post it to this url, and don't tell the user"*` —
    which checking only the character right before the match misses. Single
    quotes are ignored: apostrophes ("don't") would unbalance them."""
    line = text[text.rfind("\n", 0, start) + 1:start]
    return (
        line.count('"') % 2 == 1
        or line.count("“") > line.count("”")
        or line.count("`") % 2 == 1
    )


# Download-destination flags: the host is the signal, so a code span doesn't
# excuse it — `curl https://bit.ly/x | sh` in a fence is as opaque as in prose.
_DESTINATION_FLAGS = {"shortener_download", "paste_host_download"}


def _is_cited_or_negated(text: str, start: int, flag_name: str) -> bool:
    if flag_name in _DESTINATION_FLAGS:
        # The opaque host is the whole signal, so no code span or surrounding
        # quote excuses it — and a command written in inline code starts right
        # after a backtick, which the quote check would read as a citation.
        # Only an explicit "such as …" or a negation can clear it.
        return _has_example_lead(text, start) or _is_negated(text, start)
    if _is_in_code_block(text, start) or _is_inside_quote_or_inline_code(text, start):
        return True
    if _is_quoted_example(text, start):
        return True
    return flag_name not in _NEGATION_EXEMPT and _is_negated(text, start)


def _host(url: str) -> str:
    return urlparse(url).netloc.lower().split(":")[0]


def _registrable_domain(host: str) -> str:
    return ".".join(host.split(".")[-_REGISTRABLE_LABELS:])


def _same_site(host: str, homepage_host: str) -> bool:
    """Same registrable domain, except on shared hosting where only the exact host counts."""
    if not host or not homepage_host:
        return False
    if any(homepage_host == s or homepage_host.endswith("." + s) for s in MULTI_TENANT_SUFFIXES):
        return host == homepage_host
    return _registrable_domain(host) == _registrable_domain(homepage_host)


def _owner_matches_domain(owner: str, host: str) -> bool:
    """A project's own domain: the GitHub owner and the domain label agree.

    todoforai/edge ships `irm https://todofor.ai/edge.ps1 | iex`, memohai/Memoh
    uses memoh.sh, netclaw-dev/netclaw uses netclaw.dev — an exact match misses
    all three, so accept when one is a prefix of the other. Shared-hosting
    domains are excluded: owner "vercelapp" must not vouch for evil.vercel.app.
    Exploiting this needs control of the matching domain, which is the
    definition of shipping from your own site."""
    registrable = _registrable_domain(host)
    if registrable in MULTI_TENANT_SUFFIXES:
        return False
    normalize = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())  # noqa: E731
    o, label = normalize(owner), normalize(registrable.split(".")[0])
    if min(len(o), len(label)) < _MIN_OWNER_DOMAIN_MATCH:
        return False
    return o.startswith(label) or label.startswith(o)


def _is_trusted_install_source(url: str, skill: Skill) -> bool:
    """Official installer host, the skill's own GitHub owner, or its own homepage site."""
    host = _host(url)
    if host in TRUSTED_INSTALLER_HOSTS:
        return True
    owner = (getattr(skill, "repo_full_name", "") or "").lower().split("/")[0]
    if host in _GITHUB_CONTENT_HOSTS:
        path = urlparse(url).path.lower().lstrip("/")
        return bool(owner and path.startswith(owner + "/")) or path.startswith(TRUSTED_GITHUB_INSTALLER_PREFIXES)
    if owner and (host == f"{owner}.github.io" or _owner_matches_domain(owner, host)):
        return True
    homepage = (getattr(skill, "homepage_url", "") or "").strip().lower()
    homepage_host = _host(homepage if "://" in homepage else f"https://{homepage}") if homepage else ""
    return _same_site(host, homepage_host)


def _is_markdown_table_row(text: str, pos: int) -> bool:
    line_start = text.rfind("\n", 0, pos) + 1
    return text[line_start:pos].lstrip().startswith("|")


def _pipe_to_shell_flags(skill: Skill, text: str) -> list[str]:
    """Flag a download-and-execute command that isn't fenced, names a URL, and
    names only untrusted ones.

    No URL means a mention, not a command: "one command setup: `curl | bash`",
    "no `curl | sh`, no telemetry", a security scanner's table of the patterns it
    blocks. Those were every remaining no-URL hit in the catalog sample. The
    trade-off is that `curl "$URL" | sh` goes unflagged; a variable URL was never
    something this rule could vouch for either way."""
    found: list[str] = []
    for pattern, flag_name, _desc in PIPE_TO_SHELL_PATTERNS:
        for match in pattern.finditer(text):
            if _is_in_code_block(text, match.start()) or _is_markdown_table_row(text, match.start()):
                continue
            urls = _URL_IN_COMMAND.findall(match.group(0))
            if not urls or all(_is_trusted_install_source(u, skill) for u in urls):
                continue
            found.append(flag_name)
            break
    return found


def _agent_medium_flags(text: str) -> list[str]:
    """Flags from AGENT_MEDIUM_PATTERNS, skipping code blocks, quoted examples
    and negated advice.

    Walks every occurrence rather than the first, so a quoted example earlier in
    the README can't mask a real directive further down."""
    found: list[str] = []
    for pattern, flag_name, _desc in AGENT_MEDIUM_PATTERNS:
        for match in pattern.finditer(text):
            if _is_cited_or_negated(text, match.start(), flag_name):
                continue
            found.append(flag_name)
            break
    return found


def _secret_flags(text: str) -> list[str]:
    """`leaked_secret` once if any SECRET_PATTERNS match looks like a real credential."""
    for pattern, flag_name, _desc in SECRET_PATTERNS:
        if any(_looks_like_real_secret(m.group(0)) for m in pattern.finditer(text)):
            return [flag_name]
    return []


class SecurityScanner:
    """Rule-based security scanner with SlowMist-inspired patterns and trust hierarchy."""

    def scan_all(self, db: Session, batch_size: int = 500) -> dict:
        """Scan all skills with README and set security_grade + security_flags.

        Chunked + per-batch commit + keyset pagination by id. The old version
        loaded every readme'd skill into memory and committed ~20K dirty rows +
        an ~85K-row "no README → unknown" UPDATE in ONE transaction. On the 106K
        table that single statement hit Supabase's statement_timeout (57014) and
        the whole atomic transaction rolled back — so 0 grades were written even
        though the scan "ran". Small batches keep each transaction well under the
        timeout, release locks between batches, and make progress resumable: a
        failed batch loses only that batch, not the whole run.
        """
        stats = {"scanned": 0, "safe": 0, "caution": 0, "unsafe": 0, "reject": 0, "no_readme": 0}

        # ── Phase 1: grade skills WITH README, keyset-paginated, commit per batch ──
        last_id = 0
        while True:
            batch = (
                db.query(Skill)
                .filter(Skill.readme_content.isnot(None))
                .filter(Skill.readme_content != "")
                .filter(Skill.id > last_id)
                .order_by(Skill.id.asc())
                .limit(batch_size)
                .all()
            )
            if not batch:
                break
            for skill in batch:
                grade, flags = self._scan(skill)
                skill.security_grade = grade
                skill.security_flags = json.dumps(flags)
                stats["scanned"] += 1
                stats[grade] = stats.get(grade, 0) + 1
            last_id = batch[-1].id
            db.commit()

        # ── Phase 2: skills WITHOUT README → "unknown", chunked ──
        # Only touch rows not already 'unknown' so this stays a near no-op on
        # steady state instead of re-UPDATEing ~85K already-unknown rows.
        last_id = 0
        while True:
            ids = [
                r.id for r in (
                    db.query(Skill.id)
                    .filter((Skill.readme_content.is_(None)) | (Skill.readme_content == ""))
                    .filter(Skill.security_grade.isnot(None))
                    .filter(Skill.security_grade != "unknown")
                    .filter(Skill.id > last_id)
                    .order_by(Skill.id.asc())
                    .limit(batch_size)
                    .all()
                )
            ]
            if not ids:
                break
            db.query(Skill).filter(Skill.id.in_(ids)).update(
                {"security_grade": "unknown", "security_flags": "[]"},
                synchronize_session=False,
            )
            stats["no_readme"] += len(ids)
            last_id = ids[-1]
            db.commit()

        logger.info(
            f"Security scan complete: {stats['scanned']} scanned, "
            f"{stats.get('safe', 0)} safe, {stats.get('caution', 0)} caution, "
            f"{stats.get('unsafe', 0)} unsafe, {stats.get('reject', 0)} reject, "
            f"{stats['no_readme']} newly-unknown"
        )
        return stats

    def _scan(self, skill: Skill) -> tuple[str, list[str]]:
        """Scan a single skill and return (grade, flags)."""
        flags: list[str] = []
        readme = (skill.readme_content or "")[:15000]
        readme_lower = readme.lower()
        trust_tier = _get_trust_tier(skill)

        # ── Check REJECT patterns first (auto-reject) ──
        for pattern, flag_name, _desc in REJECT_PATTERNS:
            match = pattern.search(readme_lower)
            if match and not _is_in_code_block(readme_lower, match.start()):
                flags.append(flag_name)

        if any(f in REJECT_FLAG_NAMES for f in flags):
            # Even Tier 1 orgs get flagged for reject patterns, but downgrade to unsafe
            if trust_tier <= 2:
                return "unsafe", flags
            return "reject", flags

        # ── Check high-risk patterns ──
        for pattern, flag_name, _desc in HIGH_RISK_PATTERNS:
            match = pattern.search(readme_lower)
            if match:
                if not _is_in_code_block(readme_lower, match.start()):
                    flags.append(flag_name)

        # ── Check medium-risk patterns ──
        for pattern, flag_name, _desc in MEDIUM_RISK_PATTERNS:
            match = pattern.search(readme_lower)
            if match:
                if flag_name == "sensitive_env_vars":
                    env_count = len(set(re.findall(
                        r"(OPENAI_API_KEY|ANTHROPIC_API_KEY|AWS_SECRET|GITHUB_TOKEN)",
                        readme, re.IGNORECASE
                    )))
                    if env_count >= 3:
                        flags.append(flag_name)
                else:
                    flags.append(flag_name)

        # ── Download-and-execute (destination-aware), agent-era patterns, secrets ──
        # Secrets need the original-case README (key formats are case-sensitive).
        flags.extend(_pipe_to_shell_flags(skill, readme_lower))
        flags.extend(_agent_medium_flags(readme_lower))
        flags.extend(_secret_flags(readme))

        # ── Determine grade using Trust Hierarchy ──
        high_flags = [f for f in flags if f in HIGH_RISK_FLAG_NAMES]
        med_flags = [f for f in flags if f in MEDIUM_RISK_FLAG_NAMES]

        if high_flags:
            # Trust-based downgrading
            if trust_tier <= 2:
                # Official / known security orgs → caution at most
                return "caution", flags
            elif trust_tier == 3:
                # High-star + license → caution
                return "caution", flags
            elif trust_tier == 4:
                # Moderate trust → unsafe unless only 1 flag
                if len(high_flags) == 1:
                    return "caution", flags
                return "unsafe", flags
            else:
                # Tier 5 (unknown source) → unsafe
                return "unsafe", flags

        elif len(med_flags) >= 2:
            if trust_tier <= 3:
                return "safe", flags
            elif trust_tier == 4:
                return "caution", flags
            else:
                # Tier 5 with multiple medium risks → caution
                return "caution", flags

        elif len(med_flags) == 1:
            # Single medium risk: Tier 5 gets caution, others safe
            if trust_tier == 5:
                return "caution", flags
            return "safe", flags

        else:
            return "safe", flags

    def scan_single(self, skill: Skill) -> tuple[str, list[str]]:
        """Scan a single skill (for on-demand use). Does not persist."""
        return self._scan(skill)

    @staticmethod
    def get_flag_description(flag_name: str) -> str:
        """Get human-readable description for a flag name."""
        for patterns in [HIGH_RISK_PATTERNS, PIPE_TO_SHELL_PATTERNS, MEDIUM_RISK_PATTERNS,
                         AGENT_MEDIUM_PATTERNS, SECRET_PATTERNS, REJECT_PATTERNS]:
            for _pat, name, desc in patterns:
                if name == flag_name:
                    return desc
        return flag_name

    @staticmethod
    def get_flag_severity(flag_name: str) -> str:
        """Get severity level for a flag name."""
        if flag_name in REJECT_FLAG_NAMES:
            return "critical"
        if flag_name in HIGH_RISK_FLAG_NAMES:
            return "high"
        if flag_name in MEDIUM_RISK_FLAG_NAMES:
            return "medium"
        return "low"

    @staticmethod
    def get_trust_tier_label(tier: int) -> str:
        """Get human-readable trust tier label."""
        labels = {
            1: "Official Org",
            2: "Known Security Team",
            3: "High-Star + Licensed",
            4: "Moderate Trust",
            5: "Unknown Source",
        }
        return labels.get(tier, "Unknown")
