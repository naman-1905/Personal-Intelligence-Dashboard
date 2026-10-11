from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ArticleOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id", serialization_alias="id")
    source: str
    category: str
    title: str
    summary: str = ""
    url: str
    published_at: datetime | None = None
    scraped_at: datetime | None = None
    importance: Literal["low", "medium", "high"] = "medium"
    tags: list[str] = []
    status: str = "active"
    read: bool = False
    bookmarked: bool = False


class CategoryOut(BaseModel):
    slug: str
    name: str
    icon: str = ""
    display_order: int = 0
    enabled: bool = True
    unread_count: int = 0


class SourceOut(BaseModel):
    name: str
    display_name: str = ""
    category: str
    type: str
    url: str
    trust_tier: int = 1
    enabled: bool = True


class TopicOut(BaseModel):
    slug: str
    name: str
    query: str = ""
    source_name: str = ""
    article_count: int = 0


class PreferencesIn(BaseModel):
    selected_categories: list[str] | None = None
    category_order: list[str] | None = None
    mute_keywords: list[str] | None = None
    theme: Literal["system", "light", "dark"] | None = None
    digest_hour: int | None = None
    refresh_interval_minutes: int | None = None
    show_thumbnails: bool | None = None
    notify_high_importance: bool | None = None


class PreferencesOut(BaseModel):
    user_id: str
    selected_categories: list[str] = []
    category_order: list[str] = []
    mute_keywords: list[str] = []
    theme: str = "system"
    digest_hour: int = 7
    refresh_interval_minutes: int | None = None
    show_thumbnails: bool = False
    notify_high_importance: bool = False


class StatsOut(BaseModel):
    articles_active: int
    articles_filtered_today: int
    sources_enabled: int
    articles_read: int
    bookmarks: int
    time_saved_minutes_estimate: int


class HealthOut(BaseModel):
    status: str
    mongo: bool
    redis: bool
    details: dict[str, Any] = {}


class TriggerScrapeOut(BaseModel):
    accepted: bool
    message: str


class PaginatedArticles(BaseModel):
    items: list[ArticleOut]
    page: int
    page_size: int
    total: int
    has_more: bool
