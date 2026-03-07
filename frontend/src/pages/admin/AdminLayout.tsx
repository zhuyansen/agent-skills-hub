import { useState } from "react";
import { MastersPage } from "./MastersPage";
import { ExtraReposPage } from "./ExtraReposPage";
import { SearchQueriesPage } from "./SearchQueriesPage";
import { SkillsPage } from "./SkillsPage";
import { SubscribersPage } from "./SubscribersPage";
import { SyncPage } from "./SyncPage";

type AdminTab = "masters" | "skills" | "repos" | "queries" | "subscribers" | "sync";

const TABS: { key: AdminTab; label: string }[] = [
  { key: "masters", label: "Masters" },
  { key: "skills", label: "Skills" },
  { key: "repos", label: "Extra Repos" },
  { key: "queries", label: "Search Queries" },
  { key: "subscribers", label: "Subscribers" },
  { key: "sync", label: "Sync" },
];

export function AdminLayout() {
  const [token, setToken] = useState(() => localStorage.getItem("admin_token") || "");
  const [tokenInput, setTokenInput] = useState(token);
  const [tab, setTab] = useState<AdminTab>("masters");
  const [authenticated, setAuthenticated] = useState(!!token);

  const handleLogin = () => {
    if (tokenInput.trim()) {
      setToken(tokenInput.trim());
      localStorage.setItem("admin_token", tokenInput.trim());
      setAuthenticated(true);
    }
  };

  const handleLogout = () => {
    setToken("");
    setTokenInput("");
    localStorage.removeItem("admin_token");
    setAuthenticated(false);
  };

  if (!authenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-xl shadow-lg border border-gray-200 w-full max-w-md">
          <h1 className="text-xl font-bold text-gray-900 mb-1">Admin Login</h1>
          <p className="text-sm text-gray-500 mb-6">Enter your admin token to continue</p>
          <input
            type="password"
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            placeholder="Admin token..."
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={handleLogin}
            className="w-full mt-4 px-4 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Login
          </button>
          <a
            href="/"
            className="block mt-4 text-center text-sm text-gray-400 hover:text-gray-600"
          >
            Back to Home
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <a href="/" className="text-gray-400 hover:text-gray-600 text-sm">Home</a>
            <span className="text-gray-300">/</span>
            <h1 className="text-lg font-bold text-gray-900">Admin</h1>
          </div>
          <button
            onClick={handleLogout}
            className="px-3 py-1.5 text-xs text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
          >
            Logout
          </button>
        </div>
        {/* Tab nav */}
        <div className="max-w-7xl mx-auto px-4 flex gap-1 border-t border-gray-100">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                tab === t.key
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {tab === "masters" && <MastersPage token={token} />}
        {tab === "skills" && <SkillsPage token={token} />}
        {tab === "repos" && <ExtraReposPage token={token} />}
        {tab === "queries" && <SearchQueriesPage token={token} />}
        {tab === "subscribers" && <SubscribersPage token={token} />}
        {tab === "sync" && <SyncPage token={token} />}
      </main>
    </div>
  );
}
