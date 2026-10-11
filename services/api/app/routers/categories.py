from fastapi import APIRouter

from app.core.config import get_settings
from app.db.mongo import get_db
from app.models.schemas import CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories() -> list[CategoryOut]:
    db = get_db()
    user_id = get_settings().user_id
    prefs = await db.user_preferences.find_one({"user_id": user_id}) or {}
    order = prefs.get("category_order") or []

    cursor = db.categories.find({"enabled": True}).sort("display_order", 1)
    items: list[CategoryOut] = []
    async for doc in cursor:
        slug = doc["slug"]
        read_ids = [
            s["article_id"]
            async for s in db.user_article_state.find(
                {"user_id": user_id, "read": True}, {"article_id": 1}
            )
        ]
        unread = await db.articles.count_documents(
            {
                "category": slug,
                "status": "active",
                "_id": {"$nin": read_ids} if read_ids else {"$exists": True},
            }
        )
        items.append(
            CategoryOut(
                slug=slug,
                name=doc.get("name", slug),
                icon=doc.get("icon", ""),
                display_order=doc.get("display_order", 0),
                enabled=doc.get("enabled", True),
                unread_count=unread,
            )
        )

    if order:
        rank = {s: i for i, s in enumerate(order)}
        items.sort(key=lambda c: rank.get(c.slug, 999))
    return items
