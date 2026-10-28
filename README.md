# Taskboard: Real-Time Collaborative Task Board

A Trello-style board where multiple people work on shared boards at the same time. Move a
card and everyone viewing the board sees it move instantly.

**Stack:** React (Vite) · FastAPI (Python) · SQLite locally / PostgreSQL in production · WebSockets · dnd-kit

**Status:** Auth, data model, secured REST API, React frontend,
drag-and-drop, real-time sync, presence. Deployment is next.

<!-- Add a GIF here of two browser windows syncing: it is the best demo of this project. -->

## Features
- Accounts with hashed passwords and JWT authentication
- Boards with lists and cards; create, rename, edit, delete
- Drag-and-drop cards within and between lists (mouse and keyboard)
- **Real-time sync:** every change is pushed to everyone viewing the board
- **Presence:** see who else is on the board right now
- Share a board with another user by email; owners control deletion and invites
- Auto-reconnect with backoff if the connection drops

## Run it locally (Windows, Git Bash)

**Backend** (terminal 1):
```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
cp .env.example .env               # paste a real JWT_SECRET into .env
python -m uvicorn app.main:app --reload
```

**Frontend** (terminal 2):
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. To see real-time sync, sign up two accounts (use a normal
window and an incognito window), share a board from one to the other, and open it in both.

API docs: http://127.0.0.1:8000/docs

## Architecture
```
React app ──REST (create/update/delete)──▶ FastAPI ──▶ Database (source of truth)
    ▲                                         │
    └──────── WebSocket: updated board ◀──────┘  broadcast to everyone on that board
```
1. A user changes something; the frontend sends a normal REST request.
2. FastAPI checks permissions, writes to the database, and responds.
3. After responding, it broadcasts the updated board over WebSockets to every viewer.
4. Each client replaces its local board with the server's version.

## Design decisions
- **REST for changes, WebSockets for notifications.** Writes go through normal, testable,
  permission-checked endpoints. The socket only pushes results, so the database is always
  the source of truth and a page refresh always shows the real state.
- **Broadcast the full board, not deltas.** Every client gets the authoritative snapshot, so
  clients can never drift out of sync. Fine at this scale; very large boards would switch to
  sending only the changed items.
- **Optimistic drag-and-drop.** A dropped card moves instantly on your screen, and the
  server's broadcast confirms it. If the request fails, the board reloads to the true state.
- **No jumping mid-drag.** If another user's change arrives while you're dragging, it's held
  until you drop, so the board doesn't shift under your cursor.
- **Float positions.** Dropping a card between positions 1 and 2 gives it 1.5, so a move
  updates one row instead of renumbering the whole list.
- **JWT in the WebSocket URL.** Browsers can't set headers on WebSocket connections, so the
  token goes in the query string and is validated before the socket joins the board.
- **404 instead of 403** for boards you can't access, so the API never confirms a private
  board exists.
- **Known limit:** connected sockets live in one server's memory. Running several server
  instances would need a shared pub/sub layer such as Redis.

## Testing
- **Backend:** 17 pytest tests covering auth, CRUD, reordering, access control, cascade
  deletes, and WebSockets (token rejection, access rejection, presence, live broadcast).
  Run: `cd backend && python -m pytest -q`
- **End-to-end:** `e2e/test_two_users.py` drives two real browsers as two users and checks
  sharing, presence, live updates, drag-and-drop across and within lists, and persistence
  across reloads (9 checks). Setup instructions are at the top of the file.

## Project structure
| Path | What it does |
|---|---|
| `backend/app/auth.py` | bcrypt hashing, JWTs, current-user dependency |
| `backend/app/access.py` | Who can access which board, list, or card |
| `backend/app/realtime.py` | WebSocket connection manager, presence, broadcasts |
| `backend/app/routers/` | REST endpoints and the WebSocket endpoint |
| `frontend/src/api.js` | Fetch wrapper that attaches the JWT |
| `frontend/src/useBoardSocket.js` | WebSocket hook with auto-reconnect |
| `frontend/src/pages/BoardPage.jsx` | The board: drag-and-drop, live updates, presence |
| `e2e/` | Two-user browser test |
