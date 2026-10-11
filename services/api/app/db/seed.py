import json
from pathlib import Path

CATALOG_PATH = Path("/app/sources-catalog.json")

DEFAULT_CATEGORIES = [
    {"slug": "technology", "name": "Technology", "icon": "cpu", "display_order": 1, "enabled": True},
    {"slug": "software-dev", "name": "Software & Programming", "icon": "code", "display_order": 2, "enabled": True},
    {"slug": "ai-ml", "name": "AI & Machine Learning", "icon": "brain", "display_order": 3, "enabled": True},
    {"slug": "gaming", "name": "Gaming", "icon": "gamepad", "display_order": 4, "enabled": True},
    {"slug": "india", "name": "India", "icon": "flag", "display_order": 5, "enabled": True},
    {"slug": "politics-policy", "name": "Politics & Policy", "icon": "landmark", "display_order": 6, "enabled": True},
    {"slug": "business", "name": "Business & Technology", "icon": "briefcase", "display_order": 7, "enabled": True},
    {"slug": "cars", "name": "Cars & Automotive", "icon": "car", "display_order": 8, "enabled": True},
    {"slug": "f1", "name": "Formula 1", "icon": "gauge", "display_order": 9, "enabled": True},
    {"slug": "marvel", "name": "Marvel", "icon": "film", "display_order": 10, "enabled": True},
    {"slug": "science", "name": "Science", "icon": "atom", "display_order": 11, "enabled": True},
    {"slug": "world", "name": "World", "icon": "globe", "display_order": 12, "enabled": True},
]

DEFAULT_SOURCES = [
    {
        "name": "arstechnica",
        "display_name": "Ars Technica",
        "category": "technology",
        "type": "rss",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "trust_tier": 1,
        "enabled": True,
        "parser": {},
    },
    {
        "name": "hn",
        "display_name": "Hacker News Front",
        "category": "technology",
        "type": "rss",
        "url": "https://hnrss.org/frontpage",
        "trust_tier": 1,
        "enabled": True,
        "parser": {},
    },
    {
        "name": "nasa",
        "display_name": "NASA Breaking News",
        "category": "science",
        "type": "rss",
        "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "trust_tier": 1,
        "enabled": True,
        "parser": {},
    },
    {
        "name": "bbc-world",
        "display_name": "BBC World",
        "category": "world",
        "type": "rss",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "trust_tier": 1,
        "enabled": True,
        "parser": {},
    },
]


def load_catalog() -> list[dict]:
    """Read the source catalog JSON (name / display_name / category / url / trust_tier)."""
    try:
        raw = CATALOG_PATH.read_text(encoding="utf-8")
    except OSError:
        return []
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError:
        return []
    out: list[dict] = []
    for e in entries:
        name = (e.get("name") or "").strip()
        url = (e.get("url") or "").strip()
        category = (e.get("category") or "").strip()
        if not name or not url or not category:
            continue
        out.append(
            {
                "name": name,
                "display_name": (e.get("display_name") or name).strip(),
                "category": category,
                "type": "rss",
                "url": url,
                "trust_tier": int(e.get("trust_tier", 2)),
                "enabled": True,
                "parser": {},
            }
        )
    return out


async def ensure_seed(db) -> None:
    for c in DEFAULT_CATEGORIES:
        await db.categories.update_one({"slug": c["slug"]}, {"$setOnInsert": c}, upsert=True)
    # $setOnInsert + upsert inserts catalog entries that are new to this volume
    # (e.g. added after mongo-init ran) while leaving existing rows untouched.
    for s in DEFAULT_SOURCES + load_catalog():
        await db.sources.update_one({"name": s["name"]}, {"$setOnInsert": s}, upsert=True)
    await db.user_preferences.update_one(
        {"user_id": "local"},
        {
            "$setOnInsert": {
                "user_id": "local",
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
                "digest_hour": 7,
                "refresh_interval_minutes": None,
                "show_thumbnails": False,
                "notify_high_importance": False,
            }
        },
        upsert=True,
    )
