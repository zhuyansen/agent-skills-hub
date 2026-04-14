import { useCallback, useEffect, useState } from "react";
import {
  adminCreateSearchQuery,
  adminDeleteSearchQuery,
  adminFetchSearchQueries,
} from "../../api/client";
import type { SearchQueryData } from "../../types/skill";

interface Props {
  token: string;
}

export function SearchQueriesPage({ token }: Props) {
  const [queries, setQueries] = useState<SearchQueryData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [newQuery, setNewQuery] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    adminFetchSearchQueries(token)
      .then(setQueries)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  const handleAdd = async () => {
    if (!newQuery.trim()) return;
    try {
      await adminCreateSearchQuery(token, newQuery.trim());
      setNewQuery("");
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Remove this search query?")) return;
    try {
      await adminDeleteSearchQuery(token, id);
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    }
  };

  return (
    <div>
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Search Queries
      </h2>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">
          {error}
        </div>
      )}

      <div className="flex gap-2 mb-6">
        <input
          value={newQuery}
          onChange={(e) => setNewQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          placeholder="e.g. mcp-server in:name,topics"
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
                <th className="text-left px-4 py-3 font-medium text-gray-500">
                  Query
                </th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">
                  Active
                </th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">
                  Added
                </th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {queries.map((q) => (
                <tr
                  key={q.id}
                  className="border-b border-gray-50 hover:bg-gray-50"
                >
                  <td className="px-4 py-3 font-mono text-xs">{q.query}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 text-xs rounded-full ${q.is_active ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}
                    >
                      {q.is_active ? "Yes" : "No"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {new Date(q.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(q.id)}
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
