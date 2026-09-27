"""
Alert: raised when Step 4's classifier/anomaly logic decides a hotspot
looks like a genuine new/abnormal event (e.g. accident_explosion, or any
category with is_anomaly=True). Analysts review/acknowledge these from the
live alerts feed.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    hotspot_id = Column(Integer, ForeignKey("hotspots.id"), nullable=False)
    hotspot = relationship("Hotspot", lazy="joined")

    severity = Column(String, nullable=False)  # low / medium / high / critical
    category = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    zscore = Column(Float, nullable=True)

    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by = Column(String, nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
