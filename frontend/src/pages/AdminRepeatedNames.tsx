import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { RepeatedName } from "../api/types";

export function AdminRepeatedNames() {
  const [names, setNames] = useState<RepeatedName[] | null>(null);

  useEffect(() => {
    api.getStats().then((s) => setNames(s.repeated_names));
  }, []);

  if (!names) return <p className="muted">Loading...</p>;

  return (
    <div>
      <h2>Repeated names</h2>
      <p className="secondary" style={{ maxWidth: 640 }}>
        Names mentioned in the free-text confession/query across two or more independent submissions. This is a
        heuristic text match (not verified identity) - open the linked submissions to judge context before acting.
      </p>

      {names.length === 0 && <p className="muted">No repeated names detected yet.</p>}

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--gridline)" }}>
              <th style={{ padding: 12 }}>Name</th>
              <th style={{ padding: 12 }}>Mentions</th>
              <th style={{ padding: 12 }}>Submissions</th>
            </tr>
          </thead>
          <tbody>
            {names.map((n) => (
              <tr key={n.name} style={{ borderBottom: "1px solid var(--gridline)" }}>
                <td style={{ padding: 12, fontWeight: 600 }}>{n.name}</td>
                <td style={{ padding: 12, fontVariantNumeric: "tabular-nums" }}>{n.mention_count}</td>
                <td style={{ padding: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {n.submission_ids.map((id, i) => (
                    <Link key={id} to={`/admin/submissions/${id}`}>
                      #{i + 1}
                    </Link>
                  ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
