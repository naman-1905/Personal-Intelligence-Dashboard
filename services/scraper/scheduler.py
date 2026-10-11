from __future__ import annotations

import json
import logging
import sys
import threading
import time

import redis
from apscheduler.schedulers.background import BackgroundScheduler

from config import get_settings
from pipeline import run_scrape_cycle

logging.basicConfig(
    level=getattr(logging, get_settings().log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("scheduler")


def _listen_triggers():
    settings = get_settings()
    while True:
        try:
            r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
            pubsub = r.pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe("scraper:commands")
            logger.info("Listening on Redis channel scraper:commands")
            for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                try:
                    payload = json.loads(message["data"])
                except (TypeError, json.JSONDecodeError):
                    payload = {"action": "scrape_now"}
                if payload.get("action") == "scrape_now":
                    logger.info("Manual scrape trigger received")
                    try:
                        # Consume the key fallback immediately so the main
                        # loop's polling doesn't start a second overlapping
                        # cycle while this one is still running.
                        r.delete("scraper:trigger")
                    except Exception:  # noqa: BLE001
                        pass
                    try:
                        run_scrape_cycle(full=True)
                    except Exception:  # noqa: BLE001
                        logger.exception("Triggered scrape failed")
        except Exception:  # noqa: BLE001
            logger.exception("Trigger listener error; retrying in 5s")
            time.sleep(5)


def main() -> None:
    settings = get_settings()
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        run_scrape_cycle,
        "interval",
        hours=settings.scrape_interval_hours,
        id="full_scrape",
        kwargs={"full": True},
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        run_scrape_cycle,
        "interval",
        minutes=settings.breaking_check_minutes,
        id="breaking_check",
        kwargs={"full": False},
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started: full every %sh, light every %smin",
        settings.scrape_interval_hours,
        settings.breaking_check_minutes,
    )

    t = threading.Thread(target=_listen_triggers, daemon=True)
    t.start()

    if settings.run_on_start:
        logger.info("Running initial scrape on start")
        try:
            run_scrape_cycle(full=True)
        except Exception:  # noqa: BLE001
            logger.exception("Initial scrape failed")

    try:
        while True:
            # poll key-based trigger as fallback
            try:
                r = redis.Redis.from_url(settings.redis_url, decode_responses=True)
                if r.get("scraper:trigger") == "1":
                    r.delete("scraper:trigger")
                    logger.info("Key-based scrape trigger")
                    run_scrape_cycle(full=True)
                r.close()
            except Exception:  # noqa: BLE001
                pass
            time.sleep(5)
    except KeyboardInterrupt:
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
