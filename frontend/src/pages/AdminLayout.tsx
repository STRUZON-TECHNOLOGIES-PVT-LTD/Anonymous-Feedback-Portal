import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../utils/auth";

export function AdminLayout() {
  const { username, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/admin/login");
  }

  const linkStyle = ({ isActive }: { isActive: boolean }) => ({
    padding: "8px 14px",
    borderRadius: 6,
    textDecoration: "none",
    color: isActive ? "#fff" : "var(--text-primary)",
    background: isActive ? "var(--series-1)" : "transparent",
  });

  return (
    <div>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "12px 24px",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <nav style={{ display: "flex", gap: 8 }}>
          <NavLink to="/admin" end style={linkStyle}>
            Submissions
          </NavLink>
          <NavLink to="/admin/stats" style={linkStyle}>
            Statistics
          </NavLink>
          <NavLink to="/admin/repeated-names" style={linkStyle}>
            Repeated names
          </NavLink>
        </nav>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span className="muted">{username}</span>
          <button
            onClick={handleLogout}
            style={{ padding: "6px 12px", borderRadius: 6, border: "1px solid var(--border)", background: "transparent", cursor: "pointer" }}
          >
            Log out
          </button>
        </div>
      </header>
      <main style={{ padding: 24 }}>
        <Outlet />
      </main>
    </div>
  );
}
