-- Run once after app.database.init_db() has created the base tables
-- (hotspots, industrial_sites, alerts) via SQLAlchemy. These GIST indexes
-- are what make the spatial join (Task #10) fast at scale.

CREATE INDEX IF NOT EXISTS idx_hotspots_geom ON hotspots USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_industrial_sites_geom ON industrial_sites USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_hotspots_source_key ON hotspots (source_key);
CREATE INDEX IF NOT EXISTS idx_hotspots_acq_date ON hotspots (acq_date);
CREATE INDEX IF NOT EXISTS idx_hotspots_category ON hotspots (category);
