"""
Endpoints backing Task #2 (map marker rendering), Task #3 (category
filter), and Task #4 (site-detail panel with historical chart).
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.hotspot import Hotspot
from app.schemas import HotspotOut, HotspotHistoryPoint

router = APIRouter(prefix="/api/hotspots", tags=["hotspots"])

VALID_CATEGORIES = {
    "gas_flare", "accident_explosion", "crop_burning",
    "coal_seam_fire", "wildfire", "desert_glare_false_alarm", "unclassified",
}


@router.get("", response_model=List[HotspotOut])
def list_hotspots(
    category: Optional[str] = Query(None, description="Filter by classified category"),
    is_anomaly: Optional[bool] = Query(None),
    bbox: Optional[str] = Query(None, description="west,south,east,north — restrict to map viewport"),
    since_date: Optional[str] = Query(None, description="YYYY-MM-DD, only hotspots on/after this date"),
    limit: int = Query(1000, le=5000),
    db: Session = Depends(get_db),
):
    """Main feed for the interactive map (Task #2) + legend/category filter (Task #3)."""
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(400, f"Unknown category. Valid: {sorted(VALID_CATEGORIES)}")

    query = db.query(Hotspot)
    if category:
        query = query.filter(Hotspot.category == category)
    if is_anomaly is not None:
        query = query.filter(Hotspot.is_anomaly == is_anomaly)
    if since_date:
        query = query.filter(Hotspot.acq_date >= since_date)
    if bbox:
        try:
            west, south, east, north = [float(x) for x in bbox.split(",")]
        except ValueError:
            raise HTTPException(400, "bbox must be 'west,south,east,north'")
        query = query.filter(
            Hotspot.longitude.between(west, east),
            Hotspot.latitude.between(south, north),
        )

    return query.order_by(Hotspot.ingested_at.desc()).limit(limit).all()


@router.get("/{hotspot_id}", response_model=HotspotOut)
def get_hotspot(hotspot_id: int, db: Session = Depends(get_db)):
    hotspot = db.query(Hotspot).get(hotspot_id)
    if not hotspot:
        raise HTTPException(404, "Hotspot not found")
    return hotspot


@router.get("/{hotspot_id}/history", response_model=List[HotspotHistoryPoint])
def get_hotspot_history(hotspot_id: int, db: Session = Depends(get_db)):
    """
    Task #4 — site-detail panel historical chart: every prior detection at
    the same source_key (same physical location), oldest first, so the
    frontend can plot a brightness-over-time line with category coloring.
    """
    hotspot = db.query(Hotspot).get(hotspot_id)
    if not hotspot:
        raise HTTPException(404, "Hotspot not found")

    rows = (
        db.query(Hotspot)
        .filter(Hotspot.source_key == hotspot.source_key)
        .order_by(Hotspot.acq_date.asc(), Hotspot.acq_time.asc())
        .all()
    )
    return [
        HotspotHistoryPoint(
            acq_date=r.acq_date, acq_time=r.acq_time, brightness=r.brightness,
            frp=r.frp, category=r.category, is_anomaly=r.is_anomaly, zscore=r.zscore,
        )
        for r in rows
    ]
