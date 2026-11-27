# AgentSkillsHub Edge Proxy (Cloudflare Worker)

GitHub Pages serves static files directly and does not support:
- Content negotiation (`Accept: text/markdown` -> `Content-Type: text/markdown; charset=utf-8`)
- Custom HTTP response headers such as RFC 8288 `Link` headers on `/`

This Worker sits in front of `agentskillshub.top/` (once DNS is on Cloudflare with Orange Cloud proxy enabled) and adds both capabilities while passing every other route straight through to GitHub Pages.

## Deploy (once DNS is moved from Spaceship to Cloudflare)

1. Move `agentskillshub.top` nameservers at Spaceship to Cloudflare (Free plan) and keep the four GitHub Pages A records (`185.199.108-111.153`) with Proxy status **Proxied** (orange cloud), SSL/TLS mode **Full (strict)**.
2. Uncomment the `routes` block in `wrangler.toml`.
3. Deploy:
   ```bash
   cd ops/edge-proxy
   npx wrangler deploy
   ```
4. Verify:
   ```bash
   curl -sI https://agentskillshub.top/ | grep -i '^link:'
   curl -sI -H 'Accept: text/markdown' https://agentskillshub.top/ | grep -i '^content-type:'
   ```

## Gone audit pages → skill pages (2026-11)

`auditGoneRedirect` in `worker.js`: when GitHub Pages answers 404 for `/audit/<owner>/<repo>/` (the build stopped writing that audit page, usually a SAFE repo under 500 stars) and `/skill/<owner>/<repo>/` exists, the Worker answers `301` to the skill page, which shows the same grade. Any other 404 is passed through unchanged, and `/best/*` is never touched. Bingbot's own fetches in the KV log (11-22 to 11-25) hit 86 such 404s out of 293 audit URLs.

`bot-ranges.js` also carries Bing's published Bingbot ranges (`https://www.bing.com/toolbox/bingbot.json`), so Bingbot rows in the KV log say `verified` or `unverified_ip` instead of `no_cidr_list`.

Nothing deploys this Worker automatically. After review: `cd ops/edge-proxy && node --test worker.test.mjs && npx wrangler deploy`, then check one gone URL, e.g. `curl -sI https://agentskillshub.top/audit/bitwarden/mcp-server/` should answer `301` with `location: https://agentskillshub.top/skill/bitwarden/mcp-server/`.
