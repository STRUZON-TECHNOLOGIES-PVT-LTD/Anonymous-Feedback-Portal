import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { SubmissionListResponse } from "../api/types";

const PAGE_SIZE = 20;

export function AdminSubmissions() {
  const [data, setData] = useState<SubmissionListResponse | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    api.listSubmissions(page, PAGE_SIZE).then(setData);
  }, [page]);

  if (!data) return <p className="muted">Loading...</p>;

  const totalPages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));

  return (
    <div>
      <h2>Submissions ({data.total})</h2>

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid var(--gridline)" }}>
              <th style={{ padding: 12 }}>Submitted</th>
              <th style={{ padding: 12 }}>Preview</th>
              <th style={{ padding: 12 }}>IP address</th>
              <th style={{ padding: 12 }}>Device</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((item) => (
              <tr key={item.id} style={{ borderBottom: "1px solid var(--gridline)" }}>
                <td style={{ padding: 12, whiteSpace: "nowrap" }}>{new Date(item.created_at).toLocaleString()}</td>
                <td style={{ padding: 12 }}>
                  <Link to={`/admin/submissions/${item.id}`}>{item.confession_preview || <span className="muted">(no text - ratings only)</span>}</Link>
                </td>
                <td style={{ padding: 12, fontVariantNumeric: "tabular-nums" }}>{item.ip_address || "—"}</td>
                <td style={{ padding: 12 }} className="muted">
                  {item.device_fingerprint ? item.device_fingerprint.slice(0, 10) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 16, alignItems: "center" }}>
        <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          Previous
        </button>
        <span className="muted">
          Page {page} of {totalPages}
        </span>
        <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
          Next
        </button>
      </div>
    </div>
  );
}
