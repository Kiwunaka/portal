from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import Settings
from account_foundation_service import run_account_foundation_backfill_once
from migrations import POSTGRES_SCHEMA_BOOTSTRAP_LOCK, run_migrations
from models import Base


engine = create_engine(Settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def _create_schema() -> None:
    if str(engine.dialect.name or "") != "postgresql":
        Base.metadata.create_all(engine)
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                f"SELECT pg_advisory_xact_lock(hashtext('{POSTGRES_SCHEMA_BOOTSTRAP_LOCK}'))"
            )
        )
        Base.metadata.create_all(bind=connection)


def init_db() -> None:
    """
    SQLite has no schema migration engine here; we do:
    1) create_all for new tables
    2) idempotent ALTER TABLE / indexes for legacy DBs
    """
    _create_schema()
    run_migrations(engine)
    with SessionLocal() as session:
        run_account_foundation_backfill_once(session)
        session.commit()
