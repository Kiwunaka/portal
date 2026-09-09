from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from config import Settings
from db_pool_runtime import ObservedQueuePool
from account_foundation_service import run_account_foundation_backfill_once
from support_account_service import run_support_account_ownership_backfill_once
from migrations import POSTGRES_SCHEMA_BOOTSTRAP_LOCK, run_migrations
from models import Base


pool_options = (
    {"poolclass": ObservedQueuePool}
    if make_url(Settings.DATABASE_URL).get_backend_name() == "postgresql"
    else {}
)
engine = create_engine(
    Settings.DATABASE_URL, pool_pre_ping=True, hide_parameters=True, **pool_options
)
SessionLocal = sessionmaker(bind=engine)


def database_pool_snapshot() -> dict[str, int] | None:
    return engine.pool.wait_snapshot() if isinstance(engine.pool, ObservedQueuePool) else None


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
        run_support_account_ownership_backfill_once(session)
        session.commit()
