"""
Step 1 (part B) — Pull OpenStreetMap industrial-site boundaries via the
Overpass API. We query a small set of tags that reliably mark the facility
types this project cares about: refineries, power plants, steel mills/works,
LNG/gas terminals, and mining land (useful for filtering out coal-seam fires
that sit on mining land but outside an active industrial polygon).
"""
import json
import logging
from typing import List, Dict

import requests
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon, MultiPolygon

from app.config import settings
from app.models.industrial_site import IndustrialSite

logger = logging.getLogger(__name__)

# man_made=works / landuse=industrial / power=plant / industrial=oil_refinery / etc.
OVERPASS_QUERY_TEMPLATE = """
[out:json][timeout:60];
(
  way["man_made"="works"]({bbox});
  way["landuse"="industrial"]({bbox});
  way["power"="plant"]({bbox});
  way["industrial"="oil"]({bbox});
  way["industrial"="refinery"]({bbox});
  way["landuse"="quarry"]({bbox});
  relation["man_made"="works"]({bbox});
  relation["landuse"="industrial"]({bbox});
  relation["power"="plant"]({bbox});
);
out body;
>;
out skel qt;
"""


def _classify_site_type(tags: Dict) -> str:
    if tags.get("power") == "plant":
        return "power_plant"
    if tags.get("industrial") in ("oil", "refinery") or "refinery" in (tags.get("name", "") or "").lower():
        return "refinery"
    if tags.get("landuse") == "quarry" or tags.get("industrial") == "mine":
        return "mine"
    if "steel" in (tags.get("name", "") or "").lower():
        return "steel_mill"
    if "lng" in (tags.get("name", "") or "").lower() or tags.get("industrial") == "gas":
        return "lng_terminal"
    return "industrial_generic"


def fetch_osm_industrial_polygons() -> List[Dict]:
    """
    Query Overpass and return a list of {osm_id, name, tags, polygon(shapely)}.
    Uses the Overpass "out body; >; out skel qt;" pattern to also pull node
    coordinates, then reconstructs way polygons in Python.
    """
    query = OVERPASS_QUERY_TEMPLATE.format(bbox=settings.OSM_BBOX)
    resp = requests.post(settings.OVERPASS_URL, data={"data": query}, timeout=90)
    resp.raise_for_status()
    data = resp.json()

    nodes = {}
    ways = []
    for el in data.get("elements", []):
        if el["type"] == "node":
            nodes[el["id"]] = (el["lon"], el["lat"])
        elif el["type"] == "way":
            ways.append(el)

    results = []
    for way in ways:
        coords = [nodes[n] for n in way.get("nodes", []) if n in nodes]
        if len(coords) < 3:
            continue
        if coords[0] != coords[-1]:
            coords.append(coords[0])  # close the ring
        try:
            poly = Polygon(coords)
            if not poly.is_valid or poly.area == 0:
                continue
        except Exception:
            continue

        tags = way.get("tags", {})
        results.append({
            "osm_id": f"way/{way['id']}",
            "name": tags.get("name"),
            "site_type": _classify_site_type(tags),
            "tags": json.dumps(tags),
            "polygon": poly,
        })

    logger.info("Overpass returned %d usable industrial polygons", len(results))
    return results


def upsert_industrial_sites(db: Session, parsed: List[Dict]) -> int:
    """Upsert by osm_id: update geometry/tags if it exists, else insert."""
    count = 0
    for item in parsed:
        existing = db.query(IndustrialSite).filter_by(osm_id=item["osm_id"]).first()
        geom = from_shape(item["polygon"], srid=4326)
        if existing:
            existing.name = item["name"]
            existing.site_type = item["site_type"]
            existing.tags = item["tags"]
            existing.geom = geom
        else:
            db.add(IndustrialSite(
                osm_id=item["osm_id"],
                name=item["name"],
                site_type=item["site_type"],
                tags=item["tags"],
                geom=geom,
            ))
        count += 1
    db.commit()
    return count


def run_osm_refresh(db: Session) -> int:
    """Full Step 1b pipeline: fetch from Overpass, then persist/update."""
    parsed = fetch_osm_industrial_polygons()
    return upsert_industrial_sites(db, parsed)
