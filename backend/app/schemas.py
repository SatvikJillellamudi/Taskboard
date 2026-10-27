"""Request and response shapes. Separate from the tables so we never leak hashed_password."""
from pydantic import BaseModel, Field


# ---- auth ----
class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=64)


class UserRead(BaseModel):
    id: int
    email: str
    name: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- boards ----
class BoardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class BoardUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class BoardRead(BaseModel):
    id: int
    name: str
    owner_id: int


class MemberAdd(BaseModel):
    email: str


# ---- lists ----
class ListCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)


class ListUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    position: float | None = None


# ---- cards ----
class CardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)


class CardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    position: float | None = None
    list_id: int | None = None  # set this to move the card to another list


class CardRead(BaseModel):
    id: int
    list_id: int
    title: str
    description: str
    position: float


class ListRead(BaseModel):
    id: int
    board_id: int
    title: str
    position: float


class ListWithCards(ListRead):
    cards: list[CardRead]


class BoardDetail(BoardRead):
    lists: list[ListWithCards]
