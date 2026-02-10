from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import Settings
from migrations import run_migrations
from models import Base


engine = create_engine(Settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    """
    SQLite has no schema migration engine here; we do:
    1) create_all for new tables
    2) idempotent ALTER TABLE / indexes for legacy DBs
    """
    Base.metadata.create_all(engine)
    run_migrations(engine)
