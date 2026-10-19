import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { existsSync, readdirSync } from 'fs'
import { fileURLToPath } from 'url'

// /stats/ exists once its first monthly snapshot is committed (ops/stats/monthly_snapshot.py,
// the 1st of each month). Until then the app leaves its links out, so none points at a 404.
// The static-page generators ask the same question through scripts/stats-live.mjs.
const statsDir = fileURLToPath(new URL('./public/stats/data', import.meta.url))
const statsLive = existsSync(statsDir) && readdirSync(statsDir).some((f) => /^\d{4}-\d{2}\.json$/.test(f))

export default defineConfig({
  // Custom domain (agentskillshub.top) → "/"
  // Without custom domain on GitHub Pages → "/agent-skills-hub/"
  base: "/",
  plugins: [react(), tailwindcss()],
  define: {
    __STATS_LIVE__: JSON.stringify(statsLive),
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
