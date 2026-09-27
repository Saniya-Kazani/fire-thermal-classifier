"""
Pydantic response/request models. Kept separate from the ORM models
(app/models/) so the DB schema can evolve without breaking the API contract.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class IndustrialSiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    osm_id: str
    name: Optional[str] = None
    site_type: str


class HotspotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    latitude: float
    longitude: float
    brightness: float
    frp: Optional[float] = None
    confidence: Optional[str] = None
    satellite: Optional[str] = None
    sensor: Optional[str] = None
    acq_date: str
    acq_time: str
    source_key: str

    inside_industrial_buffer: bool
    distance_to_site_m: Optional[float] = None
    site_match_confidence: Optional[float] = None
    land_use: Optional[str] = None

    category: Optional[str] = None
    classification_confidence: Optional[float] = None
    classification_reason: Optional[str] = None
    is_anomaly: bool
    zscore: Optional[float] = None

    ingested_at: datetime


class HotspotHistoryPoint(BaseModel):
    acq_date: str
    acq_time: str
    brightness: float
    frp: Optional[float] = None
    category: Optional[str] = None
    is_anomaly: bool
    zscore: Optional[float] = None


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    hotspot_id: int
    severity: str
    category: str
    reason: Optional[str] = None
    zscore: Optional[float] = None
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    created_at: datetime


class AlertAcknowledge(BaseModel):
    acknowledged_by: str


class IngestionRunResult(BaseModel):
    fetched: int
    matched_to_site: int
    classified: int
    alerts_raised: int
