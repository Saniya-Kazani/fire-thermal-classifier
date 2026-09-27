"""
Step 1 (part C) — land-use tagging ("is this spot farmland, forest, mining
land, etc."). The classifier (services/classifier.py) reads Hotspot.land_use
to distinguish crop_burning / wildfire / coal_seam_fire.

Kept as a lightweight, separate PostGIS table (`land_use_polygons`) rather
than re-fetching from Overpass per-hotspot, so it can be refreshed on the
same slow cadence as industrial sites (OSM_REFRESH_INTERVAL_HOURS) without
adding request latency to the classification pipeline.
"""
import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.hotspot import Hotspot

logger = logging.getLogger(__name__)

# NOTE: land_use_polygons is created via the raw-SQL migration in
# migrations/002_land_use_polygons.sql (see that file for the OSM tags used
# to populate it: landuse=farmland/forest, natural=desert/sand/scrub, etc.)
NEAREST_LAND_USE_SQL = text("""
    SELECT land_use_type
    FROM land_use_polygons
    WHERE ST_DWithin(geom::geography, :point::geography, 100)
    ORDER BY ST_Distance(geom::geography, :point::geography) ASC
    LIMIT 1
""")


def lookup_land_use(db: Session, latitude: float, longitude: float) -> Optional[str]:
    point_wkt = f"SRID=4326;POINT({longitude} {latitude})"
    try:
        row = db.execute(NEAREST_LAND_USE_SQL, {"point": point_wkt}).first()
    except Exception:
        # land_use_polygons table not yet created/populated — fail soft.
        logger.debug("land_use_polygons lookup unavailable, defaulting to unknown")
        return None
    return row[0] if row else None


def tag_land_use(db: Session, hotspots: list[Hotspot]) -> int:
    tagged = 0
    for h in hotspots:
        land_use = lookup_land_use(db, h.latitude, h.longitude)
        h.land_use = land_use or "unknown"
        tagged += 1
    db.commit()
    return tagged
