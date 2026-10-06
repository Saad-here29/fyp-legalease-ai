"""Scraping freshness for GET /research/stats (additive fields).

Never breaks the stats endpoint: if the scraping tables don't exist (the
shared database before the merge is approved) or the database is down, the
answer is {"available": False}. Cached for CACHE_SECONDS, since the stats
endpoint is public and shown on the landing page.
"""

from __future__ import annotations

import time

from sqlalchemy import func, inspect
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.scraping import ScrapedDocument, ScrapeRun

CACHE_SECONDS = 60
_cache: dict = {"at": 0.0, "value": None}


def scrape_updates(db: Session) -> dict:
    if not inspect(db.get_bind()).has_table(ScrapeRun.__tablename__):
        return {"available": False}
    run = (db.query(ScrapeRun).filter(ScrapeRun.dry_run.is_(False), ScrapeRun.finished_at.isnot(None))
           .order_by(ScrapeRun.started_at.desc()).first())
    if run is None:
        return {"available": False}
    last_updated = (db.query(func.max(ScrapedDocument.fetched_at))
                    .filter(ScrapedDocument.change_kind.in_(("new", "changed"))).scalar())
    sources = [
        {"name": name, "content_type": c.get("content_type"), "checked": c.get("checked", 0),
         "new": c.get("new", 0), "changed": c.get("changed", 0), "errors": c.get("errors", 0)}
        for name, c in (run.per_source or {}).items()
    ]
    return {
        "available": True,
        "last_checked": run.finished_at,
        "last_updated": last_updated,
        "pages_checked": run.pages_checked,
        "new": run.new_count, "changed": run.changed_count, "errors": run.error_count,
        "sources": sources,
    }


def cached_scrape_updates(session_factory) -> dict:
    now = time.monotonic()
    if _cache["value"] is not None and now - _cache["at"] < CACHE_SECONDS:
        return _cache["value"]
    try:
        db = session_factory()
        try:
            value = scrape_updates(db)
        finally:
            db.close()
    except Exception as e:  # noqa: BLE001 - stats must never fail because of this
        logger.warning(f"Scraping stats unavailable: {type(e).__name__}: {e}")
        value = {"available": False}
    _cache.update(at=now, value=value)
    return value
