import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import AuthPage from "./pages/AuthPage.jsx";
import BoardsPage from "./pages/BoardsPage.jsx";
import BoardPage from "./pages/BoardPage.jsx";
import ServerWakeNotice from "./components/ServerWakeNotice.jsx";

function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  if (loading)
    return (
      <div className="center">
        <div className="loading-stack">
          <span className="muted">Loading…</span>
          <ServerWakeNotice />
        </div>
      </div>
    );
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage />} />
      <Route path="/" element={<RequireAuth><BoardsPage /></RequireAuth>} />
      <Route path="/boards/:boardId" element={<RequireAuth><BoardPage /></RequireAuth>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
