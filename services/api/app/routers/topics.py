from fastapi import APIRouter

from app.db.mongo import get_db
from app.models.schemas import TopicOut

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=list[TopicOut])
async def list_topics() -> list[TopicOut]:
    db = get_db()
    items: list[TopicOut] = []
    async for doc in db.topics.find({"enabled": True}).sort("name", 1):
        count = await db.articles.count_documents(
            {"source": doc.get("source_name"), "status": "active"}
        )
        items.append(
            TopicOut(
                slug=doc["slug"],
                name=doc.get("name", doc["slug"]),
                query=doc.get("query", ""),
                source_name=doc.get("source_name", ""),
                article_count=count,
            )
        )
    return items
