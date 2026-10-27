"""Database tables. One board has many lists; one list has many cards."""
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    name: str
    hashed_password: str
    created_at: datetime = Field(default_factory=utcnow)


class Board(SQLModel, table=True):
    __tablename__ = "boards"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    owner_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=utcnow)


class BoardMember(SQLModel, table=True):
    """Who besides the owner can access a board."""
    __tablename__ = "board_members"
    board_id: int = Field(foreign_key="boards.id", primary_key=True)
    user_id: int = Field(foreign_key="users.id", primary_key=True)


class TaskList(SQLModel, table=True):
    """A column on a board (named TaskList to avoid clashing with Python's list)."""
    __tablename__ = "lists"
    id: int | None = Field(default=None, primary_key=True)
    board_id: int = Field(foreign_key="boards.id", index=True)
    title: str
    position: float  # sort key; floats let us insert between two items later


class Card(SQLModel, table=True):
    __tablename__ = "cards"
    id: int | None = Field(default=None, primary_key=True)
    list_id: int = Field(foreign_key="lists.id", index=True)
    title: str
    description: str = ""
    position: float
    created_at: datetime = Field(default_factory=utcnow)
