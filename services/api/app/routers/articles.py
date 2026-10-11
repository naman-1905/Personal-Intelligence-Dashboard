from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.db.mongo import get_db
from app.models.schemas import ArticleOut, PaginatedArticles

router = APIRouter(prefix="/articles", tags=["articles"])


def _serialize(doc: dict, state: dict | None = None) -> ArticleOut:
    state = state or {}
    return ArticleOut(
        _id=str(doc["_id"]),
        source=doc.get("source", ""),
        category=doc.get("category", ""),
        title=doc.get("title", ""),
        summary=doc.get("summary", ""),
        article=doc.get("article") or doc.get("summary", ""),
        url=doc.get("url", ""),
        published_at=doc.get("published_at"),
        scraped_at=doc.get("scraped_at"),
        importance=doc.get("importance", "medium"),
        tags=doc.get("tags") or [],
        status=doc.get("status", "active"),
        read=bool(state.get("read", False)),
        bookmarked=bool(state.get("bookmarked", False)),
    )


async def _states_map(user_id: str, article_ids: list[ObjectId]) -> dict[str, dict]:
    if not article_ids:
        return {}
    db = get_db()
    out: dict[str, dict] = {}
    async for s in db.user_article_state.find(
        {"user_id": user_id, "article_id": {"$in": article_ids}}
    ):
        out[str(s["article_id"])] = s
    return out


async def _mute_keywords(user_id: str) -> list[str]:
    prefs = await get_db().user_preferences.find_one({"user_id": user_id}) or {}
    return [k.lower() for k in prefs.get("mute_keywords") or []]


def _apply_mute(query: dict, mutes: list[str]) -> dict:
    if not mutes:
        return query
    clauses = []
    for kw in mutes:
        clauses.append({"title": {"$not": {"$regex": kw, "$options": "i"}}})
        clauses.append({"summary": {"$not": {"$regex": kw, "$options": "i"}}})
    query = {**query, "$and": query.get("$and", []) + clauses}
    return query


@router.get("", response_model=PaginatedArticles)
async def list_articles(
    category: str | None = None,
    topic: str | None = None,
    importance: str | None = None,
    since: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
) -> PaginatedArticles:
    db = get_db()
    user_id = get_settings().user_id
    mutes = await _mute_keywords(user_id)

    query: dict = {"status": "active"}
    if category:
        query["category"] = category
    if topic:
        query["source"] = f"topic:{topic}"
    if importance:
        query["importance"] = importance
    if since:
        query["published_at"] = {"$gte": since}
    if q:
        query["$text"] = {"$search": q}

    query = _apply_mute(query, mutes)
    total = await db.articles.count_documents(query)
    skip = (page - 1) * page_size
    cursor = (
        db.articles.find(query)
        .sort([("published_at", -1), ("_id", -1)])
        .skip(skip)
        .limit(page_size)
    )
    docs = [doc async for doc in cursor]
    states = await _states_map(user_id, [d["_id"] for d in docs])
    items = [_serialize(d, states.get(str(d["_id"]))) for d in docs]
    return PaginatedArticles(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        has_more=skip + len(items) < total,
    )


@router.get("/digest", response_model=list[ArticleOut])
async def morning_digest(when: str = "morning", limit: int = Query(15, ge=1, le=50)) -> list[ArticleOut]:
    db = get_db()
    user_id = get_settings().user_id
    prefs = await db.user_preferences.find_one({"user_id": user_id}) or {}
    hour = prefs.get("digest_hour", get_settings().digest_default_hour)
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)
    if when == "morning":
        since = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if since > now:
            since = since - timedelta(days=1)

    mutes = await _mute_keywords(user_id)
    query: dict = {
        "status": "active",
        "importance": "high",
        "published_at": {"$gte": since},
    }
    selected = prefs.get("selected_categories")
    if selected:
        query["category"] = {"$in": selected}
    query = _apply_mute(query, mutes)

    docs = [
        doc
        async for doc in db.articles.find(query)
        .sort([("published_at", -1)])
        .limit(limit)
    ]
    if len(docs) < limit:
        fallback = {
            "status": "active",
            "published_at": {"$gte": since},
            "_id": {"$nin": [d["_id"] for d in docs]},
        }
        if selected:
            fallback["category"] = {"$in": selected}
        fallback = _apply_mute(fallback, mutes)
        extra = [
            doc
            async for doc in db.articles.find(fallback)
            .sort([("importance", -1), ("published_at", -1)])
            .limit(limit - len(docs))
        ]
        docs.extend(extra)

    states = await _states_map(user_id, [d["_id"] for d in docs])
    return [_serialize(d, states.get(str(d["_id"]))) for d in docs]


@router.get("/bookmarks", response_model=list[ArticleOut])
async def list_bookmarks() -> list[ArticleOut]:
    db = get_db()
    user_id = get_settings().user_id
    bookmarked = [
        s
        async for s in db.user_article_state.find(
            {"user_id": user_id, "bookmarked": True}
        )
    ]
    ids = [s["article_id"] for s in bookmarked]
    if not ids:
        return []
    docs = [doc async for doc in db.articles.find({"_id": {"$in": ids}})]
    by_id = {d["_id"]: d for d in docs}
    state_by_id = {s["article_id"]: s for s in bookmarked}
    items = []
    for aid in ids:
        doc = by_id.get(aid)
        if doc:
            items.append(_serialize(doc, state_by_id.get(aid)))
    return items


@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(article_id: str) -> ArticleOut:
    if not ObjectId.is_valid(article_id):
        raise HTTPException(status_code=400, detail="Invalid article id")
    db = get_db()
    doc = await db.articles.find_one({"_id": ObjectId(article_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    user_id = get_settings().user_id
    state = await db.user_article_state.find_one(
        {"user_id": user_id, "article_id": doc["_id"]}
    )
    return _serialize(doc, state)


@router.post("/{article_id}/read", response_model=ArticleOut)
async def mark_read(article_id: str) -> ArticleOut:
    if not ObjectId.is_valid(article_id):
        raise HTTPException(status_code=400, detail="Invalid article id")
    db = get_db()
    oid = ObjectId(article_id)
    doc = await db.articles.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    user_id = get_settings().user_id
    await db.user_article_state.update_one(
        {"user_id": user_id, "article_id": oid},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    state = await db.user_article_state.find_one(
        {"user_id": user_id, "article_id": oid}
    )
    return _serialize(doc, state)


@router.post("/{article_id}/bookmark", response_model=ArticleOut)
async def toggle_bookmark(article_id: str) -> ArticleOut:
    if not ObjectId.is_valid(article_id):
        raise HTTPException(status_code=400, detail="Invalid article id")
    db = get_db()
    oid = ObjectId(article_id)
    doc = await db.articles.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    user_id = get_settings().user_id
    existing = await db.user_article_state.find_one(
        {"user_id": user_id, "article_id": oid}
    )
    new_val = not bool(existing and existing.get("bookmarked"))
    await db.user_article_state.update_one(
        {"user_id": user_id, "article_id": oid},
        {"$set": {"bookmarked": new_val}},
        upsert=True,
    )
    state = await db.user_article_state.find_one(
        {"user_id": user_id, "article_id": oid}
    )
    return _serialize(doc, state)
