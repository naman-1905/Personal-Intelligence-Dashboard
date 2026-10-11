from fastapi import APIRouter

from app.db.mongo import get_db
from app.models.schemas import SourceOut

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
async def list_sources() -> list[SourceOut]:
    cursor = get_db().sources.find().sort("name", 1)
    items: list[SourceOut] = []
    async for doc in cursor:
        items.append(
            SourceOut(
                name=doc["name"],
                display_name=doc.get("display_name") or doc["name"],
                category=doc["category"],
                type=doc["type"],
                url=doc["url"],
                trust_tier=doc.get("trust_tier", 1),
                enabled=doc.get("enabled", True),
            )
        )
    return items
