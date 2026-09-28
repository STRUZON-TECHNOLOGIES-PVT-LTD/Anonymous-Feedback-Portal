import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { SubmissionDetail } from "../api/types";

export function AdminSubmissionDetail() {
  const { id } = useParams<{ id: string }>();
  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);

  useEffect(() => {
    if (id) api.getSubmission(id).then(setSubmission);
  }, [id]);

  if (!submission) return <p className="muted">Loading...</p>;

  const logRows: [string, string | null][] = [
    ["IP address", submission.ip_address],
    ["Device fingerprint", submission.device_fingerprint],
    ["User agent", submission.user_agent],
    ["Platform", submission.platform],
    ["Screen resolution", submission.screen_resolution],
    ["Timezone", submission.timezone],
    ["Language", submission.language],
  ];

  return (
    <div style={{ maxWidth: 720 }}>
      <Link to="/admin">&larr; Back to submissions</Link>
      <h2>Submission detail</h2>
      <p className="muted">{new Date(submission.created_at).toLocaleString()}</p>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginTop: 0 }}>Confession / query</h3>
        <p style={{ whiteSpace: "pre-wrap" }}>{submission.confession_text || <span className="muted">No free text submitted.</span>}</p>

        {submission.extracted_names.length > 0 && (
          <>
            <h4>Names mentioned</h4>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {submission.extracted_names.map((n) => (
                <span key={n} style={{ background: "var(--gridline)", padding: "4px 10px", borderRadius: 12, fontSize: 13 }}>
                  {n}
                </span>
              ))}
            </div>
          </>
        )}
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h3 style={{ marginTop: 0 }}>Question answers</h3>
        {submission.answers.map((a) => (
          <div key={a.question_id} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--gridline)" }}>
            <span className="secondary">{a.question_text}</span>
            <strong>{a.selected_option}</strong>
          </div>
        ))}
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Device / request log</h3>
        {logRows.map(([label, value]) => (
          <div key={label} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--gridline)" }}>
            <span className="secondary">{label}</span>
            <span style={{ fontVariantNumeric: "tabular-nums" }}>{value || "—"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
