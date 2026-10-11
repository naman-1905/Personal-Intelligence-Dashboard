import json

from fastapi import APIRouter

from app.db.redis_client import get_redis
from app.models.schemas import TriggerScrapeOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/trigger-scrape", response_model=TriggerScrapeOut)
async def trigger_scrape() -> TriggerScrapeOut:
    """Signal the scraper service via Redis pub/sub. No cloud webhooks."""
    redis = get_redis()
    await redis.publish("scraper:commands", json.dumps({"action": "scrape_now"}))
    await redis.set("scraper:trigger", "1", ex=300)
    return TriggerScrapeOut(
        accepted=True,
        message="Scrape trigger published to local Redis channel scraper:commands",
    )
