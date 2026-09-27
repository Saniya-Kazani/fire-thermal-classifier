"""
Serves industrial site polygons for the map overlay (frontend draws the
facility boundary + buffer visually, per Problem Statement 2.4's fix for
boundary misalignment: "show that buffer visually so it's clear how the
decision was made").
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape

from app.database import get_db
from app.models.industrial_site import IndustrialSite
from app.schemas import IndustrialSiteOut

router = APIRouter(prefix="/api/sites", tags=["sites"])


@router.get("", response_model=List[IndustrialSiteOut])
def list_sites(db: Session = Depends(get_db)):
    return db.query(IndustrialSite).all()


@router.get("/{site_id}/geojson")
def get_site_geojson(site_id: int, db: Session = Depends(get_db)):
    """Raw GeoJSON polygon for a single site, for the map library to render directly."""
    site = db.query(IndustrialSite).get(site_id)
    if not site:
        raise HTTPException(404, "Site not found")
    shape = to_shape(site.geom)
    return {
        "type": "Feature",
        "properties": {"id": site.id, "name": site.name, "site_type": site.site_type},
        "geometry": shape.__geo_interface__,
    }
