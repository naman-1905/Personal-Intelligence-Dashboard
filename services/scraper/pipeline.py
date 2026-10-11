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


def run_scrape_cycle(full: bool = True) -> dict:
    settings, db, r, mongo = _clients()
    started = datetime.now(timezone.utc)
    query = {"enabled": True}
    sources = list(db.sources.find(query))
    if not sources:
        logger.warning("No enabled sources in Mongo — seeding defaults skipped (mongo-init)")
    total_raw = 0
    total_staged = 0

    for source in sources:
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
        "sources": len(sources),
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
        "Scrape done: sources=%d raw=%d staged=%d passed=%d filtered=%d",
        len(sources),
        total_raw,
        total_staged,
        passed,
        filtered_out,
    )
    return {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in run_doc.items()}
