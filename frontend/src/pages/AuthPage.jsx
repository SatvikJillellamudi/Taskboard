import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export default function AuthPage() {
  const { user, login, signup } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "login") await login(form.email, form.password);
      else await signup(form.name, form.email, form.password);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <form className="auth-card" onSubmit={submit}>
        <h1>Taskboard</h1>
        <p className="muted">{mode === "login" ? "Log in to your boards" : "Create an account"}</p>
        {mode === "signup" && (
          <input placeholder="Name" value={form.name} onChange={update("name")} required />
        )}
        <input type="email" placeholder="Email" value={form.email} onChange={update("email")} required />
        <input type="password" placeholder="Password (8+ characters)" value={form.password}
               onChange={update("password")} minLength={8} required />
        {error && <div className="error">{error}</div>}
        <button className="primary" disabled={busy}>
          {busy ? "Working…" : mode === "login" ? "Log in" : "Sign up"}
        </button>
        <button type="button" className="link"
                onClick={() => { setMode(mode === "login" ? "signup" : "login"); setError(""); }}>
          {mode === "login" ? "No account? Sign up" : "Have an account? Log in"}
        </button>
      </form>
    </div>
  );
}
