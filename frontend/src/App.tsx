import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import { I18nProvider } from "./i18n/I18nContext";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Home } from "./pages/Home";
import { CompareBar } from "./components/CompareBar";

const SkillDetailPage = lazy(() =>
  import("./pages/SkillDetailPage").then((m) => ({
    default: m.SkillDetailPage,
  })),
);
const CategoryPage = lazy(() =>
  import("./pages/CategoryPage").then((m) => ({ default: m.CategoryPage })),
);
const ComparePage = lazy(() =>
  import("./pages/ComparePage").then((m) => ({ default: m.ComparePage })),
);
const AnalyzerPage = lazy(() =>
  import("./pages/AnalyzerPage").then((m) => ({ default: m.AnalyzerPage })),
);
const VerifyEmailPage = lazy(() =>
  import("./pages/VerifyEmailPage").then((m) => ({
    default: m.VerifyEmailPage,
  })),
);
const VerifiedCreatorApplicationPage = lazy(() =>
  import("./pages/VerifiedCreatorApplicationPage").then((m) => ({
    default: m.VerifiedCreatorApplicationPage,
  })),
);
const SubmitPage = lazy(() =>
  import("./pages/SubmitPage").then((m) => ({ default: m.SubmitPage })),
);
const AuthorPage = lazy(() =>
  import("./pages/AuthorPage").then((m) => ({ default: m.AuthorPage })),
);
const BookIndexPage = lazy(() =>
  import("./pages/BookIndexPage").then((m) => ({ default: m.BookIndexPage })),
);
const BookChapterPage = lazy(() =>
  import("./pages/BookChapterPage").then((m) => ({
    default: m.BookChapterPage,
  })),
);
const AdminLayout = lazy(() =>
  import("./pages/admin/AdminLayout").then((m) => ({ default: m.AdminLayout })),
);
const EnterprisePage = lazy(() =>
  import("./pages/EnterprisePage").then((m) => ({
    default: m.EnterprisePage,
  })),
);
const FavoritesPage = lazy(() =>
  import("./pages/FavoritesPage").then((m) => ({ default: m.FavoritesPage })),
);
const ProPage = lazy(() => import("./pages/ProPage"));
const ProBoardPage = lazy(() => import("./pages/ProBoardPage"));

const PAGE_FALLBACK = (
  <div className="flex items-center justify-center min-h-[60vh]">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
  </div>
);

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ThemeProvider>
          <I18nProvider>
            <BrowserRouter>
              <Suspense fallback={PAGE_FALLBACK}>
                <Routes>
                  <Route path="/" element={<Home />} />
                  <Route path="/skill/:id" element={<SkillDetailPage />} />
                  <Route
                    path="/skill/:owner/:repo"
                    element={<SkillDetailPage />}
                  />
                  <Route path="/category/:slug" element={<CategoryPage />} />
                  <Route path="/compare" element={<ComparePage />} />
                  <Route path="/analyzer" element={<AnalyzerPage />} />
                  <Route path="/analyzer/" element={<AnalyzerPage />} />
                  <Route path="/verify-email" element={<VerifyEmailPage />} />
                  <Route
                    path="/verified-creator"
                    element={<Navigate to="/enterprise/" replace />}
                  />
                  <Route
                    path="/verified-creator/"
                    element={<Navigate to="/enterprise/" replace />}
                  />
                  <Route
                    path="/verified-creator/apply"
                    element={<VerifiedCreatorApplicationPage />}
                  />
                  <Route
                    path="/verified-creator/apply/"
                    element={<VerifiedCreatorApplicationPage />}
                  />
                  <Route path="/pro/board" element={<ProBoardPage />} />
                  <Route path="/pro/board/" element={<ProBoardPage />} />
                  <Route path="/pro" element={<ProPage />} />
                  <Route path="/pro/" element={<ProPage />} />
                  <Route path="/submit" element={<SubmitPage />} />
                  <Route path="/submit/" element={<SubmitPage />} />
                  <Route
                    path="/business"
                    element={<Navigate to="/enterprise/" replace />}
                  />
                  <Route
                    path="/business/"
                    element={<Navigate to="/enterprise/" replace />}
                  />
                  <Route path="/author/:username" element={<AuthorPage />} />
                  <Route path="/author/:username/" element={<AuthorPage />} />
                  {/* Organizations get their own namespace; AuthorPage detects
                      the route and renders Organization schema/labels. */}
                  <Route
                    path="/organization/:username"
                    element={<AuthorPage />}
                  />
                  <Route
                    path="/organization/:username/"
                    element={<AuthorPage />}
                  />
                  <Route path="/book" element={<BookIndexPage />} />
                  <Route path="/book/" element={<BookIndexPage />} />
                  <Route path="/book/:slug" element={<BookChapterPage />} />
                  <Route path="/book/:slug/" element={<BookChapterPage />} />
                  <Route path="/admin/*" element={<AdminLayout />} />
                  <Route path="/arena" element={<Navigate to="/" replace />} />
                  <Route path="/arena/" element={<Navigate to="/" replace />} />
                  <Route path="/enterprise" element={<EnterprisePage />} />
                  <Route path="/enterprise/" element={<EnterprisePage />} />
                  <Route path="/favorites" element={<FavoritesPage />} />
                  <Route path="/favorites/" element={<FavoritesPage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Suspense>
              <CompareBar />
            </BrowserRouter>
          </I18nProvider>
        </ThemeProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
