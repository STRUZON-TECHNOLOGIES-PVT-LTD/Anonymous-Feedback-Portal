export function StatTile({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="card" style={{ minWidth: 160 }}>
      <div className="muted" style={{ fontSize: 13 }}>
        {label}
      </div>
      <div style={{ fontSize: 32, fontWeight: 600, marginTop: 4 }}>{value}</div>
    </div>
  );
}
