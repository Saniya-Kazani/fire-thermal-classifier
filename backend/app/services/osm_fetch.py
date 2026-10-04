"""
Step 1 (part B) — Pull OpenStreetMap industrial-site boundaries via the
Overpass API. We query a small set of tags that reliably mark the facility
types this project cares about: refineries, power plants, steel mills/works,
LNG/gas terminals, and mining land (useful for filtering out coal-seam fires
that sit on mining land but outside an active industrial polygon).

Overpass public servers are free and often busy (HTTP 429 / 504 / timeouts),
so requests go through a list of mirrors with retries and an overall time
budget (kept under ~90s so the hosting proxy does not cut the request off).
"""
import json
import logging
import time
from typing import List, Dict

import requests
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon

from app.config import settings
from app.models.industrial_site import IndustrialSite

logger = logging.getLogger(__name__)

# Tried in order after settings.OVERPASS_URL. Duplicates are removed.
FALLBACK_MIRRORS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

HEADERS = {"User-Agent": "fire-thermal-classifier/1.0 (SIH26162 student project)"}
RETRY_STATUS = {429, 502, 503, 504}
CONNECT_TIMEOUT_S = 8
READ_TIMEOUT_S = 30        # per request
TOTAL_BUDGET_S = 80        # across all mirrors/retries
PAUSE_BETWEEN_TRIES_S = 3

# Only ways are used below, so relations are not requested (keeps the
# query light for free mirrors). Server-side timeout is kept short.
OVERPASS_QUERY_TEMPLATE = """
[out:json][timeout:25];
(
  way["man_made"="works"]({bbox});
  way["landuse"="industrial"]({bbox});
  way["power"="plant"]({bbox});
  way["industrial"="oil"]({bbox});
  way["industrial"="refinery"]({bbox});
  way["landuse"="quarry"]({bbox});
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


def _overpass_urls() -> List[str]:
    urls, seen = [], set()
    for u in [settings.OVERPASS_URL] + FALLBACK_MIRRORS:
        if u and u not in seen:
            seen.add(u)
            urls.append(u)
    return urls


def _post_overpass(query: str) -> dict:
    """POST the query to each mirror in turn until one returns usable JSON."""
    deadline = time.monotonic() + TOTAL_BUDGET_S
    urls = _overpass_urls()
    last_err = "no attempt made"

    # Cycle through the mirrors up to twice, bounded by the time budget.
    for url in urls + urls:
        remaining = deadline - time.monotonic()
        if remaining < 10:
            break
        try:
            resp = requests.post(
                url,
                data={"data": query},
                headers=HEADERS,
                timeout=(CONNECT_TIMEOUT_S, min(READ_TIMEOUT_S, remaining)),
            )
            if resp.status_code in RETRY_STATUS:
                last_err = f"{url} -> HTTP {resp.status_code}"
                logger.warning("Overpass mirror busy: %s", last_err)
                time.sleep(PAUSE_BETWEEN_TRIES_S)
                continue
            resp.raise_for_status()
            data = resp.json()

            # Overpass can answer HTTP 200 with a 'remark' (timeout / out of memory).
            if data.get("remark") and not data.get("elements"):
                last_err = f"{url} -> remark: {data['remark'][:120]}"
                logger.warning("Overpass returned a remark and no data: %s", last_err)
                time.sleep(PAUSE_BETWEEN_TRIES_S)
                continue
            if data.get("remark"):
                logger.warning("Overpass partial result, remark: %s", data["remark"][:120])

            logger.info("Overpass OK via %s (%d elements)", url, len(data.get("elements", [])))
            return data
        except (requests.RequestException, ValueError) as e:
            last_err = f"{url} -> {type(e).__name__}: {str(e)[:150]}"
            logger.warning("Overpass request failed: %s", last_err)
            time.sleep(PAUSE_BETWEEN_TRIES_S)

    raise RuntimeError(f"All Overpass mirrors failed. Last error: {last_err}")


def fetch_osm_industrial_polygons() -> List[Dict]:
    """
    Query Overpass and return a list of {osm_id, name, tags, polygon(shapely)}.
    Uses the Overpass "out body; >; out skel qt;" pattern to also pull node
    coordinates, then reconstructs way polygons in Python.
    """
    query = OVERPASS_QUERY_TEMPLATE.format(bbox=settings.OSM_BBOX)
    data = _post_overpass(query)

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
