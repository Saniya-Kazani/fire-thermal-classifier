"""
Manual trigger endpoints — useful both for the scheduler's underlying logic
and for forcing a fresh pull right before the live demo (Task #15: "Demo
dataset prep ... and rehearsal").
"""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.pipeline import run_full_pipeline
from app.services.osm_fetch import run_osm_refresh
from app.schemas import IngestionRunResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


@router.post("/run", response_model=IngestionRunResult)
def trigger_pipeline_run(db: Session = Depends(get_db)):
    """Runs FIRMS fetch -> spatial join -> classify -> alerts, once, synchronously."""
    return run_full_pipeline(db)


@router.post("/osm-refresh")
def trigger_osm_refresh(db: Session = Depends(get_db)):
    """Re-pulls industrial site polygons from OSM Overpass."""
    count = run_osm_refresh(db)
    return {"sites_upserted": count}
