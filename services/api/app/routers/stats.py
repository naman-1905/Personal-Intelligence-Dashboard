from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings
from app.db.mongo import get_db
from app.db.redis_client import get_redis
from app.models.schemas import StatsOut

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
async def get_stats() -> StatsOut:
    db = get_db()
    user_id = get_settings().user_id
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    articles_active = await db.articles.count_documents({"status": "active"})
    sources_enabled = await db.sources.count_documents({"enabled": True})
    articles_read = await db.user_article_state.count_documents(
        {"user_id": user_id, "read": True}
    )
    bookmarks = await db.user_article_state.count_documents(
        {"user_id": user_id, "bookmarked": True}
    )

    filtered_today = 0
    try:
        raw = await get_redis().get("stats:filtered_today")
        if raw is not None:
            filtered_today = int(raw)
    except Exception:  # noqa: BLE001
        pass

    if filtered_today == 0:
        run = await db.scrape_runs.find_one(
            {"started_at": {"$gte": start}},
            sort=[("started_at", -1)],
        )
        if run:
            filtered_today = int(run.get("filtered_out", 0))

    # Rough: ~2 minutes avoided per filtered article + unread noise not opened
    time_saved = filtered_today * 2 + max(0, articles_active - articles_read) // 5

    return StatsOut(
        articles_active=articles_active,
        articles_filtered_today=filtered_today,
        sources_enabled=sources_enabled,
        articles_read=articles_read,
        bookmarks=bookmarks,
        time_saved_minutes_estimate=time_saved,
    )
