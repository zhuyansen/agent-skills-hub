# PostHog + First-Party Reverse Proxy Setup

Replaces Plausible in `agentskillshub.top` with PostHog Cloud (Free tier: 1M events/month, 5k session recordings) routed through a Cloudflare Worker reverse proxy to avoid ad-blocker loss on developer traffic.

## 1. Create a PostHog Project (1 min)
1. Sign up at <https://us.posthog.com> (free tier).
2. Create a project (e.g. `agentskillshub.top`).
3. Copy:
   - **Project API Key** (`phc_...`) from **Project Settings → General**
   - **Project ID** (numeric) from the project URL or **Project Settings → General**
4. Create a **Personal API Key** (`phx_...`) at **Account Settings → Personal API Keys** with scope **`query:read`** (used only by the daily GitHub Actions sweep).

## 2. Deploy the Cloudflare Worker Reverse Proxy (1 min)
```bash
cd ops/posthog/proxy
npx wrangler login
npx wrangler deploy
```
This gives you an endpoint like `https://agentskillshub-posthog-proxy.<your-handle>.workers.dev` (or map `e.agentskillshub.top/*` in `wrangler.toml` if your DNS is on Cloudflare). Neither URL contains `posthog`, so uBlock / Brave Shields let it through.

## 3. Enable in Frontend (2-line edit)
Edit [`frontend/public/ph.js`](../../frontend/public/ph.js):
```js
var POSTHOG_KEY = "phc_your_project_key";
var POSTHOG_HOST = "https://agentskillshub-posthog-proxy.<your-handle>.workers.dev";
```
Every page on the site (`index.html`, SPA routes, `/best/*`, `/skill/*`, `/author/*`, `/blog/*`, `/stats/`, `/book/*`, `/privacy/`, `/terms/`) already loads `/ph.js`.

## 4. Enable in Daily Analytics Digest (GitHub Secrets)
Add two repository secrets so [`.github/workflows/analytics-daily.yml`](../../.github/workflows/analytics-daily.yml) pulls daily HogQL metrics:
```bash
gh secret set POSTHOG_API_KEY --body "phx_..."
gh secret set POSTHOG_PROJECT_ID --body "12345"
# Optional if using EU Cloud:
# gh secret set POSTHOG_HOST --body "https://eu.posthog.com"
```
