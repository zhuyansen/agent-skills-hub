import { useCallback, useEffect, useState } from "react";
import {
  adminApproveExtraRepo,
  adminCreateExtraRepo,
  adminDeleteExtraRepo,
  adminFetchExtraRepos,
  adminRejectExtraRepo,
} from "../../api/client";
import type { ExtraRepoData } from "../../types/skill";

interface Props {
  token: string;
}

const statusBadge: Record<string, string> = {
  pending: "bg-yellow-50 text-yellow-700 border-yellow-200",
  approved: "bg-green-50 text-green-700 border-green-200",
  rejected: "bg-red-50 text-red-700 border-red-200",
};

export function ExtraReposPage({ token }: Props) {
  const [repos, setRepos] = useState<ExtraRepoData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [newRepo, setNewRepo] = useState("");
  const [filter, setFilter] = useState<"all" | "pending" | "approved" | "rejected">("all");

  const load = useCallback(() => {
    setLoading(true);
    adminFetchExtraRepos(token)
      .then(setRepos)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const handleAdd = async () => {
    if (!newRepo.includes("/")) return;
    try {
      await adminCreateExtraRepo(token, newRepo.trim());
      setNewRepo("");
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleApprove = async (id: number) => {
    try {
      await adminApproveExtraRepo(token, id);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleReject = async (id: number) => {
    try {
      await adminRejectExtraRepo(token, id);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Remove ${name}?`)) return;
    try {
      await adminDeleteExtraRepo(token, id);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const filtered = filter === "all" ? repos : repos.filter((r) => r.status === filter);
  const pendingCount = repos.filter((r) => r.status === "pending").length;

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Submissions & Extra Repos</h2>
        {pendingCount > 0 && (
          <span className="px-2 py-0.5 text-xs font-bold bg-yellow-100 text-yellow-700 rounded-full">
            {pendingCount} pending
          </span>
        )}
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>}

      {/* Add new repo */}
      <div className="flex gap-2 mb-4">
        <input
          value={newRepo}
          onChange={(e) => setNewRepo(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          placeholder="owner/repo (e.g. joeseesun/skill-publisher)"
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
        />
        <button
          onClick={handleAdd}
          className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Add
        </button>
      </div>

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
                <th className="text-left px-4 py-3 font-medium text-gray-500">Full Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Submitted</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                    No submissions found
                  </td>
                </tr>
              )}
              {filtered.map((r) => (
                <tr key={r.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <a
                      href={`https://github.com/${r.full_name}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-blue-600 hover:text-blue-800 hover:underline"
                    >
                      {r.full_name}
                    </a>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${statusBadge[r.status] || statusBadge.pending}`}>
                      {r.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {new Date(r.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      {r.status === "pending" && (
                        <>
                          <button
                            onClick={() => handleApprove(r.id)}
                            className="px-2.5 py-1 text-xs font-medium bg-green-50 text-green-700 rounded-md hover:bg-green-100 border border-green-200 transition-colors"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => handleReject(r.id)}
                            className="px-2.5 py-1 text-xs font-medium bg-red-50 text-red-600 rounded-md hover:bg-red-100 border border-red-200 transition-colors"
                          >
                            Reject
                          </button>
                        </>
                      )}
                      {r.status === "rejected" && (
                        <button
                          onClick={() => handleApprove(r.id)}
                          className="px-2.5 py-1 text-xs font-medium bg-green-50 text-green-700 rounded-md hover:bg-green-100 border border-green-200 transition-colors"
                        >
                          Approve
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(r.id, r.full_name)}
                        className="px-2.5 py-1 text-xs text-red-500 hover:text-red-700"
                      >
                        Delete
                      </button>
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
