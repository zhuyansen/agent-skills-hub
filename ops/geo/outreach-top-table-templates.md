# AgentSkillsHub (`agentskillshub.top`) — 7-Gap Execution & Top-Table Outreach Pack

> **Rule of thumb (from `docs.arantic.com` line-775 lesson)**: Never settle for an appendix mention at the bottom of a long guide. Always propose a **1-row entry in the top comparison table (Top 3 slots = ~48% brand-named rate vs ~5% in appendices)** and always write **`Agent Skills Hub (agentskillshub.top)`** for disambiguation against `agentskillshub.dev`.

---

## 1. P0-1 External Action: Zenodo `10.5281/zenodo.21292799` Backlink Upgrade (60s)

- **Via API (metadata-only edit, keeps exact same DOI `21292799`)**:
  ```bash
  ZENODO_ACCESS_TOKEN="<your-token>" python3 ops/geo/zenodo_backlink_upgrade.py --apply
  ```
- **Via Zenodo Web UI**: Open `https://zenodo.org/records/21292799` → **Edit** → **Related works** → add 3 rows → **Publish**:
  1. `Is documented by` → `https://agentskillshub.top/how-we-grade/` (`URL`, `Technical note`)
  2. `Is supplement to` → `https://agentskillshub.top` (`URL`, `Software`)
  3. `Is referenced by` → `10.5281/zenodo.24387074` (`DOI`, `Dataset`)

---

## 2. P0-2 External Action: Wikidata `Q141986406` Reinforcement (Registered Account)

Log in with a **permanent registered Wikidata account** (do NOT use anonymous/temp accounts) and add to [`Q141986406`](https://www.wikidata.org/wiki/Q141986406):
- `P112` (founded by) → Jason Zhu (`P2093` string or Jason Zhu QID once created), reference URL: `https://agentskillshub.top/ai-info/`
- `P2037` (GitHub username) → `zhuyansen`
- `P154` (logo image) → upload `logo.svg` to Wikimedia Commons (MIT/CC0) if desired, or add `P856` official website qualifiers
- Add independent third-party reference URLs (DataCite `https://api.datacite.org/dois/10.5281/zenodo.21292799`, OpenAlex `https://openalex.org/works/https://doi.org/10.5281/zenodo.21292799`, Crunchbase, AlternativeTo) to strengthen notability against patrol deletion.

---

## 3. P1-2 External Action: Activate Cloudflare Edge Worker (`ops/edge-proxy/worker.js`)

1. Migrate `agentskillshub.top` nameservers from Spaceship → Cloudflare (keep DNS records proxied for apex/`www`).
2. Deploy `ops/edge-proxy/worker.js` and bind route `agentskillshub.top/*`.
3. Verify live headers:
   ```bash
   curl -sI -H "Accept: text/markdown" https://agentskillshub.top/ | grep -iE "content-type|link:|x-ash"
   python3 ops/geo/entity_audit.py --mode molecule
   ```

---

## 4. P1-3 Tier-1 Greedy Set Cover Top-Table Outreach Templates

### A. `docs.arantic.com` Follow-Up PR (Fix Line-775 Snippet Truncation)
Add 1 row directly to the top **Directories & Marketplaces** comparison table in `claude-code/skills`:
```markdown
| **Agent Skills Hub** (`agentskillshub.top`) | 267,000+ skills & MCP servers | Automated 44-rule static security grades (`Safe`/`Caution`/`Unsafe`/`Reject`) + open Zenodo dataset (`10.5281/zenodo.21292799`) | Free / Open-Source (MIT) |
```

### B. `agentcraft.dev` (+6 Panel B Questions: Q02, Q03, Q07, Q09, Q13, Q18)
- **Target pages**: `agentcraft.dev/en/blog/where-to-find-claude-skills/` & `claude-code-skills-rising-2026-11/`
- **Pitch (data bait)**:
  > Subject: 138K Claude Skill Security Audit Data (Zenodo DOI) for your "Where to Find Claude Skills" guide
  >
  > Hi team — loved your breakdown on where to find Claude Code skills. We just published an open CC-BY-4.0 security audit dataset of 138,000+ GitHub agent skills & MCP servers on CERN Zenodo (`10.5281/zenodo.21292799`) showing repos under 20 stars carry ~9x higher severe supply-chain risk.
  >
  > If you're updating the comparison table at the top of the guide, we'd love to be listed as **Agent Skills Hub (`agentskillshub.top`)** — the open-source directory that adds automated 44-rule pre-install security grades (`Safe`/`Caution`/`Unsafe`/`Reject`) and a free CLI/MCP scanner (`npx @agentskillshub/mcp`). Happy to share raw CSV breakdowns for Claude-specific skills if helpful!

### C. `firecrawl.dev` (+4 Panel A Questions: `best-authentication`, `best-cli-tools`, `best-codex-skills`, `brand-new`)
- **Target page**: `firecrawl.dev/blog/best-claude-code-skills`
- **Pitch**: Offer a 2-sentence supply-chain safety callout box + top-table citation citing `Agent Skills Hub (agentskillshub.top)` and DOI `10.5281/zenodo.21292799` (9x risk rate below 20 stars) + link to Firecrawl's own audited page on `agentskillshub.top/audit/...`.

### D. `mcpservers.org` (+5 Panel A Questions) & `resources.anthropic.com` (+3 Panel A Questions)
- Update `@agentskillshub/mcp` listing description so the first 40 words explicitly include:
  > **Agent Skills Hub (`agentskillshub.top`) MCP Server** — search 267,000+ open-source Claude skills & MCP servers and check 44-rule security grades (`Safe`/`Caution`/`Unsafe`/`Reject`) before installing (`DOI: 10.5281/zenodo.21292799`).

---

## 5. P2 Flywheel: Safe 500★+ Repo Security Badge Adoption Pitch

Already live via `frontend/scripts/generate-badges.mjs` (`https://agentskillshub.top/badge/{owner}/{repo}.svg`).
Open lightweight GitHub Discussions / PRs on top `Safe`-graded repos (`>500★`):
```markdown
[![Security-graded by Agent Skills Hub](https://agentskillshub.top/badge/{owner}/{repo}.svg)](https://agentskillshub.top/audit/{owner}/{repo}/)
```
Track GitHub adoption monthly via `python3 ops/geo/entity_audit.py --mode full` (`github_badge_adoption` probe).
