# Brief: "Is this skill safe to install?" — Agent Skills Hub, October 2026

Audience: engineering managers deciding which open-source AI agent skills their team may install.
Length: 8 to 10 slides. Tone: clear, factual, no hype.

## 1. The problem
Teams now install third-party "skills" (SKILL.md folders, MCP servers, plugins) into Claude Code, Codex and other agents. A skill runs with the agent's permissions, but most are installed after a glance at the README.

## 2. What Agent Skills Hub does
- Indexes 186,000+ GitHub repositories of agent skills, MCP servers and agent tools, refreshed every 8 hours.
- Security-grades every skill with a fetched README: SAFE, CAUTION, UNSAFE or UNAUDITED.
- Grading covers 11 red-flag categories, including credential harvesting, data exfiltration and `curl | sh` installers.
- Coverage: 93% of skills over 100 stars and 98% over 1,000 stars are graded.

## 3. A worked example: 205 PPT skills
| Route | How it works | Entries |
|---|---|---|
| Native PPTX | writes the PowerPoint file | 98 |
| Web slides | writes HTML and CSS | 55 |
| Image-first | an image model paints each slide | 7 |
Of the 9 PPT skills flagged CAUTION or UNSAFE, all 9 are flagged for how they install (sudo, curl | sh), none for what they do while making slides.

## 4. How to choose a skill
1. Pick by who touches the output next (a colleague who edits, you presenting, a social post).
2. Check four things: does it plan the story, does it keep one layout system, is the output editable, does it check its own work.
3. Check the security grade before you install.

## 5. Call to action
Look up any skill at agentskillshub.top before installing it; paste a GitHub URL for a free check.
