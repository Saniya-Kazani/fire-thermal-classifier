"""
Task #6 — Backend project setup + REST API skeleton.

Wires together the DB init, scheduler, and all routers. Run with:
    uvicorn app.main:app --reload --port 8000
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.scheduler import start_scheduler, stop_scheduler
from app.routers import hotspots, sites, alerts, ingestion, industrial_ai

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initializing DB (PostGIS extension + tables)")
    init_db()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Industrial Fire & Thermal Source Classification API",
    description="Backend for SIH26162 — classifies NASA FIRMS thermal hotspots "
                "(gas flare / accident / crop burning / coal seam fire / wildfire / "
                "false alarm) using industrial-site spatial joins and time-series pattern rules.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hotspots.router)
app.include_router(sites.router)
app.include_router(alerts.router)
app.include_router(ingestion.router)
app.include_router(industrial_ai.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "env": settings.ENV}
