from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone

import redis
from dateutil.parser import isoparse
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from agent.dedupe import content_hash, title_hash
from agent.filter import filter_item
from config import get_settings
from sources import fetch_source
from topics import sync_topics

logger = logging.getLogger(__name__)


def _clients():
    settings = get_settings()
    mongo = MongoClient(settings.mongo_uri)
    db = mongo[settings.mongo_db]
    r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return settings, db, r, mongo


def stage_items(r, items: list[dict], ttl: int) -> int:
    staged = 0
    for item in items:
        h = content_hash(item["title"], item["url"])
        key = f"staging:{item['category']}:{h}"
        if r.exists(key):
            continue
        r.setex(key, ttl, json.dumps(item))
        staged += 1
    return staged


def drain_staging(r, db, settings) -> tuple[int, int]:
    passed = 0
    filtered_out = 0
    keys = list(r.scan_iter("staging:*", count=200))
    for key in keys:
        raw = r.get(key)
        if not raw:
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            r.delete(key)
            continue

        th = title_hash(item["title"])
        if r.sismember("dedup:titles", th):
            filtered_out += 1
            r.delete(key)
            continue

        decision = filter_item(item)
        if not decision.get("pass", False):
            filtered_out += 1
            r.delete(key)
            continue

        dedup = content_hash(item["title"], item["url"])
        try:
            published = isoparse(item["published_at"])
        except (ValueError, TypeError):
            published = datetime.now(timezone.utc)
        try:
            scraped = isoparse(item["scraped_at"])
        except (ValueError, TypeError):
            scraped = datetime.now(timezone.utc)

        doc = {
            "source": item["source"],
            "category": item["category"],
            "title": item["title"],
            "summary": decision.get("summary") or item.get("raw_text", "")[:300],
            "article": decision.get("article") or decision.get("summary") or item.get("raw_text", ""),
            "url": item["url"],
            "published_at": published,
            "scraped_at": scraped,
            "importance": decision.get("importance", "medium"),
            "tags": decision.get("tags") or [],
            "dedup_hash": dedup,
            "status": "active",
        }
        try:
            db.articles.update_one(
                {"dedup_hash": dedup},
                {"$setOnInsert": doc},
                upsert=True,
            )
            passed += 1
            r.sadd("dedup:titles", th)
            r.expire("dedup:titles", settings.dedup_ttl_seconds)
        except DuplicateKeyError:
            filtered_out += 1
        r.delete(key)

    if filtered_out:
        r.incrby("stats:filtered_today", filtered_out)
        # reset counter roughly daily
        r.expire("stats:filtered_today", 86400)

    return passed, filtered_out


def _pick_source_batch(db, r, total: int, limit: int) -> tuple[list[dict], int]:
    """Round-robin slice of enabled sources.

    With a large catalog (600+ sources), scraping everything in one cycle would
    take hours on CPU LLM filtering. Instead each cycle fetches `limit` sources
    starting from a Redis cursor, so the whole catalog is covered over several
    cycles without any single source being starved.
    """
    query = {"enabled": True}
    if total == 0:
        return [], 0
    if limit <= 0 or limit >= total:
        return list(db.sources.find(query).sort("name", 1)), 0
    cursor_key = "scraper:source_cursor"
    try:
        start = int(r.get(cursor_key) or 0) % total
    except (TypeError, ValueError):
        start = 0
    batch = list(db.sources.find(query).sort("name", 1).skip(start).limit(limit))
    r.set(cursor_key, (start + len(batch)) % total)
    return batch, start


def run_scrape_cycle(full: bool = True) -> dict:
    settings, db, r, mongo = _clients()
    started = datetime.now(timezone.utc)
    total_sources = db.sources.count_documents({"enabled": True})
    if total_sources == 0:
        logger.warning("No enabled sources in Mongo — seeding defaults skipped (mongo-init)")
    batch, cursor_start = _pick_source_batch(db, r, total_sources, settings.sources_per_cycle)
    total_raw = 0
    total_staged = 0

    for source in batch:
        items = fetch_source(source)
        total_raw += len(items)
        total_staged += stage_items(r, items, settings.staging_ttl_seconds)
        time.sleep(settings.request_delay_seconds)

    passed, filtered_out = drain_staging(r, db, settings)
    ended = datetime.now(timezone.utc)
    run_doc = {
        "started_at": started,
        "ended_at": ended,
        "full": full,
        "sources": len(batch),
        "total_sources": total_sources,
        "cursor_start": cursor_start,
        "raw_items": total_raw,
        "staged": total_staged,
        "passed": passed,
        "filtered_out": filtered_out,
    }
    db.scrape_runs.insert_one(run_doc)

    # Refresh research topics after every cycle: new domains/topics added
    # to topics.txt become sources for the next run.
    try:
        sync_topics(db, settings.topics_file)
    except Exception:  # noqa: BLE001
        logger.exception("Topic sync failed")

    mongo.close()
    r.close()
    logger.info(
        "Scrape done: sources=%d/%d (cursor=%d) raw=%d staged=%d passed=%d filtered=%d",
        len(batch),
        total_sources,
        cursor_start,
        total_raw,
        total_staged,
        passed,
        filtered_out,
    )
    return {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in run_doc.items()}
