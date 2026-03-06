import { useI18n } from "../i18n/I18nContext";

interface Props {
  completeness: number;
  clarity: number;
  specificity: number;
  examples: number;
  structure?: number; // readme_structure_score, 0-1
  agentReadiness?: number; // quality_agent_readiness, 0-1
  size?: "sm" | "md";
}

export function QualityRadar({ completeness, clarity, specificity, examples, structure, agentReadiness, size = "md" }: Props) {
  const { t } = useI18n();
  const hasStructure = typeof structure === "number" && structure > 0;
  const hasAgent = typeof agentReadiness === "number" && agentReadiness > 0;

  const dimensions: number[] = [completeness, clarity, specificity, examples];
  const labels: string[] = [t("detail.completeness"), t("detail.clarity"), t("detail.specificity"), t("detail.examples")];

  if (hasStructure) {
    dimensions.push(structure);
    labels.push(t("detail.structure"));
  }
  if (hasAgent) {
    dimensions.push(agentReadiness);
    labels.push(t("detail.agentReadiness"));
  }

  const dimCount = dimensions.length;
  const dimLabel = dimCount > 4 ? `(${dimCount}D)` : "";
  const avg = dimensions.reduce((a, b) => a + b, 0) / dimensions.length;

  const w = size === "sm" ? 140 : 200;
  const h = w;
  const cx = w / 2;
  const cy = h / 2;
  const maxR = size === "sm" ? 50 : 72;
  const labelR = maxR + (size === "sm" ? 14 : 20);

  const n = dimensions.length;
  const angles = dimensions.map((_, i) => -90 + (360 / n) * i);

  function polarToXY(angleDeg: number, r: number): [number, number] {
    const rad = (angleDeg * Math.PI) / 180;
    return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
  }

  const rings = [0.25, 0.5, 0.75, 1.0];

  const dataPoints = dimensions.map((val, i) => polarToXY(angles[i], val * maxR));
  const dataPath = dataPoints.map((p, i) => `${i === 0 ? "M" : "L"}${p[0]},${p[1]}`).join(" ") + "Z";

  return (
    <div className="flex flex-col items-center">
      <svg width={w} height={h} className="overflow-visible">
        {/* Grid rings */}
        {rings.map((r) => (
          <polygon
            key={r}
            points={angles.map((a) => polarToXY(a, r * maxR).join(",")).join(" ")}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={0.5}
          />
        ))}

        {/* Axis lines */}
        {angles.map((a, i) => {
          const [ex, ey] = polarToXY(a, maxR);
          return <line key={i} x1={cx} y1={cy} x2={ex} y2={ey} stroke="#d1d5db" strokeWidth={0.5} />;
        })}

        {/* Data polygon */}
        <polygon
          points={dataPoints.map((p) => p.join(",")).join(" ")}
          fill="rgba(59, 130, 246, 0.15)"
          stroke="#3b82f6"
          strokeWidth={1.5}
        />
        <path d={dataPath} fill="rgba(59, 130, 246, 0.08)" />

        {/* Data dots */}
        {dataPoints.map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r={2.5} fill="#3b82f6" />
        ))}

        {/* Labels */}
        {labels.map((label, i) => {
          const [lx, ly] = polarToXY(angles[i], labelR);
          const angleMod = ((angles[i] % 360) + 360) % 360;
          const anchor = angleMod > 45 && angleMod < 135 ? "start"
            : angleMod > 225 && angleMod < 315 ? "end"
            : "middle";
          const dy = angleMod < 45 || angleMod > 315 ? -2
            : angleMod > 135 && angleMod < 225 ? 8
            : 3;
          return (
            <text
              key={label}
              x={lx}
              y={ly + dy}
              textAnchor={anchor}
              className="fill-gray-500"
              fontSize={size === "sm" ? 8 : 10}
            >
              {label}
            </text>
          );
        })}

        {/* Dimension values */}
        {dimensions.map((val, i) => {
          const [px, py] = polarToXY(angles[i], val * maxR);
          const angleMod = ((angles[i] % 360) + 360) % 360;
          const offsetX = angleMod > 45 && angleMod < 135 ? 8
            : angleMod > 225 && angleMod < 315 ? -8
            : 0;
          const offsetY = angleMod < 45 || angleMod > 315 ? -8
            : angleMod > 135 && angleMod < 225 ? 12
            : 0;
          return (
            <text
              key={`v${i}`}
              x={px + offsetX}
              y={py + offsetY}
              textAnchor="middle"
              className="fill-blue-600 font-medium"
              fontSize={size === "sm" ? 7 : 9}
            >
              {(val * 100).toFixed(0)}
            </text>
          );
        })}
      </svg>
      <div className="mt-1 text-xs text-gray-500">
        Quality: <span className="font-semibold text-blue-600">{(avg * 100).toFixed(0)}</span>/100
        {dimLabel && <span className="ml-1 text-gray-400">{dimLabel}</span>}
      </div>
    </div>
  );
}
