"""
Steps 3-4 — Look at the pattern over time, then classify + alert.

This is a RULE-BASED baseline classifier (Task #11 in the task table: "Basic
stats, NOT deep ML — any developer can do this"). It runs for every hotspot
and is what actually powers the demo. The optional XGBoost upgrade
(Task #12, app/services/ml_classifier.py-style extension) can slot in later
using the same feature set without changing the API contract — category +
classification_confidence + classification_reason stay the same shape.

Pattern logic (from Problem Statement 2.3, Step 3), turned into a decision
tree:
  - Steady strength, same spot, for months            -> gas_flare
  - Sudden unusual spike vs. that spot's own history   -> accident_explosion
  - Many hotspots at once, over farmland, farm season  -> crop_burning
  - Constant strength, outside any industrial buffer,
    on mining/exposed land                             -> coal_seam_fire
  - Spreading / moving cluster, over forest/scrub       -> wildfire
  - High confidence match to bare-soil/desert + low FRP -> desert_glare_false_alarm
  - Otherwise                                           -> unclassified
"""
import logging
import statistics
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.hotspot import Hotspot

logger = logging.getLogger(__name__)

# Rough India crop-burning season windows (paddy stubble: Oct-Nov, wheat: Apr-May).
CROP_BURNING_MONTHS = {4, 5, 10, 11}

HISTORY_SQL = text("""
    SELECT brightness, frp, acq_date, acq_time
    FROM hotspots
    WHERE source_key = :source_key AND id != :current_id
    ORDER BY acq_date DESC, acq_time DESC
    LIMIT 60
""")

NEARBY_SAME_DAY_SQL = text("""
    SELECT COUNT(*) FROM hotspots
    WHERE acq_date = :acq_date
      AND source_key != :source_key
      AND ST_DWithin(geom::geography, :point::geography, 5000)
""")


@dataclass
class ClassificationResult:
    category: str
    confidence: float
    reason: str
    is_anomaly: bool
    zscore: Optional[float]


def _get_history(db: Session, hotspot: Hotspot) -> List[float]:
    rows = db.execute(
        HISTORY_SQL, {"source_key": hotspot.source_key, "current_id": hotspot.id}
    ).fetchall()
    return [r[0] for r in rows if r[0] is not None]


def _compute_zscore(current_value: float, history: List[float]) -> Optional[float]:
    if len(history) < settings.MIN_HISTORY_POINTS_FOR_ZSCORE:
        return None
    mean = statistics.mean(history)
    stdev = statistics.pstdev(history)
    if stdev == 0:
        return 0.0
    return round((current_value - mean) / stdev, 2)


def _count_nearby_same_day(db: Session, hotspot: Hotspot) -> int:
    point_wkt = f"SRID=4326;POINT({hotspot.longitude} {hotspot.latitude})"
    result = db.execute(
        NEARBY_SAME_DAY_SQL,
        {"acq_date": hotspot.acq_date, "source_key": hotspot.source_key, "point": point_wkt},
    ).scalar()
    return result or 0


def _acq_month(hotspot: Hotspot) -> Optional[int]:
    try:
        return int(hotspot.acq_date.split("-")[1])
    except (IndexError, ValueError, AttributeError):
        return None


def classify_hotspot(db: Session, hotspot: Hotspot) -> ClassificationResult:
    """
    Runs the full pattern decision tree for one hotspot and returns a
    ClassificationResult. Also computes the z-score anomaly flag used by
    Step 4's "raise an alert if something looks like a genuine new/abnormal
    event".
    """
    history = _get_history(db, hotspot)
    zscore = _compute_zscore(hotspot.brightness, history)
    history_len = len(history)
    nearby_count = _count_nearby_same_day(db, hotspot)
    month = _acq_month(hotspot)

    is_anomaly = zscore is not None and abs(zscore) >= settings.ANOMALY_ZSCORE_THRESHOLD

    # --- Desert glare / false alarm: low FRP, low confidence, no industrial match ---
    low_intensity = (hotspot.frp or 0) < 1.0 and (hotspot.confidence or "").lower() in ("low", "l")
    if low_intensity and not hotspot.inside_industrial_buffer and nearby_count == 0:
        return ClassificationResult(
            category="desert_glare_false_alarm",
            confidence=0.7,
            reason="Low FRP, low satellite confidence, isolated single detection, no industrial match — "
                   "consistent with sun-glare/surface reflection rather than combustion.",
            is_anomaly=False,
            zscore=zscore,
        )

    # --- Accident / explosion: sudden spike inside an industrial site ---
    if hotspot.inside_industrial_buffer and is_anomaly and zscore > 0:
        return ClassificationResult(
            category="accident_explosion",
            confidence=min(0.95, 0.6 + abs(zscore) * 0.05),
            reason=f"Sudden brightness spike (z-score={zscore}) at a known industrial site "
                   f"('{hotspot.industrial_site.name or hotspot.industrial_site.site_type if hotspot.industrial_site else 'matched site'}') "
                   f"vs. that site's own history — this is not the site's normal baseline.",
            is_anomaly=True,
            zscore=zscore,
        )

    # --- Gas flare: steady strength, same spot, industrial site, plenty of history, not anomalous ---
    if hotspot.inside_industrial_buffer and history_len >= settings.MIN_HISTORY_POINTS_FOR_ZSCORE and not is_anomaly:
        return ClassificationResult(
            category="gas_flare",
            confidence=0.85,
            reason=f"Recurs at this exact location inside an industrial site with {history_len} prior "
                   f"detections at steady strength (z-score={zscore}) — matches a routine flare stack pattern.",
            is_anomaly=False,
            zscore=zscore,
        )

    # --- Crop burning: many simultaneous detections, farm season, not on an industrial site ---
    if nearby_count >= 5 and month in CROP_BURNING_MONTHS and not hotspot.inside_industrial_buffer:
        return ClassificationResult(
            category="crop_burning",
            confidence=0.8,
            reason=f"{nearby_count} other hotspots detected within 5km on the same day during a known "
                   f"crop-burning month, outside any industrial boundary — matches stubble-burning pattern.",
            is_anomaly=False,
            zscore=zscore,
        )

    # --- Coal seam fire: constant, outside industrial boundary, on mine/exposed land ---
    if not hotspot.inside_industrial_buffer and history_len >= settings.MIN_HISTORY_POINTS_FOR_ZSCORE \
            and not is_anomaly and (hotspot.land_use in ("mining", "exposed", "barren")):
        return ClassificationResult(
            category="coal_seam_fire",
            confidence=0.75,
            reason=f"Constant low-level detection at this location for {history_len} prior passes, "
                   f"outside any industrial facility boundary, on mining/exposed land — matches a "
                   f"slow-burning subsurface coal seam fire.",
            is_anomaly=False,
            zscore=zscore,
        )

    # --- Wildfire: spreading cluster, on forest land, growing FRP ---
    if nearby_count >= 3 and hotspot.land_use == "forest" and not hotspot.inside_industrial_buffer:
        return ClassificationResult(
            category="wildfire",
            confidence=0.7,
            reason=f"Cluster of {nearby_count} nearby simultaneous detections over forest land, "
                   f"outside any industrial boundary — matches a spreading wildfire front.",
            is_anomaly=is_anomaly,
            zscore=zscore,
        )

    return ClassificationResult(
        category="unclassified",
        confidence=0.3,
        reason="Insufficient history or pattern match for any known category — flagged for manual review.",
        is_anomaly=is_anomaly,
        zscore=zscore,
    )


def classify_and_persist(db: Session, hotspots: List[Hotspot]) -> int:
    """Runs classify_hotspot() for each hotspot and writes results back."""
    classified = 0
    for hotspot in hotspots:
        result = classify_hotspot(db, hotspot)
        hotspot.category = result.category
        hotspot.classification_confidence = result.confidence
        hotspot.classification_reason = result.reason
        hotspot.is_anomaly = result.is_anomaly
        hotspot.zscore = result.zscore
        classified += 1
    db.commit()
    logger.info("Classified %d hotspots", classified)
    return classified
