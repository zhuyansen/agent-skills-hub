import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { useI18n } from "../../i18n/I18nContext";
import type { Skill } from "../../types/skill";

const GRADIENT_COLORS = [
  "#3b82f6", "#6366f1", "#8b5cf6", "#a855f7", "#c084fc",
  "#d8b4fe", "#93c5fd", "#7dd3fc", "#67e8f9", "#a5f3fc",
];

interface Props {
  skills: Skill[];
}

export function StarTrendChart({ skills }: Props) {
  const { t } = useI18n();

  if (!skills.length) return null;

  // Take top 10 skills by stars
  const top = [...skills]
    .sort((a, b) => b.stars - a.stars)
    .slice(0, 10)
    .map((s, i) => ({
      name: s.repo_name.length > 18 ? s.repo_name.slice(0, 16) + ".." : s.repo_name,
      stars: s.stars,
      color: GRADIENT_COLORS[i % GRADIENT_COLORS.length],
    }));

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h3 className="font-semibold text-gray-900 mb-3">{t("chart.starTrend")}</h3>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={top} margin={{ left: 5, right: 20, top: 5, bottom: 30 }}>
            <XAxis
              dataKey="name"
              tick={{ fontSize: 10, fill: "#6b7280" }}
              axisLine={false}
              tickLine={false}
              angle={-35}
              textAnchor="end"
              interval={0}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#9ca3af" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(v)}
            />
            <Tooltip
              formatter={(value) => [`${Number(value).toLocaleString()} stars`]}
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid #e5e7eb",
                fontSize: "12px",
                boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)",
              }}
            />
            <Bar dataKey="stars" radius={[4, 4, 0, 0]} barSize={28}>
              {top.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
