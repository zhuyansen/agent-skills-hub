# Where to find agent skills and MCP servers: directory facts (draft)

Status: complete draft, all 19 sites plus our own site, read 2026-11-09. Not committed. The summary table comes first; every claim in it is backed by a URL and quote in the per-site notes further down.

## How these facts were collected

- Every page was read on 2026-11-09 with curl through the local proxy (127.0.0.1:7897) and a generic desktop Chrome User-Agent. No logins.
- Only each site's own public pages, docs, `llms.txt`, its own GitHub repos and its own npm packages were used.
- "not stated" = not found on the site's own pages that were checked. It does not prove the thing doesn't exist.
- "blocked" = the site answered with a Cloudflare challenge, a Cloudflare block, a Vercel checkpoint or a 403. Nothing was done to get around it.
- "not verified" = we could not read it from the site itself (blocked site, or lobehub.com which we do not fetch).
- No traffic or visit numbers are recorded. Several sites print their own visitor counts or third-party SEO metrics (DR, backlinks) on advertise/submit pages. Those were deliberately left out.
- Quotes are kept short and exact. Counts are copied exactly, not rounded.

---

## Summary table

Counts are each site's own words and use different units (skills, repos, MCP servers, plugins), so they cannot be compared directly. "Per-item security" means a result shown on each listing; a scan that only gates entry is noted but is not a per-item result.

| # | Site | Lists | Catalog size (site's own words) | Per-item security result (basis) | Ranking | Getting listed (paid?) | Install path | Agent access | Open source | Freshness | Languages | Notable |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | skills.sh | Skills, packs | Not stated in words; tab reads "All Time (1,292,103)", unit unlabelled | Yes: pass / warn / fail per partner scanner (Gen Agent Trust Hub, Socket, Snyk; API also names Runlayer, ZeroLeaks). Skills failing every partner are excluded | Installs from CLI telemetry; all-time / trending / hot | Automatic once installed through the CLI; no form. Paid: not stated | `npx skills add owner/repo` | REST API, needs a Vercel OIDC token | CLI MIT (vercel-labs/skills); site repo not linked | Hourly dedup; otherwise not stated | EN | Run by Vercel |
| 2 | SkillsMP | blocked | not verified | not verified | not verified | not verified | not verified | not verified | not verified | not verified | not verified | Cloudflare challenge |
| 3 | ClawHub | Skills, OpenClaw plugins | Not stated | Yes: Pass / Review / Warn / Malicious, plus Low / Medium / High risk (SkillSpector, Tencent A.I.G, ClawScan review) | Featured / Trending / Official / New; downloads, stars | Self-publish with CLI after sign-in; moderated. Paid: not stated | `openclaw skills install …` or `clawhub install …` | Public read API (no token); CLI | Yes, MIT | Not stated | EN | OpenClaw Foundation |
| 4 | Anthropic (claude.com marketplace; claude.ai directory) | Plugins (skills only inside plugins); MCP connectors | "529 plugins"; "1095 connectors" | No grade. "Anthropic verified" label; scan + human review gate entry; "Verification isn't a security audit." | Installs shown; connectors "usage-based" | Developer portal; submitting needs a paid Claude plan | `/plugin install <name>@claude-plugins-official` | No public API; catalog JSON on GitHub | Catalog repo Apache-2.0 | Not stated | 7 (EN, JA, DE, FR, KO, IT, ES) | claude.ai/directory blocked for us |
| 5 | Glama | MCP servers, remote connectors, tools | "118,148 servers"; "42,492 remote connectors" | No security letter. License / quality / maintenance grades + TDQS; sandbox behaviour scan, "Risky" findings shown | 8 sorts (usage, npm/PyPI downloads, stars…); paid Boost gets priority | Auto-indexed + maintainer submit. Boost $49/mo; sponsored cards $200/mo | Config block; hosting | REST API (key + attribution required) | TDQS open source; data licensed | "updated daily"; re-scan per commit | 7 | "superset of the official MCP Registry" |
| 6 | mcp.so | MCP servers, clients, skills, agents, CLIs | Not stated | Not for servers (0–100 availability/quality score for hosted ones). Skill page data carries Gen / Socket / Snyk results | Stars / newest; Top 100 by demand + stars + checks; skills by skills.sh installs | Free reviewed submit, or $39 to skip review incl. a "Verified badge"; ads $699–$1,299/mo | README config; `npx skills add …` | Not stated | Repo Apache-2.0 (tie to live site not stated) | Daily quality checks | Switcher; full list not stated | "Verified" is a paid perk |
| 7 | PulseMCP | blocked | not verified | not verified | not verified | not verified | not verified | not verified | not verified | not verified | not verified | Cloudflare block |
| 8 | Smithery | MCP servers | "214 servers" | Not stated | Not stated | Not stated (accounts closed) | Vendor's direct MCP URL | API and CLI shut down 2026-10-31 | Not stated | Not stated | EN | "now part of Arcade"; proxy, hosting URLs, API, CLI, accounts ended 2026-10-31; registry stays |
| 9 | LobeHub (GitHub/npm only) | Agents, MCP servers, skills | not verified | No security scan described; MCP "Grade" from validation, install method, features, repo info | MCP: featured / installs / updated; skills: downloads / date / stars + ratings | MCP via market CLI; skills via GitHub repo. Paid: not stated | `npx -y @lobehub/market-cli skills install …` | Market CLI (MIT); API not verified | App under "LobeHub Community License" | not verified | Docs EN + zh-CN | lobehub.com not fetched |
| 10 | Tessl Registry | Skills, docs, rules | Not stated | Yes: Snyk severity (Passed / Advisory / Risky / Critical) + Quality % + Impact from evals | "Data-driven rankings" from evals; semantic search | Publish with CLI (account). Publishing free; evals use paid credits | `npx tessl i …` | Registry MCP server (search needs no auth); CLI | Not stated | Not stated | EN | Company (London) |
| 11 | Skills Directory | Skills | "717,866 indexed skills" (also "717,964", "over 100,000", "103,619 scanned") | Yes: A–F from a static scan of SKILL.md only | Recent / upvoted / viewed / stars; grade filter | Indexed + reviewed submissions. Pro $19 once or $4/mo; sponsors $399–$999/mo | Copy command; Pro ZIP | API (key; 100/day free); MCP for Pro | Not stated | "updated just now" | EN | Its own counts disagree |
| 12 | SkillsLLM | GitHub repos (skills, MCP, CLI…) | "6,682 Skills"; "6,699" catalog repos | Yes: PASS / WARNING / FAIL (Semgrep, npm audit, pip-audit, prompt-injection heuristics) | Stars / recent / name / votes | Daily crawl (100+ stars) + submit. Featured $49 or $99 per 30 days | `git clone`; ZIP | Not stated | Not stated | Daily crawl | EN | Sample item last scanned 7/16/2026 |
| 13 | Skillget | Skills, agents, workflows, MCP | "33635 results" | Yes: Pass / Fail (health, code patterns, permissions); no method page | New / trending / top rated / recently updated | Submit repo (GitHub sign-in). Paid: not stated | `npx @keremsolmaz/skillget install …` | Public API (60 per 15 min); CLI | CLI MIT | Many items "Last sync: Mar 30, 2026" | EN, TR | |
| 14 | Claude Marketplaces | Skills, MCP, marketplaces, plugins | "23,391 skills"; "7,783 servers"; "3,147 marketplaces"; "16063+ plugins" | None | Installs (from skills.sh) and stars | Crawlers + free submit; $4 priority review; sponsor slots $1,000–$1,200/mo | Copy command | `llms.txt` only | Not stated | "every day" | EN | One editor |
| 15 | agentskillshub.dev | MCP, skills, workflows (+ OpenClaw set) | "1,220" entries; OpenClaw "2,993" | Shows A–F letters but says they are "catalog metadata, not proof" of an audit | Grade-weighted formula; stars | Free manual review; paid submissions and commercial reviews | Install guidance | Not stated | Not stated | "Latest recorded scan 2026-05-20" | EN | Uses the name "Agent Skills Hub" |
| 16 | Skillselion | Skills, MCP, marketplaces | "59,762 skills indexed"; "82,124 tools" | Mirrors skills.sh audits ("2 / 3 scanners passed") | Skills by installs; MCP and marketplaces by stars | Automatic daily. Sponsored guide slots from $29/mo | "single command" | Public API + MCP, no key | Datasets CC BY 4.0 | Daily | EN, JA | Ellelion LLC |
| 17 | Skillstore | Skills, packs | "6945 Skills"; "5553 skills" | Yes: Safe … Critical + score; deterministic + semantic review | Recent / popular / recommended | Submit repo (anonymous OK); vendor audits, first one free | One command | MCP (no token for discovery) | Repo public, no license | Not stated | 11 | |
| 18 | cursor.directory | blocked; repo: plugins (rules, MCP, skills, agents, hooks, LSP) | not verified | Repo: AI scan safe / suspicious / malicious goes to an admin queue | not verified | Website submit (GitHub/Google sign-in) per repo | not verified | Admin-only MCP | Repo public, no license | not verified | not verified | Repo now under github.com/cursor |
| 19 | mcpservers.org | blocked; repo: MCP servers | not verified | not verified | not verified | Submit on website, no PRs (repo) | not verified | not verified | Awesome list MIT | not verified | not verified | |
| — | **Agent Skills Hub (ours)** | Skills, MCP servers, agent tools (GitHub repos) | "267,000+" (home) vs "186,000+" (About, Enterprise); "132,000+ graded" | Yes: Safe / Caution / Unsafe / Reject, or Unaudited; 43 rules on the README only | Data-driven score, stars, star velocity | Auto from GitHub + submit page; no pay-for-placement | Command from the README | MCP + CLI (npm, MIT); skill.md | Code MIT; dataset CC-BY-4.0 (DOI) | Every 8 hours | EN, ZH | Our own pages disagree (see notes) |

## What this means for an honest comparison (our reading of the facts above)

1. **A per-item security result is no longer unique to us.** Sites that show one: skills.sh, ClawHub, Tessl, Skills Directory, SkillsLLM, Skillget, Skillstore, and us. Skillselion and mcp.so mirror the skills.sh partner results. Anthropic and Glama scan as a gate or for behaviour, but show no security grade per item.
2. **Our scan reads the least.** We grade the README (first 15,000 characters) and nothing else. Skills Directory reads SKILL.md. skills.sh partners, ClawHub and Skillstore audit the skill's contents, and Glama runs each server in a sandbox. The fair claim is "a transparent, rule-based first pass over the widest set of GitHub repos", not "the deepest audit".
3. **Catalog numbers measure different things.** Ours counts GitHub repos, including general AI tools. skills.sh shows 1,292,103 with no unit, Skills Directory says 717,866 skills, Glama 118,148 MCP servers. The page should label units and avoid "largest".
4. **Fix our own pages first.** Our catalog size (267,000+ vs 186,000+), quality-score dimensions (6 vs 9 vs 10) and grade names disagree across pages. Skills Directory and Skillstore show the same kind of mismatch; we should not publish a comparison while ours stands.
5. **Name collision.** agentskillshub.dev calls itself "Agent Skills Hub" and shows A–F letters it says are not audits. The page should name both domains.
6. **Disclose the business model the way others do.** Our About page says there is no pay-for-placement tier, and we also have an Enterprise audit page. Glama, Skillstore, mcp.so and agentskillshub.dev state their paid audits or placements on their own pages.
7. **Shut down / paid.** Smithery ended its proxy, API, CLI and accounts on 2026-10-31 and is now a 214-server registry "part of Arcade". No directory is paid-only to browse, but submitting to Anthropic's directory needs a paid Claude plan, and Glama's and skills.sh's APIs need a key or token. mcp.so sells its "Verified" badge.
8. **Where we stand out on these pages:** MIT code plus a citable CC-BY dataset with a DOI, a free no-key MCP server and CLI, an 8-hour refresh and EN/ZH pages. Others match parts of this: ClawHub is MIT, Skillselion publishes CC BY datasets and a no-key API/MCP, Skillstore and Tessl offer agent search, and Glama and Skillstore cover more languages.

---

## Per-site notes

### 1. skills.sh (operated by Vercel)

- **What it lists:** agent skills, plus "packs" (bundles of skills).
  - https://www.skills.sh/about (read 2026-11-09): "skills.sh is the open directory for AI agent skills."
- **Catalog size:** not stated in words. The leaderboard tab shows a bare number with no unit.
  - https://www.skills.sh/ (read 2026-11-09): "All Time (1,292,103)". The page's embedded data calls this field `allTimeTotal`; the page does not say whether it counts skills.
  - https://www.skills.sh/docs/api (read 2026-11-09): "The unfiltered all-time list uses a 100,000-row serving window."
- **Security (per item):** yes. Each skill page shows a result per partner scanner.
  - https://www.skills.sh/vercel-labs/skills/find-skills (read 2026-11-09): "Gen Agent Trust Hub Pass", "Socket Pass", "Snyk Warn".
  - https://www.skills.sh/audits (read 2026-11-09): "Combined security audit results from Gen Agent Trust Hub, Socket, and Snyk."
  - https://www.skills.sh/docs/api (read 2026-11-09): partners listed as "Gen Agent Trust Hub, Socket, Snyk, Runlayer, ZeroLeaks"; verdicts "pass" (safe), "warn" (review recommended), "fail" (likely dangerous).
  - https://www.skills.sh/about (read 2026-11-09): "Skills that fail every partner audit are excluded from the directory entirely."
  - https://www.skills.sh/docs (read 2026-11-09): "routine security audits that assess skills and their contents for malicious content".
  - Basis: third-party partner scanners. skills.sh does not publish its own scanning method; the method belongs to each partner.
- **Ranking:** install counts from the `skills` CLI telemetry. Views: All Time, Trending (24h), Hot.
  - https://www.skills.sh/about (read 2026-11-09): "rank them by anonymous install telemetry"; "Deduplication runs hourly to prevent artificial inflation."
- **Getting listed:** automatic once people install the skill through the CLI. No submission form. Paid tier: not stated.
  - https://www.skills.sh/docs/faq (read 2026-11-09): "Skills appear on the leaderboard automatically through anonymous telemetry".
- **Installing:** `npx skills add <owner/repo>`.
  - https://www.skills.sh/docs/cli (read 2026-11-09): "npx skills add vercel-labs/agent-skills".
- **Agent access:** REST API under `/api/v1/` (list, search, curated, detail, audit). Authentication is a Vercel project OIDC token, so callers need an app deployed on Vercel or a linked Vercel project. 600 requests/minute.
  - https://www.skills.sh/docs/api (read 2026-11-09): "authenticate using the project's OIDC token".
- **Openness:** the CLI is open source (github.com/vercel-labs/skills). The About page also says the site and pipeline are open source, but no site repo link was found on the pages checked.
  - https://www.skills.sh/about (read 2026-11-09): "The CLI, the ingestion pipeline, and this site are open source."
  - https://www.skills.sh/docs (read 2026-11-09): "The skills CLI that powers this leaderboard is open source at github.com/vercel-labs/skills."
- **Freshness:** dedup hourly (above); "Hot" compares the last hour with the same hour yesterday (API docs). Catalog refresh frequency otherwise not stated.
- **Languages:** English only (`lang="en"`, no language switcher seen).
- **Notable:** CLI telemetry is on by default; opt-out with `DISABLE_TELEMETRY=1` (https://www.skills.sh/docs/cli, read 2026-11-09: "To opt out, set the DISABLE_TELEMETRY=1 environment variable.").

### 2. SkillsMP (skillsmp.com) — blocked

- https://skillsmp.com/ (read 2026-11-09): HTTP 403 with a Cloudflare "Just a moment..." challenge. Recorded as **blocked**; no further attempts.
- All fields: **not verified**.
- A GitHub repo `yan-labs/skillsmp` ("SkillsMP - Skills Marketplace") turns up in a GitHub search, but it has no homepage set and nothing ties it to skillsmp.com, so it was not used.

### 3. ClawHub (clawhub.ai, OpenClaw)

- **What it lists:** skills (SKILL.md bundles) and OpenClaw plugins (code plugins, bundle plugins), plus experimental Template packages.
  - https://docs.openclaw.ai/clawhub/ (read 2026-11-09): "ClawHub is the public registry for OpenClaw skills and plugins."
- **Catalog size:** not stated. (The homepage has a decorative scrolling ticker that reads "30 skills 12 plugins" next to strings like "/api/v1/skills /owners /audit /ship"; it is not presented as a catalog count and should not be cited as one.)
- **Security (per item):** yes. Each release gets an audit status and a risk level, with findings.
  - https://docs.openclaw.ai/clawhub/security-audits (read 2026-11-09): statuses "Pass", "Review", "Warn", "Malicious", "Pending", "Error"; risk levels Low / Medium / High.
  - Same page: "The audit page combines: SkillSpector, A.I.G, Risk analysis"; A.I.G is described as "Tencent Zhuque Lab's A.I.G scanner", feeding "ClawScan's artifact-wide review".
  - https://clawhub.ai/audits (read 2026-11-09): "Latest security audits for skills and plugins".
  - https://raw.githubusercontent.com/openclaw/clawhub/main/README.md (read 2026-11-09): "security analysis checks these declarations against actual skill behavior".
  - Method published: https://docs.openclaw.ai/clawhub/security-audits
- **Ranking:** homepage tabs Featured / Trending / Official / New; listings show downloads and stars; search is semantic.
  - https://clawhub.ai/ (read 2026-11-09): "Featured Trending Official New".
  - README (read 2026-11-09): "Search via embeddings (vector index) instead of brittle keywords."
- **Getting listed:** self-publish with the `clawhub` CLI after signing in (GitHub OAuth per README). Releases pass upload gates, automated checks and moderation. Paid tier: not stated.
  - https://docs.openclaw.ai/clawhub/how-it-works (read 2026-11-09): "subject to upload gates, automated checks, user reports, and moderator action."
- **Installing:** `openclaw skills install @openclaw/demo`, `openclaw plugins install clawhub:<package>`, or `clawhub install @openclaw/demo`.
  - https://docs.openclaw.ai/clawhub/ (read 2026-11-09): "openclaw skills install @openclaw/demo".
- **Agent access:** public read API, no token needed; OpenAPI schema; `clawhub search` CLI; `llms.txt`.
  - https://docs.openclaw.ai/clawhub/api (read 2026-11-09): "Public read: no token required."
  - https://clawhub.ai/llms.txt (read 2026-11-09): OpenAPI at https://clawhub.ai/api/v1/openapi.json
- **Openness:** open source, MIT. https://github.com/openclaw/clawhub
  - GitHub API for openclaw/clawhub (read 2026-11-09): license MIT; description "Skill + Plugin Registry for OpenClaw".
- **Freshness:** not stated.
- **Languages:** English (`lang="en"`); no other languages seen.
- **Notable:** third-party catalogs may reuse the API if they link back (https://docs.openclaw.ai/clawhub/how-it-works, read 2026-11-09: "when they link back to the canonical ClawHub listing"). Footer: "© 2026 OpenClaw Foundation".

### 4. Anthropic: Claude Marketplace (claude.com) and the Claude directory (claude.ai)

- **Access:** https://claude.ai/directory (read 2026-11-09) returned 403 with a Cloudflare "Just a moment..." challenge → **blocked**. https://claude.com/plugins redirects to https://claude.com/marketplace/plugins, which loaded. Docs on claude.com/docs and code.claude.com loaded.
- **What it lists:** plugins (bundles of skills, MCP connector references, commands, agents, hooks) and MCP connectors. Skills are not listed on their own.
  - https://claude.com/docs/directory/publish.md (read 2026-11-09): "Skills aren't a submission type on their own. Put them in a bundle."
- **Catalog size:** "529 plugins".
  - https://claude.com/marketplace/plugins (read 2026-11-09): "529 plugins".
- **Security (per item):** no per-item security grade is shown. Items carry an "Anthropic verified" label; connectors carry Verified / Community labels. Security scanning is a gate before listing, not a public score.
  - https://claude.com/docs/directory/publish.md (read 2026-11-09): "every version gets automated validation and a security scan".
  - https://claude.com/docs/connectors/directory.md (read 2026-11-09): "Verification isn't a security audit."
  - Method (what the scan checks): https://claude.com/docs/plugins/pre-submission-checklist.md
- **Ranking:** item pages show install counts; the connectors directory ranks by usage.
  - https://claude.com/marketplace/plugins/frontend-design (read 2026-11-09): "Installs 1,134,112".
  - https://claude.com/docs/connectors/directory.md (read 2026-11-09): "Ranking is usage-based, similar to other app stores".
- **Getting listed:** submit a GitHub repo through the developer portal (claude.ai/directory/manage); automated scan plus human review of new listings. Submitting needs a paid Claude plan. No listing fee is stated.
  - https://claude.com/docs/directory/publish.md (read 2026-11-09): "Anyone on a paid Claude plan can submit"; "Free accounts can't submit".
- **Installing:** in Claude Code `/plugin install <name>@claude-plugins-official`; in claude.ai via Customize > Plugins.
  - https://raw.githubusercontent.com/anthropics/claude-plugins-official/main/README.md (read 2026-11-09): "/plugin install {plugin-name}@claude-plugins-official".
  - https://claude.com/docs/plugins/overview.md (read 2026-11-09): "The directory's plugins appear on Pro, Max, Ultra, Team, and Enterprise plans."
- **Agent access:** no public search API stated. Inside Claude Code, the `/plugin` Discover tab searches the marketplaces; the catalog file is public on GitHub.
  - https://code.claude.com/docs/en/plugins/anthropic-marketplaces.md (read 2026-11-09): "That file is the catalog itself." (`.claude-plugin/marketplace.json`)
- **Openness:** the official marketplace catalog is a public GitHub repo, https://github.com/anthropics/claude-plugins-official (GitHub API, read 2026-11-09: license Apache-2.0; "Official, Anthropic-managed directory of high quality Claude Code Plugins."). There is also a community marketplace repo, anthropics/claude-plugins-community. Website code: not stated.
- **Freshness:** not stated. https://code.claude.com/docs/en/plugins/anthropic-marketplaces.md (read 2026-11-09): "The catalog changes often".
- **Languages:** the marketplace page links English, 日本語, Deutsch, Français, 한국어, Italiano, Español (https://claude.com/marketplace/plugins, read 2026-11-09).
- **Notable:** Anthropic says it does not review third-party marketplaces (https://code.claude.com/docs/en/plugins/anthropic-marketplaces.md, read 2026-11-09: "Anthropic doesn't review third-party marketplaces").

### 5. Glama (glama.ai, MCP)

- **What it lists:** MCP servers, remote MCP connectors, MCP clients, and the tools servers expose.
- **Catalog size:** 118,148 servers; 42,492 remote connectors; 1,285,498 tools.
  - https://glama.ai/mcp/servers (read 2026-11-09): "118,148 servers. Updated 2026-11-09 10:47".
  - https://glama.ai/llms.txt (read 2026-11-09): "118,148 Model Context Protocol servers and 42,492 remote connectors"; "1,285,498 tools".
- **Security (per item):** no letter "security" grade on listing cards. Cards show letter grades for license, quality and maintenance (e.g. "A license A quality B maintenance"), and server pages show a Tool Definition Quality Score (e.g. "TDQS A 4.1/5.0"). Behavioural scanning runs in a sandbox; "Risky" findings are shown on the listing and "Malicious" ones go to review or delisting.
  - https://glama.ai/mcp/methodology (read 2026-11-09): "The finding is surfaced on the server's public registry listing" (for "Risky" findings).
  - https://glama.ai/mcp/faq (read 2026-11-09): "automated quality checks (license detection, security scan, health test)".
  - Method published: https://glama.ai/mcp/methodology ; TDQS is open source at github.com/glama-ai/tool-definition-quality-score (stated on the methodology page).
- **Ranking:** sort by Search Relevance, Recent Usage, Date Added, Date Updated, Weekly npm Downloads, Weekly PyPI Downloads, GitHub Stars, Recent GitHub Stars (https://glama.ai/mcp/servers, read 2026-11-09). Paid "Boost" adds priority in default discovery (below).
- **Getting listed:** indexed from GitHub, the official MCP Registry and submissions; maintainers can submit via "Add MCP Server" (GitHub OAuth, must have write access to the repo). Paid placements exist.
  - https://glama.ai/llms.txt (read 2026-11-09): "indexed from GitHub, the official MCP Registry, and community submissions".
  - https://glama.ai/advertise (read 2026-11-09): "Boosted listings ( $49/month per listing)"; "Sponsored cards ( $200/month per category)"; "Payment changes placement. It does not affect our scores".
- **Installing:** copy a pre-filled client config; Glama also offers hosting, a gateway and an in-browser Inspector.
  - https://glama.ai/mcp/faq (read 2026-11-09): "ships with a pre-filled config block for both clients".
- **Agent access:** REST API with an API key; attribution required; OpenAPI document.
  - https://glama.ai/mcp/reference (read 2026-11-09): "Directory read endpoints require an API key."; "This data is licensed, not public domain."
- **Openness:** directory data is licensed (attribution rules). TDQS framework is open source. Registry code: not stated as public (the methodology page says codebases "live at github.com/glama-ai" without naming a registry repo).
- **Freshness:** "servers updated daily" (meta description of https://glama.ai/mcp/servers, read 2026-11-09); every new commit triggers a re-scan (https://glama.ai/mcp/methodology: "Every new commit and every rebuild triggers a full re-run").
- **Languages:** de, en, es, ja, ko, ru, zh (language links on https://glama.ai/mcp/servers/github/github-mcp-server, read 2026-11-09).
- **Notable:** describes itself as "A superset of the official MCP Registry" (https://glama.ai/llms.txt). Server pages carry labelled ads ("Ad").

### 6. mcp.so

- **What it lists:** MCP servers, remote servers, clients, CLI tools, "Loops", skills and agents (site navigation).
- **Catalog size:** not stated on the pages checked (only per-category counts in page data).
- **Security (per item):** no security grade for MCP servers. A separate "Quality Leaderboard" scores hosted servers 0–100 on availability/protocol/sign-in/tool descriptions (not a security scan). Skill pages carry partner audit results in their page data.
  - https://mcp.so/rankings (read 2026-11-09): "Hosted MCP servers scored 0–100 by mcp.so's own daily checks".
  - https://mcp.so/skills (read 2026-11-09): skills listed "with install commands, source repositories, use cases, and security information".
  - https://mcp.so/skills/frontend-design (read 2026-11-09): page data includes `securityAudits` "Gen Agent Trust Hub: Pass", "Socket: Pass", "Snyk: Pass" (the same partners skills.sh uses; mcp.so does not say where the results come from).
- **Ranking:** servers sort by GitHub stars or newest; Top 100 by search demand, stars and quality checks; skills by skills.sh installs.
  - https://mcp.so/servers (read 2026-11-09): "sort by GitHub stars or newest additions".
  - https://mcp.so/rankings (read 2026-11-09): "ranked by search demand, GitHub stars and our own quality checks"; "ranked by total installs reported by skills.sh".
- **Getting listed:** free submission with review, or a paid submission that skips review and includes a "Verified" badge.
  - https://mcp.so/ FAQ (read 2026-11-09): "Listings go live after review."
  - https://mcp.so/submit (read 2026-11-09): "$39 one-time publishing fee"; "Publish immediately without review"; "Verified badge"; "Featured and priority placement"; "Dofollow project link". Page meta: "Choose free review or publish immediately with Premium."
  - https://mcp.so/advertise (read 2026-11-09): "Platinum Sponsor $1,299 / month"; "Gold Sponsor $699 / month".
- **Installing:** server pages show a config block when one can be parsed from the README; skill pages show the `npx skills add ...` command.
  - https://mcp.so/skills/frontend-design (read 2026-11-09): "npx skills add https://github.com/anthropics/skills --skill frontend-design".
- **Agent access:** not stated.
- **Openness:** repo https://github.com/chatmcp/mcpso (GitHub API, read 2026-11-09: Apache-2.0, "directory for Awesome MCP Servers", homepage mcp.so). Whether it is the code of the current site: not stated.
- **Freshness:** rankings "updated as the underlying data changes"; quality checks daily (https://mcp.so/rankings, read 2026-11-09).
- **Languages:** has a "Switch language" control; the options are not in the server-rendered HTML. The ad form accepts English (required), Chinese and Japanese (https://mcp.so/advertise, read 2026-11-09). Full list: not stated.
- **Notable:** the "Verified" badge on mcp.so is part of the paid submission package.

### 7. PulseMCP (pulsemcp.com) — blocked

- https://www.pulsemcp.com/servers (read 2026-11-09): HTTP 403, Cloudflare "Sorry, you have been blocked". Recorded as **blocked**; no further attempts on pulsemcp.com.
- All directory fields: **not verified**.
- Its GitHub org (https://github.com/pulsemcp, read 2026-11-09 via GitHub API) has repos such as `pulsemcp/mcp-servers` ("MCP (Model Context Protocol) Servers authored and maintained by the PulseMCP team"), but none describe the directory, so nothing about the directory could be confirmed there.

### 8. Smithery (smithery.ai)

- **Status (confirmed from Smithery's own site):** Smithery is "now part of Arcade". On 2026-10-31 it shut down its proxy, managed identity, API, Connect, Toolbox, accounts, API keys, CLI and SDKs; it stays up only as a public, non-proxied registry.
  - https://smithery.ai/ (read 2026-11-09), page title: "Smithery · MCP servers, now part of Arcade".
  - https://smithery.ai/future (read 2026-11-09): "On October 31, 2026, we're shutting down Smithery's connection management services."
  - Same page: "Smithery will remain as a public (non-proxied) MCP registry."
  - Same page, under what stops working: "Smithery API, Connect, and Toolbox"; "Smithery accounts and API keys"; "The Smithery CLI and SDKs."; "Server URLs on run.tools and server.smithery.ai".
  - Same page: paid plans are refunded for charges "since August 5".
  - Wording note: the pages checked say "now part of Arcade" and "powered by Arcade.dev". The word "acquired" does not appear on them, so the comparison page should use Smithery's own wording.
- **What it lists:** MCP servers, plus Arcade toolkits.
- **Catalog size:** "214 servers" (https://smithery.ai/servers, read 2026-11-09).
- **Security (per item):** not stated.
- **Ranking:** not stated.
- **Getting listed:** not stated (accounts are shut down). The announcement mentions "A curated set of verified servers".
- **Installing:** registry pages show the vendor's direct MCP URL (https://smithery.ai/future: "registry pages will show direct MCP URLs").
- **Agent access:** API and CLI shut down on 2026-10-31 (above).
- **Openness:** not stated (footer GitHub link goes to github.com/ArcadeAI).
- **Freshness / Languages:** not stated / English.

### 9. LobeHub — lobehub.com not fetched; facts from LobeHub's GitHub and npm only

- **Rule followed:** lobehub.com was not fetched. Everything below comes from https://github.com/lobehub/lobehub (README and the `docs/` folder) and LobeHub's npm package. Anything that would need the live site is **not verified**.
- **What it lists:** agents, MCP servers, skills (and an AI/LLM icon set).
  - https://github.com/lobehub/lobehub README (read 2026-11-09): "Find agents, MCP servers and skills on lobehub.com".
- **Catalog size:** not verified.
  - docs/usage/community/mcp-market.mdx (read 2026-11-09): "Marketplace counts and rankings change over time."
- **Security (per item):** no security scan is described. MCP cards show a combined "Grade" that is not a security grade.
  - README (read 2026-11-09): MCP servers "rated on activity, stability and community feedback".
  - docs/usage/community/mcp-market.mdx (read 2026-11-09): grade "based on validation, installation method, features, and repository information".
- **Ranking:** MCP sorted "by featured status, installs, update time"; skills "by downloads, creation date, update time, name, or GitHub Stars", with ratings and reviews (docs/usage/community/mcp-market.mdx and skills-market.mdx, read 2026-11-09).
- **Getting listed:** MCP servers via the market CLI; skills by submitting a GitHub repo. Paid tier: not stated.
  - README (read 2026-11-09): "npx -y @lobehub/market-cli plugin submit https://github.com/OWNER/REPOSITORY".
- **Installing:** inside LobeHub with "Install MCP Server"; for other agents a CLI command.
  - docs/usage/community/skills-market.mdx (read 2026-11-09): "npx -y @lobehub/market-cli skills install <identifier> --agent codex".
- **Agent access:** the `@lobehub/market-cli` CLI (npm, MIT, v0.0.46 published 2026-10-30, description "LobeHub Marketplace CLI"). Public search API: not verified.
- **Openness:** the LobeHub app repo is under the "LobeHub Community License" (README, read 2026-11-09: "This project is [LobeHub Community License](./LICENSE) licensed."). The CLI's npm metadata points to `lobehub-biz/lobehub-market`; whether that repo is public: not verified.
- **Freshness:** not verified. **Languages:** the repo docs exist in English and zh-CN; site languages not verified.

### 10. Tessl Registry (tessl.io/registry)

- **What it lists:** skills, docs and rules (packaged as plugins).
  - https://tessl.io/registry/discover (read 2026-11-09): "Discover and install skills, docs, and rules".
- **Catalog size:** not stated.
- **Security (per item):** yes, a Snyk-powered result on each skill card, next to Tessl's own Quality and Impact (eval) scores.
  - https://tessl.io/registry (read 2026-11-09): "Automated vulnerability scanning powered by Snyk."; card example "Security by Passed No findings from the security scan".
  - https://docs.tessl.io/tutorials/protecting-against-insecure-skills.md (read 2026-11-09): severities "LOW, MEDIUM, HIGH, or CRITICAL", shown as "Passed", "Advisory", "Risky", "Critical".
  - Method published: the docs page above.
- **Ranking:** "Top performing" lists based on eval results; CLI search is semantic.
  - https://tessl.io/registry/discover (read 2026-11-09): "Data-driven rankings. Real results from real agents."
- **Getting listed:** publish with the Tessl CLI to a workspace and mark it public; Tessl account required. Publishing is free; reviews, evals and agent runs use credits (Free $0 with 1,000 credits/month; Team $100/month).
  - https://tessl.io/pricing (read 2026-11-09): "Publishing and installing plugins is always free".
  - https://docs.tessl.io/guides/distribute/sharing-plugins-publicly.md (read 2026-11-09): "Anyone can discover and install them via the Tessl Registry" (when `"private": false`).
- **Installing:** `npx tessl i github:anthropics/skills --skill docx` (https://tessl.io/registry, read 2026-11-09) or `tessl install <workspace>/<skillname>`.
- **Agent access:** Tessl Registry MCP server and CLI; search needs no auth.
  - https://docs.tessl.io/reference/mcp-tools.md (read 2026-11-09): "The registry MCP server exposes 27 tools"; `search` — "Not required" (authentication).
- **Openness / Freshness:** not stated / not stated.
- **Languages:** English.
- **Notable:** run by a company ("Tessl AI Ltd", London, per the registry footer).

### 11. Skills Directory (skillsdirectory.com)

- **What it lists:** agent skills.
- **Catalog size:** the site states several different numbers on the same day.
  - https://www.skillsdirectory.com/ (read 2026-11-09): "717,866 indexed skills · updated just now"; "Skills scanned 717,866".
  - https://www.skillsdirectory.com/pro (read 2026-11-09): "Download any of our 717,964 skills".
  - https://www.skillsdirectory.com/about (read 2026-11-09): "We index over 100,000 skills".
  - https://www.skillsdirectory.com/skills (read 2026-11-09), in a house ad: "Look up any of 103,619 scanned skills".
  - (The "38,681" next to `npx -y skills find` on the homepage is the GitHub star count of the skills CLI, not a catalog size.)
- **Security (per item):** yes, an A–F grade from a static scan of SKILL.md only; bundled scripts don't count toward the grade.
  - https://www.skillsdirectory.com/security/methodology (read 2026-11-09): "The grade covers SKILL.md."; A = 90–100 ... F = 0–39; "Sponsors ... cannot buy a security grade".
  - https://www.skillsdirectory.com/ (read 2026-11-09): "Detection patterns 120", "Threat categories 10".
  - Method published: https://www.skillsdirectory.com/security/methodology
- **Ranking:** sort by Most recent, Most upvoted, Most viewed, GitHub stars; filter by minimum grade (https://www.skillsdirectory.com/skills, read 2026-11-09).
- **Getting listed:** indexing plus a submit form behind sign-in; submissions are reviewed.
  - https://www.skillsdirectory.com/ (read 2026-11-09): "All submissions are reviewed before being published."
- **Paid tiers:** Pro "$19 once" or "$4/mo"; one skill "$2 once"; sponsor slots "$399/mo" and exclusive "$999/mo"; API Enterprise "$199/mo". The Pro page said "Priced for Thailand", so prices may vary by country (https://www.skillsdirectory.com/pro, /advertise, /api-docs, read 2026-11-09).
- **Installing:** copy the command from the skill page; Pro adds ZIP downloads.
  - https://www.skillsdirectory.com/about (read 2026-11-09): "copy the install command straight from any skill page".
- **Agent access:** REST API (key required; free 100 requests/day) and an MCP server for Pro members; a scan API for CI.
  - https://www.skillsdirectory.com/api-docs (read 2026-11-09): "All API requests require an API key."; "Pro members can connect Claude Code to Skills Directory."
- **Openness:** not stated.
- **Freshness:** "updated just now" (homepage).
- **Languages:** English.

### 12. SkillsLLM (skillsllm.com)

- **What it lists:** GitHub repos for AI skills, agents, MCP servers, CLI tools, IDE extensions.
- **Catalog size:** "6,682 Skills" on the homepage; "Catalog repositories 6,699" on the index page a few minutes later.
  - https://skillsllm.com/ (read 2026-11-09): "6,682 Skills".
  - https://skillsllm.com/insights/ai-skills-index (read 2026-11-09): "Catalog repositories 6,699" (catalog "read at: Mon, 09 Nov 2026 11:01:41 GMT").
- **Security (per item):** yes, a PASS / WARNING / FAIL badge from dependency audits and static/prompt-injection checks.
  - https://skillsllm.com/faq (read 2026-11-09): "Every skill is scanned daily by a CI workflow"; Semgrep, npm audit, pip-audit; "PASS, WARNING, or FAIL".
  - https://skillsllm.com/about (read 2026-11-09): "npm audit + pip-audit" and "prompt-injection heuristics".
  - Example: https://skillsllm.com/skill/rea (read 2026-11-09): "Last scanned: 7/16/2026".
- **Ranking:** sort by stars, recent, name; community votes (https://skillsllm.com/faq, read 2026-11-09: "sort by stars, recency, or community votes").
- **Getting listed:** daily GitHub crawl with a 100-star floor, plus submissions (GitHub OAuth). Paid featured placement.
  - https://skillsllm.com/about (read 2026-11-09): "Only repositories with 100+ stars are included."
  - https://skillsllm.com/sponsorship-policy (read 2026-11-09): "$49 USD for 30 days" (category), "$99 USD for 30 days" (homepage + category); needs a passing scan.
- **Installing:** mostly `git clone` (https://skillsllm.com/faq, read 2026-11-09: "installed by cloning the GitHub repository"); ZIP download on item pages.
- **Agent access:** not stated (a Chrome extension exists).
- **Openness:** not stated.
- **Freshness:** "Our scraper searches GitHub daily" (https://skillsllm.com/about, read 2026-11-09).
- **Languages:** English.

### 13. Skillget (skillget.dev)

- **What it lists:** skills, agents, workflows, MCP servers (GitHub repos).
- **Catalog size:** "33635 results" on Explore with no filters (https://skillget.dev/explore?lang=en, read 2026-11-09).
- **Security (per item):** yes, a "Security Audit" Pass / Fail with Health, Code and Permissions checks. No method page found.
  - https://skillget.dev/listings/n8n-io-n8n?lang=en (read 2026-11-09): "Security Audit Fail Mar 30, 2026"; code checks such as "execSync — Synchronous shell command execution".
- **Ranking:** sort New, Trending, Top rated, Recently updated; "Verified only" filter (https://skillget.dev/explore?lang=en, read 2026-11-09).
- **Getting listed:** "Submit Repo" (GitHub sign-in). Paid tier: not stated.
- **Installing:** `npx @keremsolmaz/skillget install <slug>` (https://skillget.dev/cli?lang=en, read 2026-11-09).
- **Agent access:** public API and CLI; rate limit stated in Turkish on the English page.
  - https://skillget.dev/cli?lang=en (read 2026-11-09): "GET /api/v1/search?q=mcp&type=mcp&sort=top&limit=10"; "Rate limit: 60 istek / 15 dakika."
- **Openness:** CLI is MIT on npm (@keremsolmaz/skillget 1.0.0, published 2026-03-30; repo listed as github.com/skillget/cli). Site: not stated.
- **Freshness:** per-item sync dates vary; several top items show "Last sync: Mar 30, 2026" (https://skillget.dev/, read 2026-11-09).
- **Languages:** English and Turkish (language menu "TR - Turkce", "EN - English").

### 14. Claude Marketplaces (claudemarketplaces.com)

- **What it lists:** Claude Code skills, MCP servers, plugin marketplaces and plugins.
- **Catalog size:**
  - https://claudemarketplaces.com/ (read 2026-11-09): "23,391 skills"; "7,783 servers"; "3,147 marketplaces".
  - https://claudemarketplaces.com/llms.txt (read 2026-11-09): "16063+ plugins indexed"; "Last updated: 2026-11-08".
- **Security (per item):** not stated; users are told to review code themselves.
  - https://claudemarketplaces.com/about (read 2026-11-09): "Users should review plugin code and repositories before installation".
- **Ranking:** installs and stars; skills show skills.sh install counts.
  - https://claudemarketplaces.com/ (read 2026-11-09): "ranked by real installs"; skill rows read e.g. "1.5M skills.sh installs".
- **Getting listed:** crawlers (skills.sh, GitHub, MCP registries) plus a free submit form behind GitHub sign-in; paid priority review; paid sponsor slots.
  - https://claudemarketplaces.com/submit (read 2026-11-09): "Submitting is free."; "priority review costs $4".
  - https://claudemarketplaces.com/ (read 2026-11-09): "Slot 1 $1,200/mo"; "Slot 2 $1,000/mo".
- **Installing:** copy the install command from the detail page (homepage FAQ, read 2026-11-09).
- **Agent access:** `llms.txt` only; API not stated.
- **Openness:** not stated.
- **Freshness:** "refreshed from GitHub every day" (https://claudemarketplaces.com/, read 2026-11-09).
- **Languages:** English.
- **Notable:** edited by one person (https://claudemarketplaces.com/about: "The directory is edited by Mert Düzgün"); "Not affiliated with Anthropic".

### 15. agentskillshub.dev (a different site that also calls itself "Agent Skills Hub")

- **Identity:** not us. It uses the same name on its own pages.
  - https://agentskillshub.dev/llms.txt (read 2026-11-09): "site_name: Agent Skills Hub".
- **What it lists:** MCP servers, agent skills and workflows, plus a separate OpenClaw skills dataset.
- **Catalog size:**
  - https://agentskillshub.dev/ (read 2026-11-09): "1,220 MCP skills, workflows, and integrations".
  - https://agentskillshub.dev/skills/ (read 2026-11-09): "Directory entries 1,220"; "Reviewed labels 1,005"; "Official entries 120".
  - https://agentskillshub.dev/ (read 2026-11-09): OpenClaw leaderboard from "2,993 cleaned OpenClaw skills".
- **Security (per item):** items show A–F letters, but the site itself says they are catalog metadata, not audit results.
  - https://agentskillshub.dev/ (read 2026-11-09): "stored grades are catalog metadata, not proof of a completed security audit".
  - https://agentskillshub.dev/review-methodology/ (read 2026-11-09): "Some import paths assign B and 80 points by default".
  - Method published: https://agentskillshub.dev/review-methodology/ (its interactive analyzer reads at most 14 files with five pattern groups).
- **Ranking:** the OpenClaw leaderboard uses a formula that starts from grade points (https://agentskillshub.dev/review-methodology/, read 2026-11-09: "starts from grade points (A 95, B 84, C 68, D 48, F 20)"); the directory has featured, trending, grade-A and stars views.
- **Getting listed:** free manual-review form; paid submissions and commercial review services also exist (price not stated).
  - https://agentskillshub.dev/submit/ (read 2026-11-09): "Submitting is free and does not guarantee a listing".
  - https://agentskillshub.dev/review-methodology/ (read 2026-11-09): "also offers commercial review services"; "Paid submissions may receive a scoped review workflow or placement window".
- **Installing:** per-page install guidance (homepage: "with source links and installation guidance").
- **Agent access / Openness:** not stated / not stated.
- **Freshness:** https://agentskillshub.dev/skills/ (read 2026-11-09): "Latest recorded scan 2026-05-20"; llms.txt "last_verified: 2026-08-03".
- **Languages:** English.

### 16. Skillselion (skillselion.com)

- **What it lists:** agent skills, MCP servers, plugin marketplaces, workflows.
- **Catalog size:**
  - https://skillselion.com/ (read 2026-11-09): "59,762 skills indexed"; "Last updated November 9, 2026".
  - https://skillselion.com/llms.txt (read 2026-11-09): "82,124 tools indexed in total: 59,433 agent skills, 9,894 MCP servers, 12,797 plugin marketplaces".
- **Security (per item):** shows the skills.sh partner audit result, not its own scan.
  - https://skillselion.com/skills/vercel-labs/skills/find-skills (read 2026-11-09): "Security audit 2 / 3 scanners passed", source "skills.sh audit".
- **Ranking:** skills by installs (from skills.sh), MCP servers and marketplaces by GitHub stars.
  - https://skillselion.com/AGENTS.md (read 2026-11-09): "Skills are ranked by installs; MCP servers and marketplaces are ranked by GitHub stars."
- **Getting listed:** automatic daily sync; a submission form: not stated. Paid sponsored guide slots that don't change ranking.
  - https://skillselion.com/about (read 2026-11-09): "refreshed daily from the skills.sh registry, GitHub and MCP registries".
  - https://skillselion.com/advertise (read 2026-11-09): "$29 every month, $69 every 3 months, or $99 every 6 months"; "It does not change search ranking".
- **Installing:** https://skillselion.com/ (read 2026-11-09): "Install with a single command."
- **Agent access:** public API and remote MCP server, no key.
  - https://skillselion.com/AGENTS.md (read 2026-11-09): "Public API (no auth)"; MCP "Streamable HTTP, no sign-in or API key."
- **Openness:** research datasets are free to reuse (https://skillselion.com/about, read 2026-11-09: "free to reuse with attribution under CC BY 4.0"). Site code: not stated.
- **Freshness:** daily (about page, above).
- **Languages:** English and Japanese (language link "日本語").
- **Notable:** https://skillselion.com/AGENTS.md (read 2026-11-09): "Operated by Ellelion LLC."

### 17. Skillstore (skillstore.io)

- **What it lists:** skills and curated skill packs for Claude, Codex and Claude Code.
- **Catalog size:** two numbers on the same day.
  - https://skillstore.io/about (read 2026-11-09): "6945 Skills".
  - https://skillstore.io/skills (read 2026-11-09): "5553 skills".
- **Security (per item):** yes, a risk label with a score (e.g. "Safe 92"); filter levels Safe / Low Risk / Medium Risk / High Risk / Critical.
  - https://skillstore.io/ (read 2026-11-09): "universal-audit Safe 92".
  - https://skillstore.io/security (read 2026-11-09, page "Methodology 2026-07-14"): "The audit combines deterministic inspection with semantic review."; "Public means a Skill is approved for the public catalog. It is not a safety pass."
  - Method published: https://skillstore.io/security
- **Ranking:** sort Recent, Popular, Recommended (https://skillstore.io/skills, read 2026-11-09).
- **Getting listed:** submit a GitHub repo URL; anonymous submission allowed; scripts get extra review. Vendors can buy audits; first audit free; prices not stated.
  - https://skillstore.io/submit (read 2026-11-09): "Skills with scripts will undergo additional security review".
  - https://skillstore.io/verified (read 2026-11-09): "Get your first audit free"; "Paying for an audit never buys a passing result."
- **Installing:** https://skillstore.io/ (read 2026-11-09): "one command for Claude, Codex & Claude Code".
- **Agent access:** MCP server; discovery needs no token.
  - https://skillstore.io/agents (read 2026-11-09): "Public discovery does not require a token."; endpoint https://skillstore.io/api/mcp
- **Openness:** repo https://github.com/aiskillstore/marketplace (GitHub API, read 2026-11-09: no license detected). Site code: not stated.
- **Freshness:** not stated.
- **Languages:** 11 (https://skillstore.io/about, read 2026-11-09: "11 Languages"; hreflang: ar, de, en, es, fr, ja, ko, pt, ru, zh-Hans, zh-Hant).

### 18. cursor.directory — blocked (facts from its GitHub repo only)

- https://cursor.directory/ (read 2026-11-09): HTTP 429 "Vercel Security Checkpoint", "We're verifying your browser". Recorded as **blocked**.
- Its repo: the GitHub API request for `pontusab/directories` returned `cursor/community-plugins` (homepage cursor.directory), so the repo now lives under the `cursor` GitHub org. README: https://raw.githubusercontent.com/cursor/community-plugins/main/README.md (read 2026-11-09).
- **What it lists (README):** "The directory of plugins from the Cursor community." Auto-detected parts: rules, MCP servers, skills, agents, hooks, LSP servers.
- **Getting listed (README):** "All content is submitted through the website — no pull requests needed for data."; sign in with GitHub or Google and paste a repo URL.
- **Security (README):** submissions are reviewed by an AI agent with a "safe / suspicious / malicious" verdict that "surfaces in the admin queue". The README does not say the verdict is shown publicly.
- **Agent access (README):** the MCP server at `/api/mcp` is for admins only ("requires the user to be an admin").
- **Openness:** public repo; GitHub API reports no license.
- Catalog size, ranking, install path, freshness, languages: **not verified**.

### 19. mcpservers.org — blocked (facts from its GitHub repo only)

- https://mcpservers.org/ (read 2026-11-09): HTTP 403, Cloudflare "Just a moment..." challenge. Recorded as **blocked**.
- Its repo https://github.com/wong2/awesome-mcp-servers (GitHub API, read 2026-11-09: homepage https://mcpservers.org, license MIT, "A curated list of Model Context Protocol (MCP) servers").
  - README (read 2026-11-09): "We do not accept PRs. Please submit your MCP on the website".
  - README has a "Sponsors" section.
- All other fields: **not verified**.

### 20. MCPYP / MCP Yellow Pages (mcpyp.com, read 2026-11-17)

- **Run by:** Oasis Education Inc. (`© 2026 Oasis Education Inc.` in footer, https://mcpyp.com/).
- **What it lists:** Remote MCP servers with public endpoints.
  - https://mcpyp.com/#/why (read 2026-11-17): "We list remote MCP servers only — a server with no public endpoint can't be independently probed, so it isn't listed."
- **Catalog size:** 12,754 servers listed and probed; 46,933 servers in full census; 161,533 tools measured; 200,199 checks recorded (https://mcpyp.com/#/why, read 2026-11-17).
- **Security (per item):** No safety certification; publishes dated liveness and live tool-run evidence (`Verified`, `Stable`, `Trial`, `Untested`).
  - https://mcpyp.com/#/why (read 2026-11-17): "we never certify a server 'safe'. We present risk evidence; the decision stays yours." Aligned with OWASP MCP Top 10, NIST AI RMF, MITRE ATLAS, and ISO/IEC 42001.
- **Ranking:** Measured order, Most tools, or Random (`#sortSelect`). "Payment never buys a score, a label, or a rank. Sponsored placement is labelled and kept out of the measured ranking."
- **Getting listed:** Free submission with manual review and ownership verification (`#/publish`); listing is always free and never for sale (`#/services`, `#/terms`). Paid options: manual Pre-integration check Pilot, labelled Sponsored visibility, and upcoming Intelligence API / Enterprise admission.
- **Agent access:** Free REST API (`https://api.mcpyp.com/v1/find`, `/v1/mcp/{name_or_slug}`, `/v1/config/{name_or_slug}`, `/v1/explore`, `/v1/refine`, `/v1/pick`) and streamable-HTTP Meta-MCP (`https://api.mcpyp.com/mcp`, 6 read-only tools), no API key needed (`limit` max 100, `offset` max 100).
- **Openness:** "Our standards and definitions are open for anyone to audit" (`#/why`); Terms section 3 forbids bulk scraping or catalog redistribution; no source repo linked.
- **Freshness:** "re-tested continuously"; "measured history is earned daily" (`#/why`; HTTP `last-modified: Tue, 17 Nov 2026 18:09:36 GMT`).
- **Languages:** 3 (English, 中文, Français in `#langSelect`).

### Ours: Agent Skills Hub (agentskillshub.top)

Recorded from our own public pages the same way as everyone else, so the comparison holds us to the same standard.

- **What it lists:** GitHub repos for agent skills, MCP servers and agent tools.
- **Catalog size:** our pages disagree.
  - https://agentskillshub.top/ (read 2026-11-09): "open-source directory of 267,000+ AI agent skills, MCP servers and agent tools"; "132,000+ graded so far".
  - https://agentskillshub.top/about/ (read 2026-11-09, page says "Last updated: 2026-04-24"): "186,000+ indexed skills".
  - https://agentskillshub.top/enterprise/ (read 2026-11-09): "Audit 186,000+ open-source agent skills and MCP servers".
  - https://agentskillshub.top/llms.txt (read 2026-11-09): Hugging Face dataset with "130,173 graded skills/servers".
- **Security (per item):** yes. Safe / Caution / Unsafe / Reject, or Unaudited; 43 published rules applied to the README only.
  - https://agentskillshub.top/how-we-grade/ (read 2026-11-09): "The README, its first 15,000 characters"; "We do not run the code, and we do not read the repository's other files."
  - https://agentskillshub.top/skill/anthropics/skills/ (read 2026-11-09): "Security audit verdict: SAFE · quality 62/100".
  - Method published: https://agentskillshub.top/how-we-grade/ ; free analyzer at https://agentskillshub.top/analyzer/
- **Ranking:** data-driven scores, stars and star velocity; no manual curation of ranking.
  - https://agentskillshub.top/ (read 2026-11-09): "No manual curation is applied to ranking".
- **Getting listed:** automatic from GitHub search patterns, plus a submit page. No pay-for-placement tier; an Enterprise page exists (prices not in the page HTML).
  - https://agentskillshub.top/about/ (read 2026-11-09): "Every GitHub repository matching our search patterns flows through a 6-phase pipeline"; "no \"pay for placement\" tier".
  - https://agentskillshub.top/submit/ (read 2026-11-09): "Submit a Skill, compose a Workflow, or apply for Verified Creator."
- **Installing:** the README's own command (https://agentskillshub.top/skill/anthropics/skills/, read 2026-11-09: "Taken from the project's README on GitHub.").
- **Agent access:** MCP server, CLI and skill.md.
  - https://agentskillshub.top/llms.txt (read 2026-11-09): "MCP server: `npx -y @agentskillshub/mcp`"; "CLI: `npx @agentskillshub/cli search <query>`".
  - npm (read 2026-11-09): @agentskillshub/mcp 0.3.0 and @agentskillshub/cli 0.5.0, both MIT.
- **Openness:** code MIT at https://github.com/zhuyansen/agent-skills-hub (GitHub API, read 2026-11-09: license MIT); dataset "DOI 10.5281/zenodo.21292799 (CC-BY-4.0)" (homepage).
- **Freshness:** "refreshed from GitHub every 8 hours" (homepage).
- **Languages:** English and Chinese (homepage link "中文版"; hreflang zh).
- **Self-consistency problems found on our own pages (fix before the comparison goes live):**
  1. Catalog size: "267,000+" (home) vs "186,000+" (About, last updated 2026-04-24; Enterprise).
  2. Quality score: home says "a 0–100 composite score across six dimensions"; the skill page says "nine heuristic checks"; About says "The 10-dimension quality score" and then lists six items.
  3. Grade names: home lists "SAFE, CAUTION, UNSAFE, or UNAUDITED"; How we grade lists Safe, Caution, Unsafe, Reject plus Unaudited; llms.txt lists "SAFE / CAUTION / UNSAFE / REJECT".
  4. Home says "Every indexed repository carries a security grade" while also saying 132,000+ of 267,000+ are graded. The rest carry "Unaudited", which How we grade defines as "Not graded yet".
  5. About still says "Verified Creator decisions (Q2 2026 launch)".
