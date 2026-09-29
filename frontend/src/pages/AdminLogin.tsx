import { useState } from "react";
import { useNavigate } from "react-router-dom";
import struzonLogo from "../assets/struzon-logo.png";
import { useAuth } from "../utils/auth";

export function AdminLogin() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await login(username, password);
      navigate("/admin");
    } catch {
      setError("Invalid credentials.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ maxWidth: 360, margin: "100px auto", padding: "0 16px" }}>
      <img src={struzonLogo} alt="Struzon Technologies" style={{ height: 40, margin: "0 auto 12px", display: "block" }} />
      <h2 style={{ textAlign: "center" }}>Admin login</h2>
      <form onSubmit={handleSubmit} className="card">
        <label htmlFor="username" style={{ display: "block", marginBottom: 4 }}>
          Username
        </label>
        <input
          id="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{ width: "100%", padding: 8, marginBottom: 12, borderRadius: 6 }}
          autoComplete="username"
        />

        <label htmlFor="password" style={{ display: "block", marginBottom: 4 }}>
          Password
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ width: "100%", padding: 8, marginBottom: 16, borderRadius: 6 }}
          autoComplete="current-password"
        />

        {error && (
          <p className="alert-error" role="alert">
            {error}
          </p>
        )}

        <button type="submit" className="btn-primary" disabled={submitting} style={{ width: "100%" }}>
          {submitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}
