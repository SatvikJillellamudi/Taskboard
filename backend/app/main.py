from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routers import auth, boards, cards, lists


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # create tables on startup
    yield


app = FastAPI(title="Taskboard API", version="0.1.0", lifespan=lifespan)

# Allow the React dev server (and later the deployed frontend) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(boards.router)
app.include_router(lists.router)
app.include_router(cards.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
