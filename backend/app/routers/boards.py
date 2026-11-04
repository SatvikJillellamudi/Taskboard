from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from sqlmodel import Session, delete, or_, select

from ..access import get_board_or_404
from ..board_view import build_board_detail
from ..realtime import queue_board_deleted, queue_board_update
from ..auth import get_current_user
from ..database import get_session
from ..models import Board, BoardMember, Card, TaskList, User
from ..schemas import BoardCreate, BoardDetail, BoardRead, BoardUpdate, MemberAdd, UserRead

router = APIRouter(prefix="/boards", tags=["boards"])


@router.get("", response_model=list[BoardRead])
def list_boards(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    member_of = select(BoardMember.board_id).where(BoardMember.user_id == user.id)
    stmt = select(Board).where(or_(Board.owner_id == user.id, Board.id.in_(member_of))).order_by(Board.id)
    return session.exec(stmt).all()


@router.post("", response_model=BoardRead, status_code=status.HTTP_201_CREATED)
def create_board(data: BoardCreate, user: User = Depends(get_current_user),
                 session: Session = Depends(get_session)):
    board = Board(name=data.name.strip(), owner_id=user.id)
    session.add(board)
    session.commit()
    session.refresh(board)
    return board


@router.get("/{board_id}", response_model=BoardDetail)
def get_board(board_id: int, user: User = Depends(get_current_user),
              session: Session = Depends(get_session)):
    """The full board: lists in order, each with its cards in order."""
    return build_board_detail(get_board_or_404(board_id, user, session), session)


@router.patch("/{board_id}", response_model=BoardRead)
def rename_board(board_id: int, data: BoardUpdate, bg: BackgroundTasks,
                 user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    board = get_board_or_404(board_id, user, session)
    board.name = data.name.strip()
    session.add(board)
    session.commit()
    session.refresh(board)
    queue_board_update(bg, board, session)
    return board


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(board_id: int, bg: BackgroundTasks, user: User = Depends(get_current_user),
                 session: Session = Depends(get_session)):
    board = get_board_or_404(board_id, user, session)
    if board.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the owner can delete a board")
    # Delete in foreign-key order: cards -> lists -> memberships -> board.
    # Explicit statements make the order guaranteed, so Postgres never sees a row
    # still pointing at something already deleted.
    list_ids = select(TaskList.id).where(TaskList.board_id == board.id)
    session.exec(delete(Card).where(Card.list_id.in_(list_ids)))
    session.exec(delete(TaskList).where(TaskList.board_id == board.id))
    session.exec(delete(BoardMember).where(BoardMember.board_id == board.id))
    session.exec(delete(Board).where(Board.id == board.id))
    session.commit()
    queue_board_deleted(bg, board_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{board_id}/members", response_model=list[UserRead])
def list_members(board_id: int, user: User = Depends(get_current_user),
                 session: Session = Depends(get_session)):
    board = get_board_or_404(board_id, user, session)
    member_ids = select(BoardMember.user_id).where(BoardMember.board_id == board.id)
    return session.exec(
        select(User).where(or_(User.id == board.owner_id, User.id.in_(member_ids))).order_by(User.id)
    ).all()


@router.post("/{board_id}/members", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def add_member(board_id: int, data: MemberAdd, user: User = Depends(get_current_user),
               session: Session = Depends(get_session)):
    board = get_board_or_404(board_id, user, session)
    if board.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the owner can add members")
    invitee = session.exec(select(User).where(User.email == data.email.lower().strip())).first()
    if invitee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No user with that email")
    if invitee.id == board.owner_id or session.get(BoardMember, (board.id, invitee.id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "User already has access")
    session.add(BoardMember(board_id=board.id, user_id=invitee.id))
    session.commit()
    return invitee
