import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  // For GitHub Pages: /agent-skills-hub/
  // For local dev: /
  base: process.env.GITHUB_ACTIONS ? "/agent-skills-hub/" : "/",
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
