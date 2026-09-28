import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AdminLayout } from "./pages/AdminLayout";
import { AdminLogin } from "./pages/AdminLogin";
import { AdminRepeatedNames } from "./pages/AdminRepeatedNames";
import { AdminStats } from "./pages/AdminStats";
import { AdminSubmissionDetail } from "./pages/AdminSubmissionDetail";
import { AdminSubmissions } from "./pages/AdminSubmissions";
import { SubmitFeedback } from "./pages/SubmitFeedback";
import { AuthProvider } from "./utils/auth";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<SubmitFeedback />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<AdminSubmissions />} />
          <Route path="submissions/:id" element={<AdminSubmissionDetail />} />
          <Route path="stats" element={<AdminStats />} />
          <Route path="repeated-names" element={<AdminRepeatedNames />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
