import importlib
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Query, sessionmaker


def test_support_attachment_cleanup_service_exposes_reconciler() -> None:
    module = importlib.import_module("support_attachment_cleanup_service")

    assert callable(module.reconcile_support_attachments)


def test_support_attachment_cleanup_service_exposes_bounded_cursor() -> None:
    module = importlib.import_module("support_attachment_cleanup_service")

    cursor = module.SupportAttachmentCleanupCursor()
    assert cursor.file_after == ""
    assert cursor.file_cycle_cutoff_ns == 0
    assert cursor.row_after_id == 0
    assert cursor.row_cycle_high_water_id == 0


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _session_factory(tmp_path):
    from models import SupportAttachment

    engine = create_engine(f"sqlite:///{(tmp_path / 'attachments.db').as_posix()}")
    SupportAttachment.__table__.create(engine)
    return engine, sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _attachment(*, stored_name: str, now: datetime, expires_at: datetime | None, **overrides):
    from models import SupportAttachment

    values = {
        "stored_name": stored_name,
        "owner_tg_id": 1001,
        "owner_account_id": "cleanup-owner",
        "original_name": stored_name,
        "content_type": "text/plain",
        "size_bytes": 7,
        "media_type": "file",
        "expires_at": expires_at,
        "created_at": now - timedelta(hours=3),
    }
    values.update(overrides)
    return SupportAttachment(**values)


def _age(path, when: datetime) -> None:
    timestamp = when.replace(tzinfo=timezone.utc).timestamp()
    os.utime(path, (timestamp, timestamp))


def _set_mtime_ns(path, timestamp_ns: int) -> None:
    os.utime(path, ns=(timestamp_ns, timestamp_ns))


def test_reconciler_removes_only_old_temp_and_rowless_canonical_files(tmp_path) -> None:
    cleanup = importlib.import_module("support_attachment_cleanup_service")
    now = _utcnow()
    engine, sessions = _session_factory(tmp_path)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    old_temp = upload_dir / ".20260714-tempfile01.txt.deadbeef.tmp"
    old_orphan = upload_dir / "20260714-orphan001.txt"
    recent_orphan = upload_dir / "20260714-orphan002.txt"
    row_present = upload_dir / "20260714-present01.txt"
    unrelated = upload_dir / "notes.txt"
    for path in (old_temp, old_orphan, recent_orphan, row_present, unrelated):
        path.write_bytes(path.name.encode("ascii"))
    for path in (old_temp, old_orphan, row_present, unrelated):
        _age(path, now - timedelta(hours=2))
    _age(recent_orphan, now - timedelta(minutes=5))

    session = sessions()
    try:
        session.add(_attachment(stored_name=row_present.name, now=now, expires_at=None))
        session.commit()
    finally:
        session.close()

    try:
        report = cleanup.reconcile_support_attachments(
            sessions,
            upload_dir=upload_dir,
            now=now,
            grace_seconds=3600,
            batch_size=10,
            scan_limit=20,
        )
    finally:
        engine.dispose()

    assert report["temp_files_removed"] == 1
    assert report["orphan_files_removed"] == 1
    assert report["file_candidates_selected"] <= 20
    assert not old_temp.exists()
    assert not old_orphan.exists()
    assert recent_orphan.exists()
    assert row_present.exists()
    assert unrelated.exists()
    assert all(isinstance(value, int) for value in report.values())


def test_cleanup_directory_fsync_is_posix_only(monkeypatch, tmp_path) -> None:
    cleanup = importlib.import_module("support_attachment_cleanup_service")
    expected_flags = cleanup.os.O_RDONLY | getattr(cleanup.os, "O_DIRECTORY", 0)
    calls: list[tuple] = []

    monkeypatch.setattr(cleanup.os, "name", "posix")
    monkeypatch.setattr(
        cleanup.os,
        "open",
        lambda path, flags: calls.append(("open", path, flags)) or 73,
    )
    monkeypatch.setattr(cleanup.os, "fsync", lambda fd: calls.append(("fsync", fd)))
    monkeypatch.setattr(cleanup.os, "close", lambda fd: calls.append(("close", fd)))

    cleanup._fsync_directory(tmp_path)

    assert calls == [
        ("open", str(tmp_path), expected_flags),
        ("fsync", 73),
        ("close", 73),
    ]

    calls.clear()
    monkeypatch.setattr(cleanup.os, "name", "nt")
    cleanup._fsync_directory(tmp_path)
    assert calls == []


def test_reconciler_fsyncs_directory_after_successful_unlinks(monkeypatch, tmp_path) -> None:
    cleanup = importlib.import_module("support_attachment_cleanup_service")
    now = _utcnow()
    engine, sessions = _session_factory(tmp_path)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    old_temp = upload_dir / ".20260714-fsynctest1.txt.deadbeef.tmp"
    old_temp.write_bytes(b"old")
    _age(old_temp, now - timedelta(hours=2))
    synced: list = []
    monkeypatch.setattr(cleanup, "_fsync_directory", lambda path: synced.append(path))

    try:
        report = cleanup.reconcile_support_attachments(
            sessions,
            upload_dir=upload_dir,
            now=now,
            grace_seconds=3600,
            batch_size=10,
            scan_limit=20,
        )
    finally:
        engine.dispose()

    assert report["temp_files_removed"] == 1
    assert synced == [upload_dir.resolve()]


def test_reconciler_reports_directory_fsync_failure(monkeypatch, tmp_path) -> None:
    cleanup = importlib.import_module("support_attachment_cleanup_service")
    now = _utcnow()
    engine, sessions = _session_factory(tmp_path)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    old_orphan = upload_dir / "20260714-fsyncfail1.txt"
    old_orphan.write_bytes(b"old")
    _age(old_orphan, now - timedelta(hours=2))

    def fail_fsync(_path):
        raise OSError("forced directory fsync failure")

    monkeypatch.setattr(cleanup, "_fsync_directory", fail_fsync)
    try:
        report = cleanup.reconcile_support_attachments(
            sessions,
            upload_dir=upload_dir,
            now=now,
            grace_seconds=3600,
            batch_size=10,
            scan_limit=20,
        )
    finally:
        engine.dispose()

    assert report["orphan_files_removed"] == 1
    assert report["file_errors"] == 1


def test_reconciler_retries_same_file_window_after_directory_fsync_failure(
    monkeypatch, tmp_path
) -> None:
    cleanup = importlib.import_module("support_attachment_cleanup_service")
    now = _utcnow()
    engine, sessions = _session_factory(tmp_path)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    first = upload_dir / "20260714-fsyncretry1.txt"
    second = upload_dir / "20260714-fsyncretry2.txt"
    for path in (first, second):
        path.write_bytes(b"old")
        _age(path, now - timedelta(hours=2))
    cursor = cleanup.SupportAttachmentCleanupCursor()

    monkeypatch.setattr(
        cleanup,
        "_fsync_directory",
        lambda _path: (_ for _ in ()).throw(OSError("forced directory fsync failure")),
    )
    try:
        failed = cleanup.reconcile_support_attachments(
            sessions,
            upload_dir=upload_dir,
            now=now,
            grace_seconds=3600,
            batch_size=10,
            scan_limit=1,
            cursor=cursor,
        )

        assert failed["orphan_files_removed"] == 1
        assert failed["file_errors"] == 1
        assert cursor.file_after == ""
        assert cursor.file_cycle_cutoff_ns > 0

        first.write_bytes(b"reappeared-after-power-loss")
        _age(first, now - timedelta(hours=2))
        monkeypatch.setattr(cleanup, "_fsync_directory", lambda _path: None)
        retried = cleanup.reconcile_support_attachments(
            sessions,
            upload_dir=upload_dir,
            now=now,
            grace_seconds=3600,
            batch_size=10,
            scan_limit=1,
            cursor=cursor,
        )
    finally:
        engine.dispose()

    assert retried["orphan_files_removed"] == 1
    assert not first.exists()
    assert second.exists()
    assert cursor.file_after == first.name


def test_reconciler_cleans_expired_rows_but_preserves_bound_and_legacy_rows_idempotently(tmp_path) -> None:
    from models import SupportAttachment

    cleanup = importlib.import_module("support_attachment_cleanup_service")
    now = _utcnow()
    engine, sessions = _session_factory(tmp_path)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    expired_file = upload_dir / "20260714-expired01.txt"
    bound_file = upload_dir / "20260714-bound001.txt"
    legacy_file = upload_dir / "20260714-legacy001.txt"
    for path in (expired_file, bound_file, legacy_file):
        path.write_bytes(path.name.encode("ascii"))

    session = sessions()
    try:
        session.add_all(
            [
                _attachment(
                    stored_name=expired_file.name,
                    now=now,
                    expires_at=now - timedelta(minutes=5),
                ),
                _attachment(
                    stored_name="20260714-missing01.txt",
                    now=now,
                    expires_at=now - timedelta(minutes=4),
                ),
                _attachment(
                    stored_name=bound_file.name,
                    now=now,
                    expires_at=now - timedelta(minutes=3),
                    ticket_id=77,
                    message_id=88,
                ),
                _attachment(stored_name=legacy_file.name, now=now, expires_at=None),
            ]
        )
        session.commit()
    finally:
        session.close()

    first = cleanup.reconcile_support_attachments(
        sessions,
        upload_dir=upload_dir,
        now=now,
        grace_seconds=3600,
        batch_size=10,
        scan_limit=20,
    )
    second = cleanup.reconcile_support_attachments(
        sessions,
        upload_dir=upload_dir,
        now=now,
        grace_seconds=3600,
        batch_size=10,
        scan_limit=20,
    )

    session = sessions()
    try:
        names = {row.stored_name for row in session.query(SupportAttachment).all()}
    finally:
        session.close()
        engine.dispose()

    assert first["expired_rows_removed"] == 2
    assert first["expired_files_removed"] == 1
    assert first["expired_files_missing"] == 1
    assert second["expired_rows_removed"] == 0
    assert second["expired_files_removed"] == 0
    assert second["expired_files_missing"] == 0
    assert not expired_file.exists()
    assert bound_file.exists()
    assert legacy_file.exists()
    assert names == {bound_file.name, legacy_file.name}


def test_reconciler_reports_bounded_missing_rows_without_deleting_them(tmp_path) -> None:
    from models import SupportAttachment

    cleanup = importlib.import_module("support_attachment_cleanup_service")
    now = _utcnow()
    engine, sessions = _session_factory(tmp_path)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    session = sessions()
    try:
        session.add_all(
            [
                _attachment(
                    stored_name="20260714-missingbound.txt",
                    now=now,
                    expires_at=now - timedelta(minutes=1),
                    ticket_id=7,
                    message_id=8,
                ),
                _attachment(
                    stored_name="20260714-missinglive1.txt",
                    now=now,
                    expires_at=now + timedelta(hours=1),
                ),
                _attachment(stored_name="20260714-missinglegacy.txt", now=now, expires_at=None),
            ]
        )
        session.commit()
    finally:
        session.close()

    report = cleanup.reconcile_support_attachments(
        sessions,
        upload_dir=upload_dir,
        now=now,
        grace_seconds=3600,
        batch_size=10,
        scan_limit=2,
    )
    session = sessions()
    try:
        names = {row.stored_name for row in session.query(SupportAttachment).all()}
    finally:
        session.close()
        engine.dispose()

    assert report["rows_scanned"] == 2
    assert report["rows_missing_files"] == 2
    assert names == {
        "20260714-missingbound.txt",
        "20260714-missinglive1.txt",
        "20260714-missinglegacy.txt",
    }


def test_reconciler_never_maps_malformed_db_name_to_canonical_file(tmp_path) -> None:
    cleanup = importlib.import_module("support_attachment_cleanup_service")
    now = _utcnow()
    engine, sessions = _session_factory(tmp_path)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    protected = upload_dir / "20260714-protected1.txt"
    protected.write_bytes(b"must remain")
    _age(protected, now - timedelta(hours=2))

    session = sessions()
    try:
        session.add_all(
            [
                _attachment(
                    stored_name=f"nested/{protected.name}",
                    now=now,
                    expires_at=now - timedelta(minutes=1),
                ),
                _attachment(stored_name=protected.name, now=now, expires_at=None),
            ]
        )
        session.commit()
    finally:
        session.close()

    try:
        report = cleanup.reconcile_support_attachments(
            sessions,
            upload_dir=upload_dir,
            now=now,
            grace_seconds=3600,
            batch_size=10,
            scan_limit=20,
        )
    finally:
        engine.dispose()

    assert protected.exists()
    assert report["malformed_rows_skipped"] == 1


def test_reconciler_preserves_file_when_row_reappears_after_expired_commit(tmp_path) -> None:
    cleanup = importlib.import_module("support_attachment_cleanup_service")
    now = _utcnow()
    engine, sessions = _session_factory(tmp_path)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    stored_name = "20260714-reappeared.txt"
    stored_path = upload_dir / stored_name
    stored_path.write_bytes(b"replacement-owned file")

    session = sessions()
    try:
        session.add(
            _attachment(
                stored_name=stored_name,
                now=now,
                expires_at=now - timedelta(minutes=1),
            )
        )
        session.commit()
    finally:
        session.close()

    factory_calls = 0

    class _ReplaceAfterCloseSession:
        def __init__(self, inner):
            self._inner = inner

        def close(self):
            self._inner.close()
            replacement = sessions()
            try:
                replacement.add(_attachment(stored_name=stored_name, now=now, expires_at=None))
                replacement.commit()
            finally:
                replacement.close()

        def __getattr__(self, name):
            return getattr(self._inner, name)

    def replacing_factory():
        nonlocal factory_calls
        factory_calls += 1
        inner = sessions()
        return _ReplaceAfterCloseSession(inner) if factory_calls == 1 else inner

    try:
        report = cleanup.reconcile_support_attachments(
            replacing_factory,
            upload_dir=upload_dir,
            now=now,
            grace_seconds=3600,
            batch_size=10,
            scan_limit=20,
        )
    finally:
        engine.dispose()

    assert stored_path.exists()
    assert report["expired_files_removed"] == 0


def test_reconciler_uses_postgres_skip_locked_for_expired_batch(tmp_path, monkeypatch) -> None:
    cleanup = importlib.import_module("support_attachment_cleanup_service")
    now = _utcnow()
    engine, sessions = _session_factory(tmp_path)
    engine.dialect.name = "postgresql"
    upload_dir = tmp_path / "uploads"
    calls: list[dict] = []
    original = Query.with_for_update

    def recording_with_for_update(query, *args, **kwargs):
        calls.append(dict(kwargs))
        return original(query, *args, **kwargs)

    monkeypatch.setattr(Query, "with_for_update", recording_with_for_update)
    try:
        cleanup.reconcile_support_attachments(
            sessions,
            upload_dir=upload_dir,
            now=now,
            grace_seconds=3600,
            batch_size=10,
            scan_limit=20,
        )
    finally:
        engine.dispose()

    assert calls == [{"skip_locked": True}]


def test_reconciler_advances_frozen_windows_then_starts_new_cycles(tmp_path) -> None:
    cleanup = importlib.import_module("support_attachment_cleanup_service")
    now = _utcnow()
    engine, sessions = _session_factory(tmp_path)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    present_names = ("20260714-file0001.txt", "20260714-file0002.txt")
    orphan_names = ("20260714-orphan01.txt", "20260714-orphan02.txt")
    for name in (*present_names, *orphan_names):
        path = upload_dir / name
        path.write_bytes(name.encode("ascii"))
        _age(path, now - timedelta(hours=2))

    session = sessions()
    try:
        session.add_all(
            [
                _attachment(stored_name=name, now=now, expires_at=None)
                for name in present_names
            ]
            + [
                _attachment(stored_name=name, now=now, expires_at=None)
                for name in ("20260714-missing01.txt", "20260714-missing02.txt")
            ]
        )
        session.commit()
    finally:
        session.close()

    cursor = cleanup.SupportAttachmentCleanupCursor()
    reports = []
    try:
        for _ in range(3):
            reports.append(
                cleanup.reconcile_support_attachments(
                    sessions,
                    upload_dir=upload_dir,
                    now=now,
                    grace_seconds=3600,
                    batch_size=10,
                    scan_limit=2,
                    cursor=cursor,
                )
            )
    finally:
        engine.dispose()

    assert reports[0]["orphan_files_removed"] == 0
    assert reports[0]["rows_missing_files"] == 0
    assert reports[1]["orphan_files_removed"] == 2
    assert reports[1]["rows_missing_files"] == 2
    assert reports[2]["orphan_files_removed"] == 0
    assert reports[2]["rows_missing_files"] == 0
    assert [report["file_window_wrapped"] for report in reports] == [0, 0, 1]
    assert [report["row_window_wrapped"] for report in reports] == [0, 1, 0]
    assert [report["file_candidates_selected"] for report in reports] == [2, 2, 0]
    assert all(report["rows_scanned"] == 2 for report in reports)
    assert all(isinstance(value, int) for report in reports for value in report.values())
    assert all((upload_dir / name).exists() for name in present_names)
    assert all(not (upload_dir / name).exists() for name in orphan_names)


def test_reconciler_frozen_cycles_finish_under_sustained_growth_and_revisit_changes(tmp_path) -> None:
    from models import SupportAttachment

    cleanup = importlib.import_module("support_attachment_cleanup_service")
    now = _utcnow()
    engine, sessions = _session_factory(tmp_path)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    initial_names = tuple(f"20260714-m{index:07d}.txt" for index in range(1, 6))
    for name in initial_names:
        path = upload_dir / name
        path.write_bytes(name.encode("ascii"))
        _age(path, now - timedelta(hours=2))

    session = sessions()
    try:
        session.add_all(
            [_attachment(stored_name=name, now=now, expires_at=None) for name in initial_names]
        )
        session.commit()
    finally:
        session.close()

    cursor = cleanup.SupportAttachmentCleanupCursor()
    first = cleanup.reconcile_support_attachments(
        sessions,
        upload_dir=upload_dir,
        now=now,
        grace_seconds=3600,
        batch_size=10,
        scan_limit=2,
        cursor=cursor,
    )
    assert first["file_window_wrapped"] == 0
    assert first["row_window_wrapped"] == 0
    assert cursor.file_cycle_cutoff_ns > 0
    assert cursor.row_cycle_high_water_id > 0

    session = sessions()
    try:
        session.query(SupportAttachment).filter_by(stored_name=initial_names[0]).delete()
        session.commit()
    finally:
        session.close()
    (upload_dir / initial_names[1]).unlink()

    reports = [first]
    frozen_cutoff = cursor.file_cycle_cutoff_ns
    frozen_high_water = cursor.row_cycle_high_water_id
    for run_index in range(1, 4):
        for offset in range(3):
            sequence = run_index * 3 + offset
            name = f"20260714-z{sequence:07d}.txt"
            path = upload_dir / name
            path.write_bytes(name.encode("ascii"))
            _set_mtime_ns(path, frozen_cutoff + 1_000_000 + sequence)
            assert path.stat().st_mtime_ns > frozen_cutoff
            session = sessions()
            try:
                session.add(_attachment(stored_name=name, now=now, expires_at=None))
                session.commit()
            finally:
                session.close()

        report = cleanup.reconcile_support_attachments(
            sessions,
            upload_dir=upload_dir,
            now=now,
            grace_seconds=3600,
            batch_size=10,
            scan_limit=2,
            cursor=cursor,
        )
        reports.append(report)
        if run_index == 1:
            assert cursor.file_cycle_cutoff_ns == frozen_cutoff
            assert cursor.row_cycle_high_water_id == frozen_high_water
        elif run_index == 2:
            assert report["file_window_wrapped"] == 1
            assert report["row_window_wrapped"] == 1
            assert cursor.file_cycle_cutoff_ns == 0
            assert cursor.row_cycle_high_water_id == 0

    try:
        assert [report["file_candidates_selected"] for report in reports[:3]] == [2, 2, 1]
        assert [report["rows_scanned"] for report in reports[:3]] == [2, 2, 1]
        assert [report["file_window_wrapped"] for report in reports[:3]] == [0, 0, 1]
        assert [report["row_window_wrapped"] for report in reports[:3]] == [0, 0, 1]
        assert reports[3]["orphan_files_removed"] == 1
        assert reports[3]["rows_missing_files"] == 1
        assert cursor.file_cycle_cutoff_ns > frozen_cutoff
        assert cursor.row_cycle_high_water_id > frozen_high_water
        assert not (upload_dir / initial_names[0]).exists()
        assert all(report["file_candidates_selected"] <= 2 for report in reports)
        assert all(report["rows_scanned"] <= 2 for report in reports)
        assert all(
            report["filesystem_entries_enumerated"] >= report["file_candidates_selected"]
            for report in reports
        )
        assert all(isinstance(value, int) for report in reports for value in report.values())
    finally:
        engine.dispose()


def test_reconciler_wraps_empty_and_deleted_snapshot_gaps(tmp_path) -> None:
    from models import SupportAttachment

    cleanup = importlib.import_module("support_attachment_cleanup_service")
    now = _utcnow()
    engine, sessions = _session_factory(tmp_path)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    cursor = cleanup.SupportAttachmentCleanupCursor()

    empty = cleanup.reconcile_support_attachments(
        sessions,
        upload_dir=upload_dir,
        now=now,
        grace_seconds=3600,
        batch_size=10,
        scan_limit=1,
        cursor=cursor,
    )
    assert empty["file_window_wrapped"] == 1
    assert empty["row_window_wrapped"] == 1
    assert empty["file_candidates_selected"] == 0
    assert empty["rows_scanned"] == 0
    assert cursor.file_cycle_cutoff_ns == 0
    assert cursor.row_cycle_high_water_id == 0

    names = tuple(f"20260714-gap{index:05d}.txt" for index in range(1, 4))
    for name in names:
        path = upload_dir / name
        path.write_bytes(name.encode("ascii"))
        _age(path, now - timedelta(hours=2))
    session = sessions()
    try:
        session.add_all([_attachment(stored_name=name, now=now, expires_at=None) for name in names])
        session.commit()
    finally:
        session.close()

    started = cleanup.reconcile_support_attachments(
        sessions,
        upload_dir=upload_dir,
        now=now,
        grace_seconds=3600,
        batch_size=10,
        scan_limit=1,
        cursor=cursor,
    )
    assert started["file_window_wrapped"] == 0
    assert started["row_window_wrapped"] == 0

    for name in names[1:]:
        (upload_dir / name).unlink()
    session = sessions()
    try:
        session.query(SupportAttachment).filter(SupportAttachment.stored_name.in_(names[1:])).delete(
            synchronize_session=False
        )
        session.commit()
    finally:
        session.close()

    gap = cleanup.reconcile_support_attachments(
        sessions,
        upload_dir=upload_dir,
        now=now,
        grace_seconds=3600,
        batch_size=10,
        scan_limit=1,
        cursor=cursor,
    )
    try:
        assert gap["file_window_wrapped"] == 1
        assert gap["row_window_wrapped"] == 1
        assert gap["file_candidates_selected"] == 0
        assert gap["rows_scanned"] == 0
        assert cursor.file_after == ""
        assert cursor.file_cycle_cutoff_ns == 0
        assert cursor.row_after_id == 0
        assert cursor.row_cycle_high_water_id == 0
    finally:
        engine.dispose()
