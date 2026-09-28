import { useState } from "react";

interface Point {
  date: string;
  count: number;
}

/** Single-series trend line: 2px line, 10% area wash, hover crosshair + tooltip. */
export function LineChart({ data }: { data: Point[] }) {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const width = 640;
  const height = 220;
  const padding = { top: 16, right: 16, bottom: 28, left: 36 };
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;

  if (data.length === 0) {
    return <p className="muted">No submissions in the last 30 days yet.</p>;
  }

  const max = Math.max(1, ...data.map((d) => d.count));
  const xStep = data.length > 1 ? innerW / (data.length - 1) : 0;

  const xy = (i: number, v: number) => [
    padding.left + i * xStep,
    padding.top + innerH - (v / max) * innerH,
  ];

  const linePath = data.map((d, i) => xy(i, d.count)).map(([x, y], i) => `${i === 0 ? "M" : "L"}${x},${y}`).join(" ");
  const areaPath =
    linePath +
    ` L${padding.left + (data.length - 1) * xStep},${padding.top + innerH} L${padding.left},${padding.top + innerH} Z`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      style={{ width: "100%", height: "auto" }}
      onMouseLeave={() => setHoverIdx(null)}
    >
      {/* gridlines */}
      {[0, 0.5, 1].map((t) => (
        <line
          key={t}
          x1={padding.left}
          x2={width - padding.right}
          y1={padding.top + innerH * t}
          y2={padding.top + innerH * t}
          stroke="var(--gridline)"
          strokeWidth={1}
        />
      ))}

      <path d={areaPath} fill="var(--series-1)" opacity={0.1} stroke="none" />
      <path d={linePath} fill="none" stroke="var(--series-1)" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />

      {data.map((d, i) => {
        const [x, y] = xy(i, d.count);
        return (
          <g key={d.date}>
            <rect
              x={x - xStep / 2}
              y={padding.top}
              width={Math.max(xStep, 1)}
              height={innerH}
              fill="transparent"
              onMouseEnter={() => setHoverIdx(i)}
            />
            {hoverIdx === i && (
              <line x1={x} x2={x} y1={padding.top} y2={padding.top + innerH} stroke="var(--baseline)" strokeWidth={1} />
            )}
            <circle
              cx={x}
              cy={y}
              r={4}
              fill="var(--series-1)"
              stroke="var(--surface-1)"
              strokeWidth={2}
              opacity={hoverIdx === null || hoverIdx === i ? 1 : 0.4}
            />
          </g>
        );
      })}

      {hoverIdx !== null &&
        (() => {
          const [x, y] = xy(hoverIdx, data[hoverIdx].count);
          const tooltipX = Math.min(Math.max(x, padding.left + 50), width - padding.right - 50);
          return (
            <g transform={`translate(${tooltipX}, ${Math.max(y - 34, 4)})`}>
              <rect x={-46} y={0} width={92} height={28} rx={6} fill="var(--surface-1)" stroke="var(--border)" />
              <text x={0} y={14} textAnchor="middle" fontSize={11} fill="var(--text-secondary)">
                {data[hoverIdx].date}
              </text>
              <text x={0} y={25} textAnchor="middle" fontSize={11} fill="var(--text-primary)" fontWeight={600}>
                {data[hoverIdx].count} submission{data[hoverIdx].count === 1 ? "" : "s"}
              </text>
            </g>
          );
        })()}
    </svg>
  );
}
