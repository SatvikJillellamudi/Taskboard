from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlmodel import Session

from ..access import get_card_or_404, get_list_or_404, next_position
from ..auth import get_current_user
from ..database import get_session
from ..models import Board, Card, TaskList, User
from ..realtime import queue_board_update
from ..schemas import CardCreate, CardRead, CardUpdate

router = APIRouter(tags=["cards"])


@router.post("/lists/{list_id}/cards", response_model=CardRead, status_code=status.HTTP_201_CREATED)
def create_card(list_id: int, data: CardCreate, bg: BackgroundTasks, user: User = Depends(get_current_user),
                session: Session = Depends(get_session)):
    lst = get_list_or_404(list_id, user, session)
    card = Card(list_id=lst.id, title=data.title.strip(), description=data.description,
                position=next_position(session, Card, Card.list_id, lst.id))
    session.add(card)
    session.commit()
    session.refresh(card)
    queue_board_update(bg, session.get(Board, lst.board_id), session)
    return card


@router.patch("/cards/{card_id}", response_model=CardRead)
def update_card(card_id: int, data: CardUpdate, bg: BackgroundTasks, user: User = Depends(get_current_user),
                session: Session = Depends(get_session)):
    """Edit a card, reorder it (position), or move it to another list (list_id)."""
    card = get_card_or_404(card_id, user, session)
    if data.list_id is not None and data.list_id != card.list_id:
        source = get_list_or_404(card.list_id, user, session)
        target = get_list_or_404(data.list_id, user, session)
        if target.board_id != source.board_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Can only move cards within the same board")
        card.list_id = target.id
        if data.position is None:  # no position given: drop it at the end of the new list
            card.position = next_position(session, Card, Card.list_id, target.id)
    if data.title is not None:
        card.title = data.title.strip()
    if data.description is not None:
        card.description = data.description
    if data.position is not None:
        card.position = data.position
    session.add(card)
    session.commit()
    session.refresh(card)
    board_id = session.get(TaskList, card.list_id).board_id
    queue_board_update(bg, session.get(Board, board_id), session)
    return card


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: int, bg: BackgroundTasks, user: User = Depends(get_current_user),
                session: Session = Depends(get_session)):
    card = get_card_or_404(card_id, user, session)
    board_id = session.get(TaskList, card.list_id).board_id
    session.delete(card)
    session.commit()
    queue_board_update(bg, session.get(Board, board_id), session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
