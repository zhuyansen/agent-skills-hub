import { useEffect, useState } from "react";
import { adminFetchSubscribers, adminDeleteSubscriber, type SubscriberData } from "../../api/client";

interface Props {
  token: string;
}

export function SubscribersPage({ token }: Props) {
  const [subscribers, setSubscribers] = useState<SubscriberData[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    adminFetchSubscribers(token)
      .then(setSubscribers)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(load, [token]);

  const handleDelete = async (id: number, email: string) => {
    if (!confirm(`Remove subscriber "${email}"?`)) return;
    await adminDeleteSubscriber(token, id);
    load();
  };

  const activeCount = subscribers.filter((s) => s.is_active).length;
  const verifiedCount = subscribers.filter((s) => s.verified).length;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Newsletter Subscribers</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            {subscribers.length} total · {activeCount} active · {verifiedCount} verified
          </p>
        </div>
        <button
          onClick={load}
          className="px-3 py-1.5 text-xs border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : subscribers.length === 0 ? (
        <div className="text-center py-12 text-gray-400">No subscribers yet</div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 font-medium text-gray-600">ID</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Email</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Subscribed</th>
                <th className="text-center px-4 py-3 font-medium text-gray-600">Active</th>
                <th className="text-center px-4 py-3 font-medium text-gray-600">Verified</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Verified At</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody>
              {subscribers.map((sub) => (
                <tr key={sub.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-400">{sub.id}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">{sub.email}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {sub.subscribed_at
                      ? new Date(sub.subscribed_at).toLocaleDateString("zh-CN", {
                          year: "numeric",
                          month: "2-digit",
                          day: "2-digit",
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "-"}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {sub.is_active ? (
                      <span className="inline-block w-2 h-2 rounded-full bg-green-400" title="Active" />
                    ) : (
                      <span className="inline-block w-2 h-2 rounded-full bg-gray-300" title="Inactive" />
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {sub.verified ? (
                      <span className="text-green-600 text-xs font-medium">✓ Verified</span>
                    ) : (
                      <span className="text-yellow-600 text-xs font-medium">Pending</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {sub.verified_at
                      ? new Date(sub.verified_at).toLocaleDateString("zh-CN", {
                          year: "numeric",
                          month: "2-digit",
                          day: "2-digit",
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "-"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(sub.id, sub.email)}
                      className="text-xs text-red-500 hover:text-red-700 transition-colors"
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
