import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { Question } from "../api/types";
import { collectDeviceInfo } from "../utils/fingerprint";
import struzonLogo from "../assets/struzon-logo.png";

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

  const glowBlobs = (
    <>
      <div className="fp-glow fp-glow-crimson" aria-hidden="true" />
      <div className="fp-glow fp-glow-ocean" aria-hidden="true" />
    </>
  );

  if (status === "done") {
    return (
      <div className="feedback-portal">
        {glowBlobs}
        <div className="fp-content" style={{ textAlign: "center", paddingTop: 80 }}>
          <div className="fp-glass" style={{ padding: 48 }}>
            <div style={{ fontSize: 40, marginBottom: 16, color: "var(--crimson-600)" }}>✓</div>
            <h2 style={{ marginBottom: 8 }}>Thank you.</h2>
            <p className="secondary">Your feedback has been submitted anonymously.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="feedback-portal">
      {glowBlobs}
      <div className="fp-content">
        <img src={struzonLogo} alt="Struzon Technologies" className="fp-logo" />
        <h1 className="fp-title">Anonymous Feedback Portal</h1>
        <p className="fp-subtitle">
          Share a confession, question, or concern, and answer a few quick questions. No account or login is
          required — nothing here is tied back to you.
        </p>

        <form onSubmit={handleSubmit}>
          <section className="fp-section">
            <div className="fp-section-header">
              <div className="fp-section-kicker">Section 01</div>
              <div className="fp-section-title">Feedback</div>
              <p className="fp-section-hint">Share a confession, question, or concern in your own words</p>
            </div>

            <div className="fp-glass">
              <textarea
                id="confession"
                rows={6}
                value={confessionText}
                onChange={(e) => setConfessionText(e.target.value)}
                placeholder="Write anything you'd like management to know..."
                className="fp-textarea"
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
          </section>

          <section className="fp-section">
            <div className="fp-section-header">
              <div className="fp-section-kicker">Section 02</div>
              <div className="fp-section-title">Questionnaire</div>
              <p className="fp-section-hint">{questions.length || 10} short questions, tap to answer</p>
            </div>

            <div className="fp-glass">
              {questions.map((q) => (
                <div key={q.id} className="fp-question">
                  <div className="fp-question-text">{q.text}</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                    {q.options.map((opt) => {
                      const selected = answers[q.id] === opt;
                      return (
                        <button
                          type="button"
                          key={opt}
                          onClick={() => setAnswers((prev) => ({ ...prev, [q.id]: opt }))}
                          className={`fp-pill${selected ? " selected" : ""}`}
                        >
                          {opt}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
              {questions.length === 0 && !error && <p className="muted" style={{ margin: 0 }}>Loading questions...</p>}
            </div>
          </section>

          {error && (
            <p className="fp-alert-error" role="alert">
              {error}
            </p>
          )}

          <button type="submit" className="fp-submit" disabled={status === "submitting" || questions.length === 0}>
            {status === "submitting" ? "Submitting..." : "Submit anonymously"}
          </button>
        </form>
      </div>
    </div>
  );
}
