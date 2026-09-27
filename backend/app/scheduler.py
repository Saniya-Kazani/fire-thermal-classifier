"""
Task #7 — FIRMS data-fetch + scheduled ingestion job ("calling a public API
on a timer"). Uses APScheduler's BackgroundScheduler inside the FastAPI
process — simplest option for a hackathon deployment; swap for Celery/cron
if this needs to run across multiple worker processes later.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.database import SessionLocal
from app.services.pipeline import run_full_pipeline
from app.services.osm_fetch import run_osm_refresh

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _scheduled_firms_run():
    db = SessionLocal()
    try:
        result = run_full_pipeline(db)
        logger.info("Scheduled FIRMS run complete: %s", result)
    except Exception:
        logger.exception("Scheduled FIRMS ingestion failed")
    finally:
        db.close()


def _scheduled_osm_refresh():
    db = SessionLocal()
    try:
        count = run_osm_refresh(db)
        logger.info("Scheduled OSM refresh complete: %d sites", count)
    except Exception:
        logger.exception("Scheduled OSM refresh failed")
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(
        _scheduled_firms_run,
        "interval",
        minutes=settings.FIRMS_POLL_INTERVAL_MINUTES,
        id="firms_poll",
        replace_existing=True,
    )
    scheduler.add_job(
        _scheduled_osm_refresh,
        "interval",
        hours=settings.OSM_REFRESH_INTERVAL_HOURS,
        id="osm_refresh",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started: FIRMS every %d min, OSM every %d hr",
        settings.FIRMS_POLL_INTERVAL_MINUTES, settings.OSM_REFRESH_INTERVAL_HOURS,
    )


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
