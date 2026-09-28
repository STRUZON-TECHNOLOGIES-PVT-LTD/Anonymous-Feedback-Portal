import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Stats } from "../api/types";
import { BarChart } from "../components/BarChart";
import { LineChart } from "../components/LineChart";
import { StatTile } from "../components/StatTile";

export function AdminStats() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    api.getStats().then(setStats);
  }, []);

  if (!stats) return <p className="muted">Loading...</p>;

  return (
    <div>
      <h2>Statistics</h2>

      <div style={{ display: "flex", gap: 16, marginBottom: 24, flexWrap: "wrap" }}>
        <StatTile label="Total submissions" value={stats.total_submissions} />
        <StatTile label="Repeated names flagged" value={stats.repeated_names.length} />
        <StatTile label="Repeated devices flagged" value={stats.top_repeated_fingerprints.length} />
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <h3 style={{ marginTop: 0 }}>Submissions, last 30 days</h3>
        <LineChart data={stats.submissions_last_30_days.map((d) => ({ date: d.date, count: d.count }))} />
      </div>

      {stats.question_breakdown.map((q) => (
        <div key={q.question_id} className="card" style={{ marginBottom: 16 }}>
          <h4 style={{ marginTop: 0 }}>{q.text}</h4>
          <BarChart data={Object.entries(q.option_counts).map(([label, value]) => ({ label, value }))} />
        </div>
      ))}

      {stats.top_repeated_fingerprints.length > 0 && (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Repeated devices (possible duplicate submitters)</h3>
          <p className="muted" style={{ fontSize: 13 }}>
            Same browser fingerprint seen across multiple submissions - not a guaranteed identity match.
          </p>
          <BarChart
            color="var(--series-2)"
            data={stats.top_repeated_fingerprints.map((f) => ({ label: f.device_fingerprint.slice(0, 8), value: f.count }))}
          />
        </div>
      )}
    </div>
  );
}
