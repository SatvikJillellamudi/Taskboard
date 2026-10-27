# Taskboard: Real-Time Collaborative Task Board

A Trello-style board where multiple users collaborate on shared boards in real time.
React frontend (coming), FastAPI backend, PostgreSQL in production, WebSockets for live sync.

**Status:** backend with auth, data model, secured REST API, and tests.

## Backend quick start (Windows, Git Bash)

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate        # Mac/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env                 # then paste a real JWT_SECRET into .env
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive API docs. Sign up via `POST /auth/signup`,
then click **Authorize** (top right) and log in with your email as the username. Every
request after that is authenticated automatically.

Run the tests: `python -m pytest -q`

(`python -m uvicorn` and `python -m pytest` avoid the Windows "command not found" PATH issue.)

## How the backend is organized

| File | What it does |
|---|---|
| `app/main.py` | Creates the app, enables CORS, mounts the routers |
| `app/config.py` | Settings from environment variables (`.env`) |
| `app/database.py` | Database engine and the per-request session dependency |
| `app/models.py` | Database tables: users, boards, board_members, lists, cards |
| `app/schemas.py` | Request/response shapes (keeps password hashes out of responses) |
| `app/auth.py` | bcrypt hashing, JWT creation/validation, `get_current_user` |
| `app/access.py` | Access control: who can see which board, list, or card |
| `app/routers/` | The endpoints, grouped by resource |
| `tests/` | 12 tests: auth, CRUD, reordering, access control, cascade delete |

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/signup` | Create an account |
| POST | `/auth/login` | Get a JWT (form: username=email, password) |
| GET | `/auth/me` | Current user |
| GET / POST | `/boards` | Boards you own or are a member of / create one |
| GET / PATCH / DELETE | `/boards/{id}` | Full board with lists and cards / rename / delete (owner) |
| GET / POST | `/boards/{id}/members` | List members / invite by email (owner) |
| POST | `/boards/{id}/lists` | Add a list |
| PATCH / DELETE | `/lists/{id}` | Rename or reorder / delete a list |
| POST | `/lists/{id}/cards` | Add a card |
| PATCH / DELETE | `/cards/{id}` | Edit, reorder, or move a card / delete it |

## Design decisions

- **JWT auth**: the API stays stateless; the frontend sends `Authorization: Bearer <token>`.
  Passwords are hashed with bcrypt (salted, deliberately slow).
- **404 instead of 403** for boards you can't access, so the API never confirms a private
  board exists.
- **Float positions** for ordering: dragging a card between positions 1 and 2 gives it 1.5,
  with no need to renumber everything else.
- **One access-control module**: every lookup goes through `access.py`, so permission rules
  live in one place instead of being repeated (and possibly forgotten) in each endpoint.
- **SQLite locally, Postgres in production**: same code, switched by `DATABASE_URL`.

