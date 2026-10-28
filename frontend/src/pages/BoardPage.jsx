import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  DndContext, DragOverlay, KeyboardSensor, PointerSensor,
  closestCorners, useSensor, useSensors,
} from "@dnd-kit/core";
import { arrayMove, sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { positionBetween } from "../positions.js";
import { useBoardSocket } from "../useBoardSocket.js";
import ListColumn from "../components/ListColumn.jsx";
import CardModal from "../components/CardModal.jsx";
import ShareDialog from "../components/ShareDialog.jsx";
import { CardView } from "../components/CardItem.jsx";

// dnd-kit ids: cards are "c<id>", list drop zones are "l<id>"
const cardKey = (c) => `c${c.id}`;
function findList(board, dndId) {
  const id = String(dndId);
  if (id.startsWith("l")) return board.lists.find((l) => l.id === Number(id.slice(1)));
  return board.lists.find((l) => l.cards.some((c) => cardKey(c) === id));
}

export default function BoardPage() {
  const { boardId } = useParams();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [board, setBoard] = useState(null);
  const [viewers, setViewers] = useState([]);
  const [error, setError] = useState("");
  const [openCard, setOpenCard] = useState(null);
  const [sharing, setSharing] = useState(false);
  const [newList, setNewList] = useState("");
  const [activeCard, setActiveCard] = useState(null);
  const [editingName, setEditingName] = useState(false);
  const [boardName, setBoardName] = useState("");

  const boardRef = useRef(null);
  boardRef.current = board;
  const dragging = useRef(false);   // true while a card is being dragged
  const pending = useRef(null);     // a server update that arrived mid-drag
  const dragOrigin = useRef(null);  // where the dragged card started

  // Server is the source of truth, but never yank the board out from under an active drag
  const applyServerBoard = useCallback((b) => {
    if (dragging.current) pending.current = b;
    else setBoard(b);
  }, []);

  const reload = useCallback(() => {
    return api(`/boards/${boardId}`).then(applyServerBoard).catch((e) => {
      if (e.status === 404) navigate("/", { replace: true });
      else setError(e.message);
    });
  }, [boardId, applyServerBoard, navigate]);

  useEffect(() => { reload(); }, [reload]);

  const status = useBoardSocket(boardId, {
    onBoard: applyServerBoard,
    onPresence: setViewers,
    onDeleted: () => navigate("/", { replace: true }),
    onUnauthorized: logout,
  });
  const statusRef = useRef(status);
  statusRef.current = status;

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }), // a click still opens the card
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }) // keyboard drag for accessibility
  );

  // Run a change. When live, the WebSocket broadcast updates the UI; if offline, refetch.
  async function mutate(fn) {
    setError("");
    try {
      await fn();
      if (statusRef.current !== "live") await reload();
    } catch (e) {
      setError(e.message);
      reload();
    }
  }

  if (!board) return <div className="center muted">{error || "Loading board…"}</div>;
  const isOwner = board.owner_id === user.id;

  // ---------- drag and drop ----------
  function onDragStart({ active }) {
    dragging.current = true;
    const list = findList(board, active.id);
    const card = list.cards.find((c) => cardKey(c) === active.id);
    setActiveCard(card);
    dragOrigin.current = { listId: list.id, index: list.cards.indexOf(card) };
  }

  // While dragging over another list, move the card there in local state so it previews in place
  function onDragOver({ active, over }) {
    if (!over) return;
    setBoard((b) => {
      const from = findList(b, active.id);
      const to = findList(b, over.id);
      if (!from || !to || from.id === to.id) return b;
      const card = from.cards.find((c) => cardKey(c) === active.id);
      const overIdx = to.cards.findIndex((c) => cardKey(c) === String(over.id));
      const insertAt = overIdx >= 0 ? overIdx : to.cards.length;
      return {
        ...b,
        lists: b.lists.map((l) => {
          if (l.id === from.id) return { ...l, cards: l.cards.filter((c) => c.id !== card.id) };
          if (l.id === to.id) {
            const cards = [...l.cards];
            cards.splice(insertAt, 0, { ...card, list_id: to.id });
            return { ...l, cards };
          }
          return l;
        }),
      };
    });
  }

  function finishDrag() {
    dragging.current = false;
    setActiveCard(null);
  }

  function onDragEnd({ active, over }) {
    finishDrag();
    const b = boardRef.current;
    const origin = dragOrigin.current;
    const list = over && findList(b, active.id);
    if (!list) return onDragCancel();

    const oldIndex = list.cards.findIndex((c) => cardKey(c) === active.id);
    let newIndex = oldIndex;
    const overIdx = list.cards.findIndex((c) => cardKey(c) === String(over.id));
    if (overIdx >= 0) newIndex = overIdx;

    const moved = list.id !== origin.listId || newIndex !== origin.index;
    if (!moved) {
      if (pending.current) setBoard(pending.current); // apply anything that arrived mid-drag
      pending.current = null;
      return;
    }

    let cards = arrayMove(list.cards, oldIndex, newIndex);
    const position = positionBetween(cards[newIndex - 1], cards[newIndex + 1]);
    cards = cards.map((c, i) => (i === newIndex ? { ...c, position, list_id: list.id } : c));
    // Optimistic update: show the result now; the server's broadcast confirms it a moment later
    setBoard({ ...b, lists: b.lists.map((l) => (l.id === list.id ? { ...l, cards } : l)) });
    pending.current = null;
    mutate(() => api(`/cards/${cards[newIndex].id}`, { method: "PATCH", body: { list_id: list.id, position } }));
  }

  function onDragCancel() {
    finishDrag();
    pending.current = null;
    reload(); // restore the true state
  }

  // ---------- actions ----------
  const addCard = (listId, title) =>
    mutate(() => api(`/lists/${listId}/cards`, { method: "POST", body: { title } }));
  const renameList = (listId, title) =>
    mutate(() => api(`/lists/${listId}`, { method: "PATCH", body: { title } }));
  const deleteList = (list) =>
    confirm(`Delete list "${list.title}" and its ${list.cards.length} card(s)?`) &&
    mutate(() => api(`/lists/${list.id}`, { method: "DELETE" }));

  function addList(e) {
    e.preventDefault();
    if (!newList.trim()) return;
    mutate(() => api(`/boards/${board.id}/lists`, { method: "POST", body: { title: newList } }));
    setNewList("");
  }

  function saveCard(cardId, fields) {
    setOpenCard(null);
    mutate(() => api(`/cards/${cardId}`, { method: "PATCH", body: fields }));
  }

  function deleteCard(card) {
    if (!confirm(`Delete "${card.title}"?`)) return;
    setOpenCard(null);
    mutate(() => api(`/cards/${card.id}`, { method: "DELETE" }));
  }

  function saveBoardName() {
    setEditingName(false);
    if (boardName.trim() && boardName !== board.name)
      mutate(() => api(`/boards/${board.id}`, { method: "PATCH", body: { name: boardName } }));
  }

  return (
    <div className="page board-page">
      <header className="topbar">
        <Link to="/" className="ghost">← Boards</Link>
        {editingName ? (
          <input className="board-name-input" autoFocus value={boardName}
                 onChange={(e) => setBoardName(e.target.value)} onBlur={saveBoardName}
                 onKeyDown={(e) => e.key === "Enter" && saveBoardName()} />
        ) : (
          <h1 className="board-name" title="Click to rename"
              onClick={() => { setBoardName(board.name); setEditingName(true); }}>{board.name}</h1>
        )}
        <span className="spacer" />
        <div className="presence" data-testid="presence">
          {viewers.map((v) => (
            <span key={v.id} className={`avatar${v.id === user.id ? " me" : ""}`}
                  title={v.id === user.id ? `${v.name} (you)` : `${v.name} is viewing`}>
              {v.name.slice(0, 1).toUpperCase()}
            </span>
          ))}
        </div>
        <span className={`status status-${status}`} data-testid="status">
          {status === "live" ? "Live" : status === "connecting" ? "Connecting…" : "Reconnecting…"}
        </span>
        <button className="primary" onClick={() => setSharing(true)}>Share</button>
      </header>

      {error && <div className="error banner">{error}</div>}

      <DndContext sensors={sensors} collisionDetection={closestCorners}
                  onDragStart={onDragStart} onDragOver={onDragOver}
                  onDragEnd={onDragEnd} onDragCancel={onDragCancel}>
        <div className="lists">
          {board.lists.map((list) => (
            <ListColumn key={list.id} list={list} onAddCard={addCard} onRename={renameList}
                        onDelete={deleteList} onOpenCard={setOpenCard} />
          ))}
          <form className="column add-list" onSubmit={addList}>
            <input placeholder="+ Add a list" value={newList} onChange={(e) => setNewList(e.target.value)} />
          </form>
        </div>
        <DragOverlay>{activeCard ? <CardView card={activeCard} dragging /> : null}</DragOverlay>
      </DndContext>

      {openCard && (
        <CardModal card={openCard} onSave={saveCard} onDelete={deleteCard} onClose={() => setOpenCard(null)} />
      )}
      {sharing && <ShareDialog board={board} isOwner={isOwner} onClose={() => setSharing(false)} />}
    </div>
  );
}
