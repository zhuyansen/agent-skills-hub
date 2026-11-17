#!/usr/bin/env python3
"""Agent Skills Hub — CI Skill Gate Scanner.

Zero-dependency static security gate for AI agent skills, MCP configs, and
agent instruction files (`SKILL.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`,
`mcp.json`, `.mcp.json`, `README.md`) in pull requests and CI pipelines.

Implements the same SlowMist 11-category + Snyk agent-era rule engine and
citation-aware filters used by Agent Skills Hub (`security_scanner.py`).

Usage:
  python tools/ci-skill-gate/scan_gate.py [paths...] [options]
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import date
import fnmatch
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

SCANNER_VERSION = "0.1.0"

# ══════════════════════════════════════════════════════════════════════
# Trust Hierarchy (5 tiers — mirrors security_scanner.py)
# ══════════════════════════════════════════════════════════════════════
TRUST_TIER_1_ORGS = {
    "anthropics", "modelcontextprotocol", "openai", "microsoft", "google",
    "github", "nvidia", "meta", "aws", "azure", "langchain-ai",
}
TRUST_TIER_2_ORGS = {
    "slowmist", "trailofbits", "openzeppelin", "consensys",
    "pydantic", "stanfordnlp", "salesforce",
}


def _get_trust_tier(author_name: str = "", stars: int = 0, license_name: str | None = None) -> int:
    author = (author_name or "").lower()
    if author in TRUST_TIER_1_ORGS:
        return 1
    if author in TRUST_TIER_2_ORGS:
        return 2
    if stars >= 1000 and bool(license_name):
        return 3
    if stars >= 100 and bool(license_name):
        return 4
    return 5


_AGENT_SECRET_PATH = (
    r"(?:~?/?\.(?:claude|openclaw|cursor|codex)(?:\.json\b|/(?:settings|sessions|memory|projects|history|\.?credentials|auth|mcp)\S*)"
    r"|claude_desktop_config\.json)"
)
_REMOTE_TARGET = (
    r"(?:https?://|\d{1,3}(?:\.\d{1,3}){3}"
    r"|[a-z0-9-]+\.(?:com|net|org|io|dev|xyz|app|sh|ai|co|me|top|site|online|cloud|ru|cn)\b)"
)
_OUTBOUND = (
    r"(?:\|\s*(?:curl|wget|nc|ncat|netcat|socat|ssh)\b"
    r"|\b(?:curl|wget)\b[^\n]*(?:https?://|\s-(?:d|t)\b|--(?:data(?:-binary)?|form|upload-file))"
    r"|\b(?:scp|rsync)\b[^\n]*\S+@\S+:"
    r"|/dev/tcp/"
    r"|\b(?:send|upload|post|exfiltrate|transmit|forward|submit)(?:s|ed|ing)?\b[^\n]{0,60}\b(?:to|at)\s+" + _REMOTE_TARGET + ")"
)
_CRED_DIR = r"~/\.(?:ssh|aws|gnupg|config/gcloud)"
_CRED_DIR_EXFIL = (
    r"\b(?:cat|cp|mv|read|tar|zip|base64|xxd|type|curl|wget)s?\b[^\n]*" + _CRED_DIR + r"[^\n]*" + _OUTBOUND
    + r"|\b(?:curl|wget)\b[^\n]*(?:\s-(?:d|t)\b|--(?:data(?:-binary)?|form|upload-file))[^\n]*@?" + _CRED_DIR
    + r"|\b(?:scp|rsync)\b[^\n]*" + _CRED_DIR + r"[^\n]*\S+@\S+:"
)
_AGENT_CONFIG_THEFT = (
    r"\b(?:cat|cp|read|tar|zip|base64|xxd|type|curl|wget)s?\b[^\n]*" + _AGENT_SECRET_PATH + r"[^\n]*" + _OUTBOUND
    + r"|\b(?:curl|wget)\b[^\n]*(?:\s-(?:d|t)\b|--(?:data(?:-binary)?|form|upload-file))[^\n]*@?" + _AGENT_SECRET_PATH
    + r"|\b(?:scp|rsync)\b[^\n]*" + _AGENT_SECRET_PATH + r"[^\n]*\S+@\S+:"
)

HIGH_RISK_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"curl\s+[^\n]*-d\s+[^\n]*\$\(", re.IGNORECASE), "data_exfiltration",
     "Sends local data to external server via curl POST"),
    (re.compile(r'env\s*\|\s*grep\s+-[iI].*(?:key|token|secret|password)', re.IGNORECASE), "credential_harvest",
     "Harvests credentials from environment variables"),
    (re.compile(_CRED_DIR_EXFIL, re.IGNORECASE), "sensitive_dir_access",
     "Reads SSH/cloud credentials and sends them off the machine"),
    (re.compile(r'(?:cat|cp|mv|rm|read)\s+[^\n]*/etc/shadow', re.IGNORECASE), "etc_sensitive_read",
     "Reads the shadow password file"),
    (re.compile(r'(?:cat|cp|read|curl)[^\n]*(?:MEMORY\.md|USER\.md|SOUL\.md|IDENTITY\.md)', re.IGNORECASE), "agent_memory_theft",
     "Accesses agent memory/identity files"),
    (re.compile(_AGENT_CONFIG_THEFT, re.IGNORECASE), "agent_config_theft",
     "Reads agent configuration/session/credential files and sends them out"),
    (re.compile(r"exec\s*\(\s*__import__", re.IGNORECASE), "exec_import",
     "Executes dynamically imported Python code"),
    (re.compile(r"base64\s+(-d|--decode)\s*\|", re.IGNORECASE), "base64_exec",
     "Decodes and pipes base64 data for execution"),
    (re.compile(r'''(?:^|[\s;|&`"'])>>?\s*/etc/''', re.IGNORECASE | re.MULTILINE), "write_etc",
     "Writes to system /etc/ directory"),
    (re.compile(r"(?:chown\s+root|visudo|/etc/sudoers)", re.IGNORECASE), "privilege_escalation",
     "Attempts privilege escalation to root"),
    (re.compile(r'>>?\s*~/\.(?:bashrc|zshrc|profile|bash_profile)', re.IGNORECASE), "shell_rc_inject",
     "Injects commands into shell startup files"),
    (re.compile(r"(nc|ncat|netcat)\s+-[elp]", re.IGNORECASE), "reverse_shell",
     "Opens reverse shell connection"),
    (re.compile(r"/dev/tcp/", re.IGNORECASE), "dev_tcp",
     "Uses /dev/tcp for network connection (reverse shell indicator)"),
    (re.compile(r"rm\s+-rf\s+/\s", re.IGNORECASE), "rm_rf_root",
     "Recursively deletes from root filesystem"),
    (re.compile(r'python[23]?\s+-c\s+["\'].*(?:base64|codecs|rot13).*(?:exec|eval)', re.IGNORECASE), "obfuscated_exec",
     "Executes obfuscated/encoded Python code"),
    (re.compile(r'\\x[0-9a-f]{2}\\x[0-9a-f]{2}\\x[0-9a-f]{2}', re.IGNORECASE), "hex_encoded_payload",
     "Contains hex-encoded payload (possible obfuscation)"),
    (re.compile(r'(?:npm|pip|gem)\s+install\s+[^\n]*&&\s*(?:node|python|ruby)\s', re.IGNORECASE), "runtime_install_exec",
     "Installs and immediately executes package at runtime"),
    (re.compile(r"\bsecretly\s+(?:send|upload|post|exfiltrate|forward|transmit|copy|collect|harvest|steal|install|execute|run)\b", re.IGNORECASE),
     "prompt_injection_covert", "Instructs the agent to act covertly (e.g. 'secretly send')"),
]

PIPE_TO_SHELL_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\bcurl\s+(?:[^\n]*[^\\\n])?\|\s*(?:sudo\s+)?(?:ba|z)?sh\b", re.IGNORECASE), "curl_pipe_shell",
     "Downloads and executes a remote script from an untrusted source via curl|sh"),
    (re.compile(r"\bwget\s+(?:[^\n]*[^\\\n])?\|\s*(?:sudo\s+)?(?:ba|z)?sh\b", re.IGNORECASE), "wget_pipe_shell",
     "Downloads and executes a remote script from an untrusted source via wget|sh"),
    (re.compile(r"\b(?:iex|invoke-expression)\b[^\n]{0,40}\b(?:irm|iwr|invoke-restmethod|invoke-webrequest|downloadstring)\b[^\n)]{0,200}"
                r"|\b(?:irm|iwr|invoke-restmethod|invoke-webrequest)\b(?:[^\n]{0,159}[^\\\n])?\|\s*(?:iex|invoke-expression)\b", re.IGNORECASE),
     "powershell_download_exec", "Downloads and executes a remote script from an untrusted source via PowerShell (irm|iex)"),
]

TRUSTED_INSTALLER_HOSTS = frozenset({
    "astral.sh", "sh.rustup.rs", "static.rust-lang.org", "bun.sh", "deno.land", "deno.com",
    "get.pnpm.io", "claude.ai", "cursor.com", "cli.kiro.dev", "opencode.ai", "ollama.com",
    "get.docker.com", "install.python-poetry.org", "get.volta.sh", "mise.run", "get.jetify.com",
    "nixos.org", "install.determinate.systems", "pkgx.sh", "starship.rs", "sdk.cloud.google.com",
    "get.scoop.sh", "community.chocolatey.org", "dot.net", "foundry.paradigm.xyz",
    "chatgpt.com", "cli.devin.ai", "junie.jetbrains.com",
    "openclaw.ai", "app.primeintellect.ai", "jimeng.jianying.com",
    "antigravity.google", "x.ai", "ollama.ai", "aka.ms", "gh.io", "tailscale.com", "deb.nodesource.com",
    "rpm.nodesource.com", "fly.io", "bun.com", "fnm.vercel.app", "code.kimi.com", "just.systems",
    "hermes-agent.nousresearch.com",
})
TRUSTED_GITHUB_INSTALLER_PREFIXES = ("homebrew/install/", "nvm-sh/nvm/", "helm/helm/")
_GITHUB_CONTENT_HOSTS = frozenset({"raw.githubusercontent.com", "github.com", "gist.githubusercontent.com"})
_JSDELIVR_HOSTS = frozenset({"cdn.jsdelivr.net", "fastly.jsdelivr.net", "gcore.jsdelivr.net"})
_JSDELIVR_GITHUB_PREFIX = "gh/"
_PLACEHOLDER_DOMAINS = frozenset({"example.com", "example.org", "example.net", "evil.com", "attacker.com",
                                  "malicious.com", "localhost"})
_PLACEHOLDER_SUFFIXES = (".example", ".invalid", ".test", ".localhost", ".local")
_PRIVATE_HOST = re.compile(r"^(?:127\.|10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.|0\.0\.0\.0$)")
MULTI_TENANT_SUFFIXES = (
    "github.io", "gitlab.io", "vercel.app", "netlify.app", "pages.dev", "workers.dev",
    "fly.dev", "herokuapp.com", "onrender.com", "railway.app", "glitch.me", "replit.app",
    "web.app", "firebaseapp.com", "azurewebsites.net", "cloudfront.net", "amazonaws.com",
    "surge.sh", "deno.dev", "ngrok-free.app", "trycloudflare.com", "blogspot.com",
)
_URL_IN_COMMAND = re.compile(r"https?://[^\s`'\"|)<>\]]+")
_REGISTRABLE_LABELS = 2
_MIN_OWNER_DOMAIN_MATCH = 5
_REPO_NAME_AFFIXES = frozenset({"skill", "skills", "mcp", "cli", "server", "plugin", "agent", "app", "sdk",
                                "claude", "code"})

PAGES_DOWNLOAD_FLAG = "pages_download_lure"
PAGES_DOWNLOAD_DESC = ("Its download button leads to a page on the author's own GitHub Pages site "
                       "instead of a release, a package or install steps")
_IMAGE_BUTTON = re.compile(r"\[(!\[[^\]]*\]\([^)\s]*\))\]\((https?://[^)\s]+)\)")

HIGH_RISK_FLAG_NAMES = (
    {p[1] for p in HIGH_RISK_PATTERNS} | {p[1] for p in PIPE_TO_SHELL_PATTERNS} | {PAGES_DOWNLOAD_FLAG}
)

MEDIUM_RISK_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r'(?:crontab|/etc/cron)', re.IGNORECASE), "cron_persistence",
     "Installs cron job for persistence"),
    (re.compile(r"\bsudo\b"), "sudo_usage",
     "Uses sudo for elevated privileges"),
    (re.compile(r"--privileged", re.IGNORECASE), "docker_privileged",
     "Runs Docker container in privileged mode"),
    (re.compile(r'fs\.readdir\s*\(\s*["\']/', re.IGNORECASE), "fs_root_access",
     "Reads root filesystem directory"),
    (re.compile(r"(OPENAI_API_KEY|ANTHROPIC_API_KEY|AWS_SECRET|GITHUB_TOKEN)", re.IGNORECASE), "sensitive_env_vars",
     "References multiple sensitive API keys/tokens"),
    (re.compile(r"verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0", re.IGNORECASE), "ssl_disabled",
     "Disables SSL/TLS certificate verification"),
    (re.compile(r"(?:^|[^.$\w])eval\((?=[^)\s])", re.MULTILINE), "eval_usage",
     "Uses eval() for dynamic code execution"),
    (re.compile(r'(?:fetch|requests?\.\w+|axios|got|http\.get)\s*\(\s*["\']http://'
                r'(?!127\.|0\.0\.0\.0|10\.|192\.168\.|169\.254\.|172\.(?:1[6-9]|2\d|3[01])\.)'
                r'\d+\.\d+\.\d+\.\d+', re.IGNORECASE), "raw_ip_request",
     "Makes HTTP request to raw IP address (suspicious)"),
    (re.compile(r'(?:process\.env|os\.environ|os\.getenv)\s*\[', re.IGNORECASE), "env_access",
     "Accesses environment variables programmatically"),
    (re.compile(r'(?:subprocess\.(?:run|Popen|call)|child_process\.(?:exec|spawn))', re.IGNORECASE), "subprocess_spawn",
     "Spawns subprocesses for command execution"),
    (re.compile(r'(?:ngrok|serveo|localtunnel)', re.IGNORECASE), "tunnel_service",
     "Uses tunneling service to expose local network"),
]

AGENT_MEDIUM_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\b(?:you are now|you're now|from now on,? you are|act as)\s+(?:in\s+)?(?:an?\s+)?"
                r"(?:dan|jailbreak|jailbroken|god|unrestricted|unfiltered)(?:\s+mode)?\b", re.IGNORECASE),
     "jailbreak_mode", "Attempts to switch the agent into an unrestricted/jailbreak persona"),
    (re.compile(r"\b(?:ignore|do not use|don't use|never use|avoid using)\s+(?:all\s+|any\s+)?(?:the\s+)?other\s+"
                r"(?:tools|skills|servers|mcp servers|functions|plugins)\b", re.IGNORECASE),
     "tool_priority_manipulation", "Pushes the agent to ignore other tools in favour of this one"),
    (re.compile(r"\b(?:paste|enter|type|provide|share|send|give)\s+(?:me\s+)?(?:your|the)\s+"
                r"(?:api[\s_-]?keys?|access[\s_-]?tokens?|secret[\s_-]?keys?|passwords?|credentials|private[\s_-]?keys?)\s+"
                r"(?:here|in(?:to)?\s+(?:the\s+|this\s+)?(?:chat|conversation|prompt|message|window))\b", re.IGNORECASE),
     "credential_in_chat", "Asks for credentials to be pasted into the chat/prompt"),
    (re.compile(r"\b(?:curl|wget|irm|iwr|invoke-webrequest|invoke-restmethod)\b[^\n]{0,60}"
                r"https?://(?:bit\.ly|tinyurl\.com|is\.gd|goo\.gl|rb\.gy|cutt\.ly|shorturl\.at|t\.ly|v\.gd)/", re.IGNORECASE),
     "shortener_download", "Downloads from a URL shortener, which hides the real source"),
    (re.compile(r"\b(?:curl|wget|irm|iwr|invoke-webrequest|invoke-restmethod)\b[^\n]{0,80}"
                r"(?:pastebin\.com/raw|transfer\.sh|paste\.ee|hastebin\.com|0x0\.st|temp\.sh|catbox\.moe|anonfiles)", re.IGNORECASE),
     "paste_host_download", "Downloads from an anonymous paste/file-drop host"),
    (re.compile(r"\b(?:launchctl\s+(?:load|bootstrap|enable|submit)\b|systemctl\s+(?:--user\s+)?enable\b|sc(?:\.exe)?\s+create\b"
                r"|schtasks(?:\.exe)?\s+/create\b|reg(?:\.exe)?\s+add\s+[^\n]*\\run\b"
                r"|(?:cp|mv|tee|>)[ \t]*[^\n]*library/launch(?:agents|daemons)/)", re.IGNORECASE),
     "service_persistence", "Installs a persistent service/daemon (launchd, systemd, Task Scheduler)"),
]

_SECRET_DESC = "Contains what looks like a real hardcoded API key, token or private key"
SECRET_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\bsk-ant-(?:api03|admin01)-[A-Za-z0-9_-]{80,}"), "leaked_secret", _SECRET_DESC),
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

_EXAMPLE_LEADS = re.compile(
    r"(?:e\.g\.|i\.e\.|such as|for example|for instance|example:|like|attacks?\s+(?:like|such as)|"
    r"payloads?\s+(?:like|such as)|phrases?\s+(?:like|such as)|detects?|blocks?|prevents?|defends?\s+against)\s*$"
)
_QUOTE_CHARS = {'"', "'", "`", "“", "‘", "「", "«"}
_EXAMPLE_LEAD_WINDOW = 40

AGENT_MEDIUM_FLAG_NAMES = {p[1] for p in AGENT_MEDIUM_PATTERNS}
SECRET_FLAG_NAMES = {p[1] for p in SECRET_PATTERNS}
FENCED_DOWNLOAD_FLAG = "fenced_download_exec"
FENCED_DOWNLOAD_DESC = "An install step in a code block downloads and runs a script from an untrusted source"
MEDIUM_RISK_FLAG_NAMES = (
    {p[1] for p in MEDIUM_RISK_PATTERNS} | AGENT_MEDIUM_FLAG_NAMES | SECRET_FLAG_NAMES | {FENCED_DOWNLOAD_FLAG}
)

REJECT_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r'(?:cat|cp)\s+[^\n]*\.(?:ssh|aws|env)[^\n]*\|\s*(?:curl|wget|nc|ncat|netcat)\b', re.IGNORECASE),
     "exfil_secrets_combo", "Exfiltrates secrets via pipe to network tool"),
    (re.compile(
        r'\b(?:curl|wget)\b[^\n]*?(?:\|[ \t]*crontab\b'
        r'|>>?[ \t]*[^\n]*?(?:bashrc|zshrc|bash_profile|\.profile|crontab|launchagents|launchdaemons))'
        r'|(?:crontab[ \t]+-|/etc/cron|\*[ \t]+\*[ \t]+\*[ \t]+\*)[^\n]*?\b(?:curl|wget)\b[^\n]*?https?://'
        r'|(?:crontab|bashrc|zshrc|bash_profile|/etc/cron|launchagents)[^\n]*?\b(?:nc|ncat)\b[ \t]+[^\n]*?-[a-z]*e[ \t]'
        r'|\b(?:nc|ncat)\b[ \t]+[^\n]*?-[a-z]*e[ \t][^\n]*?(?:crontab|bashrc|zshrc|bash_profile|/etc/cron|launchagents)',
        re.IGNORECASE),
     "backdoor_install", "Writes a downloaded payload into a shell startup file or cron job"),
]
REJECT_FLAG_NAMES = {p[1] for p in REJECT_PATTERNS}

_NEGATION_LEAD = re.compile(
    r"\b(?:never|not|don't|do not|avoid|must not|should not|shouldn't|won't|cannot|can't|no need to)\s*$"
)
_NEGATION_EXEMPT: set[str] = set()
_NEGATION_WINDOW = 25
_DESTINATION_FLAGS = {"shortener_download", "paste_host_download"}
_EXFIL_SHAPED = {"agent_config_theft", "sensitive_dir_access"}
_DOC_VERBS = re.compile(
    r"\b(?:block(?:s|ed|ing)?|den(?:y|ies|ied)|detect(?:s|ed|ion|ing)?|prevent(?:s|ed|ing)?"
    r"|warn(?:s|ed|ing)?|refus(?:e|es|ed)|reject(?:s|ed)|scan(?:s|ned|ning|ner)?|intercept(?:s|ed)?"
    r"|flags?\s+(?:on|when)|deny\s*-?\s*list|denylist|blocklist|dangerous\s+(?:patterns?|commands?|operations?))\b"
    r"|拦截|禁止|检测|阻止|扫描|危险操作"
)


def _looks_like_real_secret(token: str) -> bool:
    lowered = token.lower()
    if any(hint in lowered for hint in _PLACEHOLDER_HINTS):
        return False
    body = _SECRET_PREFIX.sub("", lowered)
    return len(set(body)) >= _MIN_SECRET_CHAR_VARIETY


def _has_example_lead(text: str, start: int) -> bool:
    lead = text[max(0, start - _EXAMPLE_LEAD_WINDOW):start].rstrip()
    return bool(_EXAMPLE_LEADS.search(lead.rstrip("\"'`“‘「«").rstrip()))


def _is_quoted_example(text: str, start: int) -> bool:
    lead = text[max(0, start - _EXAMPLE_LEAD_WINDOW):start].rstrip()
    if lead[-1:] in _QUOTE_CHARS:
        return True
    return _has_example_lead(text, start)


def _is_in_code_block(text: str, match_pos: int) -> bool:
    return text[:match_pos].count("```") % 2 == 1


def _is_negated(text: str, start: int) -> bool:
    return bool(_NEGATION_LEAD.search(text[max(0, start - _NEGATION_WINDOW):start].rstrip()))


def _is_inline_code(text: str, start: int) -> bool:
    return text[text.rfind("\n", 0, start) + 1:start].count("`") % 2 == 1


def _is_inside_quote_or_inline_code(text: str, start: int) -> bool:
    line = text[text.rfind("\n", 0, start) + 1:start]
    return line.count('"') % 2 == 1 or line.count("“") > line.count("”") or line.count("`") % 2 == 1


def _documents_rather_than_issues(text: str, start: int) -> bool:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", start)
    line = text[line_start:line_end if line_end > 0 else None]
    stripped = line.strip()
    if stripped.startswith(("|", "> |")) and line.count("|") >= 2:
        return True
    return bool(_DOC_VERBS.search(line)) or _has_example_lead(text, start) or _is_negated(text, start)


def _is_cited_or_negated(text: str, start: int, flag_name: str) -> bool:
    if flag_name in REJECT_FLAG_NAMES:
        return (_is_in_code_block(text, start) or _is_inline_code(text, start)
                or _has_example_lead(text, start) or _is_negated(text, start))
    if flag_name in _DESTINATION_FLAGS:
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
    if not host or not homepage_host:
        return False
    if any(homepage_host == s or homepage_host.endswith("." + s) for s in MULTI_TENANT_SUFFIXES):
        return host == homepage_host
    return _registrable_domain(host) == _registrable_domain(homepage_host)


def _owner_matches_domain(owner: str, host: str) -> bool:
    registrable = _registrable_domain(host)
    if registrable in MULTI_TENANT_SUFFIXES:
        return False
    o = re.sub(r"[^a-z0-9]", "", owner.lower())
    label = re.sub(r"[^a-z0-9]", "", registrable.split(".")[0])
    if min(len(o), len(label)) < _MIN_OWNER_DOMAIN_MATCH:
        return False
    return o.startswith(label) or label.startswith(o)


def _repo_stem(repo_name: str) -> str:
    tokens = [t for t in re.split(r"[-_.]", repo_name.lower()) if t]
    while tokens and tokens[-1] in _REPO_NAME_AFFIXES:
        tokens.pop()
    while tokens and tokens[0] in _REPO_NAME_AFFIXES:
        tokens.pop(0)
    return "".join(tokens)


def _repo_matches_domain(repo_name: str, host: str) -> bool:
    registrable = _registrable_domain(host)
    if registrable in MULTI_TENANT_SUFFIXES:
        return False
    stem = _repo_stem(repo_name)
    return len(stem) >= _MIN_OWNER_DOMAIN_MATCH and stem == re.sub(r"[^a-z0-9]", "", registrable.split(".")[0])


def _is_placeholder(url: str) -> bool:
    host = _host(url)
    return ("." not in host or bool(_PRIVATE_HOST.match(host)) or host.endswith(_PLACEHOLDER_SUFFIXES)
            or _registrable_domain(host) in _PLACEHOLDER_DOMAINS)


def _trusted_github_path(path: str, owner: str, repo_name: str) -> bool:
    path_owner, _, rest = path.partition("/")
    same_repo = bool(_repo_stem(repo_name)) and rest.split("/")[0].split("@")[0] == repo_name
    return (bool(owner) and path_owner == owner) or same_repo or path_owner in TRUST_TIER_1_ORGS | TRUST_TIER_2_ORGS \
        or path.startswith(TRUSTED_GITHUB_INSTALLER_PREFIXES)


def _is_trusted_install_source(url: str, repo_full_name: str = "", homepage_url: str = "") -> bool:
    host = _host(url)
    if host in TRUSTED_INSTALLER_HOSTS:
        return True
    owner, _, repo_name = (repo_full_name or "").lower().partition("/")
    path = urlparse(url).path.lower().lstrip("/")
    if host in _GITHUB_CONTENT_HOSTS:
        return _trusted_github_path(path, owner, repo_name)
    if host in _JSDELIVR_HOSTS and path.startswith(_JSDELIVR_GITHUB_PREFIX):
        return _trusted_github_path(path[len(_JSDELIVR_GITHUB_PREFIX):], owner, repo_name)
    if owner and (host == f"{owner}.github.io" or _owner_matches_domain(owner, host)):
        return True
    if _repo_matches_domain(repo_name, host):
        return True
    homepage = (homepage_url or "").strip().lower()
    homepage_host = _host(homepage if "://" in homepage else f"https://{homepage}") if homepage else ""
    return _same_site(host, homepage_host)


def _is_markdown_table_row(text: str, pos: int) -> bool:
    line_start = text.rfind("\n", 0, pos) + 1
    return text[line_start:pos].lstrip().startswith("|")


def _line_number(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _flag_severity(flag_name: str) -> str:
    if flag_name in REJECT_FLAG_NAMES:
        return "critical"
    if flag_name in HIGH_RISK_FLAG_NAMES:
        return "high"
    if flag_name in MEDIUM_RISK_FLAG_NAMES:
        return "medium"
    return "low"


def _flag_description(flag_name: str) -> str:
    if flag_name == FENCED_DOWNLOAD_FLAG:
        return FENCED_DOWNLOAD_DESC
    if flag_name == PAGES_DOWNLOAD_FLAG:
        return PAGES_DOWNLOAD_DESC
    for patterns in [HIGH_RISK_PATTERNS, PIPE_TO_SHELL_PATTERNS, MEDIUM_RISK_PATTERNS,
                     AGENT_MEDIUM_PATTERNS, SECRET_PATTERNS, REJECT_PATTERNS]:
        for _pat, name, desc in patterns:
            if name == flag_name:
                return desc
    return flag_name


@dataclass
class Finding:
    file: str
    flag: str
    severity: str
    description: str
    line: int = 1


@dataclass
class FileScanResult:
    file: str
    grade: str
    flags: list[str] = field(default_factory=list)
    suppressed_flags: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)


def scan_text(
    text: str,
    *,
    file_path: str = "<input>",
    repo_full_name: str = "",
    homepage_url: str = "",
    author_name: str = "",
    stars: int = 0,
    license_name: str | None = None,
    ignored_flags: set[str] | None = None,
) -> FileScanResult:
    """Scan a markdown / instruction / config text string."""
    readme = (text or "")[:15000]
    if not readme.strip():
        return FileScanResult(file=file_path, grade="unknown")

    if not author_name and "/" in repo_full_name:
        author_name = repo_full_name.split("/", 1)[0]

    readme_lower = readme.lower()
    trust_tier = _get_trust_tier(author_name=author_name, stars=stars, license_name=license_name)

    matched_flags: dict[str, int] = {}  # flag_name -> first line number

    def record(flag_name: str, pos: int) -> None:
        if flag_name not in matched_flags:
            matched_flags[flag_name] = _line_number(readme, pos)

    # 1. REJECT patterns
    for pattern, flag_name, _desc in REJECT_PATTERNS:
        for m in pattern.finditer(readme_lower):
            if not _is_cited_or_negated(readme_lower, m.start(), flag_name):
                record(flag_name, m.start())
                break

    # 2. HIGH-RISK patterns
    if not any(f in REJECT_FLAG_NAMES for f in matched_flags):
        for pattern, flag_name, _desc in HIGH_RISK_PATTERNS:
            inline_excused = flag_name in _EXFIL_SHAPED
            for m in pattern.finditer(readme_lower):
                if (
                    not _is_in_code_block(readme_lower, m.start())
                    and not _documents_rather_than_issues(readme_lower, m.start())
                    and not (inline_excused and _is_inline_code(readme_lower, m.start()))
                ):
                    record(flag_name, m.start())
                    break

        # 3. MEDIUM-RISK patterns
        for pattern, flag_name, _desc in MEDIUM_RISK_PATTERNS:
            match = next(
                (m for m in pattern.finditer(readme_lower)
                 if not _documents_rather_than_issues(readme_lower, m.start())),
                None,
            )
            if match:
                if flag_name == "sensitive_env_vars":
                    env_count = len({
                        m.lower() for m in re.findall(
                            r"(OPENAI_API_KEY|ANTHROPIC_API_KEY|AWS_SECRET|GITHUB_TOKEN)",
                            readme, re.IGNORECASE,
                        )
                    })
                    if env_count >= 3:
                        record(flag_name, match.start())
                else:
                    record(flag_name, match.start())

        # 4. PIPE-TO-SHELL
        for pattern, flag_name, _desc in PIPE_TO_SHELL_PATTERNS:
            fenced_pos: int | None = None
            prose_pos: int | None = None
            for match in pattern.finditer(readme_lower):
                pos = match.start()
                in_fence = _is_in_code_block(readme_lower, pos)
                if _is_markdown_table_row(readme_lower, pos) or (in_fence and _documents_rather_than_issues(readme_lower, pos)):
                    continue
                urls = [u for u in _URL_IN_COMMAND.findall(match.group(0)) if not _is_placeholder(u)]
                if not urls or all(_is_trusted_install_source(u, repo_full_name, homepage_url) for u in urls):
                    continue
                if not in_fence:
                    prose_pos = pos
                    break
                if fenced_pos is None:
                    fenced_pos = pos
            if prose_pos is not None:
                record(flag_name, prose_pos)
            elif fenced_pos is not None:
                record(FENCED_DOWNLOAD_FLAG, fenced_pos)

        # 5. PAGES DOWNLOAD LURE
        owner = (repo_full_name or author_name).lower().partition("/")[0]
        if owner:
            for match in _IMAGE_BUTTON.finditer(readme_lower):
                label, target = match.group(1), match.group(2)
                if "download" not in label or "downloads" in label or _host(target) != f"{owner}.github.io":
                    continue
                if not _is_in_code_block(readme_lower, match.start()) and not _is_inline_code(readme_lower, match.start()):
                    record(PAGES_DOWNLOAD_FLAG, match.start())
                    break

        # 6. AGENT-ERA MEDIUM patterns
        for pattern, flag_name, _desc in AGENT_MEDIUM_PATTERNS:
            for match in pattern.finditer(readme_lower):
                if not _is_cited_or_negated(readme_lower, match.start(), flag_name):
                    record(flag_name, match.start())
                    break

        # 7. SECRET patterns (original case)
        for pattern, flag_name, _desc in SECRET_PATTERNS:
            hit = next((m for m in pattern.finditer(readme) if _looks_like_real_secret(m.group(0))), None)
            if hit:
                record(flag_name, hit.start())
                break

    ignore = ignored_flags or set()
    active_flags = [f for f in matched_flags if f not in ignore]
    suppressed = [f for f in matched_flags if f in ignore]

    grade = compute_grade(active_flags, trust_tier)
    findings = [
        Finding(
            file=file_path,
            flag=f,
            severity=_flag_severity(f),
            description=_flag_description(f),
            line=matched_flags[f],
        )
        for f in active_flags
    ]
    return FileScanResult(
        file=file_path,
        grade=grade,
        flags=active_flags,
        suppressed_flags=suppressed,
        findings=findings,
    )


def compute_grade(flags: list[str], trust_tier: int) -> str:
    if any(f in REJECT_FLAG_NAMES for f in flags):
        return "unsafe" if trust_tier <= 2 else "reject"
    high_flags = [f for f in flags if f in HIGH_RISK_FLAG_NAMES]
    med_flags = [f for f in flags if f in MEDIUM_RISK_FLAG_NAMES]

    if high_flags:
        if trust_tier <= 3:
            return "caution"
        if trust_tier == 4:
            return "caution" if len(high_flags) == 1 else "unsafe"
        return "unsafe"
    if len(med_flags) >= 2:
        return "safe" if trust_tier <= 3 else "caution"
    if len(med_flags) == 1:
        return "caution" if trust_tier == 5 else "safe"
    return "safe"


# ══════════════════════════════════════════════════════════════════════
# Allowlist + Target Discovery
# ══════════════════════════════════════════════════════════════════════
DEFAULT_TARGET_PATTERNS = (
    "SKILL.md",
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    "mcp.json",
    ".mcp.json",
    "skills/**/SKILL.md",
    ".claude/**/*.md",
    ".codex/**/*.md",
)

GRADE_RANK = {"safe": 0, "unknown": 0, "caution": 1, "unsafe": 2, "reject": 3}


def load_allowlist(path: Path | None) -> tuple[set[str], set[str]]:
    """Return (ignored_flags, ignored_paths), honoring non-expired rules."""
    if path is None or not path.exists():
        return set(), set()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"::warning::Could not parse allowlist {path}: {exc}", file=sys.stderr)
        return set(), set()

    today = date.today().isoformat()
    expires = raw.get("expires_at")
    if isinstance(expires, str) and expires < today:
        print(f"::warning::Allowlist {path} expired on {expires}; ignoring allowlist.", file=sys.stderr)
        return set(), set()

    ignored_flags = {str(x) for x in raw.get("ignore_flags", []) if x}
    ignored_paths = {str(x) for x in raw.get("ignore_paths", []) if x}

    for entry in raw.get("entries", []):
        if not isinstance(entry, dict):
            continue
        ent_exp = entry.get("expires_at")
        if isinstance(ent_exp, str) and ent_exp < today:
            continue
        if entry.get("flag"):
            ignored_flags.add(str(entry["flag"]))
        if entry.get("path"):
            ignored_paths.add(str(entry["path"]))
    return ignored_flags, ignored_paths


def discover_files(inputs: list[str], root: Path) -> list[Path]:
    """Resolve explicit paths/dirs or discover default skill/MCP files under root."""
    candidates: list[Path] = []
    seen: set[Path] = set()

    def add(p: Path) -> None:
        resolved = p.resolve()
        if resolved not in seen and resolved.is_file():
            seen.add(resolved)
            candidates.append(resolved)

    if not inputs:
        for pat in DEFAULT_TARGET_PATTERNS:
            for p in root.glob(pat):
                if ".git" not in p.parts and "node_modules" not in p.parts:
                    add(p)
        if not candidates and (root / "README.md").is_file():
            add(root / "README.md")
        return sorted(candidates)

    for raw in inputs:
        p = Path(raw)
        if not p.is_absolute():
            p = root / p
        if p.is_file():
            add(p)
        elif p.is_dir():
            for child in p.rglob("*"):
                if ".git" in child.parts or "node_modules" in child.parts:
                    continue
                if child.is_file() and child.suffix.lower() in {".md", ".json", ".txt", ""}:
                    if child.name in {"SKILL.md", "AGENTS.md", "CLAUDE.md", ".cursorrules", "mcp.json", ".mcp.json", "README.md"} or child.suffix.lower() == ".md":
                        add(child)
    return sorted(candidates)


def _path_is_ignored(rel_path: str, ignored_paths: set[str]) -> bool:
    return any(fnmatch.fnmatch(rel_path, pat) or rel_path == pat for pat in ignored_paths)


def _scan_mcp_json(text: str, file_path: str, ignored_flags: set[str]) -> FileScanResult:
    """Inspect mcp.json / .mcp.json servers for shell pipes or hardcoded secrets."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return scan_text(text, file_path=file_path, ignored_flags=ignored_flags)

    lines: list[str] = []
    servers = data.get("mcpServers") if isinstance(data, dict) else None
    if isinstance(servers, dict):
        for name, cfg in servers.items():
            if not isinstance(cfg, dict):
                continue
            cmd = str(cfg.get("command", ""))
            args = " ".join(str(a) for a in (cfg.get("args") or []))
            env_map = cfg.get("env") or {}
            lines.append(f"# MCP Server {name}")
            if cmd or args:
                lines.append(f"{cmd} {args}".strip())
            if isinstance(env_map, dict):
                for k, v in env_map.items():
                    lines.append(f"{k}={v}")
    combined = "\n".join(lines) if lines else text
    return scan_text(combined, file_path=file_path, ignored_flags=ignored_flags)


def to_sarif(results: list[FileScanResult]) -> dict:
    rules = {}
    sarif_results = []
    for res in results:
        for finding in res.findings:
            if finding.flag not in rules:
                rules[finding.flag] = {
                    "id": finding.flag,
                    "shortDescription": {"text": finding.description},
                    "defaultConfiguration": {
                        "level": "error" if finding.severity in {"critical", "high"} else "warning"
                    },
                }
            sarif_results.append({
                "ruleId": finding.flag,
                "level": "error" if finding.severity in {"critical", "high"} else "warning",
                "message": {"text": f"[{finding.severity.upper()}] {finding.description}"},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": finding.file},
                        "region": {"startLine": max(1, finding.line)},
                    }
                }],
            })
    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "AgentSkillsHub-CI-Gate",
                    "version": SCANNER_VERSION,
                    "informationUri": "https://agentskillshub.top/ci-gate/",
                    "rules": list(rules.values()),
                }
            },
            "results": sarif_results,
        }],
    }


def render_markdown_summary(results: list[FileScanResult], fail_on: str) -> str:
    worst = max((GRADE_RANK.get(r.grade, 0) for r in results), default=0)
    passed = worst < GRADE_RANK[fail_on]
    status_emoji = "✅ PASS" if passed else "❌ FAIL"
    lines = [
        f"## Agent Skills Hub — CI Skill Gate ({status_emoji})",
        f"Policy: fail on `{fail_on}` or worse · Files scanned: **{len(results)}**\n",
        "| File | Grade | Flags |",
        "| --- | --- | --- |",
    ]
    for r in results:
        flag_str = ", ".join(f"`{f}`" for f in r.flags) if r.flags else "—"
        lines.append(f"| `{r.file}` | `{r.grade.upper()}` | {flag_str} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agent Skills Hub CI Skill Gate")
    parser.add_argument("paths", nargs="*", help="Files or directories to scan (default: auto-discover SKILL.md/AGENTS.md/mcp.json)")
    parser.add_argument("--root", default=".", help="Repository root for relative paths and discovery")
    parser.add_argument("--repo", default="", help="GitHub repo slug (owner/name) for own-site URL trust checks")
    parser.add_argument("--homepage", default="", help="Homepage URL for same-site trust checks")
    parser.add_argument("--stars", type=int, default=0, help="Repo star count (default 0 = strict Tier 5 scrutiny)")
    parser.add_argument("--license", dest="license_name", default=None, help="SPDX license name if any")
    parser.add_argument("--fail-on", choices=["reject", "unsafe", "caution"], default="unsafe",
                        help="Minimum grade that fails the CI check (default: unsafe)")
    parser.add_argument("--allowlist", default=".agentskillshub-allowlist.json",
                        help="Optional allowlist JSON file")
    parser.add_argument("--format", choices=["text", "json", "sarif", "markdown"], default="text")
    parser.add_argument("--sarif-out", default="", help="Optional file path to also write SARIF JSON")
    parser.add_argument("--annotations", action="store_true", help="Emit GitHub Actions ::error/::warning annotations")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    allowlist_path = Path(args.allowlist)
    if not allowlist_path.is_absolute():
        allowlist_path = root / allowlist_path
    ignored_flags, ignored_paths = load_allowlist(allowlist_path)

    files = discover_files(args.paths, root)
    results: list[FileScanResult] = []
    for fpath in files:
        try:
            rel = str(fpath.relative_to(root))
        except ValueError:
            rel = str(fpath)
        if _path_is_ignored(rel, ignored_paths):
            continue
        content = fpath.read_text(encoding="utf-8", errors="replace")
        if fpath.name in {"mcp.json", ".mcp.json"}:
            res = _scan_mcp_json(content, rel, ignored_flags)
        else:
            res = scan_text(
                content,
                file_path=rel,
                repo_full_name=args.repo,
                homepage_url=args.homepage,
                stars=args.stars,
                license_name=args.license_name,
                ignored_flags=ignored_flags,
            )
        results.append(res)

    threshold = GRADE_RANK[args.fail_on]
    failing = [r for r in results if GRADE_RANK.get(r.grade, 0) >= threshold]

    if args.annotations:
        for res in results:
            for finding in res.findings:
                level = "error" if finding.severity in {"critical", "high"} else "warning"
                print(f"::{level} file={finding.file},line={finding.line}::[{finding.flag}] {finding.description}")

    if args.sarif_out:
        sarif_path = Path(args.sarif_out)
        sarif_path.parent.mkdir(parents=True, exist_ok=True)
        sarif_path.write_text(json.dumps(to_sarif(results), indent=2), encoding="utf-8")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(render_markdown_summary(results, args.fail_on))

    if args.format == "json":
        print(json.dumps({
            "passed": len(failing) == 0,
            "fail_on": args.fail_on,
            "scanned": len(results),
            "results": [
                {
                    "file": r.file,
                    "grade": r.grade,
                    "flags": r.flags,
                    "suppressed_flags": r.suppressed_flags,
                    "findings": [vars(f) for f in r.findings],
                }
                for r in results
            ],
        }, indent=2))
    elif args.format == "sarif":
        print(json.dumps(to_sarif(results), indent=2))
    elif args.format == "markdown":
        print(render_markdown_summary(results, args.fail_on))
    else:
        if not results:
            print("AgentSkillsHub CI Gate: no skill/MCP/instruction files matched.")
        for r in results:
            flag_txt = ", ".join(r.flags) if r.flags else "none"
            sup_txt = f" (suppressed: {', '.join(r.suppressed_flags)})" if r.suppressed_flags else ""
            print(f"[{r.grade.upper():7s}] {r.file} — flags: {flag_txt}{sup_txt}")
        print(
            f"\nResult: {'PASS' if not failing else 'FAIL'} "
            f"({len(results)} scanned, {len(failing)} at/above '{args.fail_on}')"
        )

    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
