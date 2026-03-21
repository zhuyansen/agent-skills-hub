"""
LLM Security Analyzer — Uses Claude Haiku for semantic security analysis.

Phase 2: For skills flagged as caution/unsafe by the rule-based scanner,
this service provides deeper semantic analysis using Anthropic's Claude API.

Cost estimate: ~$0.5 for 500 skills (Haiku pricing).
"""

import json
import logging
import time
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# System prompt for security analysis
SYSTEM_PROMPT = """You are a security analyst for open-source AI agent skills and MCP servers.
Analyze the README content and metadata to assess security risks.

Your task:
1. Determine if the repository poses genuine security risks to users
2. Distinguish between legitimate tool usage (install scripts, API keys) and actual threats
3. Consider the repository's reputation (stars, license) as trust signals

Common FALSE POSITIVES to watch for:
- curl|bash install scripts for well-known package managers (npm, pip, homebrew)
- API key configuration instructions (OPENAI_API_KEY, etc.) — normal for AI tools
- sudo usage in Docker setup or system package installation
- eval() in legitimate template engines or REPL tools

Respond with ONLY valid JSON (no markdown fences):
{
  "grade": "safe" | "caution" | "unsafe",
  "confidence": 0.0-1.0,
  "risk_summary": "One sentence summary",
  "findings": [
    {
      "severity": "high" | "medium" | "low",
      "description": "What was found",
      "mitigation": "Why it may or may not be a real risk"
    }
  ],
  "recommendation": "Brief recommendation for users"
}"""

USER_PROMPT_TEMPLATE = """Analyze this repository for security risks:

## Repository Metadata
- Name: {full_name}
- Stars: {stars}
- License: {license}
- Category: {category}
- Description: {description}

## Rule-Based Scanner Flags
The following patterns were detected by our rule-based scanner:
{flags}

## README Content (first 8000 chars)
{readme}

Provide your security analysis as JSON."""


class LLMSecurityAnalyzer:
    """Uses Claude Haiku for semantic security analysis of flagged skills."""

    def __init__(self, api_key: str, model: str = "claude-haiku-4-0"):
        self.api_key = api_key
        self.model = model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def analyze_single(self, readme: str, metadata: dict) -> dict:
        """Analyze a single README with LLM. Returns structured analysis dict."""
        user_prompt = USER_PROMPT_TEMPLATE.format(
            full_name=metadata.get("full_name", "unknown"),
            stars=metadata.get("stars", 0),
            license=metadata.get("license", "none"),
            category=metadata.get("category", "unknown"),
            description=metadata.get("description", ""),
            flags=", ".join(metadata.get("flags", [])) or "none",
            readme=readme[:8000],
        )

        for attempt in range(3):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                text = response.content[0].text.strip()
                # Parse JSON response
                result = json.loads(text)
                # Validate required fields
                if "grade" not in result or result["grade"] not in ("safe", "caution", "unsafe"):
                    result["grade"] = "caution"
                if "confidence" not in result:
                    result["confidence"] = 0.5
                if "findings" not in result:
                    result["findings"] = []
                if "risk_summary" not in result:
                    result["risk_summary"] = ""
                if "recommendation" not in result:
                    result["recommendation"] = ""
                return result
            except json.JSONDecodeError:
                logger.warning("LLM returned invalid JSON (attempt %d/3)", attempt + 1)
                if attempt == 2:
                    return {
                        "grade": "caution",
                        "confidence": 0.0,
                        "risk_summary": "LLM analysis failed: invalid response",
                        "findings": [],
                        "recommendation": "Manual review recommended",
                    }
            except Exception as e:
                logger.warning("LLM API error (attempt %d/3): %s", attempt + 1, e)
                if attempt < 2:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return {
                        "grade": "caution",
                        "confidence": 0.0,
                        "risk_summary": f"LLM analysis failed: {str(e)[:100]}",
                        "findings": [],
                        "recommendation": "Manual review recommended",
                    }
        # Should not reach here
        return {"grade": "caution", "confidence": 0.0, "risk_summary": "Unknown error", "findings": [], "recommendation": ""}

    def analyze_flagged(self, db: Session) -> dict:
        """Batch analyze all caution/unsafe skills. Updates security_llm_* fields."""
        from app.models.skill import Skill

        stats = {"analyzed": 0, "upgraded": 0, "downgraded": 0, "unchanged": 0, "errors": 0}

        flagged = (
            db.query(Skill)
            .filter(Skill.security_grade.in_(["caution", "unsafe"]))
            .filter(Skill.readme_content.isnot(None))
            .all()
        )

        logger.info("LLM security analysis: %d flagged skills to analyze", len(flagged))

        for skill in flagged:
            try:
                flags = json.loads(skill.security_flags or "[]")
                metadata = {
                    "full_name": skill.repo_full_name,
                    "stars": skill.stars or 0,
                    "license": skill.license or "none",
                    "category": skill.category or "unknown",
                    "description": skill.description or "",
                    "flags": flags,
                }

                result = self.analyze_single(skill.readme_content or "", metadata)

                skill.security_llm_grade = result["grade"]
                skill.security_llm_analysis = json.dumps(result)
                stats["analyzed"] += 1

                # Track grade changes
                if result["grade"] != skill.security_grade:
                    if result["grade"] == "safe":
                        stats["upgraded"] += 1
                    else:
                        stats["downgraded"] += 1
                else:
                    stats["unchanged"] += 1

                # Rate limit: 1 req/sec
                time.sleep(1)

            except Exception as e:
                logger.warning("LLM analysis failed for %s: %s", skill.repo_full_name, e)
                stats["errors"] += 1

        db.commit()
        logger.info("LLM security analysis complete: %s", stats)
        return stats

    def analyze_repo_readme(self, readme: str, repo_info: dict) -> dict:
        """Analyze a repo on-demand (for the Analyzer page). Does not persist."""
        metadata = {
            "full_name": repo_info.get("full_name", ""),
            "stars": repo_info.get("stargazers_count", repo_info.get("stars", 0)),
            "license": (repo_info.get("license") or {}).get("spdx_id", "none")
                if isinstance(repo_info.get("license"), dict)
                else repo_info.get("license", "none"),
            "category": repo_info.get("category", "unknown"),
            "description": repo_info.get("description", ""),
            "flags": repo_info.get("flags", []),
        }
        return self.analyze_single(readme, metadata)
