"""
Task #15 — Demo dataset prep for the chosen region + rehearsal.

Seeds one demo industrial site (a refinery) plus a realistic time series of
hotspots at that site: many steady "gas flare" readings, then one clean
"accident_explosion" spike — so the live demo has a guaranteed, rehearsed
"aha" moment (per Problem Statement 2.5's stated weakness/fix: the demo
needs a strong alert-firing moment).

Run with:  python -m scripts.seed_demo_data
(after `docker compose up` / migrations have created the schema)
"""
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shapely.geometry import Point, Polygon
from geoalchemy2.shape import from_shape

from app.database import SessionLocal, init_db
from app.models.industrial_site import IndustrialSite
from app.models.hotspot import Hotspot
from app.services.firms_ingest import build_source_key
from app.services.spatial_join import run_spatial_join
from app.services.classifier import classify_and_persist
from app.services.alerting import evaluate_and_raise_alerts

# Demo site: a refinery footprint near Jamnagar, Gujarat (real refinery hub,
# coordinates approximate/illustrative for the demo — not a precise boundary).
DEMO_LAT, DEMO_LON = 22.3511, 69.8654


def make_demo_site(db):
    poly = Polygon([
        (DEMO_LON - 0.01, DEMO_LAT - 0.01),
        (DEMO_LON + 0.01, DEMO_LAT - 0.01),
        (DEMO_LON + 0.01, DEMO_LAT + 0.01),
        (DEMO_LON - 0.01, DEMO_LAT + 0.01),
        (DEMO_LON - 0.01, DEMO_LAT - 0.01),
    ])
    site = IndustrialSite(
        osm_id="demo/refinery/1",
        name="Demo Refinery (Jamnagar area, illustrative)",
        site_type="refinery",
        tags="{}",
        geom=from_shape(poly, srid=4326),
    )
    db.add(site)
    db.commit()
    return site


def make_demo_hotspots(db):
    hotspots = []
    dates = [f"2026-08-{d:02d}" for d in range(1, 26)]  # 25 days of steady flare
    for d in dates:
        lat = DEMO_LAT + random.uniform(-0.0005, 0.0005)
        lon = DEMO_LON + random.uniform(-0.0005, 0.0005)
        h = Hotspot(
            latitude=lat, longitude=lon,
            brightness=330 + random.uniform(-3, 3),  # steady baseline
            frp=8 + random.uniform(-1, 1),
            confidence="nominal",
            satellite="N20", sensor="VIIRS",
            acq_date=d, acq_time="0930",
            daynight="D",
            geom=from_shape(Point(lon, lat), srid=4326),
            source_key=build_source_key(lat, lon),
        )
        db.add(h)
        hotspots.append(h)

    # The rehearsed "aha" moment: a sharp spike at the same source on day 26
    spike_lat = DEMO_LAT + random.uniform(-0.0002, 0.0002)
    spike_lon = DEMO_LON + random.uniform(-0.0002, 0.0002)
    spike = Hotspot(
        latitude=spike_lat, longitude=spike_lon,
        brightness=410.0,  # well above the ~330 baseline -> high z-score
        frp=65.0,
        confidence="high",
        satellite="N20", sensor="VIIRS",
        acq_date="2026-08-26", acq_time="0930",
        daynight="D",
        geom=from_shape(Point(spike_lon, spike_lat), srid=4326),
        source_key=build_source_key(DEMO_LAT, DEMO_LON),  # same source_key as the baseline series
    )
    db.add(spike)
    hotspots.append(spike)

    db.commit()
    for h in hotspots:
        db.refresh(h)
    return hotspots


def main():
    init_db()
    db = SessionLocal()
    try:
        print("Seeding demo industrial site...")
        make_demo_site(db)

        print("Seeding demo hotspot time series (25 steady + 1 spike)...")
        hotspots = make_demo_hotspots(db)

        print("Running spatial join...")
        run_spatial_join(db, hotspots)

        print("Running classification...")
        classify_and_persist(db, hotspots)

        print("Evaluating alerts...")
        alerts = evaluate_and_raise_alerts(db, hotspots)

        print(f"Done. Seeded {len(hotspots)} hotspots, raised {len(alerts)} alert(s).")
        print("Hit GET /api/alerts to see the accident_explosion alert fire.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
