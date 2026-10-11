from fastapi import APIRouter

from app.db.mongo import get_db
from app.db.redis_client import get_redis
from app.models.schemas import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    mongo_ok = False
    redis_ok = False
    details: dict = {}

    try:
        await get_db().command("ping")
        mongo_ok = True
    except Exception as exc:  # noqa: BLE001
        details["mongo_error"] = str(exc)

    try:
        redis_ok = (await get_redis().ping()) is True
    except Exception as exc:  # noqa: BLE001
        details["redis_error"] = str(exc)

    status = "ok" if mongo_ok and redis_ok else "degraded"
    return HealthOut(status=status, mongo=mongo_ok, redis=redis_ok, details=details)
