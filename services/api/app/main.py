from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.mongo import close_client, get_db
from app.db.redis_client import close_redis
from app.db.seed import ensure_seed
from app.routers import admin, articles, categories, health, preferences, sources, stats, topics
from app.routers.articles import list_bookmarks


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    db = get_db()
    await db.articles.create_index([("category", 1), ("published_at", -1)])
    await db.articles.create_index("dedup_hash", unique=True)
    await db.articles.create_index("importance")
    await db.articles.create_index([("title", "text"), ("summary", "text"), ("tags", "text")])
    await db.user_article_state.create_index(
        [("user_id", 1), ("article_id", 1)], unique=True
    )
    await db.topics.create_index("slug", unique=True)
    await ensure_seed(db)
    yield
    await close_redis()
    await close_client()


app = FastAPI(
    title="News Dashboard API",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["capacitor://localhost", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(categories.router)
app.include_router(sources.router)
app.include_router(topics.router)
app.include_router(articles.router)
app.include_router(preferences.router)
app.include_router(stats.router)
app.include_router(admin.router)
app.add_api_route("/bookmarks", list_bookmarks, methods=["GET"], tags=["bookmarks"])


@app.get("/")
async def root():
    return {"service": "news-dashboard-api", "docs": "/docs"}
