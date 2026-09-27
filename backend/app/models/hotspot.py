"""
Hotspot: one FIRMS thermal detection (a single satellite pass over a single
pixel). This is the core time-series record — the same physical source
(e.g. one gas flare stack) will produce many Hotspot rows over time, tied
together by `source_key` (a coarse spatial grid key) so we can build a
history and run the z-score/pattern logic per-source.
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.database import Base


class Hotspot(Base):
    __tablename__ = "hotspots"

    id = Column(Integer, primary_key=True, index=True)

    # Raw FIRMS fields
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    brightness = Column(Float, nullable=False)       # brightness temp (Kelvin), fire strength proxy
    frp = Column(Float, nullable=True)                # Fire Radiative Power (MW) - intensity
    confidence = Column(String, nullable=True)        # FIRMS confidence: low/nominal/high (or 0-100 for MODIS)
    satellite = Column(String, nullable=True)         # e.g. N, N20, Terra, Aqua
    sensor = Column(String, nullable=True)             # VIIRS / MODIS
    acq_date = Column(String, nullable=False)          # acquisition date (YYYY-MM-DD)
    acq_time = Column(String, nullable=False)          # acquisition time (HHMM, UTC)
    daynight = Column(String, nullable=True)           # D/N

    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)

    # Coarse spatial grid key (rounded lat/lon) used to group repeated
    # detections of the "same" physical source into one time series.
    source_key = Column(String, index=True, nullable=False)

    # --- Spatial-join results (Step 2) ---
    industrial_site_id = Column(Integer, ForeignKey("industrial_sites.id"), nullable=True)
    industrial_site = relationship("IndustrialSite", lazy="joined")
    inside_industrial_buffer = Column(Boolean, default=False, nullable=False)
    distance_to_site_m = Column(Float, nullable=True)
    site_match_confidence = Column(Float, nullable=True)  # 0-1, based on buffer distance

    land_use = Column(String, nullable=True)  # farmland / forest / desert / industrial / unknown

    # --- Classification results (Steps 3-4) ---
    category = Column(String, index=True, nullable=True)
    # one of: gas_flare, accident_explosion, crop_burning, coal_seam_fire,
    # wildfire, desert_glare_false_alarm, unclassified
    classification_confidence = Column(Float, nullable=True)  # 0-1
    classification_reason = Column(String, nullable=True)     # human-readable "why" (top contributing factors)
    is_anomaly = Column(Boolean, default=False, nullable=False)
    zscore = Column(Float, nullable=True)

    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = ()
