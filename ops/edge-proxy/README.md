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
