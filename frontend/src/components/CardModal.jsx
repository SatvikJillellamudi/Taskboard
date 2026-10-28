import { useState } from "react";

export default function CardModal({ card, onSave, onDelete, onClose }) {
  const [title, setTitle] = useState(card.title);
  const [description, setDescription] = useState(card.description);

  function save(e) {
    e.preventDefault();
    if (!title.trim()) return;
    onSave(card.id, { title, description });
  }

  return (
    <div className="overlay" onMouseDown={onClose}>
      <form className="modal" onMouseDown={(e) => e.stopPropagation()} onSubmit={save}>
        <input className="modal-title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <textarea rows={6} placeholder="Add a description…" value={description}
                  onChange={(e) => setDescription(e.target.value)} />
        <div className="modal-actions">
          <button type="button" className="danger" onClick={() => onDelete(card)}>Delete card</button>
          <span className="spacer" />
          <button type="button" className="ghost" onClick={onClose}>Cancel</button>
          <button className="primary">Save</button>
        </div>
      </form>
    </div>
  );
}
