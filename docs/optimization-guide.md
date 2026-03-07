# Optimization Guide — Remaining Items

## #4 CDN Deployment (GitHub Pages → Cloudflare Pages / Vercel)

**Current**: `gh-pages` branch deployed via GitHub Pages — no CDN, no edge caching.

**Recommended**: Migrate to **Vercel** (simplest for Vite/React):

```bash
# Install Vercel CLI
npm i -g vercel

# From frontend/ directory:
vercel --prod
```

Or use **Cloudflare Pages**:
1. Go to https://dash.cloudflare.com → Pages → Create project
2. Connect your GitHub repo
3. Build settings:
   - Build command: `cd frontend && npm run build`
   - Output directory: `frontend/dist`
4. Automatic deploys on push to `main`

Both provide global CDN, automatic HTTPS, and preview deployments.

---

## #5 Admin Auth → Supabase Auth (replace hardcoded token)

**Current**: `ADMIN_TOKEN` env var checked via header.

**Migration steps**:
1. Create admin user in Supabase Dashboard → Authentication → Users
2. Add RLS policy on Supabase:
   ```sql
   -- Only admin emails can access admin endpoints
   CREATE POLICY admin_access ON skills FOR ALL
     USING (auth.jwt()->>'email' IN ('your-admin@email.com'));
   ```
3. Frontend: use `supabase.auth.signInWithPassword()` on admin login page
4. Backend: verify Supabase JWT in middleware:
   ```python
   from jose import jwt

   def verify_admin(token: str):
       payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
       return payload["email"] in ADMIN_EMAILS
   ```
5. Remove `ADMIN_TOKEN` from env

---

## #8 Edge Function for Landing Bundle

**Purpose**: Single Supabase Edge Function returns all homepage data in one request (trending + top-rated + categories + stats).

```typescript
// supabase/functions/landing-bundle/index.ts
import { createClient } from "@supabase/supabase-js";

Deno.serve(async () => {
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  const [trending, topRated, categories, stats] = await Promise.all([
    supabase.from("skills").select("*").order("star_momentum", { ascending: false }).limit(10),
    supabase.from("skills").select("*").order("score", { ascending: false }).limit(10),
    supabase.rpc("get_category_counts"),
    supabase.rpc("get_dashboard_stats"),
  ]);

  return new Response(JSON.stringify({
    trending: trending.data,
    topRated: topRated.data,
    categories: categories.data,
    stats: stats.data,
  }), { headers: { "Content-Type": "application/json" } });
});
```

Deploy: `supabase functions deploy landing-bundle`

---

## #9 LLM Classification (replace heuristic)

**Current**: Keyword-based `_classify()` in `data_cleaner.py`.

**Recommended**: Use Claude Haiku for batch classification after sync:
```python
import anthropic

client = anthropic.Anthropic()

def classify_skill(name: str, description: str, topics: list) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        messages=[{
            "role": "user",
            "content": f"Classify this GitHub repo into one category: mcp-server, claude-skill, agent-tool, llm-plugin, ai-skill, codex-skill, agent-framework, or tool.\n\nName: {name}\nDescription: {description}\nTopics: {', '.join(topics)}\n\nRespond with just the category name."
        }]
    )
    return response.content[0].text.strip()
```

Run as a post-sync batch job for uncategorized/low-confidence skills only.
Cost estimate: ~5000 skills × ~100 tokens = 500K tokens ≈ $0.05/run with Haiku.

---

## #11 User Analytics

**Recommended**: Self-hosted **Plausible** or **Umami**.

**Umami** (easier self-hosting):
1. Deploy via Docker: `docker run -d ghcr.io/umami-software/umami:latest`
2. Or use Umami Cloud (free tier: 10K events/month)
3. Add tracking script to `index.html`:
   ```html
   <script async src="https://your-umami.com/script.js" data-website-id="xxx"></script>
   ```

**Plausible** (privacy-first):
- Cloud: https://plausible.io ($9/month)
- Self-hosted: https://github.com/plausible/analytics

Both are GDPR-compliant, no cookie banners needed.

---

## #13 Favorites Sync (localStorage → Supabase)

**Schema**:
```sql
CREATE TABLE user_favorites (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  skill_id INTEGER REFERENCES skills(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, skill_id)
);

-- RLS: users can only manage their own favorites
ALTER TABLE user_favorites ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own favorites" ON user_favorites
  FOR ALL USING (auth.uid() = user_id);
```

**Frontend**: Keep localStorage as fallback for anonymous users. On login, merge local favorites with Supabase.

---

## #14 Skill Change Notifications

**Architecture**:
1. Track changes during sync: compare `prev_stars`, `score`, `last_commit_at`
2. Store in `skill_changes` table:
   ```sql
   CREATE TABLE skill_changes (
     id BIGSERIAL PRIMARY KEY,
     skill_id INTEGER REFERENCES skills(id),
     change_type VARCHAR(50), -- 'score_increase', 'new_release', 'trending'
     old_value TEXT,
     new_value TEXT,
     created_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```
3. Email digest via Supabase Edge Function + Resend/SendGrid:
   - Weekly digest for subscribed users
   - Immediate notification for favorited skills with major changes

---

## #17-18 Architecture Unification

**Current**: FastAPI backend (sync + admin API) + frontend reads Supabase directly.

**Recommended approach**: Keep FastAPI for sync/admin (server-side only), remove it from production serving path:

1. **Sync**: Keep as GitHub Actions job (already works)
2. **Admin**: Migrate to Supabase Edge Functions or keep FastAPI as internal service
3. **Frontend**: Already reads from Supabase directly — this is correct
4. **Remove SQLite**: Already done (using Supabase pooler)

The dual data source issue is already resolved since sync now writes to Supabase only (when `SUPABASE_DB_URL` is set). SQLite remains as local dev fallback.

No immediate action needed — the architecture is already converging.
