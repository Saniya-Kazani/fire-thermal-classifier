"""
IndustrialSite: polygons pulled from OSM Overpass API (refineries, power
plants, steel mills, LNG terminals, mines, etc.). Used for the spatial join
that decides whether a hotspot falls inside/near a known industrial facility.
"""
from sqlalchemy import Column, Integer, String, DateTime, func
from geoalchemy2 import Geometry

from app.database import Base


class IndustrialSite(Base):
    __tablename__ = "industrial_sites"

    id = Column(Integer, primary_key=True, index=True)
    osm_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    site_type = Column(String, index=True, nullable=False)  # refinery, power_plant, steel_mill, lng_terminal, mine, etc.
    tags = Column(String, nullable=True)  # raw OSM tags as JSON string, for debugging/audit

    # Polygon geometry in WGS84 (SRID 4326)
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
