-- Supplementary land-use table (Task #9's "hotspots + history" schema also
-- needs this for the classifier's farmland/forest/mining/desert checks).
-- Populate via a Python script hitting Overpass with:
--   way["landuse"="farmland"]({bbox});
--   way["natural"="wood"]({bbox});  way["landuse"="forest"]({bbox});
--   way["natural"="desert"]({bbox}); way["natural"="sand"]({bbox}); way["natural"="scrub"]({bbox});
--   way["landuse"="quarry"]({bbox}); way["man_made"="spoil_heap"]({bbox});  -- mining/exposed
-- (mirrors the pattern in app/services/osm_fetch.py — reuse fetch_osm_industrial_polygons()'s
-- Overpass-parsing helper with a different query string, then insert with land_use_type set
-- to 'farmland' | 'forest' | 'desert' | 'mining' | 'exposed'.)

CREATE TABLE IF NOT EXISTS land_use_polygons (
    id SERIAL PRIMARY KEY,
    osm_id VARCHAR UNIQUE NOT NULL,
    land_use_type VARCHAR NOT NULL,
    geom GEOMETRY(POLYGON, 4326) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_land_use_polygons_geom ON land_use_polygons USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_land_use_polygons_type ON land_use_polygons (land_use_type);
