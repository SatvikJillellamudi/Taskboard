import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function ShareDialog({ board, isOwner, onClose }) {
  const [members, setMembers] = useState([]);
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    api(`/boards/${board.id}/members`).then(setMembers).catch((e) => setMessage(e.message));
  }, [board.id]);

  async function invite(e) {
    e.preventDefault();
    setMessage("");
    try {
      const added = await api(`/boards/${board.id}/members`, { method: "POST", body: { email } });
      setMembers([...members, added]);
      setEmail("");
      setMessage(`${added.name} can now see this board.`);
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <div className="overlay" onMouseDown={onClose}>
      <div className="modal" onMouseDown={(e) => e.stopPropagation()}>
        <h3>Share "{board.name}"</h3>
        <ul className="member-list">
          {members.map((m) => (
            <li key={m.id}>
              {m.name} <span className="muted small">{m.email}{m.id === board.owner_id ? " · owner" : ""}</span>
            </li>
          ))}
        </ul>
        {isOwner ? (
          <form className="inline-form" onSubmit={invite}>
            <input type="email" placeholder="Their account email" value={email}
                   onChange={(e) => setEmail(e.target.value)} required />
            <button className="primary">Invite</button>
          </form>
        ) : (
          <p className="muted small">Only the owner can invite people.</p>
        )}
        {message && <p className="small">{message}</p>}
        <div className="modal-actions">
          <span className="spacer" />
          <button className="ghost" onClick={onClose}>Done</button>
        </div>
      </div>
    </div>
  );
}
