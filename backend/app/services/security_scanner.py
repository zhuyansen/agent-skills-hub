"""
Security Scanner — Rule-based security analysis for skills.

Scans README content for dangerous patterns and outputs a security grade:
  - "safe": No concerning patterns detected
  - "caution": Some potentially risky patterns found
  - "unsafe": High-risk patterns detected (e.g., curl|bash, eval, backdoors)

Zero cost: pure regex/string matching, no external API calls.
"""

import json
import logging
import re
from typing import Optional

from sqlalchemy.orm import Session

from app.models.skill import Skill

logger = logging.getLogger(__name__)

# ── High-risk patterns (any one → unsafe) ────────────────────────────
HIGH_RISK_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Pipe-to-shell execution
    (re.compile(r"curl\s+[^\n]*\|\s*(ba)?sh", re.IGNORECASE), "curl_pipe_shell"),
    (re.compile(r"wget\s+[^\n]*\|\s*(ba)?sh", re.IGNORECASE), "wget_pipe_shell"),
    # Base64 decode + execute
    (re.compile(r"base64\s+(-d|--decode)\s*\|", re.IGNORECASE), "base64_exec"),
    # chmod 777 or overly permissive
    (re.compile(r"chmod\s+777\b"), "chmod_777"),
    # Write to system directories in a command context
    (re.compile(r">\s*/etc/", re.IGNORECASE), "write_etc"),
    # Reverse shell patterns
    (re.compile(r"(nc|ncat|netcat)\s+-[elp]", re.IGNORECASE), "reverse_shell"),
    (re.compile(r"/dev/tcp/", re.IGNORECASE), "dev_tcp"),
    # Obfuscated Python exec
    (re.compile(r"exec\s*\(\s*__import__", re.IGNORECASE), "exec_import"),
    # rm -rf / or similar destructive
    (re.compile(r"rm\s+-rf\s+/\s", re.IGNORECASE), "rm_rf_root"),
]

HIGH_RISK_FLAG_NAMES = {p[1] for p in HIGH_RISK_PATTERNS}

# ── Medium-risk patterns (2+ → caution) ──────────────────────────────
MEDIUM_RISK_PATTERNS: list[tuple[re.Pattern, str]] = [
    # sudo usage
    (re.compile(r"\bsudo\b"), "sudo_usage"),
    # Privileged Docker
    (re.compile(r"--privileged", re.IGNORECASE), "docker_privileged"),
    # Broad file system access patterns
    (re.compile(r'fs\.readdir\s*\(\s*["\']/', re.IGNORECASE), "fs_root_access"),
    # Requests for many sensitive env vars
    (re.compile(r"(OPENAI_API_KEY|ANTHROPIC_API_KEY|AWS_SECRET|GITHUB_TOKEN)", re.IGNORECASE), "sensitive_env_vars"),
    # Disable SSL verification
    (re.compile(r"verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0", re.IGNORECASE), "ssl_disabled"),
    # Eval in JS/Python context (not in code block explanations)
    (re.compile(r"\beval\s*\("), "eval_usage"),
]

MEDIUM_RISK_FLAG_NAMES = {p[1] for p in MEDIUM_RISK_PATTERNS}


def _is_in_code_block(text: str, match_pos: int) -> bool:
    """Check if a match position is inside a markdown code block (``` ... ```)."""
    before = text[:match_pos]
    # Count triple backticks before this position
    fence_count = before.count("```")
    # Odd count = inside a code block
    return fence_count % 2 == 1


class SecurityScanner:
    """Rule-based security scanner for skill README content."""

    def scan_all(self, db: Session, batch_size: int = 1000) -> dict:
        """Scan all skills with README content and set security_grade + security_flags."""
        stats = {"scanned": 0, "safe": 0, "caution": 0, "unsafe": 0, "no_readme": 0}

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
            stats[grade] += 1

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
            f"{stats['safe']} safe, {stats['caution']} caution, "
            f"{stats['unsafe']} unsafe, {stats['no_readme']} no README"
        )
        return stats

    def _scan(self, skill: Skill) -> tuple[str, list[str]]:
        """Scan a single skill and return (grade, flags)."""
        flags: list[str] = []
        readme = (skill.readme_content or "")[:15000]
        readme_lower = readme.lower()

        # ── Check high-risk patterns ──
        for pattern, flag_name in HIGH_RISK_PATTERNS:
            match = pattern.search(readme_lower)
            if match:
                # Only flag if NOT inside a code block (reduce false positives
                # for documentation that explains dangerous patterns)
                if not _is_in_code_block(readme_lower, match.start()):
                    flags.append(flag_name)

        # ── Check medium-risk patterns ──
        for pattern, flag_name in MEDIUM_RISK_PATTERNS:
            match = pattern.search(readme_lower)
            if match:
                # sensitive_env_vars is very common and expected; only flag
                # if it appears alongside other medium-risk patterns
                if flag_name == "sensitive_env_vars":
                    # Count distinct env var mentions
                    env_count = len(set(re.findall(
                        r"(OPENAI_API_KEY|ANTHROPIC_API_KEY|AWS_SECRET|GITHUB_TOKEN)",
                        readme, re.IGNORECASE
                    )))
                    if env_count >= 3:
                        flags.append(flag_name)
                else:
                    flags.append(flag_name)

        # ── Positive signals that reduce risk ──
        positive_signals = 0
        if skill.license:
            positive_signals += 1
        if skill.stars and skill.stars >= 100:
            positive_signals += 1
        if skill.stars and skill.stars >= 1000:
            positive_signals += 1  # Extra credit for well-known repos

        # ── Determine grade ──
        high_flags = [f for f in flags if f in HIGH_RISK_FLAG_NAMES]
        med_flags = [f for f in flags if f in MEDIUM_RISK_FLAG_NAMES]

        if high_flags:
            # High-star repos with high-risk patterns get downgraded to caution
            # (e.g., legitimate install scripts using curl|bash)
            if positive_signals >= 2:
                return "caution", flags
            return "unsafe", flags
        elif len(med_flags) >= 2:
            # Multiple medium risks, but well-known repos get a pass
            if positive_signals >= 3:
                return "safe", flags
            return "caution", flags
        else:
            return "safe", flags

    def scan_single(self, skill: Skill) -> tuple[str, list[str]]:
        """Scan a single skill (for on-demand use). Does not persist."""
        return self._scan(skill)
