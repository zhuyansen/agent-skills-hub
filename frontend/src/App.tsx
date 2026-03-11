import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { I18nProvider } from "./i18n/I18nContext";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Home } from "./pages/Home";
import { SkillDetailPage } from "./pages/SkillDetailPage";
import { ComparePage } from "./pages/ComparePage";
import { CompareBar } from "./components/CompareBar";
import { AdminLayout } from "./pages/admin/AdminLayout";
import { CategoryPage } from "./pages/CategoryPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <I18nProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/skill/:id" element={<SkillDetailPage />} />
              <Route path="/skill/:owner/:repo" element={<SkillDetailPage />} />
              <Route path="/category/:slug" element={<CategoryPage />} />
              <Route path="/compare" element={<ComparePage />} />
              <Route path="/verify-email" element={<VerifyEmailPage />} />
              <Route path="/admin/*" element={<AdminLayout />} />
            </Routes>
            <CompareBar />
          </BrowserRouter>
        </I18nProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
