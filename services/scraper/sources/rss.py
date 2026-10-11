from __future__ import annotations

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from time import mktime

import feedparser
import httpx

from config import get_settings

logger = logging.getLogger(__name__)


def _parse_date(entry) -> datetime:
    if getattr(entry, "published_parsed", None):
        return datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
    if getattr(entry, "updated_parsed", None):
        return datetime.fromtimestamp(mktime(entry.updated_parsed), tz=timezone.utc)
    for key in ("published", "updated"):
        raw = entry.get(key)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except (TypeError, ValueError, IndexError):
                pass
    return datetime.now(timezone.utc)


def fetch_rss(source: dict) -> list[dict]:
    settings = get_settings()
    url = source["url"]
    headers = {"User-Agent": settings.user_agent}
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()
            content = resp.text
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to fetch RSS %s (%s): %s", source.get("name"), url, exc)
        return []

    parsed = feedparser.parse(content)
    items: list[dict] = []
    now = datetime.now(timezone.utc).isoformat()
    for entry in parsed.entries[: settings.rss_items_per_source]:
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue
        summary = entry.get("summary") or entry.get("description") or ""
        if hasattr(summary, "strip"):
            summary = summary.strip()
        else:
            summary = str(summary)
        # Strip HTML lightly for staging
        if "<" in summary:
            from bs4 import BeautifulSoup

            summary = BeautifulSoup(summary, "html.parser").get_text(" ", strip=True)

        items.append(
            {
                "source": source["name"],
                "category": source["category"],
                "title": title,
                "url": link,
                "published_at": _parse_date(entry).isoformat(),
                "raw_text": summary[:2000],
                "scraped_at": now,
            }
        )
    logger.info("RSS %s: fetched %d items", source.get("name"), len(items))
    return items
