import { NavLink, Outlet, useNavigate } from "react-router-dom";
import struzonIcon from "../assets/struzon-icon.png";
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
    color: "#ffffff",
    background: isActive ? "rgba(255, 255, 255, 0.18)" : "transparent",
    opacity: isActive ? 1 : 0.8,
  });

  return (
    <div>
      {/* Brand stripe - navy-700, per the Struzon brand kit's "navy button / brand stripe" role */}
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "12px 24px",
          background: "var(--navy-700)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <img src={struzonIcon} alt="" style={{ height: 30, width: "auto" }} />
            <span style={{ color: "#ffffff", fontWeight: 700, letterSpacing: "0.02em" }}>
              STRUZON <span style={{ fontWeight: 400, opacity: 0.85 }}>Technologies</span>
            </span>
          </div>
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
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ color: "#ffffff", opacity: 0.8 }}>{username}</span>
          <button
            onClick={handleLogout}
            style={{
              padding: "6px 12px",
              borderRadius: 6,
              border: "1px solid rgba(255, 255, 255, 0.4)",
              background: "transparent",
              color: "#ffffff",
              cursor: "pointer",
            }}
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
