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

interface EditFormState {
  name: string;
  x_handle: string;
  bio: string;
  tags: string;
  github_aliases: string;
  x_followers: string;
  x_posts_count: string;
  x_notes: string;
}

export function MastersPage({ token }: Props) {
  const [masters, setMasters] = useState<MasterData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ github: "", name: "", x_handle: "", bio: "", tags: "", github_aliases: "" });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<EditFormState>({
    name: "", x_handle: "", bio: "", tags: "", github_aliases: "",
    x_followers: "", x_posts_count: "", x_notes: "",
  });

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
      const aliases = form.github_aliases
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      const tagList = form.tags
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      await adminCreateMaster(token, {
        github: form.github,
        name: form.name,
        x_handle: form.x_handle || undefined,
        bio: form.bio || undefined,
        github_aliases: aliases.length ? aliases : undefined,
        tags: tagList.length ? tagList : undefined,
      });
      setForm({ github: "", name: "", x_handle: "", bio: "", tags: "", github_aliases: "" });
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

  const parseTags = (raw: string): string[] => {
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  };

  const startEdit = (m: MasterData) => {
    setEditingId(m.id);
    const tags = parseTags(m.tags || "[]");
    const aliases = parseTags(m.github_aliases || "[]");
    setEditForm({
      name: m.name || "",
      x_handle: m.x_handle || "",
      bio: m.bio || "",
      tags: tags.join(", "),
      github_aliases: aliases.join(", "),
      x_followers: String(m.x_followers || 0),
      x_posts_count: String(m.x_posts_count || 0),
      x_notes: m.x_notes || "",
    });
  };

  const handleSaveEdit = async () => {
    if (editingId === null) return;
    try {
      const aliases = editForm.github_aliases
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      const tagList = editForm.tags
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      await adminUpdateMaster(token, editingId, {
        name: editForm.name || undefined,
        x_handle: editForm.x_handle,
        bio: editForm.bio,
        github_aliases: aliases,
        tags: tagList,
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

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg flex items-center justify-between">
          {error}
          <button onClick={() => setError("")} className="text-red-500 hover:text-red-700 ml-2">✕</button>
        </div>
      )}

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
            <input
              value={form.tags}
              onChange={(e) => setForm({ ...form, tags: e.target.value })}
              placeholder="Tags (comma separated)"
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
            <input
              value={form.github_aliases}
              onChange={(e) => setForm({ ...form, github_aliases: e.target.value })}
              placeholder="GitHub aliases (comma separated)"
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
        <>
          {/* Edit panel (shows above table when editing) */}
          {editingId !== null && (() => {
            const m = masters.find((x) => x.id === editingId);
            if (!m) return null;
            return (
              <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-blue-800">
                    Editing: {m.github}
                  </h3>
                  <div className="space-x-2">
                    <button onClick={handleSaveEdit} className="px-3 py-1.5 text-xs bg-emerald-600 text-white rounded-lg hover:bg-emerald-700">
                      Save
                    </button>
                    <button onClick={() => setEditingId(null)} className="px-3 py-1.5 text-xs bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
                      Cancel
                    </button>
                  </div>
                </div>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">Name</label>
                    <input
                      value={editForm.name}
                      onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">X Handle</label>
                    <input
                      value={editForm.x_handle}
                      onChange={(e) => setEditForm({ ...editForm, x_handle: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">X Followers</label>
                    <input
                      value={editForm.x_followers}
                      onChange={(e) => setEditForm({ ...editForm, x_followers: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
                      type="number"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">X Posts</label>
                    <input
                      value={editForm.x_posts_count}
                      onChange={(e) => setEditForm({ ...editForm, x_posts_count: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
                      type="number"
                    />
                  </div>
                  <div className="lg:col-span-2">
                    <label className="text-xs text-gray-500 mb-1 block">Bio</label>
                    <input
                      value={editForm.bio}
                      onChange={(e) => setEditForm({ ...editForm, bio: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">Tags (comma separated)</label>
                    <input
                      value={editForm.tags}
                      onChange={(e) => setEditForm({ ...editForm, tags: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">GitHub Aliases (comma sep)</label>
                    <input
                      value={editForm.github_aliases}
                      onChange={(e) => setEditForm({ ...editForm, github_aliases: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
                    />
                  </div>
                  <div className="lg:col-span-4">
                    <label className="text-xs text-gray-500 mb-1 block">Notes</label>
                    <input
                      value={editForm.x_notes}
                      onChange={(e) => setEditForm({ ...editForm, x_notes: e.target.value })}
                      className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm"
                      placeholder="Admin notes..."
                    />
                  </div>
                </div>
              </div>
            );
          })()}

          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">GitHub</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Name</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">X Handle</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Followers</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Posts</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Tags</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Active</th>
                  <th className="text-right px-4 py-3 font-medium text-gray-500">Actions</th>
                </tr>
              </thead>
              <tbody>
                {masters.map((m) => {
                  const tags = (() => {
                    try { const p = JSON.parse(m.tags || "[]"); return Array.isArray(p) ? p : []; }
                    catch { return []; }
                  })();
                  return (
                    <tr
                      key={m.id}
                      className={`border-b border-gray-50 hover:bg-gray-50 ${editingId === m.id ? "bg-blue-50" : ""}`}
                    >
                      <td className="px-4 py-3 font-medium">{m.github}</td>
                      <td className="px-4 py-3">{m.name}</td>
                      <td className="px-4 py-3 text-gray-500">
                        {m.x_handle ? (
                          <a href={`https://x.com/${m.x_handle}`} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                            @{m.x_handle}
                          </a>
                        ) : "-"}
                      </td>
                      <td className="px-4 py-3 text-gray-500">{m.x_followers?.toLocaleString() || "0"}</td>
                      <td className="px-4 py-3 text-gray-500">{m.x_posts_count?.toLocaleString() || "0"}</td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {tags.slice(0, 3).map((tag: string) => (
                            <span key={tag} className="px-1.5 py-0.5 text-[10px] bg-gray-100 text-gray-600 rounded">
                              {tag}
                            </span>
                          ))}
                          {tags.length > 3 && (
                            <span className="text-[10px] text-gray-400">+{tags.length - 3}</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 text-xs rounded-full ${m.is_active ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
                          {m.is_active ? "Yes" : "No"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right space-x-2 whitespace-nowrap">
                        <button
                          onClick={() => editingId === m.id ? setEditingId(null) : startEdit(m)}
                          className={`text-xs ${editingId === m.id ? "text-amber-600 hover:text-amber-800" : "text-blue-500 hover:text-blue-700"}`}
                        >
                          {editingId === m.id ? "Editing..." : "Edit"}
                        </button>
                        <button
                          onClick={() => handleDelete(m.id, m.github)}
                          className="text-xs text-red-500 hover:text-red-700"
                        >
                          Deactivate
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
