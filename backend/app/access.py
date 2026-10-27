"""Access control: every board, list, and card lookup goes through here.

Boards you can't access return 404 (not 403) so we don't reveal that they exist.
"""
from fastapi import HTTPException, status
from sqlmodel import Session, func, select

from .models import Board, BoardMember, Card, TaskList, User


def can_access(board: Board, user: User, session: Session) -> bool:
    if board.owner_id == user.id:
        return True
    return session.get(BoardMember, (board.id, user.id)) is not None


def get_board_or_404(board_id: int, user: User, session: Session) -> Board:
    board = session.get(Board, board_id)
    if board is None or not can_access(board, user, session):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Board not found")
    return board


def get_list_or_404(list_id: int, user: User, session: Session) -> TaskList:
    lst = session.get(TaskList, list_id)
    if lst is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "List not found")
    get_board_or_404(lst.board_id, user, session)
    return lst


def get_card_or_404(card_id: int, user: User, session: Session) -> Card:
    card = session.get(Card, card_id)
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Card not found")
    get_list_or_404(card.list_id, user, session)
    return card


def next_position(session: Session, model, parent_field, parent_id: int) -> float:
    """Append to the end: one more than the current max position."""
    current = session.exec(
        select(func.max(model.position)).where(parent_field == parent_id)
    ).one()
    return (current or 0) + 1
