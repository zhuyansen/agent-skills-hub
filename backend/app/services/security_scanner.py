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
from typing import Optional

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
    (re.compile(r"curl\s+[^\n]*\|\s*(ba)?sh", re.IGNORECASE), "curl_pipe_shell",
     "Downloads and executes remote script via curl|bash"),
    (re.compile(r"wget\s+[^\n]*\|\s*(ba)?sh", re.IGNORECASE), "wget_pipe_shell",
     "Downloads and executes remote script via wget|bash"),

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
]

HIGH_RISK_FLAG_NAMES = {p[1] for p in HIGH_RISK_PATTERNS}

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

MEDIUM_RISK_FLAG_NAMES = {p[1] for p in MEDIUM_RISK_PATTERNS}

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


class SecurityScanner:
    """Rule-based security scanner with SlowMist-inspired patterns and trust hierarchy."""

    def scan_all(self, db: Session, batch_size: int = 1000) -> dict:
        """Scan all skills with README content and set security_grade + security_flags."""
        stats = {"scanned": 0, "safe": 0, "caution": 0, "unsafe": 0, "reject": 0, "no_readme": 0}

        skills = (
            db.query(Skill)
            .filter(Skill.readme_content.isnot(None))
            .filter(Skill.readme_content != "")
            .all()
        )

        for skill in skills:
            grade, flags = self._scan(skill)
            skill.security_grade = grade
            skill.security_flags = json.dumps(flags)
            stats["scanned"] += 1
            stats.setdefault(grade, 0)
            stats[grade] = stats.get(grade, 0) + 1

        # Skills without README → "unknown"
        no_readme_count = (
            db.query(Skill)
            .filter((Skill.readme_content.is_(None)) | (Skill.readme_content == ""))
            .update({"security_grade": "unknown", "security_flags": "[]"}, synchronize_session=False)
        )
        stats["no_readme"] = no_readme_count

        db.commit()
        logger.info(
            f"Security scan complete: {stats['scanned']} scanned, "
            f"{stats.get('safe', 0)} safe, {stats.get('caution', 0)} caution, "
            f"{stats.get('unsafe', 0)} unsafe, {stats.get('reject', 0)} reject, "
            f"{stats['no_readme']} no README"
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
        for patterns in [HIGH_RISK_PATTERNS, MEDIUM_RISK_PATTERNS, REJECT_PATTERNS]:
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
