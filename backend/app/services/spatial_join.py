"""
Step 2 — Match each hotspot to context: is it inside/near a known
industrial facility boundary?

Uses PostGIS directly (ST_DWithin / ST_Distance on geography) rather than
pulling geometries into Python — this is the right tool for spatial joins
and scales to large hotspot volumes.

Per Task Table #10: "point-in-polygon with buffer" — instead of a strict
yes/no we compute a buffer zone + confidence score (per Problem Statement
2.4's stated fix for boundary misalignment).
"""
import logging
from typing import Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.hotspot import Hotspot

logger = logging.getLogger(__name__)

# Raw SQL is used here deliberately: PostGIS geography casts + ST_DWithin
# are far cleaner expressed directly than through the ORM, and this is a
# hot path that benefits from the spatial index on industrial_sites.geom.
NEAREST_SITE_SQL = text("""
    SELECT
    id,
    ST_Distance(geom::geography, CAST(:point AS geography)) AS distance_m
FROM industrial_sites
WHERE ST_DWithin(geom::geography, CAST(:point AS geography), :max_search_m)
ORDER BY distance_m ASC
LIMIT 1
""")


def _confidence_from_distance(distance_m: float, buffer_m: float) -> float:
    """
    1.0 if the hotspot is essentially on the boundary/inside (distance ~0),
    decaying linearly to 0.0 at the edge of the buffer. This is the
    "confidence score" the problem statement asks for instead of a strict
    yes/no match.
    """
    if distance_m <= 0:
        return 1.0
    if distance_m >= buffer_m:
        return 0.0
    return round(1.0 - (distance_m / buffer_m), 3)


def match_hotspot_to_site(db: Session, hotspot: Hotspot) -> Tuple[Optional[int], float, float]:
    """
    Returns (industrial_site_id_or_None, distance_m, confidence).
    Searches within a generous radius (3x the buffer) so we can also report
    "nearest site, but not close enough" distances for debugging/UI, while
    only counting a hotspot as inside_industrial_buffer within INDUSTRIAL_BUFFER_METERS.
    """
    search_radius = settings.INDUSTRIAL_BUFFER_METERS * 3
    point_wkt = f"SRID=4326;POINT({hotspot.longitude} {hotspot.latitude})"

    row = db.execute(
        NEAREST_SITE_SQL,
        {"point": point_wkt, "max_search_m": search_radius},
    ).first()

    if row is None:
        return None, None, 0.0

    site_id, distance_m = row
    confidence = _confidence_from_distance(distance_m, settings.INDUSTRIAL_BUFFER_METERS)
    return site_id, distance_m, confidence


def run_spatial_join(db: Session, hotspots: list[Hotspot]) -> int:
    """
    For each hotspot: find nearest industrial site, set inside_industrial_buffer,
    distance_to_site_m, site_match_confidence, industrial_site_id.
    Returns count of hotspots matched inside the buffer.
    """
    matched = 0
    for hotspot in hotspots:
        site_id, distance_m, confidence = match_hotspot_to_site(db, hotspot)
        hotspot.industrial_site_id = site_id
        hotspot.distance_to_site_m = distance_m
        hotspot.site_match_confidence = confidence
        hotspot.inside_industrial_buffer = (
            site_id is not None and distance_m <= settings.INDUSTRIAL_BUFFER_METERS
        )
        if hotspot.inside_industrial_buffer:
            matched += 1

    db.commit()
    logger.info("Spatial join: %d/%d hotspots matched inside buffer", matched, len(hotspots))
    return matched
