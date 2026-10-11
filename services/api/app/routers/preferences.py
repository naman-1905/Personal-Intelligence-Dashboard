from fastapi import APIRouter

from app.core.config import get_settings
from app.db.mongo import get_db
from app.models.schemas import PreferencesIn, PreferencesOut

router = APIRouter(prefix="/preferences", tags=["preferences"])


def _to_out(doc: dict) -> PreferencesOut:
    return PreferencesOut(
        user_id=doc.get("user_id", get_settings().user_id),
        selected_categories=doc.get("selected_categories", []),
        category_order=doc.get("category_order", []),
        mute_keywords=doc.get("mute_keywords", []),
        theme=doc.get("theme", "system"),
        digest_hour=doc.get("digest_hour", get_settings().digest_default_hour),
        refresh_interval_minutes=doc.get("refresh_interval_minutes"),
        show_thumbnails=doc.get("show_thumbnails", False),
        notify_high_importance=doc.get("notify_high_importance", False),
    )


@router.get("", response_model=PreferencesOut)
async def get_preferences() -> PreferencesOut:
    db = get_db()
    user_id = get_settings().user_id
    doc = await db.user_preferences.find_one({"user_id": user_id})
    if not doc:
        doc = {
            "user_id": user_id,
            "selected_categories": [
                "technology", "software-dev", "ai-ml", "gaming", "india",
                "politics-policy", "business", "cars", "f1", "marvel",
                "science", "world",
            ],
            "category_order": [
                "technology", "software-dev", "ai-ml", "gaming", "india",
                "politics-policy", "business", "cars", "f1", "marvel",
                "science", "world",
            ],
            "mute_keywords": [],
            "theme": "system",
            "digest_hour": get_settings().digest_default_hour,
            "show_thumbnails": False,
            "notify_high_importance": False,
        }
        await db.user_preferences.insert_one(doc)
    return _to_out(doc)


@router.post("", response_model=PreferencesOut)
async def update_preferences(body: PreferencesIn) -> PreferencesOut:
    db = get_db()
    user_id = get_settings().user_id
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if updates:
        await db.user_preferences.update_one(
            {"user_id": user_id},
            {"$set": updates},
            upsert=True,
        )
    doc = await db.user_preferences.find_one({"user_id": user_id}) or {"user_id": user_id}
    return _to_out(doc)
