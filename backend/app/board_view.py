from sqlmodel import Session, select

from .models import Board, Card, TaskList
from .schemas import BoardDetail, CardRead, ListWithCards


def build_board_detail(board: Board, session: Session) -> BoardDetail:
    """The full board: lists in order, each with its cards in order."""
    lists = session.exec(
        select(TaskList).where(TaskList.board_id == board.id).order_by(TaskList.position)
    ).all()
    list_ids = [l.id for l in lists]
    cards = session.exec(
        select(Card).where(Card.list_id.in_(list_ids)).order_by(Card.position)
    ).all() if list_ids else []
    by_list: dict[int, list[CardRead]] = {l.id: [] for l in lists}
    for c in cards:
        by_list[c.list_id].append(CardRead.model_validate(c, from_attributes=True))
    return BoardDetail(
        id=board.id, name=board.name, owner_id=board.owner_id,
        lists=[ListWithCards(id=l.id, board_id=l.board_id, title=l.title,
                             position=l.position, cards=by_list[l.id]) for l in lists],
    )
