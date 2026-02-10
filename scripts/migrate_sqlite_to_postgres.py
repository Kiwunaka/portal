from __future__ import annotations

import argparse
import os
from collections.abc import Iterable

from sqlalchemy import MetaData, Table, create_engine, inspect, select, text


def _chunked(items: list[dict], size: int) -> Iterable[list[dict]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def main() -> int:
    ap = argparse.ArgumentParser(description="One-shot data migration from SQLite to PostgreSQL.")
    ap.add_argument("--sqlite-url", default=os.getenv("SQLITE_DATABASE_URL", "sqlite:////root/portal_bot/portal.db"))
    ap.add_argument("--postgres-url", default=os.getenv("POSTGRES_DATABASE_URL", ""))
    ap.add_argument("--chunk-size", type=int, default=1000)
    ap.add_argument("--truncate-target", action="store_true")
    args = ap.parse_args()

    if not args.postgres_url:
        raise SystemExit("Missing --postgres-url (or POSTGRES_DATABASE_URL).")
    if not args.sqlite_url.startswith("sqlite"):
        raise SystemExit("--sqlite-url must point to a sqlite database.")
    if not args.postgres_url.startswith("postgresql"):
        raise SystemExit("--postgres-url must point to a postgresql database.")

    # Late import so the script can run from repository root and from /root/portal_bot on servers.
    try:
        from portal_bot.models import Base  # type: ignore  # pylint: disable=import-outside-toplevel
    except Exception:
        from models import Base  # type: ignore  # pylint: disable=import-outside-toplevel

    src_engine = create_engine(args.sqlite_url)
    dst_engine = create_engine(args.postgres_url)

    # Ensure schema exists on target.
    Base.metadata.create_all(dst_engine)

    src_inspector = inspect(src_engine)
    src_tables = set(src_inspector.get_table_names())
    ordered_tables = [t.name for t in Base.metadata.sorted_tables if t.name in src_tables]
    if not ordered_tables:
        raise SystemExit("No shared tables found between source sqlite and model metadata.")

    if args.truncate_target:
        with dst_engine.begin() as dst_conn:
            quoted = ", ".join(f'"{name}"' for name in ordered_tables)
            dst_conn.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE;"))

    src_meta = MetaData()
    src_meta.reflect(bind=src_engine, only=ordered_tables)

    total_rows = 0
    with src_engine.connect() as src_conn:
        with dst_engine.begin() as dst_conn:
            for table_name in ordered_tables:
                src_table: Table = src_meta.tables[table_name]
                dst_table: Table = Base.metadata.tables[table_name]

                src_col_names = {c.name for c in src_table.columns}
                dst_col_names = [c.name for c in dst_table.columns if c.name in src_col_names]
                if not dst_col_names:
                    print(f"{table_name}: skipped (no common columns)")
                    continue

                rows = src_conn.execute(select(src_table)).mappings().all()
                payload = [{k: row.get(k) for k in dst_col_names} for row in rows]
                if payload:
                    for chunk in _chunked(payload, max(1, int(args.chunk_size))):
                        dst_conn.execute(dst_table.insert(), chunk)
                total_rows += len(payload)
                print(f"{table_name}: copied {len(payload)} rows")

    print(f"done: copied {total_rows} total rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
