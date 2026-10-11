DEFAULT_CATEGORIES = [
    {"slug": "technology", "name": "Technology", "icon": "cpu", "display_order": 1, "enabled": True},
    {"slug": "science", "name": "Science", "icon": "atom", "display_order": 2, "enabled": True},
    {"slug": "world", "name": "World", "icon": "globe", "display_order": 3, "enabled": True},
    {"slug": "business", "name": "Business", "icon": "briefcase", "display_order": 4, "enabled": True},
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


async def ensure_seed(db) -> None:
    for c in DEFAULT_CATEGORIES:
        await db.categories.update_one({"slug": c["slug"]}, {"$setOnInsert": c}, upsert=True)
    for s in DEFAULT_SOURCES:
        await db.sources.update_one({"name": s["name"]}, {"$setOnInsert": s}, upsert=True)
    await db.user_preferences.update_one(
        {"user_id": "local"},
        {
            "$setOnInsert": {
                "user_id": "local",
                "selected_categories": ["technology", "science", "world", "business"],
                "category_order": ["technology", "science", "world", "business"],
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
