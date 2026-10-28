import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";

export default function BoardsPage() {
  const { user, logout } = useAuth();
  const [boards, setBoards] = useState(null);
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api("/boards").then(setBoards).catch((e) => setError(e.message));
  }, []);

  async function create(e) {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      const board = await api("/boards", { method: "POST", body: { name } });
      setBoards([...boards, board]);
      setName("");
    } catch (err) {
      setError(err.message);
    }
  }

  async function remove(board) {
    if (!confirm(`Delete "${board.name}" and everything on it?`)) return;
    try {
      await api(`/boards/${board.id}`, { method: "DELETE" });
      setBoards(boards.filter((b) => b.id !== board.id));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <header className="topbar">
        <span className="brand">Taskboard</span>
        <span className="muted">{user.name}</span>
        <button className="ghost" onClick={logout}>Log out</button>
      </header>
      <main className="boards-main">
        <h2>Your boards</h2>
        {error && <div className="error">{error}</div>}
        <form className="inline-form" onSubmit={create}>
          <input placeholder="New board name" value={name} onChange={(e) => setName(e.target.value)} />
          <button className="primary">Create board</button>
        </form>
        {boards === null ? (
          <p className="muted">Loading…</p>
        ) : boards.length === 0 ? (
          <p className="muted">No boards yet. Create one above.</p>
        ) : (
          <div className="board-grid">
            {boards.map((b) => (
              <div key={b.id} className="board-tile">
                <Link to={`/boards/${b.id}`}>{b.name}</Link>
                <span className="muted small">{b.owner_id === user.id ? "Owner" : "Shared with you"}</span>
                {b.owner_id === user.id && (
                  <button className="ghost small" onClick={() => remove(b)}>Delete</button>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
