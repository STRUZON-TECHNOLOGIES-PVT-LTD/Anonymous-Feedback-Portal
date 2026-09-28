import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../utils/auth";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { username, loading } = useAuth();

  if (loading) return null;
  if (!username) return <Navigate to="/admin/login" replace />;

  return <>{children}</>;
}
