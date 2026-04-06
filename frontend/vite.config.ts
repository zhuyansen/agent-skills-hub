import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  // Custom domain (agentskillshub.top) → "/"
  // Without custom domain on GitHub Pages → "/agent-skills-hub/"
  base: "/",
  plugins: [react(), tailwindcss()],
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
