import { useCallback, useEffect, useState } from "react";
import { adminFetchSyncLogs, adminTriggerSync } from "../../api/client";
import type { SyncLogData } from "../../types/skill";

interface Props {
  token: string;
}

export function SyncPage({ token }: Props) {
  const [logs, setLogs] = useState<SyncLogData[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    adminFetchSyncLogs(token)
      .then(setLogs)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const handleSync = async () => {
    if (!window.confirm("Are you sure you want to trigger a sync? This will fetch and update all skills data.")) return;
    setSyncing(true);
    try {
      await adminTriggerSync(token);
      // Wait a bit then refresh logs
      setTimeout(load, 2000);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSyncing(false);
    }
  };

  const statusColor = (status: string) => {
    if (status === "completed") return "bg-green-50 text-green-700";
    if (status === "running") return "bg-blue-50 text-blue-700";
    return "bg-red-50 text-red-700";
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Sync Management</h2>
        <div className="flex gap-2">
          <button
            onClick={load}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50"
          >
            Refresh
          </button>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {syncing ? "Starting..." : "Trigger Sync"}
          </button>
        </div>
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>}

      {loading ? (
        <div className="text-sm text-gray-400">Loading...</div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500">ID</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Started</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Finished</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Found</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">New</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Updated</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Error</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-500">{log.id}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-xs rounded-full ${statusColor(log.status)}`}>
                      {log.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {log.started_at ? new Date(log.started_at).toLocaleString() : "-"}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {log.finished_at ? new Date(log.finished_at).toLocaleString() : "-"}
                  </td>
                  <td className="px-4 py-3 text-right">{log.repos_found}</td>
                  <td className="px-4 py-3 text-right text-green-600">{log.repos_new}</td>
                  <td className="px-4 py-3 text-right text-blue-600">{log.repos_updated}</td>
                  <td className="px-4 py-3 text-xs text-red-500 max-w-[200px] truncate">
                    {log.error_message || "-"}
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
