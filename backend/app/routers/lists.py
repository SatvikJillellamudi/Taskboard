from fastapi import APIRouter, BackgroundTasks, Depends, Response, status
from sqlmodel import Session, select

from ..access import get_board_or_404, get_list_or_404, next_position
from ..auth import get_current_user
from ..database import get_session
from ..models import Board, Card, TaskList, User
from ..realtime import queue_board_update
from ..schemas import ListCreate, ListRead, ListUpdate

router = APIRouter(tags=["lists"])


@router.post("/boards/{board_id}/lists", response_model=ListRead, status_code=status.HTTP_201_CREATED)
def create_list(board_id: int, data: ListCreate, bg: BackgroundTasks, user: User = Depends(get_current_user),
                session: Session = Depends(get_session)):
    board = get_board_or_404(board_id, user, session)
    lst = TaskList(board_id=board.id, title=data.title.strip(),
                   position=next_position(session, TaskList, TaskList.board_id, board.id))
    session.add(lst)
    session.commit()
    session.refresh(lst)
    queue_board_update(bg, board, session)
    return lst


@router.patch("/lists/{list_id}", response_model=ListRead)
def update_list(list_id: int, data: ListUpdate, bg: BackgroundTasks, user: User = Depends(get_current_user),
                session: Session = Depends(get_session)):
    lst = get_list_or_404(list_id, user, session)
    if data.title is not None:
        lst.title = data.title.strip()
    if data.position is not None:
        lst.position = data.position
    session.add(lst)
    session.commit()
    session.refresh(lst)
    queue_board_update(bg, session.get(Board, lst.board_id), session)
    return lst


@router.delete("/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(list_id: int, bg: BackgroundTasks, user: User = Depends(get_current_user),
                session: Session = Depends(get_session)):
    lst = get_list_or_404(list_id, user, session)
    for c in session.exec(select(Card).where(Card.list_id == lst.id)).all():
        session.delete(c)
    board_id = lst.board_id
    session.delete(lst)
    session.commit()
    queue_board_update(bg, session.get(Board, board_id), session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
