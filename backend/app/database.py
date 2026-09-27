"""
SQLAlchemy engine + session management.
PostGIS extension is enabled at startup (see init_db()).
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session, closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create the PostGIS extension (if missing) and all ORM tables."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()

    # Import models so they register on Base.metadata before create_all
    from app.models import hotspot, industrial_site, alert  # noqa: F401

    Base.metadata.create_all(bind=engine)
