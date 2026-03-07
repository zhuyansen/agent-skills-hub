import { useCallback, useEffect, useState } from "react";
import {
  adminFetchMasterApplications,
  adminApproveMasterApplication,
  adminRejectMasterApplication,
} from "../../api/client";

interface MasterApplicationData {
  id: number;
  github: string;
  name: string;
  bio: string | null;
  repo_urls: string;
  status: string;
  created_at: string;
}

interface Props {
  token: string;
}

const statusBadge: Record<string, string> = {
  pending: "bg-yellow-50 text-yellow-700 border-yellow-200",
  approved: "bg-green-50 text-green-700 border-green-200",
  rejected: "bg-red-50 text-red-700 border-red-200",
};

export function MasterApplicationsPage({ token }: Props) {
  const [apps, setApps] = useState<MasterApplicationData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<"all" | "pending" | "approved" | "rejected">("all");

  const load = useCallback(() => {
    setLoading(true);
    adminFetchMasterApplications(token)
      .then(setApps)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const handleApprove = async (id: number) => {
    try {
      await adminApproveMasterApplication(token, id);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleReject = async (id: number) => {
    try {
      await adminRejectMasterApplication(token, id);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const filtered = filter === "all" ? apps : apps.filter((a) => a.status === filter);
  const pendingCount = apps.filter((a) => a.status === "pending").length;

  const parseRepoUrls = (urls: string): string[] => {
    try {
      return JSON.parse(urls);
    } catch {
      return urls ? [urls] : [];
    }
  };

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Master Applications</h2>
        {pendingCount > 0 && (
          <span className="px-2 py-0.5 text-xs font-bold bg-yellow-100 text-yellow-700 rounded-full">
            {pendingCount} pending
          </span>
        )}
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>}

      {/* Filter tabs */}
      <div className="flex gap-1 mb-4 bg-gray-100 rounded-lg p-0.5 w-fit">
        {(["all", "pending", "approved", "rejected"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              filter === f ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
            {f === "pending" && pendingCount > 0 && ` (${pendingCount})`}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-sm text-gray-400">Loading...</div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500">GitHub</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Bio</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Repos</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Submitted</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                    No applications found
                  </td>
                </tr>
              )}
              {filtered.map((a) => (
                <tr key={a.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <a
                      href={`https://github.com/${a.github}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-blue-600 hover:text-blue-800 hover:underline"
                    >
                      @{a.github}
                    </a>
                  </td>
                  <td className="px-4 py-3 text-gray-700">{a.name}</td>
                  <td className="px-4 py-3 text-gray-500 max-w-48 truncate">{a.bio || "-"}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col gap-0.5">
                      {parseRepoUrls(a.repo_urls).map((url, i) => (
                        <a
                          key={i}
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-500 hover:text-blue-700 truncate max-w-40 block"
                        >
                          {url.replace(/https?:\/\/github\.com\//, "")}
                        </a>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${statusBadge[a.status] || statusBadge.pending}`}>
                      {a.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {new Date(a.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {a.status === "pending" && (
                        <>
                          <button
                            onClick={() => handleApprove(a.id)}
                            className="px-2.5 py-1 text-xs font-medium bg-green-50 text-green-700 rounded-md hover:bg-green-100 border border-green-200 transition-colors"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleReject(a.id)}
                            className="px-2.5 py-1 text-xs font-medium bg-red-50 text-red-600 rounded-md hover:bg-red-100 border border-red-200 transition-colors"
                          >
                            Reject
                          </button>
                        </>
                      )}
                      {a.status === "rejected" && (
                        <button
                          onClick={() => handleApprove(a.id)}
                          className="px-2.5 py-1 text-xs font-medium bg-green-50 text-green-700 rounded-md hover:bg-green-100 border border-green-200 transition-colors"
                        >
                          Approve
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
