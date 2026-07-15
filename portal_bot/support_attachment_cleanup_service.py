from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from heapq import nsmallest
from pathlib import Path
from typing import Callable

from models import SupportAttachment


@dataclass
class SupportAttachmentCleanupCursor:
    file_after: str = ""
    file_cycle_cutoff_ns: int = 0
    row_after_id: int = 0
    row_cycle_high_water_id: int = 0


_CANONICAL_NAME_RE = re.compile(r"\d{8}-[A-Za-z0-9]{8,64}\.(?:png|jpg|jpeg|webp|pdf|txt)")
_TEMP_NAME_RE = re.compile(
    r"\.\d{8}-[A-Za-z0-9]{8,64}\.(?:png|jpg|jpeg|webp|pdf|txt)\.[A-Fa-f0-9]{8,64}\.tmp"
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _fsync_directory(path: Path) -> None:
    if os.name != "posix":
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    directory_fd = os.open(str(path), flags)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _is_old_enough(path: Path, cutoff: datetime) -> bool:
    try:
        modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(tzinfo=None)
    except (FileNotFoundError, OSError):
        return False
    return modified_at <= cutoff


def _is_cleanup_file(path: Path) -> bool:
    return (
        _TEMP_NAME_RE.fullmatch(path.name) is not None
        or _CANONICAL_NAME_RE.fullmatch(path.name) is not None
    )


def _next_file_window(
    root: Path,
    *,
    after: str,
    cycle_cutoff_ns: int,
    limit: int,
) -> tuple[list[Path], int]:
    entries_enumerated = 0

    def eligible_paths():
        nonlocal entries_enumerated
        for path in root.iterdir():
            entries_enumerated += 1
            if not _is_cleanup_file(path) or path.name <= after:
                continue
            try:
                if path.stat().st_mtime_ns <= cycle_cutoff_ns:
                    yield path
            except (FileNotFoundError, OSError):
                continue

    selected = nsmallest(limit, eligible_paths(), key=lambda item: item.name)
    return selected, entries_enumerated


def _next_row_window(
    session,
    *,
    after_id: int,
    cycle_high_water_id: int,
    limit: int,
) -> list[tuple[int, str]]:
    if cycle_high_water_id <= 0:
        return []
    rows = (
        session.query(SupportAttachment.id, SupportAttachment.stored_name)
        .filter(
            SupportAttachment.id > after_id,
            SupportAttachment.id <= cycle_high_water_id,
        )
        .order_by(SupportAttachment.id.asc())
        .limit(limit)
        .all()
    )
    return [(int(row_id), str(stored_name)) for row_id, stored_name in rows]


def reconcile_support_attachments(
    session_factory: Callable,
    *,
    upload_dir: Path,
    now: datetime | None = None,
    grace_seconds: int = 3600,
    batch_size: int = 100,
    scan_limit: int = 500,
    cursor: SupportAttachmentCleanupCursor | None = None,
) -> dict[str, int]:
    current = now or _utcnow()
    grace_cutoff = current - timedelta(seconds=max(60, int(grace_seconds)))
    row_limit = max(1, min(1000, int(batch_size)))
    file_limit = max(1, min(5000, int(scan_limit)))
    root = Path(upload_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    report = {
        "expired_rows_removed": 0,
        "expired_files_removed": 0,
        "expired_files_missing": 0,
        "expired_files_preserved": 0,
        "temp_files_removed": 0,
        "orphan_files_removed": 0,
        "rows_missing_files": 0,
        "rows_scanned": 0,
        "malformed_rows_skipped": 0,
        "file_errors": 0,
        "file_candidates_selected": 0,
        "filesystem_entries_enumerated": 0,
        "file_window_wrapped": 0,
        "row_window_wrapped": 0,
    }

    expired_names: list[str] = []
    session = session_factory()
    try:
        query = (
            session.query(SupportAttachment)
            .filter(
                SupportAttachment.ticket_id.is_(None),
                SupportAttachment.message_id.is_(None),
                SupportAttachment.expires_at.isnot(None),
                SupportAttachment.expires_at <= current,
            )
            .order_by(SupportAttachment.id.asc())
            .limit(row_limit)
        )
        if session.bind is not None and session.bind.dialect.name == "postgresql":
            query = query.with_for_update(skip_locked=True)
        for row in query.all():
            removed = (
                session.query(SupportAttachment)
                .filter(
                    SupportAttachment.id == row.id,
                    SupportAttachment.ticket_id.is_(None),
                    SupportAttachment.message_id.is_(None),
                    SupportAttachment.expires_at.isnot(None),
                    SupportAttachment.expires_at <= current,
                )
                .delete(synchronize_session=False)
            )
            if removed:
                expired_names.append(str(row.stored_name))
                session.expunge(row)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    report["expired_rows_removed"] = len(expired_names)
    expired_files_changed = False
    session = session_factory()
    try:
        for stored_name in expired_names:
            clean_name = Path(stored_name).name
            if clean_name != stored_name or _CANONICAL_NAME_RE.fullmatch(clean_name) is None:
                report["malformed_rows_skipped"] += 1
                continue
            row_reappeared = (
                session.query(SupportAttachment.id)
                .filter(SupportAttachment.stored_name == clean_name)
                .first()
                is not None
            )
            if row_reappeared:
                report["expired_files_preserved"] += 1
                continue
            path = root / clean_name
            try:
                path.unlink()
                expired_files_changed = True
                report["expired_files_removed"] += 1
            except FileNotFoundError:
                report["expired_files_missing"] += 1
            except OSError:
                report["file_errors"] += 1
    finally:
        try:
            session.close()
        finally:
            if expired_files_changed:
                try:
                    _fsync_directory(root)
                except OSError:
                    report["file_errors"] += 1

    file_after = str(cursor.file_after if cursor is not None else "")
    file_cycle_cutoff_ns = int(cursor.file_cycle_cutoff_ns if cursor is not None else 0)
    if file_cycle_cutoff_ns <= 0:
        file_cycle_cutoff_ns = time.time_ns()
    try:
        candidates, entries_enumerated = _next_file_window(
            root,
            after=file_after,
            cycle_cutoff_ns=file_cycle_cutoff_ns,
            limit=file_limit,
        )
    except FileNotFoundError:
        candidates, entries_enumerated = [], 0
    report["file_candidates_selected"] = len(candidates)
    report["filesystem_entries_enumerated"] = entries_enumerated
    file_cycle_exhausted = len(candidates) < file_limit
    report["file_window_wrapped"] = int(file_cycle_exhausted)

    candidate_files_changed = False
    candidate_fsync_failed = False
    session = session_factory()
    try:
        row_after_id = int(cursor.row_after_id if cursor is not None else 0)
        row_cycle_high_water_id = int(cursor.row_cycle_high_water_id if cursor is not None else 0)
        if row_cycle_high_water_id <= 0:
            high_water_row = (
                session.query(SupportAttachment.id)
                .order_by(SupportAttachment.id.desc())
                .first()
            )
            row_cycle_high_water_id = int(high_water_row[0]) if high_water_row is not None else 0
        rows = _next_row_window(
            session,
            after_id=row_after_id,
            cycle_high_water_id=row_cycle_high_water_id,
            limit=file_limit,
        )
        row_cycle_exhausted = (
            not rows
            or len(rows) < file_limit
            or rows[-1][0] >= row_cycle_high_water_id
        )
        report["row_window_wrapped"] = int(row_cycle_exhausted)
        for _row_id, stored_name in rows:
            clean_name = Path(stored_name).name
            report["rows_scanned"] += 1
            if clean_name != stored_name or _CANONICAL_NAME_RE.fullmatch(clean_name) is None:
                report["malformed_rows_skipped"] += 1
                continue
            path = root / clean_name
            if not path.exists() or not path.is_file():
                report["rows_missing_files"] += 1

        for path in candidates:
            if not _is_old_enough(path, grace_cutoff):
                continue
            if _TEMP_NAME_RE.fullmatch(path.name):
                try:
                    path.unlink()
                    candidate_files_changed = True
                    report["temp_files_removed"] += 1
                except FileNotFoundError:
                    continue
                except OSError:
                    report["file_errors"] += 1
                continue

            row_exists = (
                session.query(SupportAttachment.id)
                .filter(SupportAttachment.stored_name == path.name)
                .first()
                is not None
            )
            if row_exists:
                continue
            try:
                path.unlink()
                candidate_files_changed = True
                report["orphan_files_removed"] += 1
            except FileNotFoundError:
                continue
            except OSError:
                report["file_errors"] += 1
    finally:
        try:
            session.close()
        finally:
            if candidate_files_changed:
                try:
                    _fsync_directory(root)
                except OSError:
                    candidate_fsync_failed = True
                    report["file_errors"] += 1

    if cursor is not None:
        if candidate_fsync_failed:
            cursor.file_after = file_after
            cursor.file_cycle_cutoff_ns = file_cycle_cutoff_ns
        elif file_cycle_exhausted:
            cursor.file_after = ""
            cursor.file_cycle_cutoff_ns = 0
        else:
            cursor.file_after = candidates[-1].name
            cursor.file_cycle_cutoff_ns = file_cycle_cutoff_ns
        if row_cycle_exhausted:
            cursor.row_after_id = 0
            cursor.row_cycle_high_water_id = 0
        else:
            cursor.row_after_id = rows[-1][0]
            cursor.row_cycle_high_water_id = row_cycle_high_water_id

    return report
