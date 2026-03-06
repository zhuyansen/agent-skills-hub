import { useCallback, useEffect, useState } from "react";
import {
  adminCreateExtraRepo,
  adminDeleteExtraRepo,
  adminFetchExtraRepos,
} from "../../api/client";
import type { ExtraRepoData } from "../../types/skill";

interface Props {
  token: string;
}

export function ExtraReposPage({ token }: Props) {
  const [repos, setRepos] = useState<ExtraRepoData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [newRepo, setNewRepo] = useState("");

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

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Remove ${name}?`)) return;
    try {
      await adminDeleteExtraRepo(token, id);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Extra Repos</h2>

      {error && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>}

      <div className="flex gap-2 mb-6">
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

      {loading ? (
        <div className="text-sm text-gray-400">Loading...</div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Full Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Added</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              {repos.map((r) => (
                <tr key={r.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{r.full_name}</td>
                  <td className="px-4 py-3 text-gray-500">{new Date(r.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(r.id, r.full_name)}
                      className="text-xs text-red-500 hover:text-red-700"
                    >
                      Remove
                    </button>
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
