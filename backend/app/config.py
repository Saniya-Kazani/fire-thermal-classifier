"""
Central configuration. All tunables live here, loaded from environment
variables / .env so nothing is hardcoded inside business logic.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql://thermal_user:thermal_pass@localhost:5432/thermal_db"

    # NASA FIRMS
    FIRMS_MAP_KEY: str = ""
    FIRMS_SOURCE: str = "VIIRS_SNPP_NRT"
    FIRMS_BBOX: str = "68.0,6.0,97.0,37.0"  # west,south,east,north
    FIRMS_DAY_RANGE: int = 1

    # OSM Overpass
    OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
    OSM_BBOX: str = "6.0,68.0,37.0,97.0"  # south,west,north,east

    # Scheduler
    FIRMS_POLL_INTERVAL_MINUTES: int = 360
    OSM_REFRESH_INTERVAL_HOURS: int = 168

    # Spatial matching
    INDUSTRIAL_BUFFER_METERS: float = 500.0

    # Anomaly detection
    ANOMALY_ZSCORE_THRESHOLD: float = 3.0
    MIN_HISTORY_POINTS_FOR_ZSCORE: int = 5

    # App
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"


settings = Settings()
