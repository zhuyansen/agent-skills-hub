import { useCallback, useEffect, useState } from "react";
import {
  adminCreateMaster,
  adminDeleteMaster,
  adminFetchMasters,
  adminUpdateMaster,
} from "../../api/client";
import type { MasterData } from "../../types/skill";

interface Props {
  token: string;
}

export function MastersPage({ token }: Props) {
  const [masters, setMasters] = useState<MasterData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ github: "", name: "", x_handle: "", bio: "" });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState({ x_followers: "", x_posts_count: "", x_notes: "" });

  const load = useCallback(() => {
    setLoading(true);
    adminFetchMasters(token)
      .then(setMasters)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    if (!form.github || !form.name) return;
    try {
      await adminCreateMaster(token, {
        github: form.github,
        name: form.name,
        x_handle: form.x_handle || undefined,
        bio: form.bio || undefined,
      });
      setForm({ github: "", name: "", x_handle: "", bio: "" });
      setShowForm(false);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleDelete = async (id: number, github: string) => {
    if (!confirm(`Deactivate master ${github}?`)) return;
    try {
      await adminDeleteMaster(token, id);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const startEdit = (m: MasterData) => {
    setEditingId(m.id);
    setEditForm({
      x_followers: String(m.x_followers || 0),
      x_posts_count: String(m.x_posts_count || 0),
      x_notes: m.x_notes || "",
    });
  };

  const handleSaveEdit = async () => {
    if (editingId === null) return;
    try {
      await adminUpdateMaster(token, editingId, {
        x_followers: Number(editForm.x_followers) || 0,
        x_posts_count: Number(editForm.x_posts_count) || 0,
        x_notes: editForm.x_notes || undefined,
      });
      setEditingId(null);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Skill Masters</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          {showForm ? "Cancel" : "+ Add Master"}
        </button>
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>}

      {showForm && (
        <div className="mb-6 p-4 bg-white border border-gray-200 rounded-xl space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <input
              value={form.github}
              onChange={(e) => setForm({ ...form, github: e.target.value })}
              placeholder="GitHub username *"
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Display name *"
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
            <input
              value={form.x_handle}
              onChange={(e) => setForm({ ...form, x_handle: e.target.value })}
              placeholder="X handle (optional)"
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
            <input
              value={form.bio}
              onChange={(e) => setForm({ ...form, bio: e.target.value })}
              placeholder="Bio (optional)"
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>
          <button
            onClick={handleCreate}
            className="px-4 py-2 text-sm bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
          >
            Create
          </button>
        </div>
      )}

      {loading ? (
        <div className="text-sm text-gray-400">Loading...</div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500">GitHub</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">X Handle</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">X Followers</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">X Posts</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">X Notes</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Active</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              {masters.map((m) => (
                <tr key={m.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{m.github}</td>
                  <td className="px-4 py-3">{m.name}</td>
                  <td className="px-4 py-3 text-gray-500">{m.x_handle || "-"}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {editingId === m.id ? (
                      <input
                        value={editForm.x_followers}
                        onChange={(e) => setEditForm({ ...editForm, x_followers: e.target.value })}
                        className="w-20 px-2 py-1 border border-gray-300 rounded text-xs"
                        type="number"
                      />
                    ) : (
                      m.x_followers?.toLocaleString() || "0"
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {editingId === m.id ? (
                      <input
                        value={editForm.x_posts_count}
                        onChange={(e) => setEditForm({ ...editForm, x_posts_count: e.target.value })}
                        className="w-20 px-2 py-1 border border-gray-300 rounded text-xs"
                        type="number"
                      />
                    ) : (
                      m.x_posts_count?.toLocaleString() || "0"
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500 max-w-[150px] truncate">
                    {editingId === m.id ? (
                      <input
                        value={editForm.x_notes}
                        onChange={(e) => setEditForm({ ...editForm, x_notes: e.target.value })}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-xs"
                        placeholder="Notes..."
                      />
                    ) : (
                      m.x_notes || "-"
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-xs rounded-full ${m.is_active ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
                      {m.is_active ? "Yes" : "No"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right space-x-2 whitespace-nowrap">
                    {editingId === m.id ? (
                      <>
                        <button onClick={handleSaveEdit} className="text-xs text-emerald-600 hover:text-emerald-800">Save</button>
                        <button onClick={() => setEditingId(null)} className="text-xs text-gray-500 hover:text-gray-700">Cancel</button>
                      </>
                    ) : (
                      <>
                        <button onClick={() => startEdit(m)} className="text-xs text-blue-500 hover:text-blue-700">Edit X</button>
                        <button onClick={() => handleDelete(m.id, m.github)} className="text-xs text-red-500 hover:text-red-700">Deactivate</button>
                      </>
                    )}
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
