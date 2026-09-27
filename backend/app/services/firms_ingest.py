"""
Step 1 (part A) — Pull NASA FIRMS hot-spot data.

Uses FIRMS' CSV area API:
  https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SOURCE}/{west,south,east,north}/{day_range}

Returns raw hotspot rows (lat, lon, brightness, frp, confidence, acq_date,
acq_time, satellite, daynight). This module ONLY fetches + parses; it does
not touch the DB directly except via upsert_hotspots().
"""
import csv
import io
import logging
from typing import List, Dict

import requests
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.config import settings
from app.models.hotspot import Hotspot

logger = logging.getLogger(__name__)

FIRMS_BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"


def build_source_key(lat: float, lon: float, precision: int = 3) -> str:
    """
    Round lat/lon to `precision` decimals (~110m at precision=3) so repeated
    detections of the same physical source group into one time series, even
    though FIRMS gives slightly different coordinates pass to pass.
    """
    return f"{round(lat, precision)}_{round(lon, precision)}"


def fetch_firms_hotspots() -> List[Dict]:
    """Call the FIRMS API and return a list of raw row dicts."""
    if not settings.FIRMS_MAP_KEY:
        logger.warning("FIRMS_MAP_KEY not set — skipping fetch. Set it in .env")
        return []

    url = (
        f"{FIRMS_BASE_URL}/{settings.FIRMS_MAP_KEY}/{settings.FIRMS_SOURCE}/"
        f"{settings.FIRMS_BBOX}/{settings.FIRMS_DAY_RANGE}"
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    reader = csv.DictReader(io.StringIO(resp.text))
    rows = list(reader)
    logger.info("FIRMS returned %d raw rows", len(rows))
    return rows


def _parse_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def upsert_hotspots(db: Session, raw_rows: List[Dict]) -> List[Hotspot]:
    """
    Insert new Hotspot rows. FIRMS rows don't have a stable ID, so we treat
    every row as a new detection event (that's the correct semantics for a
    time series) — we only dedupe exact (lat, lon, acq_date, acq_time) repeats
    within the same batch, which FIRMS sometimes sends.
    """
    seen_in_batch = set()
    created: List[Hotspot] = []

    for row in raw_rows:
        lat = _parse_float(row.get("latitude"))
        lon = _parse_float(row.get("longitude"))
        if lat is None or lon is None:
            continue

        acq_date = row.get("acq_date", "")
        acq_time = row.get("acq_time", "")
        dedupe_key = (lat, lon, acq_date, acq_time)
        if dedupe_key in seen_in_batch:
            continue
        seen_in_batch.add(dedupe_key)

        hotspot = Hotspot(
            latitude=lat,
            longitude=lon,
            brightness=_parse_float(row.get("bright_ti4") or row.get("brightness"), default=0.0),
            frp=_parse_float(row.get("frp")),
            confidence=row.get("confidence"),
            satellite=row.get("satellite"),
            sensor=row.get("instrument") or settings.FIRMS_SOURCE.split("_")[0],
            acq_date=acq_date,
            acq_time=acq_time,
            daynight=row.get("daynight"),
            geom=from_shape(Point(lon, lat), srid=4326),
            source_key=build_source_key(lat, lon),
        )
        db.add(hotspot)
        created.append(hotspot)

    db.commit()
    for h in created:
        db.refresh(h)

    logger.info("Inserted %d new hotspots", len(created))
    return created


def run_firms_ingestion(db: Session) -> List[Hotspot]:
    """Full Step 1a pipeline: fetch from FIRMS API, then persist."""
    raw_rows = fetch_firms_hotspots()
    return upsert_hotspots(db, raw_rows)
