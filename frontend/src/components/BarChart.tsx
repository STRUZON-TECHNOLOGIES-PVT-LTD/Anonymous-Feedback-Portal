interface BarDatum {
  label: string;
  value: number;
}

/** Horizontal single-series magnitude bars: one hue, value labeled at the tip. */
export function BarChart({ data, color = "var(--series-1)" }: { data: BarDatum[]; color?: string }) {
  const max = Math.max(1, ...data.map((d) => d.value));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {data.map((d) => (
        <div key={d.label} style={{ display: "grid", gridTemplateColumns: "120px 1fr 40px", alignItems: "center", gap: 10 }}>
          <span className="secondary" style={{ fontSize: 13, textAlign: "right" }}>
            {d.label}
          </span>
          <div style={{ background: "var(--gridline)", borderRadius: 4, height: 20, position: "relative" }}>
            <div
              style={{
                width: `${(d.value / max) * 100}%`,
                height: "100%",
                background: color,
                borderRadius: 4,
                minWidth: d.value > 0 ? 4 : 0,
              }}
            />
          </div>
          <span style={{ fontSize: 13, fontVariantNumeric: "tabular-nums" }}>{d.value}</span>
        </div>
      ))}
    </div>
  );
}
