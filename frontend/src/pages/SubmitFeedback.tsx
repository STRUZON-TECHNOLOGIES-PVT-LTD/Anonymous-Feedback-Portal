import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { Question } from "../api/types";
import { collectDeviceInfo } from "../utils/fingerprint";

export function SubmitFeedback() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [confessionText, setConfessionText] = useState("");
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [status, setStatus] = useState<"idle" | "submitting" | "done" | "error">("idle");
  const [error, setError] = useState("");
  const loadedAt = useRef(Date.now());

  useEffect(() => {
    api
      .getQuestions()
      .then(setQuestions)
      .catch(() => setError("Could not load the feedback form. Please refresh and try again."));
  }, []);

  const unanswered = questions.filter((q) => !answers[q.id]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (unanswered.length > 0) {
      setError(`Please answer all questions (${unanswered.length} remaining).`);
      return;
    }

    setStatus("submitting");
    setError("");

    try {
      await api.submitFeedback({
        confession_text: confessionText,
        answers: Object.entries(answers).map(([question_id, selected_option]) => ({
          question_id: Number(question_id),
          selected_option,
        })),
        device: collectDeviceInfo(),
        website: "",
        form_seconds: (Date.now() - loadedAt.current) / 1000,
      });
      setStatus("done");
    } catch {
      setStatus("error");
      setError("Something went wrong submitting your feedback. Please try again.");
    }
  }

  if (status === "done") {
    return (
      <div style={{ maxWidth: 640, margin: "80px auto", padding: "0 16px", textAlign: "center" }}>
        <h2>Thank you.</h2>
        <p className="secondary">Your feedback has been submitted anonymously.</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 640, margin: "40px auto", padding: "0 16px" }}>
      <h1>Anonymous Feedback Portal</h1>
      <p className="secondary">
        Share a confession, question, or concern, and answer a few quick questions. No account or login is
        required.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="card" style={{ marginBottom: 20 }}>
          <label htmlFor="confession" style={{ display: "block", fontWeight: 600, marginBottom: 8 }}>
            Your confession, query, or feedback
          </label>
          <textarea
            id="confession"
            rows={6}
            value={confessionText}
            onChange={(e) => setConfessionText(e.target.value)}
            placeholder="Write anything you'd like management to know..."
            style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid var(--border)", resize: "vertical" }}
          />

          {/* Honeypot: hidden from real users via CSS, bots that fill every field trip it. */}
          <div style={{ position: "absolute", left: "-9999px" }} aria-hidden="true">
            <label htmlFor="website">Website</label>
            <input
              id="website"
              name="website"
              tabIndex={-1}
              autoComplete="off"
              onChange={(e) => (e.target.value ? setError("") : null)}
            />
          </div>
        </div>

        {questions.map((q) => (
          <div key={q.id} className="card" style={{ marginBottom: 12 }}>
            <div style={{ fontWeight: 600, marginBottom: 10 }}>{q.text}</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {q.options.map((opt) => {
                const selected = answers[q.id] === opt;
                return (
                  <button
                    type="button"
                    key={opt}
                    onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: opt }))}
                    style={{
                      padding: "8px 14px",
                      borderRadius: 20,
                      border: selected ? "1px solid var(--series-1)" : "1px solid var(--border)",
                      background: selected ? "var(--series-1)" : "var(--surface-1)",
                      color: selected ? "#fff" : "var(--text-primary)",
                      cursor: "pointer",
                    }}
                  >
                    {opt}
                  </button>
                );
              })}
            </div>
          </div>
        ))}

        {error && (
          <p style={{ color: "var(--status-critical)" }} role="alert">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={status === "submitting" || questions.length === 0}
          style={{
            padding: "12px 24px",
            borderRadius: 8,
            border: "none",
            background: "var(--series-1)",
            color: "#fff",
            fontWeight: 600,
            cursor: "pointer",
            width: "100%",
          }}
        >
          {status === "submitting" ? "Submitting..." : "Submit anonymously"}
        </button>
      </form>
    </div>
  );
}
