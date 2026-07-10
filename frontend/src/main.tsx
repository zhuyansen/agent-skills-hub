import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { HelmetProvider } from "react-helmet-async";
import "@fontsource-variable/inter/index.css"; // self-hosted Inter (bundled; works in CN)
import "./index.css";
import App from "./App.tsx";

// ── Resilience against browser translation extensions ────────────────────────
// Chrome Translate / 沉浸式翻译 (Immersive Translate) wrap and relocate text
// nodes. When React then commits a subtree swap (e.g. the newsletter form → its
// success state on subscribe) it calls removeChild/insertBefore on a node the
// extension moved → DOMException "…is not a child of this node" → the whole app
// crashes into the ErrorBoundary ("出问题了"). Soft-guard both natives to no-op
// gracefully instead of throwing. Standard React workaround (facebook/react#11538).
// The deeper fix is full Chinese i18n so users don't reach for browser translate.
if (typeof Node === "function" && Node.prototype) {
  const originalRemoveChild = Node.prototype.removeChild;
  Node.prototype.removeChild = function <T extends Node>(
    this: Node,
    child: T,
  ): T {
    if (child.parentNode !== this) return child;
    return originalRemoveChild.call(this, child) as T;
  };
  const originalInsertBefore = Node.prototype.insertBefore;
  Node.prototype.insertBefore = function <T extends Node>(
    this: Node,
    newNode: T,
    referenceNode: Node | null,
  ): T {
    if (referenceNode && referenceNode.parentNode !== this) return newNode;
    return originalInsertBefore.call(this, newNode, referenceNode) as T;
  };
}

// Don't hydrate on static-only pages (pre-rendered at build time)
// These pages have their own HTML and don't need React
const isStaticOnlyPage = window.location.pathname.startsWith("/best/");

if (!isStaticOnlyPage) {
  // index.html carries a static <meta name="description"> so non-JS crawlers
  // and og scrapers always see one. Once React mounts, Helmet owns the tag
  // (language-aware zh/en) — drop the static copy or the page serves two.
  document.querySelector('meta[name="description"]:not([data-rh])')?.remove();
  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <HelmetProvider>
        <App />
      </HelmetProvider>
    </StrictMode>,
  );
}
