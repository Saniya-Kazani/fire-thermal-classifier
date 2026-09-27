"""
Full ingestion+classification pipeline, Steps 1-4 chained together.
This is what the scheduler calls periodically, and what the manual
/ingest/run endpoint calls on demand (useful for the live demo).
"""
import logging

from sqlalchemy.orm import Session

from app.services.firms_ingest import run_firms_ingestion
from app.services.spatial_join import run_spatial_join
from app.services.land_use import tag_land_use
from app.services.classifier import classify_and_persist
from app.services.alerting import evaluate_and_raise_alerts
from app.schemas import IngestionRunResult

logger = logging.getLogger(__name__)


def run_full_pipeline(db: Session) -> IngestionRunResult:
    """
    Step 1 -> Step 2 -> Step 3/4 -> alerts, in order, for one ingestion cycle.
    Returns counts for the API response / demo dashboard.
    """
    hotspots = run_firms_ingestion(db)
    if not hotspots:
        return IngestionRunResult(fetched=0, matched_to_site=0, classified=0, alerts_raised=0)

    matched = run_spatial_join(db, hotspots)
    tag_land_use(db, hotspots)
    classified = classify_and_persist(db, hotspots)
    alerts = evaluate_and_raise_alerts(db, hotspots)

    return IngestionRunResult(
        fetched=len(hotspots),
        matched_to_site=matched,
        classified=classified,
        alerts_raised=len(alerts),
    )
