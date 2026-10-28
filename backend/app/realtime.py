"""Real-time sync.

Each open board has a set of WebSocket connections. When anything on a board changes, the
REST endpoint commits to the database and then queues a broadcast of the updated board to
everyone viewing it. The database stays the single source of truth; WebSockets only notify.

Note: connections live in this process's memory, so this works for one server instance.
Scaling to several instances would need a shared pub/sub layer (for example Redis).
"""
import asyncio

from fastapi import BackgroundTasks, WebSocket
from sqlmodel import Session

from .board_view import build_board_detail
from .models import Board


class ConnectionManager:
    def __init__(self) -> None:
        # board_id -> list of (websocket, {"id": user_id, "name": name})
        self.rooms: dict[int, list[tuple[WebSocket, dict]]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, board_id: int, ws: WebSocket, user: dict) -> None:
        async with self.lock:
            self.rooms.setdefault(board_id, []).append((ws, user))
        await self.broadcast_presence(board_id)

    async def disconnect(self, board_id: int, ws: WebSocket) -> None:
        async with self.lock:
            room = [(w, u) for (w, u) in self.rooms.get(board_id, []) if w is not ws]
            if room:
                self.rooms[board_id] = room
            else:
                self.rooms.pop(board_id, None)
        await self.broadcast_presence(board_id)

    def viewers(self, board_id: int) -> list[dict]:
        seen: dict[int, dict] = {}
        for _, u in self.rooms.get(board_id, []):
            seen[u["id"]] = u  # one entry per user even with several tabs open
        return list(seen.values())

    async def broadcast(self, board_id: int, message: dict) -> None:
        dead = []
        for ws, _ in list(self.rooms.get(board_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)  # client vanished without a clean close
        for ws in dead:
            await self.disconnect(board_id, ws)

    async def broadcast_presence(self, board_id: int) -> None:
        await self.broadcast(board_id, {"type": "presence", "users": self.viewers(board_id)})


manager = ConnectionManager()


def queue_board_update(bg: BackgroundTasks, board: Board, session: Session) -> None:
    """Call after committing a change: snapshot the board now, broadcast after the response."""
    snapshot = build_board_detail(board, session).model_dump()
    bg.add_task(manager.broadcast, board.id, {"type": "board", "board": snapshot})


def queue_board_deleted(bg: BackgroundTasks, board_id: int) -> None:
    bg.add_task(manager.broadcast, board_id, {"type": "board_deleted", "board_id": board_id})
