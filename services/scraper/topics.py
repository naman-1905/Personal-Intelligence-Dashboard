from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

DOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}$", re.IGNORECASE)

# keyword hints -> category; topics that match none fall back to "topics"
CATEGORY_HINTS: dict[str, list[str]] = {
    "ai-ml": ["ai", "machine learning", "deep learning", "llm", "neural", "openai", "anthropic"],
    "software-dev": ["programming", "software", "developer", "coding", "open source"],
    "gaming": ["gaming", "game", "esports", "playstation", "xbox", "nintendo", "steam"],
    "india": ["india", "bharat", "mumbai", "delhi", "bangalore"],
    "cars": ["automotive", "tesla", "electric vehicle", "car market"],
    "f1": ["formula 1", "formula one", "f1", "racing"],
    "marvel": ["marvel", "mcu", "avengers", "spider-man", "iron man"],
    "technology": ["tech", "internet", "chip", "semiconductor", "hardware"],
    "science": ["science", "space", "physics", "biology", "nasa", "quantum", "arxiv", "research"],
    "world": ["world", "europe", "politics", "war", "climate", "election"],
    "business": ["business", "market", "finance", "stock", "economy", "startup"],
}


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or "topic"


def is_domain(topic: str) -> bool:
    return bool(DOMAIN_RE.match(topic.strip()))


def google_news_rss_url(topic: str) -> str:
    query = f"site:{topic}" if is_domain(topic) else topic
    return (
        "https://news.google.com/rss/search?q="
        + quote_plus(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )


def map_category(topic: str, valid_categories: set[str]) -> str:
    t = topic.lower()
    for category, hints in CATEGORY_HINTS.items():
        if category not in valid_categories:
            continue
        if any(h in t for h in hints):
            return category
    return "topics"


def load_topics(path: str) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        logger.warning("Topics file not found at %s — skipping topic sync", path)
        return []
    topics: list[str] = []
    seen: set[str] = set()
    for line in lines:
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        key = entry.lower()
        if key not in seen:
            seen.add(key)
            topics.append(entry)
    return topics


def sync_topics(db, path: str) -> dict:
    """Read topics.txt and register research topics as sources.

    Called after every scrape cycle so domains/topics added to the file
    are picked up on the next run without a rebuild or restart.
    """
    topics = load_topics(path)
    valid_categories = {c["slug"] for c in db.categories.find({}, {"slug": 1})}
    if "topics" not in valid_categories:
        # mongo-init seeds this, but self-heal in case the DB predates it
        db.categories.update_one(
            {"slug": "topics"},
            {
                "$setOnInsert": {
                    "slug": "topics",
                    "name": "Topics",
                    "icon": "tag",
                    "display_order": 99,
                    "enabled": True,
                }
            },
            upsert=True,
        )
        valid_categories.add("topics")

    total = added = updated = 0
    for topic in topics:
        slug = slugify(topic)
        source_name = f"topic:{slug}"
        url = google_news_rss_url(topic)
        category = map_category(topic, valid_categories)
        total += 1

        db.topics.update_one(
            {"slug": slug},
            {
                "$setOnInsert": {
                    "slug": slug,
                    "name": topic,
                    "query": f"site:{topic}" if is_domain(topic) else topic,
                    "source_name": source_name,
                    "added_at": datetime.now(timezone.utc),
                    "enabled": True,
                }
            },
            upsert=True,
        )

        existed = db.sources.count_documents({"name": source_name}) > 0
        db.sources.update_one(
            {"name": source_name},
            {
                "$setOnInsert": {
                    "name": source_name,
                    "display_name": topic,
                    "category": category,
                    "type": "rss",
                    "url": url,
                    "trust_tier": 2,
                    "enabled": True,
                    "origin": "topics.txt",
                    "parser": {},
                }
            },
            upsert=True,
        )
        if existed:
            updated += 1
        else:
            added += 1

    logger.info("Topics synced from %s: total=%d added=%d existing=%d", path, total, added, updated)
    return {"total": total, "added": added, "existing": updated}
