import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HelmetProvider } from 'react-helmet-async'
import './index.css'
import App from './App.tsx'

// Don't hydrate on static-only pages (pre-rendered at build time)
// These pages have their own HTML and don't need React
const isStaticOnlyPage = window.location.pathname.startsWith('/best/')

if (!isStaticOnlyPage) {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <HelmetProvider>
        <App />
      </HelmetProvider>
    </StrictMode>,
  )
}
