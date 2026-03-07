import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { useI18n } from "../../i18n/I18nContext";

const LANG_COLORS: Record<string, string> = {
  TypeScript: "#3178c6",
  Python: "#3572A5",
  JavaScript: "#f1e05a",
  Go: "#00ADD8",
  Rust: "#dea584",
  Java: "#b07219",
  Ruby: "#701516",
  "C#": "#178600",
  Shell: "#89e051",
  Kotlin: "#A97BFF",
  C: "#555555",
  "C++": "#f34b7d",
  Swift: "#F05138",
  PHP: "#4F5D95",
  Dart: "#00B4AB",
};

interface Props {
  languages: { language: string; count: number }[];
}

export function LanguageBarChart({ languages }: Props) {
  const { t } = useI18n();

  if (!languages.length) return null;

  const data = languages.slice(0, 10).map((l) => ({
    name: l.language,
    count: l.count,
    fill: LANG_COLORS[l.language] || "#94a3b8",
  }));

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h3 className="font-semibold text-gray-900 mb-3">{t("chart.languageDist")}</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 5, right: 20, top: 5, bottom: 5 }}>
            <XAxis type="number" tick={{ fontSize: 11, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
            <YAxis
              type="category"
              dataKey="name"
              width={80}
              tick={{ fontSize: 11, fill: "#6b7280" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              formatter={(value) => [Number(value), t("chart.skills")]}
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid #e5e7eb",
                fontSize: "12px",
                boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)",
              }}
            />
            <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={18}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
