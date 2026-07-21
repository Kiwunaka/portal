from __future__ import annotations

import dataclasses
import importlib.util
import json
import os
import re
import stat
import sys
from pathlib import Path
from types import ModuleType

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_script() -> ModuleType:
    path = REPO_ROOT / "scripts" / "remote_postgres_backup_restore_gate.py"
    scripts_path = str(path.parent)
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)
    spec = importlib.util.spec_from_file_location("remote_postgres_backup_restore_gate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_database_guards_require_exact_confirmations_and_rehearsal_target() -> None:
    module = _load_script()

    assert module.validate_database_selection("portal", "portal", "portal_rehearsal", "portal_rehearsal") == (
        "portal",
        "portal_rehearsal",
    )

    invalid_cases = [
        ("another_prod", "another_prod", "portal_rehearsal", "portal_rehearsal"),
        ("portal-prod", "portal-prod", "portal_rehearsal", "portal_rehearsal"),
        ("portal", "wrong", "portal_rehearsal", "portal_rehearsal"),
        ("portal", "portal", "portal_copy", "portal_copy"),
        ("portal", "portal", "portal_rehearsal", "wrong"),
        ("portal_rehearsal", "portal_rehearsal", "portal_rehearsal", "portal_rehearsal"),
    ]
    for values in invalid_cases:
        with pytest.raises(module.GateError):
            module.validate_database_selection(*values)


def test_backup_location_is_allowlisted_and_basename_is_unique() -> None:
    module = _load_script()

    assert module.validate_backup_directory("/root/backups/postgres-rehearsals") == (
        "/root/backups/postgres-rehearsals"
    )
    for unsafe in ("/root/backups", "/root/backups/../tmp", "/tmp/backups", "/root/backups/a b"):
        with pytest.raises(module.GateError):
            module.validate_backup_directory(unsafe)

    first = module.make_backup_basename("portal", timestamp="20260715T120000Z", nonce="a1b2c3d4")
    second = module.make_backup_basename("portal", timestamp="20260715T120000Z", nonce="deadbeef")
    assert first == "portal-20260715T120000Z-a1b2c3d4.dump.enc"
    assert second != first
    assert "/" not in first


def test_backup_retention_is_bounded_and_preserves_the_current_archive() -> None:
    module = _load_script()
    backup_path = "/root/backups/postgres-rehearsals/portal-20260721T140028Z-4171d4bffad4.dump.enc"

    command = module.build_backup_retention_command(backup_path, retain_count=3)

    assert "# gate_backup_retention" in command
    assert "set -Eeuo pipefail" in command
    assert "head -n -3" in command
    assert 'test "$candidate" = "$current" && continue' in command
    assert 'rm -f -- "$candidate"' in command
    assert "portal\\-[0-9]{8}T[0-9]{6}Z" in command
    with pytest.raises(module.GateError):
        module.build_backup_retention_command(backup_path, retain_count=0)


def test_backup_command_encrypts_stream_and_cleans_partial_without_secret() -> None:
    module = _load_script()
    secret = "correct horse battery staple"
    backup_path = "/root/backups/postgres-rehearsals/portal-20260715T120000Z-a1b2c3d4.dump.enc"

    snapshot_id = "00000003-0000001B-1"
    command = module.build_backup_command(
        "portal", backup_path, snapshot_id=snapshot_id, server_timeout=123
    )

    assert secret not in command
    assert "pg_dump" in command and "--format=custom" in command
    assert f"--snapshot={snapshot_id}" in command
    assert "timeout --signal=TERM --kill-after=10s 123s" in command
    assert "gate_encrypted_pipeline_supervisor" in command
    assert "setsid --wait timeout --signal=TERM --kill-after=10s 123s" in command
    assert '"$passphrase_fd" 3<&-' in command
    assert "exec 3<&0 0</dev/null" in command
    assert command.index("pg_dump") < command.index("openssl enc")
    assert command.index("timeout --signal=TERM") < command.index("pg_dump")
    assert "--lock-wait-timeout=10s" in command
    assert "nice -n 10" in command and "ionice -c 2 -n 7" in command
    assert "openssl enc -aes-256-cbc" in command and "-pbkdf2" in command
    assert f"{backup_path}.partial" in command
    assert "trap cleanup" in command and 'rm -f -- "$partial"' in command
    assert "install -d -m 0700" in command and "chmod 0600" in command
    assert "sync -f" in command
    assert "mv --no-clobber" in command
    assert 'test ! -e "$partial"' in command
    assert "pg_dump" in command and "3<&- </dev/null" in command
    assert '-pass file:"$1"' in command
    assert "passphrase_fd=/proc/$$/fd/3" in command
    assert "sync -f \"$backup_dir\"" in command
    assert ".dump'" not in command


def test_verify_restore_and_evidence_commands_are_bounded_and_redacted() -> None:
    module = _load_script()
    backup_path = "/root/backups/postgres-rehearsals/portal-20260715T120000Z-a1b2c3d4.dump.enc"

    verify = module.build_verify_command(backup_path, server_timeout=234)
    restore = module.build_restore_command(
        "portal_rehearsal",
        backup_path,
        source="portal",
        server_timeout=345,
    )
    snapshot_id = "00000003-0000001B-1"
    evidence = module.build_integrity_evidence_command(
        "portal_rehearsal", snapshot_id=snapshot_id, server_timeout=120
    )

    assert "openssl enc -d -aes-256-cbc" in verify
    assert "pg_restore --list 3<&-" in verify
    assert "timeout --signal=TERM --kill-after=10s 234s" in verify
    assert "gate_encrypted_pipeline_supervisor" in verify
    assert verify.index("timeout --signal=TERM") < verify.index("openssl enc") < verify.index("pg_restore")
    assert not re.search(r"pg_restore\s+--list\s+-\s", verify)
    assert "--exit-on-error" in restore
    assert "--no-owner" in restore and "--no-privileges" in restore
    assert '--role="$role"' in restore
    assert "/root/portal_bot/.env" in restore
    assert "dotenv_values" in restore and "make_url" in restore
    assert "rolcanlogin" in restore and "NOT rolsuper" in restore
    assert "datdba" in restore and "pg_roles" in restore
    assert "--command=" not in restore
    assert "printf " in restore
    assert "portal_rehearsal" in restore
    assert "timeout --signal=TERM --kill-after=10s 345s" in restore
    assert "gate_encrypted_pipeline_supervisor" in restore
    assert "--dbname=portal_rehearsal 3<&-" in restore
    assert not re.search(r"--dbname=portal_rehearsal\s+-\s", restore)
    assert '-pass file:"$1"' in verify and '"$passphrase_fd" 3<&-' in verify
    assert '-pass file:"$1"' in restore and '"$passphrase_fd" 3<&-' in restore
    assert "exec 3<&0 0</dev/null" in verify and "exec 3<&0 0</dev/null" in restore
    assert "count(*)" in evidence.lower()
    assert f"SET TRANSACTION SNAPSHOT '{snapshot_id}'" in evidence
    assert "timeout --signal=TERM --kill-after=10s 120s" in evidence
    assert "statement_timeout" in evidence and "lock_timeout" in evidence
    assert "nice -n 10" in evidence and "ionice -c 2 -n 7" in evidence
    assert "pg_database_size" in evidence
    assert "support_attachments" in evidence
    assert all(term in evidence for term in ("bound", "unbound", "dangling"))
    assert "m.ticket_id = a.ticket_id" in evidence
    assert "stored_name" not in evidence
    assert "original_name" not in evidence

    create = module._create_target_command("portal_rehearsal", source="portal")
    assert 'createdb --owner="$role" -- portal_rehearsal' in create
    assert "REVOKE ALL ON DATABASE portal_rehearsal FROM PUBLIC" in create
    assert "REVOKE ALL ON SCHEMA public FROM PUBLIC" in create
    assert 'ALTER SCHEMA public OWNER TO :"role_name"' in create
    assert 'GRANT USAGE, CREATE ON SCHEMA public TO :"role_name"' in create
    assert "/root/portal_bot/.env" in create
    assert "rolcanlogin" in create and "NOT rolsuper" in create
    assert "--command=" not in create
    assert "printf '%s\\n'" in create

    role_evidence = module.build_target_role_evidence_command(
        "portal",
        "portal_rehearsal",
    )
    assert "gate_target_role_evidence" in role_evidence
    assert "database_owner_is_app" in role_evidence
    assert "public_schema_create" in role_evidence
    assert "public_objects_total" in role_evidence
    assert "public_objects_owned" in role_evidence
    assert "database_public_access_revoked" in role_evidence
    assert "schema_public_access_revoked" in role_evidence
    assert "DATABASE_URL" in role_evidence
    assert "postgresql://" not in role_evidence
    assert "--command=" not in role_evidence
    assert "printf '%s\\n'" in role_evidence
    for catalog in (
        "pg_namespace",
        "pg_class",
        "pg_proc",
        "pg_type",
        "pg_extension",
        "pg_collation",
        "pg_conversion",
        "pg_operator",
        "pg_opclass",
        "pg_opfamily",
        "pg_ts_dict",
        "pg_ts_config",
        "pg_statistic_ext",
        "pg_default_acl",
    ):
        assert catalog in role_evidence
    cleanup = module._partial_cleanup_command(backup_path)
    for piped_command in (
        module.build_backup_command(
            "portal", backup_path, snapshot_id=snapshot_id, server_timeout=123
        ),
        verify,
        restore,
        cleanup,
    ):
        assert "set -Eeuo pipefail" in piped_command
    assert "sync -f /root/backups/postgres-rehearsals" in cleanup
    assert "if test -d /root/backups/postgres-rehearsals; then" in cleanup
    assert cleanup.index("rm -f --") < cleanup.index("if test -d") < cleanup.index("test ! -e")


def test_source_evidence_is_read_only_from_the_first_database_statement() -> None:
    module = _load_script()
    snapshot_id = "00000003-0000001B-1"

    command = module.build_integrity_evidence_command(
        "portal", snapshot_id=snapshot_id, server_timeout=120
    )

    begin = command.index("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;")
    snapshot = command.index(f"SET TRANSACTION SNAPSHOT '{snapshot_id}';")
    assert begin < snapshot
    transaction_body = command.split(
        "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;\n", 1
    )[1]
    assert transaction_body.startswith(f"SET TRANSACTION SNAPSHOT '{snapshot_id}';\n")
    assert "\\gexec" in transaction_body
    assert "record_type" in transaction_body
    for mutating_sql in ("CREATE ", "ALTER ", "DROP ", "INSERT ", "UPDATE ", "DELETE ", "DO $"):
        assert mutating_sql not in command.upper()


def test_integrity_stream_parser_rebuilds_aggregate_without_source_storage() -> None:
    module = _load_script()
    raw = "\n".join(
        json.dumps(record, separators=(",", ":"))
        for record in (
            {
                "record_type": "database",
                "database_bytes": 8192,
                "public_table_count": 2,
            },
            {"record_type": "table", "name": "access_keys", "row_count": 3},
            {"record_type": "table", "name": "users", "row_count": 2},
            {
                "record_type": "support",
                "schema_status": "absent",
                "total": 0,
            },
        )
    )

    evidence = module._validate_integrity_evidence(
        module._parse_integrity_evidence_stream(raw, "source_integrity")
    )

    assert evidence == {
        "database_bytes": 8192,
        "public_table_count": 2,
        "tables": [
            {"name": "access_keys", "row_count": 3},
            {"name": "users", "row_count": 2},
        ],
        "support_attachments": {"schema_status": "absent", "total": 0},
    }

    duplicate_database = raw + "\n" + json.dumps(
        {"record_type": "database", "database_bytes": 8192, "public_table_count": 2}
    )
    with pytest.raises(module.GateError):
        module._parse_integrity_evidence_stream(duplicate_database, "source_integrity")


def test_support_evidence_is_structured_and_never_null() -> None:
    module = _load_script()
    base = {
        "database_bytes": 8192,
        "public_table_count": 1,
        "tables": [{"name": "users", "row_count": 2}],
    }

    available = module._validate_integrity_evidence(
        {
            **base,
            "support_attachments": {
                "schema_status": "available",
                "total": 7,
                "bound": 4,
                "unbound": 2,
                "dangling": 1,
            },
        }
    )
    legacy = module._validate_integrity_evidence(
        {**base, "support_attachments": {"schema_status": "legacy", "total": 7}}
    )
    absent = module._validate_integrity_evidence(
        {**base, "support_attachments": {"schema_status": "absent", "total": 0}}
    )

    clean_available = {
        **available,
        "support_attachments": {
            "schema_status": "available",
            "total": 6,
            "bound": 4,
            "unbound": 2,
            "dangling": 0,
        },
    }
    assert module._support_ownership_status(available) == "FAIL_DANGLING_ATTACHMENTS"
    assert module._support_ownership_status(clean_available) == "PASS"
    assert module._support_ownership_status(legacy) == "LEGACY_SCHEMA_NOT_GATED"
    assert module._support_ownership_status(absent) == "NOT_APPLICABLE_ABSENT"
    for invalid_support in (
        None,
        {"schema_status": "absent", "total": 1},
        {"schema_status": "legacy"},
        {"schema_status": "available", "total": 1, "bound": 1, "unbound": 0},
        {"schema_status": "available", "total": 2, "bound": 1, "unbound": 0, "dangling": 0},
    ):
        with pytest.raises(module.GateError):
            module._validate_integrity_evidence({**base, "support_attachments": invalid_support})


def test_report_validation_rejects_sensitive_keys_values_and_git_worktrees(tmp_path: Path) -> None:
    module = _load_script()

    module.assert_report_safe({"status": "PASS", "tables": [{"name": "users", "row_count": 3}]})
    with pytest.raises(module.GateError):
        module.assert_report_safe({"password": "anything"})
    with pytest.raises(module.GateError):
        module.assert_report_safe({"detail": "postgresql://user:pass@host/db"})
    with pytest.raises(module.GateError):
        module.assert_report_safe({"detail": "token=abc123"})
    with pytest.raises(module.GateError):
        module.assert_report_safe({"detail": "sk_live_1234567890abcdefghijklmnop"})

    worktree = tmp_path / "repo"
    worktree.mkdir()
    (worktree / ".git").write_text("gitdir: elsewhere", encoding="utf-8")
    with pytest.raises(module.GateError):
        module.validate_report_path(worktree / "evidence.json")


def test_atomic_report_uses_mode_0600_and_refuses_overwrite(monkeypatch, tmp_path: Path) -> None:
    module = _load_script()
    report_path = tmp_path / "evidence.json"
    report = {"status": "PLAN_ONLY", "source_database": "portal", "target_database": "portal_rehearsal"}
    open_calls: list[tuple[int, int]] = []
    real_open = os.open

    def recording_open(path, flags, mode=0o777):
        open_calls.append((flags, mode))
        return real_open(path, flags, mode)

    monkeypatch.setattr(module.os, "open", recording_open)

    module.write_report_atomic(report_path, report)

    assert json.loads(report_path.read_text(encoding="utf-8")) == report
    if os.name == "nt":
        assert module._windows_file_dacl_sddl(report_path).startswith("D:P")
    else:
        assert any(flags & os.O_EXCL and stat.S_IMODE(mode) == 0o600 for flags, mode in open_calls)
    assert not list(tmp_path.glob(".*.tmp"))
    with pytest.raises(module.GateError):
        module.write_report_atomic(report_path, report)


def test_atomic_report_publication_does_not_overwrite_racing_target(monkeypatch, tmp_path: Path) -> None:
    module = _load_script()
    report_path = tmp_path / "evidence.json"
    existing = '{"existing":true}\n'
    real_link = os.link

    def racing_link(source, target):
        Path(target).write_text(existing, encoding="utf-8")
        return real_link(source, target)

    monkeypatch.setattr(module.os, "link", racing_link)

    with pytest.raises(module.GateError):
        module.write_report_atomic(report_path, {"status": "PASS"})

    assert report_path.read_text(encoding="utf-8") == existing
    assert not list(tmp_path.glob(".*.tmp"))


@pytest.mark.skipif(os.name != "nt", reason="NTFS DACL contract is Windows-specific")
def test_windows_report_dacl_is_protected_and_current_user_only(tmp_path: Path) -> None:
    module = _load_script()
    report_path = tmp_path / "evidence.json"

    module.write_report_atomic(report_path, {"status": "PLAN_ONLY"})

    sid = module._windows_current_user_sid()
    sddl = module._windows_file_dacl_sddl(report_path)
    assert sddl.startswith("D:P")
    assert sid in sddl
    assert sddl.count("(A;") == 1


def test_failure_report_oserror_does_not_replace_original_generic_error(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_script()
    report_path = tmp_path / "failure.json"
    monkeypatch.setenv("NODE_PASS_BRAIN", "ssh-secret")
    monkeypatch.setenv("POKROV_POSTGRES_BACKUP_PASSPHRASE", "backup-secret")
    monkeypatch.setattr(
        module,
        "_apply_gate",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(module.remote_error("backup")),
    )
    monkeypatch.setattr(
        module,
        "write_report_atomic",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("fsync/unlink denied")),
    )

    with pytest.raises(SystemExit) as exc:
        module.main(_apply_argv(report_path))

    assert str(exc.value) == "remote_backup_failed"


def test_password_parser_skips_public_key_lines(tmp_path: Path) -> None:
    module = _load_script()
    password_file = tmp_path / "PASSWORDS.txt"
    password_file.write_text(
        "BRAINnode\n"
        "ssh-ed25519 AAAATEST comment\n"
        "ssh-rsa AAAATEST comment\n"
        "-----BEGIN PUBLIC KEY-----\n"
        "AAAATESTPUBLICKEYBODY\n"
        "-----END PUBLIC KEY-----\n"
        "operator-password\n",
        encoding="utf-8",
    )

    assert module._parse_password(password_file) == "operator-password"


def test_remote_error_mapping_never_returns_remote_stderr() -> None:
    module = _load_script()
    raw = "password=hunter2 postgresql://operator:secret@brain/portal"

    error = module.remote_error("backup", RuntimeError(raw))

    assert str(error) == "remote_backup_failed"
    assert raw not in repr(error)
    assert "hunter2" not in repr(error)


class _RunInput:
    def __init__(self) -> None:
        self.values: list[str] = []

    def write(self, value: str) -> None:
        self.values.append(value)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


class _DrainChannel:
    def __init__(
        self,
        *,
        stdout: bytes = b"",
        stderr: bytes = b"",
        code: int = 0,
        finishes: bool = True,
    ) -> None:
        self.stdout = bytearray(stdout)
        self.stderr = bytearray(stderr)
        self.code = code
        self.finishes = finishes
        self.closed = False
        self.status_received = False

    def recv_ready(self) -> bool:
        return bool(self.stdout)

    def recv(self, size: int) -> bytes:
        chunk = bytes(self.stdout[:size])
        del self.stdout[:size]
        return chunk

    def recv_stderr_ready(self) -> bool:
        return bool(self.stderr)

    def recv_stderr(self, size: int) -> bytes:
        chunk = bytes(self.stderr[:size])
        del self.stderr[:size]
        return chunk

    def exit_status_ready(self) -> bool:
        return self.finishes

    def recv_exit_status(self) -> int:
        assert not self.stdout and not self.stderr, "status requested before concurrent drain"
        self.status_received = True
        return self.code

    def close(self) -> None:
        self.closed = True
        self.finishes = True


class _ChannelStream:
    def __init__(self, channel: _DrainChannel) -> None:
        self.channel = channel


class _ChannelSSH:
    def __init__(self, channel: _DrainChannel) -> None:
        self.channel = channel
        self.stdin = _RunInput()

    def exec_command(self, _command: str, timeout: int):
        return self.stdin, _ChannelStream(self.channel), _ChannelStream(self.channel)


def test_remote_run_drains_stdout_and_stderr_before_exit_status() -> None:
    module = _load_script()
    channel = _DrainChannel(stdout=b"safe-output", stderr=b"raw-password=never-print")

    output = module._remote_run(_ChannelSSH(channel), "probe", error_class="probe", timeout=1)

    assert output == "safe-output"
    assert channel.status_received is True


def test_remote_run_hard_timeout_closes_channel() -> None:
    module = _load_script()
    channel = _DrainChannel(finishes=False)

    with pytest.raises(module.RemoteGateError) as exc:
        module._remote_run(_ChannelSSH(channel), "probe", error_class="probe", timeout=0.01)

    assert str(exc.value) == "remote_probe_timeout_failed"
    assert channel.closed is True


def test_remote_run_closes_channel_on_bounded_output_overflow() -> None:
    module = _load_script()
    channel = _DrainChannel(stdout=b"123456789")

    with pytest.raises(module.RemoteGateError) as exc:
        module._remote_run(
            _ChannelSSH(channel),
            "probe",
            error_class="probe",
            timeout=1,
            max_output_bytes=8,
        )

    assert str(exc.value) == "remote_probe_output_failed"
    assert channel.closed is True


class _InterlockedChannel(_DrainChannel):
    def __init__(self) -> None:
        super().__init__(stdout=b"A", stderr=b"E")
        self.stderr_was_read = False

    def recv_ready(self) -> bool:
        return bool(self.stdout) or not self.stderr_was_read

    def recv(self, size: int) -> bytes:
        if self.stdout:
            return super().recv(size)
        return b"X"

    def recv_stderr(self, size: int) -> bytes:
        self.stderr_was_read = True
        return super().recv_stderr(size)


def test_remote_run_fairly_drains_stderr_while_stdout_stays_ready() -> None:
    module = _load_script()
    channel = _InterlockedChannel()

    output = module._remote_run(
        _ChannelSSH(channel),
        "probe",
        error_class="probe",
        timeout=1,
        max_output_bytes=16,
    )

    assert output.startswith("A")
    assert channel.stderr_was_read is True


class _SnapshotInput(_RunInput):
    def __init__(
        self,
        channel: _DrainChannel,
        *,
        emit_snapshot: bool = True,
        identity_nonce: str = "a" * 64,
    ) -> None:
        super().__init__()
        self.channel = channel
        self.emit_snapshot = emit_snapshot
        self.identity_nonce = identity_nonce

    def write(self, value: str) -> None:
        super().write(value)
        if "pg_export_snapshot" in value:
            self.channel.stdout.extend(
                b"POKROV_EXPORTER_NONCE=" + self.identity_nonce.encode("ascii") + b"\n"
                b"POKROV_EXPORTER_PID=4242\n"
                b"POKROV_EXPORTER_PGID=4242\n"
                b"POKROV_EXPORTER_SESSION=4242\n"
                b"POKROV_EXPORTER_STARTTIME=987654\n"
            )
            if self.emit_snapshot:
                self.channel.stdout.extend(b"POKROV_SNAPSHOT=00000003-0000001B-1\n")
        if "\\q" in value:
            self.channel.finishes = True


class _SnapshotSSH:
    def __init__(self) -> None:
        self.channel = _DrainChannel(finishes=False)
        self.stdin = _SnapshotInput(self.channel)
        self.command = ""

    def exec_command(self, command: str, timeout: int):
        self.command = command
        return self.stdin, _ChannelStream(self.channel), _ChannelStream(self.channel)


def test_snapshot_exporter_stays_alive_until_explicit_commit() -> None:
    module = _load_script()
    ssh = _SnapshotSSH()
    identity_nonce = "a" * 64

    exporter = module._open_snapshot_exporter(
        ssh, "portal", timeout=1, identity_nonce=identity_nonce
    )

    assert exporter.snapshot_id == "00000003-0000001B-1"
    assert exporter.identity_nonce == identity_nonce
    assert exporter.process_id == 4242
    assert exporter.process_group_id == 4242
    assert exporter.session_id == 4242
    assert exporter.start_time == 987654
    assert exporter.active is True
    assert ssh.channel.exit_status_ready() is False
    assert "setsid --wait" in ssh.command
    assert identity_nonce in ssh.command
    assert "nice -n 10" in ssh.command and "ionice -c 2 -n 7" in ssh.command
    preflight = module._tools_preflight_command()
    assert "setsid --wait sh -c 'exit 0'" in preflight
    assert "pidfd_open" in preflight and "pidfd_send_signal" in preflight
    module._close_snapshot_exporter(exporter, commit=True, timeout=1)
    assert "COMMIT;" in "".join(ssh.stdin.values)
    assert "ROLLBACK;" not in "".join(ssh.stdin.values)
    assert exporter.active is False


def test_exporter_identity_mismatch_and_starttime_mismatch_have_no_signal_plan() -> None:
    module = _load_script()
    expected = module.ExporterIdentity(
        identity_nonce="a" * 64,
        process_id=4242,
        process_group_id=4242,
        session_id=4242,
        start_time=987654,
    )
    matching = module.ObservedProcessIdentity(
        process_id=4242,
        process_group_id=4242,
        session_id=4242,
        start_time=987654,
        command_arguments=("timeout", "pokrov-exporter-" + "a" * 64),
    )
    reused = dataclasses.replace(matching, command_arguments=("timeout", "unrelated-root-job"))
    restarted = dataclasses.replace(matching, start_time=987655)

    assert module._cleanup_signal_plan(expected, matching) == ("TERM", "KILL")
    assert module._cleanup_signal_plan(expected, reused) == ()
    assert module._cleanup_signal_plan(expected, restarted) == ()

    command = module._snapshot_force_cleanup_command(expected)
    assert command.count("verify_identity()") >= 2
    assert command.count("members = verify_identity()") == 1
    assert command.count("signal_verified(") == 2
    assert command.index("verify_identity()") < command.index("signal.SIGTERM")
    assert command.rindex("signal_pinned(") < command.index("signal.SIGKILL")
    assert "/proc/{pid}/stat" in command and "/proc/{pid}/cmdline" in command
    assert "pidfd_open" in command and "pidfd_send_signal" in command
    assert "kill -TERM" not in command and "kill -KILL" not in command
    assert "987654" in command and "pokrov-exporter-" + "a" * 64 in command
    helper = command.split("<<'POKROV_SNAPSHOT_CLEANUP'\n", 1)[1].rsplit(
        "POKROV_SNAPSHOT_CLEANUP", 1
    )[0]
    compile(helper, "<snapshot-cleanup-helper>", "exec")


def test_open_snapshot_failure_after_identity_forces_verified_cleanup() -> None:
    module = _load_script()

    class PartialIdentitySSH(_SnapshotSSH):
        def __init__(self) -> None:
            super().__init__()
            self.stdin = _SnapshotInput(self.channel, emit_snapshot=False)
            self.commands: list[str] = []

        def exec_command(self, command: str, timeout: int):
            self.commands.append(command)
            if "gate_snapshot_exporter" in command:
                self.channel.finishes = True
                return self.stdin, _ChannelStream(self.channel), _ChannelStream(self.channel)
            channel = _DrainChannel()
            return _RunInput(), _ChannelStream(channel), _ChannelStream(channel)

    ssh = PartialIdentitySSH()
    state = module.RunState(backup_path="/root/backups/postgres-rehearsals/test.dump.enc")

    with pytest.raises(module.GateError):
        module._open_snapshot_exporter(
            ssh,
            "portal",
            timeout=1,
            identity_nonce="a" * 64,
            state=state,
        )

    cleanup = next(command for command in ssh.commands if "gate_snapshot_force_cleanup" in command)
    assert "verify_identity()" in cleanup and "pidfd_send_signal" in cleanup
    assert state.snapshot_cleanup_outcome == "open_failed_force_killed"


def test_plan_mode_writes_sanitized_report_without_ssh_or_secrets(monkeypatch, tmp_path: Path, capsys) -> None:
    module = _load_script()
    report_path = tmp_path / "plan.json"
    monkeypatch.setenv("NODE_PASS_BRAIN", "ssh-super-secret")
    monkeypatch.setenv("POKROV_POSTGRES_BACKUP_PASSPHRASE", "backup-super-secret")
    monkeypatch.setattr(module.paramiko, "SSHClient", lambda: pytest.fail("plan mode must not create SSH client"))

    code = module.main(
        [
            "--brain-ip",
            "82.21.114.104",
            "--source-db",
            "portal",
            "--confirm-source",
            "portal",
            "--target-db",
            "portal_rehearsal",
            "--confirm-target",
            "portal_rehearsal",
            "--report",
            str(report_path),
        ]
    )

    output = capsys.readouterr().out
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert code == 0
    assert report["status"] == "PLAN_ONLY"
    assert report["mode"] == "plan"
    assert report["backup_restore_status"] == "NOT_RUN"
    assert report["support_ownership_status"] == "NOT_EVALUATED"
    assert "ssh-super-secret" not in output + report_path.read_text(encoding="utf-8")
    assert "backup-super-secret" not in output + report_path.read_text(encoding="utf-8")


def test_apply_requires_passphrase_from_named_environment_before_ssh(monkeypatch, tmp_path: Path) -> None:
    module = _load_script()
    monkeypatch.delenv("POKROV_POSTGRES_BACKUP_PASSPHRASE", raising=False)
    monkeypatch.setenv("NODE_PASS_BRAIN", "ssh-secret")
    monkeypatch.setattr(module.paramiko, "SSHClient", lambda: pytest.fail("missing passphrase must fail before SSH"))

    with pytest.raises(SystemExit) as exc:
        module.main(
            [
                "--brain-ip",
                "82.21.114.104",
                "--source-db",
                "portal",
                "--confirm-source",
                "portal",
                "--target-db",
                "portal_rehearsal",
                "--confirm-target",
                "portal_rehearsal",
                "--report",
                str(tmp_path / "apply.json"),
                "--apply",
            ]
        )

    assert str(exc.value) == "Missing passphrase environment variable: POKROV_POSTGRES_BACKUP_PASSPHRASE"


def test_parser_never_echoes_an_argv_passphrase(capsys, tmp_path: Path) -> None:
    module = _load_script()

    with pytest.raises(SystemExit):
        module.main(
            [
                "--brain-ip",
                "82.21.114.104",
                "--source-db",
                "portal",
                "--confirm-source",
                "portal",
                "--target-db",
                "portal_rehearsal",
                "--confirm-target",
                "portal_rehearsal",
                "--report",
                str(tmp_path / "plan.json"),
                "--passphrase",
                "argv-super-secret",
            ]
        )

    captured = capsys.readouterr()
    assert "argv-super-secret" not in captured.out + captured.err


class _FakeSSH:
    def __init__(
        self,
        *,
        target_exists: bool = False,
        fail_marker: str = "",
        mismatch_target: bool = False,
        partial_cleanup_fails: bool = False,
        support_schema_status: str = "available",
        snapshot_close_fails: bool = False,
    ) -> None:
        self.commands: list[str] = []
        self.inputs: list[_RunInput] = []
        self.connect_kwargs: dict[str, object] = {}
        self.closed = False
        self.target_exists = target_exists
        self.fail_marker = fail_marker
        self.mismatch_target = mismatch_target
        self.partial_cleanup_fails = partial_cleanup_fails
        self.support_schema_status = support_schema_status
        self.snapshot_close_fails = snapshot_close_fails
        self.snapshot_channel: _DrainChannel | None = None
        self.snapshot_input: _SnapshotInput | None = None
        self.snapshot_alive_during_backup = False
        self.backup_created = False
        self.backup_directory_exists = False

    def connect(self, hostname: str, **kwargs) -> None:
        self.connect_kwargs = {"hostname": hostname, **kwargs}

    def exec_command(self, command: str, timeout: int):
        self.commands.append(command)
        if "gate_snapshot_exporter" in command:
            channel = _DrainChannel(finishes=False)
            if self.snapshot_close_fails:
                channel.code = 1
            nonce_match = re.search(r"pokrov-exporter-([a-f0-9]{64})", command)
            assert nonce_match is not None
            stdin = _SnapshotInput(channel, identity_nonce=nonce_match.group(1))
            self.snapshot_channel = channel
            self.snapshot_input = stdin
            self.inputs.append(stdin)
            return stdin, _ChannelStream(channel), _ChannelStream(channel)

        stdin = _RunInput()
        self.inputs.append(stdin)
        code = 0
        if self.fail_marker and self.fail_marker in command:
            code = 1
        if self.partial_cleanup_fails and "gate_partial_cleanup" in command:
            code = 1
        if "gate_encrypted_backup" in command:
            self.backup_directory_exists = True
        if (
            "gate_partial_cleanup" in command
            and not self.backup_directory_exists
            and "if test -d" not in command
        ):
            code = 1
        if "gate_source_exists" in command:
            out = "1\n"
        elif "gate_target_exists" in command:
            out = "1\n" if self.target_exists else "0\n"
        elif "gate_backup_metadata" in command:
            if self.backup_created:
                out = json.dumps({"bytes": 4096, "sha256": "a" * 64, "mode": "600"})
            else:
                code = 1
                out = ""
        elif "gate_target_role_evidence" in command:
            out = json.dumps(
                {
                    "database_owner_is_app": True,
                    "database_public_access_revoked": True,
                    "public_schema_create": True,
                    "public_objects_total": 62,
                    "public_objects_owned": 62,
                    "schema_public_access_revoked": True,
                }
            )
        elif "gate_integrity_evidence" in command:
            row_count = 3 if self.mismatch_target and "portal_rehearsal" in command else 2
            if self.support_schema_status == "available":
                support = {
                    "schema_status": "available",
                    "total": 0,
                    "bound": 0,
                    "unbound": 0,
                    "dangling": 0,
                }
            elif self.support_schema_status == "legacy":
                support = {"schema_status": "legacy", "total": 7}
            else:
                support = {"schema_status": "absent", "total": 0}
            out = "\n".join(
                json.dumps(record, separators=(",", ":"))
                for record in (
                    {
                        "record_type": "database",
                        "database_bytes": 8192,
                        "public_table_count": 1,
                    },
                    {
                        "record_type": "table",
                        "name": "users",
                        "row_count": row_count,
                    },
                    {
                        "record_type": "support",
                        **support,
                    },
                )
            )
        else:
            out = ""
        if "gate_encrypted_backup" in command:
            self.snapshot_alive_during_backup = bool(
                self.snapshot_channel
                and not self.snapshot_channel.exit_status_ready()
                and not self.snapshot_channel.closed
            )
            if code == 0:
                self.backup_created = True
        channel = _DrainChannel(
            stdout=out.encode("utf-8"),
            stderr=b"password=remote-raw-secret",
            code=code,
        )
        return stdin, _ChannelStream(channel), _ChannelStream(channel)

    def close(self) -> None:
        self.closed = True


def test_apply_uses_strict_host_keys_and_retains_source_backup_and_target(monkeypatch, tmp_path: Path) -> None:
    module = _load_script()
    report_path = tmp_path / "apply.json"
    fake = _FakeSSH()
    policy_calls: list[dict[str, object]] = []
    monkeypatch.setenv("NODE_PASS_BRAIN", "ssh-secret")
    monkeypatch.setenv("POKROV_POSTGRES_BACKUP_PASSPHRASE", "backup-secret")
    monkeypatch.setattr(module.paramiko, "SSHClient", lambda: fake)
    monkeypatch.setattr(
        module,
        "configure_ssh_host_key_policy",
        lambda client, **kwargs: policy_calls.append(kwargs) or client,
    )

    assert (
        module.main(
            [
                "--brain-ip",
                "82.21.114.104",
                "--source-db",
                "portal",
                "--confirm-source",
                "portal",
                "--target-db",
                "portal_rehearsal",
                "--confirm-target",
                "portal_rehearsal",
                "--report",
                str(report_path),
                "--apply",
                "--backup-timeout",
                "601",
                "--verify-timeout",
                "602",
                "--restore-timeout",
                "603",
                "--evidence-timeout",
                "604",
            ]
        )
        == 0
    )

    report_text = report_path.read_text(encoding="utf-8")
    commands = "\n".join(fake.commands)
    assert policy_calls == [{"allow_trust_on_first_use": False}]
    assert "dropdb portal" not in commands
    assert "rm -f --" in commands and ".partial" in commands
    assert "rm -f --" + " " + report_path.name not in commands
    assert "ssh-secret" not in commands + report_text
    assert "backup-secret" not in commands + report_text
    assert any("backup-secret\n" in "".join(item.values) for item in fake.inputs)
    report = json.loads(report_text)
    assert report["status"] == "PASS"
    assert report["backup_restore_status"] == "PASS"
    assert report["support_ownership_status"] == "PASS"
    assert report["target_role_status"] == "PASS"
    assert report["target_role_evidence"] == {
        "database_owner_is_app": True,
        "database_public_access_revoked": True,
        "public_schema_create": True,
        "public_objects_total": 62,
        "public_objects_owned": 62,
        "schema_public_access_revoked": True,
    }
    assert fake.snapshot_alive_during_backup is True
    snapshot_commands = [command for command in fake.commands if "gate_integrity_evidence" in command or "gate_encrypted_backup" in command]
    assert len(snapshot_commands) >= 2
    assert all("00000003-0000001B-1" in command for command in snapshot_commands[:2])
    marker_timeouts = {
        "gate_encrypted_backup": 601,
        "gate_verify_archive": 602,
        "gate_restore_target": 603,
        "gate_integrity_evidence": 604,
    }
    for marker, timeout_value in marker_timeouts.items():
        command = next(item for item in fake.commands if marker in item)
        assert f"timeout --signal=TERM --kill-after=10s {timeout_value}s" in command
    create_index = next(i for i, command in enumerate(fake.commands) if "gate_create_target" in command)
    restore_index = next(i for i, command in enumerate(fake.commands) if "gate_restore_target" in command)
    role_index = next(i for i, command in enumerate(fake.commands) if "gate_target_role_evidence" in command)
    target_integrity_index = next(
        i
        for i, command in enumerate(fake.commands)
        if i > role_index and "gate_integrity_evidence" in command
    )
    assert create_index < restore_index < role_index < target_integrity_index
    assert fake.snapshot_input is not None
    snapshot_control = "".join(fake.snapshot_input.values)
    assert "COMMIT;" in snapshot_control and "ROLLBACK;" not in snapshot_control
    assert fake.closed is True


def test_legacy_support_schema_does_not_claim_ownership_pass(monkeypatch, tmp_path: Path) -> None:
    module = _load_script()
    report_path = tmp_path / "legacy.json"
    fake = _FakeSSH(support_schema_status="legacy")
    monkeypatch.setenv("NODE_PASS_BRAIN", "ssh-secret")
    monkeypatch.setenv("POKROV_POSTGRES_BACKUP_PASSPHRASE", "backup-secret")
    monkeypatch.setattr(module.paramiko, "SSHClient", lambda: fake)
    monkeypatch.setattr(module, "configure_ssh_host_key_policy", lambda client, **_kwargs: client)

    assert module.main(_apply_argv(report_path)) == 0

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["backup_restore_status"] == "PASS"
    assert report["support_ownership_status"] == "LEGACY_SCHEMA_NOT_GATED"
    assert report["source_integrity"]["support_attachments"] == {
        "schema_status": "legacy",
        "total": 7,
    }


def _apply_argv(report_path: Path, *, reset_target: bool = False) -> list[str]:
    argv = [
        "--brain-ip",
        "82.21.114.104",
        "--source-db",
        "portal",
        "--confirm-source",
        "portal",
        "--target-db",
        "portal_rehearsal",
        "--confirm-target",
        "portal_rehearsal",
        "--report",
        str(report_path),
        "--apply",
    ]
    if reset_target:
        argv.append("--reset-target")
    return argv


@pytest.mark.parametrize(
    ("name", "fake_kwargs", "reset_target", "phase", "backup_retained", "target_state", "cleanup"),
    [
        (
            "backup",
            {"fail_marker": "gate_encrypted_backup"},
            "unknown",
            "backup",
            "unknown",
            "absent_not_created",
            "removed_or_absent",
        ),
        (
            "verify",
            {"fail_marker": "gate_verify_archive"},
            False,
            "backup_verify",
            True,
            "absent_not_created",
            "removed_or_absent",
        ),
        (
            "restore",
            {"fail_marker": "gate_restore_target"},
            False,
            "target_restore",
            True,
            "restore_failed_retained",
            "removed_or_absent",
        ),
        (
            "mismatch",
            {"mismatch_target": True},
            False,
            "integrity_compare",
            True,
            "integrity_mismatch_retained",
            "removed_or_absent",
        ),
        (
            "reset",
            {"target_exists": True, "fail_marker": "gate_reset_target"},
            True,
            "target_reset",
            True,
            "reset_failed_unknown",
            "removed_or_absent",
        ),
        (
            "partial-cleanup",
            {"fail_marker": "gate_encrypted_backup", "partial_cleanup_fails": True},
            False,
            "backup",
            "unknown",
            "absent_not_created",
            "failed",
        ),
    ],
)
def test_failure_injection_reports_exact_run_state(
    monkeypatch,
    tmp_path: Path,
    name: str,
    fake_kwargs: dict[str, object],
    reset_target: bool,
    phase: str,
    backup_retained: bool | str,
    target_state: str,
    cleanup: str,
) -> None:
    module = _load_script()
    report_path = tmp_path / f"{name}.json"
    fake = _FakeSSH(**fake_kwargs)
    monkeypatch.setenv("NODE_PASS_BRAIN", "ssh-secret")
    monkeypatch.setenv("POKROV_POSTGRES_BACKUP_PASSPHRASE", "backup-secret")
    monkeypatch.setattr(module.paramiko, "SSHClient", lambda: fake)
    monkeypatch.setattr(module, "configure_ssh_host_key_policy", lambda client, **_kwargs: client)

    with pytest.raises(SystemExit):
        module.main(_apply_argv(report_path, reset_target=reset_target))

    report_text = report_path.read_text(encoding="utf-8")
    report = json.loads(report_text)
    assert report["status"] == "FAIL"
    assert report["backup_restore_status"] == "FAIL"
    assert report["phase"] == phase
    assert report["backup_retained"] == backup_retained
    assert report["target_state"] == target_state
    assert report["partial_cleanup_outcome"] == cleanup
    assert report["encrypted_backup"]["path"].endswith(".dump.enc")
    if backup_retained is True:
        assert report["encrypted_backup"]["bytes"] == 4096
        assert report["encrypted_backup"]["sha256"] == "a" * 64
    assert "ssh-secret" not in report_text
    assert "backup-secret" not in report_text
    assert "remote-raw-secret" not in report_text
    if name == "backup":
        assert fake.snapshot_input is not None
        assert "ROLLBACK;" in "".join(fake.snapshot_input.values)


def test_snapshot_rollback_failure_forces_bounded_remote_group_cleanup(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_script()
    report_path = tmp_path / "snapshot-cleanup.json"
    fake = _FakeSSH(
        fail_marker="gate_encrypted_backup",
        snapshot_close_fails=True,
    )
    monkeypatch.setenv("NODE_PASS_BRAIN", "ssh-secret")
    monkeypatch.setenv("POKROV_POSTGRES_BACKUP_PASSPHRASE", "backup-secret")
    monkeypatch.setattr(module.paramiko, "SSHClient", lambda: fake)
    monkeypatch.setattr(module, "configure_ssh_host_key_policy", lambda client, **_kwargs: client)

    with pytest.raises(SystemExit):
        module.main(_apply_argv(report_path))

    report = json.loads(report_path.read_text(encoding="utf-8"))
    commands = "\n".join(fake.commands)
    assert report["phase"] == "backup"
    assert report["snapshot_cleanup_outcome"] == "rollback_failed_force_killed"
    assert "gate_snapshot_force_cleanup" in commands
    assert "signal.SIGTERM" in commands and "signal.SIGKILL" in commands
    assert "pidfd_send_signal" in commands
    assert "kill -TERM" not in commands and "kill -KILL" not in commands
    assert "timeout --signal=TERM --kill-after=2s 15s" in commands


def test_source_evidence_failure_rolls_back_snapshot_before_backup(monkeypatch, tmp_path: Path) -> None:
    module = _load_script()
    report_path = tmp_path / "source-evidence.json"
    fake = _FakeSSH(fail_marker="gate_integrity_evidence")
    monkeypatch.setenv("NODE_PASS_BRAIN", "ssh-secret")
    monkeypatch.setenv("POKROV_POSTGRES_BACKUP_PASSPHRASE", "backup-secret")
    monkeypatch.setattr(module.paramiko, "SSHClient", lambda: fake)
    monkeypatch.setattr(module, "configure_ssh_host_key_policy", lambda client, **_kwargs: client)

    with pytest.raises(SystemExit):
        module.main(_apply_argv(report_path))

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["phase"] == "source_evidence"
    assert report["backup_retained"] is False
    assert report["partial_cleanup_outcome"] == "removed_or_absent"
    assert fake.snapshot_input is not None
    assert "ROLLBACK;" in "".join(fake.snapshot_input.values)
    assert not any("gate_encrypted_backup" in command for command in fake.commands)


def test_apply_refuses_existing_target_and_writes_sanitized_failure_report(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_script()
    report_path = tmp_path / "failure.json"
    fake = _FakeSSH(target_exists=True)
    monkeypatch.setenv("NODE_PASS_BRAIN", "ssh-secret")
    monkeypatch.setenv("POKROV_POSTGRES_BACKUP_PASSPHRASE", "backup-secret")
    monkeypatch.setattr(module.paramiko, "SSHClient", lambda: fake)
    monkeypatch.setattr(module, "configure_ssh_host_key_policy", lambda client, **_kwargs: client)

    with pytest.raises(SystemExit) as exc:
        module.main(
            [
                "--brain-ip",
                "82.21.114.104",
                "--source-db",
                "portal",
                "--confirm-source",
                "portal",
                "--target-db",
                "portal_rehearsal",
                "--confirm-target",
                "portal_rehearsal",
                "--report",
                str(report_path),
                "--apply",
            ]
        )

    report_text = report_path.read_text(encoding="utf-8")
    assert str(exc.value) == "Target database exists; explicit --reset-target is required"
    assert json.loads(report_text)["status"] == "FAIL"
    assert "ssh-secret" not in report_text
    assert "backup-secret" not in report_text
    assert "gate_reset_target" not in "\n".join(fake.commands)
    assert fake.closed is True


def test_ssh_setup_exception_is_generic_and_reported(monkeypatch, tmp_path: Path) -> None:
    module = _load_script()
    report_path = tmp_path / "ssh-failure.json"
    monkeypatch.setenv("NODE_PASS_BRAIN", "ssh-secret")
    monkeypatch.setenv("POKROV_POSTGRES_BACKUP_PASSPHRASE", "backup-secret")
    monkeypatch.setattr(
        module.paramiko,
        "SSHClient",
        lambda: (_ for _ in ()).throw(RuntimeError("password=ssh-secret")),
    )

    with pytest.raises(SystemExit) as exc:
        module.main(
            [
                "--brain-ip",
                "82.21.114.104",
                "--source-db",
                "portal",
                "--confirm-source",
                "portal",
                "--target-db",
                "portal_rehearsal",
                "--confirm-target",
                "portal_rehearsal",
                "--report",
                str(report_path),
                "--apply",
            ]
        )

    report_text = report_path.read_text(encoding="utf-8")
    assert str(exc.value) == "remote_ssh_setup_failed"
    assert json.loads(report_text)["status"] == "FAIL"
    assert "ssh-secret" not in report_text
    assert "backup-secret" not in report_text
