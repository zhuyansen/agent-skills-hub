import { useCallback, useEffect, useRef, useState } from "react";
import { adminDeleteSkill, adminFetchSkills } from "../../api/client";
import type { Skill } from "../../types/skill";

interface Props {
  token: string;
}

export function SkillsPage({ token }: Props) {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const load = useCallback((p: number, s: string) => {
    setLoading(true);
    adminFetchSkills(token, p, s || undefined)
      .then(setSkills)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => { load(page, search); }, [load, page, search]);

  const handleSearchChange = (val: string) => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setSearch(val);
      setPage(1);
    }, 300);
  };

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`Delete skill ${name}? This cannot be undone.`)) return;
    try {
      await adminDeleteSkill(token, id);
      load(page, search);
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Skills Management</h2>
        <div className="text-sm text-gray-400">{skills.length} results</div>
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>}

      <input
        defaultValue={search}
        onChange={(e) => handleSearchChange(e.target.value)}
        placeholder="Search skills..."
        className="w-full mb-4 px-3 py-2 border border-gray-300 rounded-lg text-sm"
      />

      {loading ? (
        <div className="text-sm text-gray-400">Loading...</div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Author</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Category</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Stars</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Score</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              {skills.map((s) => (
                <tr key={s.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="font-medium truncate max-w-[200px]">{s.repo_name}</div>
                    <div className="text-xs text-gray-400 truncate">{s.repo_full_name}</div>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{s.author_name}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 text-xs rounded-full bg-indigo-50 text-indigo-600">
                      {s.category}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">{s.stars.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right font-medium">{s.score.toFixed(1)}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(s.id, s.repo_name)}
                      className="text-xs text-red-500 hover:text-red-700"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex justify-center gap-2 mt-4">
        <button
          onClick={() => setPage(Math.max(1, page - 1))}
          disabled={page <= 1}
          className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-30"
        >
          Prev
        </button>
        <span className="px-3 py-1.5 text-sm text-gray-500">Page {page}</span>
        <button
          onClick={() => setPage(page + 1)}
          disabled={skills.length < 50}
          className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg disabled:opacity-30"
        >
          Next
        </button>
      </div>
    </div>
  );
}
