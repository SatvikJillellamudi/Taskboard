import { useState } from "react";
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import CardItem from "./CardItem.jsx";

export default function ListColumn({ list, onAddCard, onRename, onDelete, onOpenCard }) {
  const { setNodeRef, isOver } = useDroppable({ id: `l${list.id}` });
  const [title, setTitle] = useState("");
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(list.title);

  function addCard(e) {
    e.preventDefault();
    if (!title.trim()) return;
    onAddCard(list.id, title);
    setTitle("");
  }

  function saveName() {
    setEditing(false);
    if (name.trim() && name !== list.title) onRename(list.id, name);
    else setName(list.title);
  }

  return (
    <section className={`column${isOver ? " column-over" : ""}`} data-testid={`list-${list.title}`}>
      <div className="column-head">
        {editing ? (
          <input autoFocus value={name} onChange={(e) => setName(e.target.value)}
                 onBlur={saveName} onKeyDown={(e) => e.key === "Enter" && saveName()} />
        ) : (
          <h3 onClick={() => { setName(list.title); setEditing(true); }} title="Click to rename">
            {list.title} <span className="count">{list.cards.length}</span>
          </h3>
        )}
        <button className="ghost small" onClick={() => onDelete(list)} aria-label="Delete list">✕</button>
      </div>
      <SortableContext items={list.cards.map((c) => `c${c.id}`)} strategy={verticalListSortingStrategy}>
        <div ref={setNodeRef} className="card-stack">
          {list.cards.map((card) => (
            <CardItem key={card.id} card={card} onOpen={onOpenCard} />
          ))}
        </div>
      </SortableContext>
      <form onSubmit={addCard} className="add-card">
        <input placeholder="+ Add a card" value={title} onChange={(e) => setTitle(e.target.value)} />
      </form>
    </section>
  );
}
