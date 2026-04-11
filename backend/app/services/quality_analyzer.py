"""Heuristic-based quality analyzer for skills.

v3 improvements (inspired by SkillsBench paper, arXiv:2602.12670):
- Procedural content detection: rewards step-by-step, workflows, SOP content
- Instruction quality scoring: checks output paths, constraints, success criteria
- Optimal README length: "detailed" > "compact" > "comprehensive" (diminishing returns)
- README structure now penalizes overly verbose docs (paper Finding 6)
"""
import json
import logging
import re

from sqlalchemy.orm import Session

from app.models.skill import Skill

logger = logging.getLogger(__name__)


class QualityAnalyzer:
    """Scores skills on 9 quality dimensions using locally available data.

    Dimensions:
    1. Completeness (11%) - README, description, license, stars
    2. Clarity (11%) - Description quality, topics, naming
    3. Specificity (11%) - Language focus, topic count, category
    4. Examples (9%) - Code examples, commits, contributors
    5. README Structure (14%) - Sections, code blocks, badges, TOC
    6. Agent Readiness (16%) - Install, tools, usage, config, compliance
    7. Procedural Content (10%) - Step-by-step, workflows, SOP
    8. Instruction Quality (9%) - Output paths, constraints, success criteria
    9. Security Awareness (9%) - Permission docs, sandboxing, trust boundaries
    """

    def analyze_all(self, db: Session) -> int:
        skills = db.query(Skill).all()
        for skill in skills:
            self._analyze(skill)
        db.commit()
        return len(skills)

    # Section headings that indicate good README structure
    VALUABLE_SECTIONS = [
        r"(?i)^#{1,3}\s*(installation|install|setup|getting started)",
        r"(?i)^#{1,3}\s*(usage|how to use|quick start)",
        r"(?i)^#{1,3}\s*(api|api reference|reference)",
        r"(?i)^#{1,3}\s*(configuration|config|options|settings)",
        r"(?i)^#{1,3}\s*(examples?|demos?)",
        r"(?i)^#{1,3}\s*(contributing|contribute|development)",
        r"(?i)^#{1,3}\s*(license|licensing)",
        r"(?i)^#{1,3}\s*(changelog|changes|releases)",
        r"(?i)^#{1,3}\s*(requirements|prerequisites|dependencies)",
        r"(?i)^#{1,3}\s*(features|capabilities|highlights)",
        r"(?i)^#{1,3}\s*(troubleshooting|faq|known issues)",
    ]

    # Sections that indicate agent-readiness
    AGENT_SECTIONS = {
        "install": r"(?i)^#{1,3}\s*(installation|install|setup|getting started)",
        "tools": r"(?i)^#{1,3}\s*(api|tools?|functions?|endpoints?|commands?|capabilities)",
        "usage": r"(?i)^#{1,3}\s*(usage|how to use|quick start|examples?)",
        "config": r"(?i)^#{1,3}\s*(configuration|config|options|settings|environment)",
    }

    # Patterns indicating procedural content (step-by-step, workflows)
    PROCEDURAL_PATTERNS = [
        r"(?i)^#{1,3}\s*(steps?|workflow|procedure|how[- ]to|walkthrough|tutorial)",
        r"(?i)step\s*[1-9]",                    # "Step 1", "Step 2"
        r"(?m)^\s*\d+\.\s+\w",                  # Numbered lists: "1. Do this"
        r"(?i)(first|then|next|finally|after that),?\s",  # Sequence words
        r"(?i)run\s+(the\s+)?(following|this|these)",     # "Run the following"
        r"(?i)(execute|invoke|call)\s+(the\s+)?",         # Action verbs
    ]

    # Patterns indicating security awareness (inspired by ClawKeeper)
    SECURITY_AWARENESS_PATTERNS = {
        "permission_docs": [
            r"(?i)^#{1,3}\s*(security|permissions?|access\s*control|auth)",
            r"(?i)^#{1,3}\s*(trust|safety|privacy|sandbo[xk])",
            r"(?i)(required\s+permissions?|scope[sd]?|capabilities)",
        ],
        "sandboxing": [
            r"(?i)(sandbox|isolat|container|docker|jail|chroot)",
            r"(?i)(safe\s*mode|restricted|read[- ]only|no[- ]exec)",
            r"(?i)(allowedTools|allowed_tools|tool[- ]?whitelist)",
        ],
        "trust_boundaries": [
            r"(?i)(trust\s*(tier|level|boundar|hierarch|model))",
            r"(?i)(validate|sanitize|escape|filter)\s*(input|output|data)",
            r"(?i)(rate[- ]limit|throttl|quota|abuse|injection)",
        ],
        "credential_safety": [
            r"(?i)(env(ironment)?\s*var|\.env\s*file|secret[- ]?manag)",
            r"(?i)(do\s*not|never|don.t)\s*(hardcode|commit|share)\s*(secret|key|token|password)",
            r"(?i)(vault|keychain|credential\s*store|secret\s*store)",
        ],
        "threat_model": [
            r"(?i)(threat\s*model|attack\s*(surface|vector)|risk\s*assess)",
            r"(?i)(prompt\s*inject|data\s*exfil|privilege\s*escalat)",
            r"(?i)(audit\s*log|compliance|OWASP|CVE|CWE)",
        ],
    }

    # Patterns indicating instruction quality (from paper Section 2.4)
    INSTRUCTION_QUALITY_PATTERNS = {
        "output_paths": [
            r"(?i)(output|result|return|response)\s*(file|path|dir|format|type)",
            r"(?i)(saves?\s+to|writes?\s+to|outputs?\s+to)",
            r"(?i)(stdout|stderr|log\s*file|\.json|\.csv|\.txt)",
        ],
        "success_criteria": [
            r"(?i)(success|expected|should|must|assert|verify|validate|check)",
            r"(?i)(pass|fail|error\s*handling|exit\s*code)",
            r"(?i)(returns?\s+(true|false|0|1|null|none|error))",
        ],
        "constraints": [
            r"(?i)(requires?|prerequisite|dependency|must\s+have|needed)",
            r"(?i)(limit|max|min|timeout|rate[- ]limit|quota)",
            r"(?i)(not\s+supported|does\s*n['\u2019]t|cannot|won['\u2019]t|avoid)",
        ],
        "structured_req": [
            r"(?i)(input|parameter|argument|flag|option)\s*:",
            r"(?i)(type|format|schema|interface|struct)\s*:",
            r"\|\s*\w+\s*\|\s*\w+\s*\|",  # Markdown table rows
        ],
        "context_first": [
            r"(?i)^#{1,3}\s*(overview|introduction|about|what|why)",
            r"(?i)^#{1,3}\s*(background|context|motivation|purpose)",
        ],
    }

    def _analyze(self, skill: Skill) -> None:
        skill.quality_completeness = self._completeness(skill)
        skill.quality_clarity = self._clarity(skill)
        skill.quality_specificity = self._specificity(skill)
        skill.quality_examples = self._examples(skill)

        readme_struct = self._readme_structure(skill)
        skill.readme_structure_score = round(readme_struct, 3)

        agent_ready = self._agent_readiness(skill)
        skill.quality_agent_readiness = round(agent_ready, 3)

        procedural = self._procedural_content(skill)
        instruction_q = self._instruction_quality(skill)
        security_aw = self._security_awareness(skill)

        if skill.readme_content:
            # 9-dimension weighted scoring when README content is available
            skill.quality_score = (
                skill.quality_completeness * 0.11
                + skill.quality_clarity * 0.11
                + skill.quality_specificity * 0.11
                + skill.quality_examples * 0.09
                + readme_struct * 0.14
                + agent_ready * 0.16
                + procedural * 0.10
                + instruction_q * 0.09
                + security_aw * 0.09
            ) * 100
        else:
            # Without README: security_awareness gets minimal weight
            skill.quality_score = (
                skill.quality_completeness * 0.20
                + skill.quality_clarity * 0.20
                + skill.quality_specificity * 0.20
                + skill.quality_examples * 0.15
                + agent_ready * 0.15
                + procedural * 0.04
                + instruction_q * 0.03
                + security_aw * 0.03
            ) * 100

    def _completeness(self, skill: Skill) -> float:
        """How complete is the project? README, description, license, etc."""
        score = 0.0
        desc = skill.description or ""
        readme_sz = skill.readme_size or 0

        # README size — optimal range (paper: detailed > comprehensive)
        # Sweet spot: 2000-8000 chars. Penalty for >15000 (too verbose)
        if 2000 <= readme_sz <= 8000:
            score += 0.35  # optimal: detailed but focused
        elif 8000 < readme_sz <= 15000:
            score += 0.30  # still good, getting verbose
        elif readme_sz > 15000:
            score += 0.25  # comprehensive: slight penalty (paper Finding 6)
        elif readme_sz > 500:
            score += 0.15
        elif readme_sz > 0:
            score += 0.05

        # Has description
        if len(desc) > 50:
            score += 0.2
        elif len(desc) > 10:
            score += 0.1

        # Has license
        if skill.license and skill.license not in ("", "NOASSERTION"):
            score += 0.15

        # Has homepage
        if skill.homepage_url:
            score += 0.1

        # Has meaningful stars (indicates community validation)
        if skill.stars >= 100:
            score += 0.2
        elif skill.stars >= 10:
            score += 0.1

        return min(score, 1.0)

    def _clarity(self, skill: Skill) -> float:
        """How clear and well-documented is the project?"""
        score = 0.0
        desc = skill.description or ""

        # Description quality
        if 30 <= len(desc) <= 300:
            score += 0.25  # concise and descriptive
        elif len(desc) > 300:
            score += 0.15  # verbose
        elif len(desc) > 0:
            score += 0.05

        # README exists — optimal range (paper: focused > exhaustive)
        readme_sz = skill.readme_size or 0
        if 1000 <= readme_sz <= 10000:
            score += 0.3  # detailed but focused
        elif readme_sz > 10000:
            score += 0.2  # verbose, slight penalty
        elif readme_sz > 0:
            score += 0.1

        # Has topics (helps discoverability)
        topics = json.loads(skill.topics) if skill.topics else []
        if len(topics) >= 3:
            score += 0.2
        elif len(topics) >= 1:
            score += 0.1

        # Repo name is descriptive (contains hyphen/underscore = multi-word)
        if "-" in skill.repo_name or "_" in skill.repo_name:
            score += 0.15

        # Not a fork (higher originality)
        if skill.forks > 0:
            score += 0.1

        return min(score, 1.0)

    def _specificity(self, skill: Skill) -> float:
        """How focused is the project? Single-purpose is better."""
        score = 0.0

        # Has a primary language (focused codebase)
        if skill.language and skill.language != "":
            score += 0.25

        # Topics count: 2-8 is ideal (focused but descriptive)
        topics = json.loads(skill.topics) if skill.topics else []
        topic_count = len(topics)
        if 2 <= topic_count <= 8:
            score += 0.25
        elif topic_count == 1:
            score += 0.1
        elif topic_count > 8:
            score += 0.05  # too many = unfocused

        # Has a specific category (not uncategorized)
        if skill.category and skill.category != "uncategorized":
            score += 0.2

        # Size: smaller is more focused
        size_kb = skill.repo_size_kb or 0
        if 10 <= size_kb <= 500:
            score += 0.2  # sweet spot
        elif size_kb <= 5000:
            score += 0.1
        # large repos get no bonus

        # Has a clear name pattern (skill, tool, mcp, etc.)
        name_lower = skill.repo_name.lower()
        if any(kw in name_lower for kw in ["skill", "tool", "mcp", "agent", "plugin", "server"]):
            score += 0.1

        return min(score, 1.0)

    def _examples(self, skill: Skill) -> float:
        """Does the project have good examples and usage documentation?"""
        score = 0.0
        desc = (skill.description or "").lower()
        topics = json.loads(skill.topics) if skill.topics else []
        topics_lower = " ".join(topics).lower()

        # Description mentions examples or usage
        if any(kw in desc for kw in ["example", "usage", "demo", "tutorial", "getting started"]):
            score += 0.25

        # Topics mention examples
        if any(kw in topics_lower for kw in ["example", "tutorial", "demo", "starter"]):
            score += 0.15

        # README with code blocks (actual examples, not just size)
        content = (skill.readme_content or "")[:15000]
        code_blocks = len(re.findall(r"```", content)) // 2 if content else 0
        if code_blocks >= 3:
            score += 0.30  # multiple examples
        elif code_blocks >= 1:
            score += 0.20  # at least one example
        elif (skill.readme_size or 0) > 2000:
            score += 0.10  # large README but no code blocks

        # Has meaningful commit count (active development suggests documentation)
        if skill.total_commits > 50:
            score += 0.15
        elif skill.total_commits > 10:
            score += 0.1

        # Has contributors (multi-person = better docs usually)
        if skill.contributors_count > 3:
            score += 0.15
        elif skill.contributors_count > 1:
            score += 0.1

        return min(score, 1.0)

    def _agent_readiness(self, skill: Skill) -> float:
        """How ready is this skill for agent/LLM consumption? Returns 0-1.

        Inspired by Anthropic skill-creator evaluation + SkillsBench findings:
        - Functional quality (tool definitions, API docs)
        - Trigger quality (clear description for agent activation)
        - Structural quality (install, config, examples)
        """
        score = 0.0
        content = (skill.readme_content or "")[:10000]
        desc = skill.description or ""
        desc_lower = desc.lower()
        topics = json.loads(skill.topics) if skill.topics else []
        topics_lower = " ".join(topics).lower()
        name_lower = skill.repo_name.lower()

        # 1. Installation ready (max 0.15)
        if content and re.search(self.AGENT_SECTIONS["install"], content, re.MULTILINE):
            score += 0.15
        elif any(kw in desc_lower for kw in ["npm install", "pip install", "cargo install", "brew install"]):
            score += 0.10

        # 2. Tool/API definition documented (max 0.20)
        if content and re.search(self.AGENT_SECTIONS["tools"], content, re.MULTILINE):
            score += 0.20
        elif any(kw in desc_lower for kw in ["tool", "function", "api", "endpoint", "server"]):
            score += 0.10

        # 3. Usage examples (max 0.20)
        has_usage_section = bool(content and re.search(self.AGENT_SECTIONS["usage"], content, re.MULTILINE))
        code_blocks = len(re.findall(r"```", content)) // 2 if content else 0
        if has_usage_section:
            score += 0.10
        if code_blocks >= 2:
            score += 0.10
        elif code_blocks >= 1:
            score += 0.05

        # 4. Configuration documented (max 0.15)
        if content and re.search(self.AGENT_SECTIONS["config"], content, re.MULTILINE):
            score += 0.15
        elif any(kw in desc_lower for kw in [".env", "config", "settings"]):
            score += 0.08

        # 5. Skill/MCP compliance + frontmatter (max 0.15)
        compliance_text = f"{content} {topics_lower} {name_lower}"
        # YAML frontmatter with name/description (Waza-style standard)
        has_frontmatter = bool(content and re.search(
            r"^---\s*\n(?:.*\n)*?(?:name|description)\s*:", content[:500], re.MULTILINE
        ))
        if has_frontmatter:
            score += 0.08  # standardized skill definition
        if any(kw in compliance_text for kw in ["skill.md", "mcp.json", "tool-config"]):
            score += 0.04
        if any(kw in name_lower for kw in ["skill", "mcp", "tool", "agent", "server"]):
            score += 0.03

        # 6. Description quality for agent activation (max 0.15)
        if desc:
            # Action-oriented description (starts with verb or uses "for"/"that"/"to")
            action_words = ["a ", "an ", "the ", "create", "build", "generate", "manage",
                           "search", "fetch", "monitor", "analyze", "convert", "provide"]
            if any(desc_lower.startswith(w) for w in action_words) or \
               any(f" {w} " in f" {desc_lower} " for w in ["for", "that", "to"]):
                score += 0.10
            # Concise and clear (30-200 chars is ideal)
            if 30 <= len(desc) <= 200:
                score += 0.05
            elif len(desc) > 200:
                score += 0.02

        return min(score, 1.0)

    def _readme_structure(self, skill: Skill) -> float:
        """Analyze README content for structural quality. Returns 0-1.

        v3: Now penalizes overly verbose docs (paper Finding 6:
        Comprehensive Skills actually hurt performance by -2.9pp).
        """
        content = skill.readme_content
        if not content:
            return 0.0

        score = 0.0

        # Section detection (max 0.35): each valuable section +0.04, up to 8
        # Diminishing returns beyond 8 sections (paper: focused > exhaustive)
        sections_found = sum(
            1 for pattern in self.VALUABLE_SECTIONS
            if re.search(pattern, content, re.MULTILINE)
        )
        if sections_found <= 8:
            score += min(sections_found * 0.044, 0.35)
        else:
            score += 0.35  # cap: more sections don't help

        # Code blocks (max 0.25)
        code_blocks = len(re.findall(r"```", content)) // 2
        if code_blocks >= 3:
            score += 0.25
        elif code_blocks >= 1:
            score += 0.15
        elif "`" in content:
            score += 0.05

        # Badges (max 0.05, reduced from 0.1 — badges are cosmetic, not functional)
        if any(re.search(p, content) for p in [r"\[!\[", r"shields\.io", r"img\.shields"]):
            score += 0.05

        # Table of contents indicator (max 0.05)
        toc_count = sum(1 for p in [r"(?i)table of contents", r"(?i)## contents", r"\[.*\]\(#"]
                        if re.search(p, content))
        if toc_count >= 1:
            score += 0.05

        # Length adequacy — optimal range with diminishing returns
        # Paper Finding 6: Detailed (+18.8pp) > Compact (+17.1pp) > Comprehensive (-2.9pp)
        length = len(content)
        if 1000 <= length <= 5000:
            score += 0.20  # detailed: optimal range
        elif 5000 < length <= 10000:
            score += 0.15  # compact: still good
        elif 10000 < length <= 20000:
            score += 0.10  # standard: getting verbose
        elif length > 20000:
            score += 0.05  # comprehensive: diminishing returns
        elif length >= 300:
            score += 0.05  # minimal

        # Content-to-section ratio bonus (high density = focused)
        if sections_found > 0 and length > 0:
            avg_section_len = length / sections_found
            if 200 <= avg_section_len <= 1000:
                score += 0.05  # well-balanced sections

        return min(score, 1.0)

    def _procedural_content(self, skill: Skill) -> float:
        """Detect procedural content: step-by-step guides, workflows, SOPs.

        SkillsBench paper (Section 2.1): Skills must contain "procedural content"
        — how-to guidance, workflows, SOPs — not just factual descriptions.
        Paper shows curated procedural Skills improve pass rate by +16.2pp.
        """
        content = (skill.readme_content or "")[:15000]
        desc = (skill.description or "").lower()
        if not content and not desc:
            return 0.0

        score = 0.0

        # 1. Procedural section headings (max 0.20)
        if content:
            proc_sections = sum(
                1 for pattern in self.PROCEDURAL_PATTERNS[:2]  # step/workflow headings
                if re.search(pattern, content, re.MULTILINE)
            )
            score += min(proc_sections * 0.10, 0.20)

        # 2. Numbered/ordered steps in content (max 0.25)
        if content:
            # Count numbered list items: "1. ", "2. ", etc.
            numbered_items = len(re.findall(r"(?m)^\s*\d+\.\s+\w", content))
            if numbered_items >= 5:
                score += 0.25  # strong procedural structure
            elif numbered_items >= 3:
                score += 0.20
            elif numbered_items >= 1:
                score += 0.10

        # 3. Sequence/transition words (max 0.15)
        if content:
            seq_words = len(re.findall(
                r"(?i)\b(first|then|next|finally|after that|afterward|subsequently|lastly)\b",
                content
            ))
            if seq_words >= 4:
                score += 0.15
            elif seq_words >= 2:
                score += 0.10
            elif seq_words >= 1:
                score += 0.05

        # 4. Action/command verbs in content (max 0.15)
        if content:
            action_patterns = len(re.findall(
                r"(?i)\b(run|execute|invoke|call|create|configure|set up|install|deploy|start|stop|build)\b",
                content
            ))
            if action_patterns >= 6:
                score += 0.15
            elif action_patterns >= 3:
                score += 0.10
            elif action_patterns >= 1:
                score += 0.05

        # 5. Description indicates procedural nature (max 0.10)
        proc_desc_words = ["how to", "guide", "workflow", "step", "tutorial",
                          "walkthrough", "procedure", "instructions", "automate"]
        if any(w in desc for w in proc_desc_words):
            score += 0.10

        # 6. Code blocks with shell commands (max 0.15) — executable procedures
        if content:
            shell_blocks = len(re.findall(r"```(?:bash|sh|shell|zsh|console|terminal)", content))
            if shell_blocks >= 2:
                score += 0.15
            elif shell_blocks >= 1:
                score += 0.10
            else:
                # Generic code blocks also suggest procedural content
                generic_blocks = len(re.findall(r"```", content)) // 2
                if generic_blocks >= 2:
                    score += 0.05

        return min(score, 1.0)

    def _security_awareness(self, skill: Skill) -> float:
        """Evaluate security awareness in docs (ClawKeeper-inspired).

        Skills that document permissions, sandboxing, trust boundaries,
        and credential safety are more trustworthy for agent consumption.
        """
        content = (skill.readme_content or "")[:15000]
        desc = (skill.description or "").lower()
        topics = json.loads(skill.topics) if skill.topics else []
        topics_lower = " ".join(topics).lower()
        if not content and not desc:
            return 0.0

        score = 0.0

        # 1. Permission / security documentation (max 0.25)
        if content:
            perm_matches = sum(
                1 for p in self.SECURITY_AWARENESS_PATTERNS["permission_docs"]
                if re.search(p, content, re.MULTILINE)
            )
            score += min(perm_matches * 0.09, 0.25)

        # 2. Sandboxing / isolation mentions (max 0.20)
        if content:
            sandbox_matches = sum(
                1 for p in self.SECURITY_AWARENESS_PATTERNS["sandboxing"]
                if re.search(p, content)
            )
            score += min(sandbox_matches * 0.07, 0.20)

        # 3. Trust boundary awareness (max 0.20)
        if content:
            trust_matches = sum(
                1 for p in self.SECURITY_AWARENESS_PATTERNS["trust_boundaries"]
                if re.search(p, content)
            )
            score += min(trust_matches * 0.07, 0.20)

        # 4. Credential safety practices (max 0.20)
        combined = f"{content} {desc}"
        cred_matches = sum(
            1 for p in self.SECURITY_AWARENESS_PATTERNS["credential_safety"]
            if re.search(p, combined)
        )
        score += min(cred_matches * 0.07, 0.20)

        # 5. Threat model / compliance (max 0.15)
        if content:
            threat_matches = sum(
                1 for p in self.SECURITY_AWARENESS_PATTERNS["threat_model"]
                if re.search(p, content)
            )
            score += min(threat_matches * 0.05, 0.15)

        # Bonus: security-related topics (max 0.10)
        sec_topics = ["security", "safety", "sandbox", "privacy",
                      "auth", "permissions", "trust"]
        topic_bonus = sum(1 for t in sec_topics if t in topics_lower)
        score += min(topic_bonus * 0.05, 0.10)

        return min(score, 1.0)

    def _instruction_quality(self, skill: Skill) -> float:
        """Evaluate instruction quality based on SkillsBench paper criteria.

        Paper Section 2.4 evaluates instructions on 6 criteria:
        1. Explicit output paths
        2. Structured requirements
        3. Success criteria
        4. Constraints
        5. Context-first ordering

        These criteria correlate with Skill effectiveness in real benchmarks.
        """
        content = (skill.readme_content or "")[:15000]
        if not content:
            return 0.0

        score = 0.0

        # 1. Output paths documented (max 0.20)
        output_matches = sum(
            1 for pattern in self.INSTRUCTION_QUALITY_PATTERNS["output_paths"]
            if re.search(pattern, content)
        )
        score += min(output_matches * 0.07, 0.20)

        # 2. Success criteria defined (max 0.20)
        success_matches = sum(
            1 for pattern in self.INSTRUCTION_QUALITY_PATTERNS["success_criteria"]
            if re.search(pattern, content)
        )
        score += min(success_matches * 0.07, 0.20)

        # 3. Constraints documented (max 0.20)
        constraint_matches = sum(
            1 for pattern in self.INSTRUCTION_QUALITY_PATTERNS["constraints"]
            if re.search(pattern, content)
        )
        score += min(constraint_matches * 0.07, 0.20)

        # 4. Structured requirements — tables, typed parameters (max 0.20)
        struct_matches = sum(
            1 for pattern in self.INSTRUCTION_QUALITY_PATTERNS["structured_req"]
            if re.search(pattern, content, re.MULTILINE)
        )
        score += min(struct_matches * 0.07, 0.20)

        # 5. Context-first ordering — overview/introduction before details (max 0.20)
        # Check if README starts with context before jumping into code
        first_heading = re.search(r"^#{1,3}\s+(.+)", content, re.MULTILINE)
        if first_heading:
            context_matches = sum(
                1 for pattern in self.INSTRUCTION_QUALITY_PATTERNS["context_first"]
                if re.search(pattern, content[:2000], re.MULTILINE)
            )
            if context_matches > 0:
                score += 0.15
            # Also check if first code block appears after some text (not immediately)
            first_code = content.find("```")
            if first_code > 200:
                score += 0.05  # code after context = good ordering

        return min(score, 1.0)
