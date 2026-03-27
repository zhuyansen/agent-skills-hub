import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import { I18nProvider } from "./i18n/I18nContext";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Home } from "./pages/Home";
import { SkillDetailPage } from "./pages/SkillDetailPage";
import { ComparePage } from "./pages/ComparePage";
import { CompareBar } from "./components/CompareBar";
import { AdminLayout } from "./pages/admin/AdminLayout";
import { CategoryPage } from "./pages/CategoryPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";
import { AnalyzerPage } from "./pages/AnalyzerPage";

function StaticPage() {
  // For paths like /best/*, /category/*, /skill/* that have pre-rendered static HTML,
  // don't replace the content — just return null so the static HTML remains visible.
  return null;
}

function App() {
  // If we're on a static-only path (pre-rendered at build time), don't hydrate the SPA
  const path = window.location.pathname;
  const isStaticOnly = path.startsWith("/best/");

  if (isStaticOnly) {
    return <StaticPage />;
  }

  return (
    <ErrorBoundary>
      <AuthProvider>
        <ThemeProvider>
        <I18nProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/skill/:id" element={<SkillDetailPage />} />
              <Route path="/skill/:owner/:repo" element={<SkillDetailPage />} />
              <Route path="/category/:slug" element={<CategoryPage />} />
              <Route path="/compare" element={<ComparePage />} />
              <Route path="/analyzer" element={<AnalyzerPage />} />
              <Route path="/verify-email" element={<VerifyEmailPage />} />
              <Route path="/admin/*" element={<AdminLayout />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            <CompareBar />
          </BrowserRouter>
        </I18nProvider>
        </ThemeProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
