"""
Step 4 (alert half) — raise an Alert row when a hotspot looks like a
genuine new/abnormal event, so the live alerts feed (Task #5) has something
to show and Task #13's endpoint has something to trigger.

Alert-worthy conditions:
  - category == accident_explosion  -> always alert (severity scales with confidence/zscore)
  - is_anomaly == True for any other category -> alert at lower severity
    (covers e.g. an unusually large wildfire spike, or an anomalous coal
    seam reading) so analysts aren't limited to only the accident category.
"""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.hotspot import Hotspot
from app.models.alert import Alert

logger = logging.getLogger(__name__)


def _severity_for(hotspot: Hotspot) -> Optional[str]:
    if hotspot.category == "accident_explosion":
        if hotspot.zscore is not None and abs(hotspot.zscore) >= 6:
            return "critical"
        return "high"
    if hotspot.is_anomaly:
        return "medium"
    return None


def evaluate_and_raise_alerts(db: Session, hotspots: List[Hotspot]) -> List[Alert]:
    raised = []
    for hotspot in hotspots:
        severity = _severity_for(hotspot)
        if severity is None:
            continue

        alert = Alert(
            hotspot_id=hotspot.id,
            severity=severity,
            category=hotspot.category or "unclassified",
            reason=hotspot.classification_reason,
            zscore=hotspot.zscore,
        )
        db.add(alert)
        raised.append(alert)

    db.commit()
    for a in raised:
        db.refresh(a)

    if raised:
        logger.info("Raised %d new alerts", len(raised))
    return raised
