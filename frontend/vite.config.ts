import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { existsSync, readFileSync, readdirSync } from 'fs'
import { fileURLToPath } from 'url'

// /stats/ exists once its first monthly snapshot is committed (ops/stats/monthly_snapshot.py,
// the 1st of each month). Until then the app leaves its links out, so none points at a 404.
// The static-page generators ask the same question through scripts/stats-live.mjs.
const statsDir = fileURLToPath(new URL('./public/stats/data', import.meta.url))
const statsLive = existsSync(statsDir) && readdirSync(statsDir).some((f) => /^\d{4}-\d{2}\.json$/.test(f))

// How many tools each guide's own test covers, for the home page hero: counted here from the
// test data the guide itself is built from, so the hero cannot state a stale number.
const runsPath = fileURLToPath(new URL('./scripts/scenario-runs.json', import.meta.url))
const guideRuns: Record<string, { runs?: Record<string, unknown> }> = JSON.parse(readFileSync(runsPath, 'utf-8'))
const guideTested = Object.fromEntries(
  Object.entries(guideRuns).map(([slug, run]) => [slug, Object.keys(run.runs ?? {}).length]),
)

export default defineConfig({
  // Custom domain (agentskillshub.top) → "/"
  // Without custom domain on GitHub Pages → "/agent-skills-hub/"
  base: "/",
  plugins: [react(), tailwindcss()],
  define: {
    __STATS_LIVE__: JSON.stringify(statsLive),
    __GUIDE_TESTED__: JSON.stringify(guideTested),
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          recharts: ["recharts"],
          "react-vendor": ["react", "react-dom", "react-router-dom"],
        },
      },
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
