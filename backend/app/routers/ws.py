from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlmodel import Session

from ..access import can_access
from ..auth import user_from_token
from ..board_view import build_board_detail
from ..database import get_session
from ..models import Board
from ..realtime import manager

router = APIRouter(tags=["realtime"])

# Custom close codes (4000-4999 are reserved for applications)
UNAUTHORIZED = 4401
NOT_FOUND = 4404


@router.websocket("/ws/boards/{board_id}")
async def board_socket(websocket: WebSocket, board_id: int, token: str = "",
                       session: Session = Depends(get_session)):
    # Browsers can't set headers on a WebSocket, so the JWT comes as ?token=
    await websocket.accept()
    user = user_from_token(token, session)
    if user is None:
        await websocket.close(code=UNAUTHORIZED)
        return
    board = session.get(Board, board_id)
    if board is None or not can_access(board, user, session):
        await websocket.close(code=NOT_FOUND)
        return

    viewer = {"id": user.id, "name": user.name}
    snapshot = build_board_detail(board, session).model_dump()
    session.close()  # release the DB connection; we don't need it while the socket is open

    await websocket.send_json({"type": "board", "board": snapshot})
    await manager.connect(board_id, websocket, viewer)
    try:
        while True:
            await websocket.receive_text()  # we only push; incoming messages are keepalives
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(board_id, websocket)
