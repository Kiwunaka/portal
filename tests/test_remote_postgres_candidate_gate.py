from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import re
import stat
import subprocess
import sys
import tarfile
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from sqlalchemy.exc import ProgrammingError


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "remote_postgres_candidate_gate.py"
RUNNER_PATH = REPO_ROOT / "scripts" / "remote_postgres_candidate_runner.py"


def _load_script() -> ModuleType:
    assert SCRIPT_PATH.is_file(), "candidate gate script is not implemented"
    scripts_path = str(SCRIPT_PATH.parent)
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)
    spec = importlib.util.spec_from_file_location("remote_postgres_candidate_gate", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("remote_postgres_candidate_runner", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_runner_failure_code_includes_only_safe_sqlstate() -> None:
    runner = _load_runner()
    original = SimpleNamespace(
        pgcode="42703",
        diag=SimpleNamespace(message_primary='column "missing_column" does not exist'),
    )
    error = ProgrammingError("SELECT sensitive_sql", {"password": "hidden"}, original)

    code = runner._safe_exception_code("migrations", error)

    assert code.startswith("migrations_programmingerror_42703_column_missing_column_stmt_")
    assert re.fullmatch(r"[a-z0-9_]{1,96}", code)
    assert "sensitive_sql" not in code
    assert "password" not in code


def test_runner_rejects_same_count_legacy_entitlement_mutation() -> None:
    runner = _load_runner()
    fingerprint = {
        "status": "PASS",
        "rows_sha256": "a" * 64,
        "schema_sha256": "b" * 64,
    }
    pre = {
        "users": {"total": 3},
        "support_tickets": {"total": 2},
        "support_attachments": {"total": 1},
        "support_ticket_messages": 4,
        "entitlement_grants": 2,
        "legacy_entitlement_grants": fingerprint,
    }

    for field in ("rows_sha256", "schema_sha256"):
        post = json.loads(json.dumps(pre))
        post["legacy_entitlement_grants"][field] = "c" * 64
        with pytest.raises(runner.RunnerError, match="legacy_entitlement_grants_changed"):
            runner._assert_preserved(pre, post)


def _git(repo: Path, *args: str, stdout=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        stdout=stdout if stdout is not None else subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=stdout is None,
    )


def _candidate_repo(tmp_path: Path) -> tuple[Path, Path, str, str]:
    repo = tmp_path / "candidate-repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    _git(repo, "config", "user.name", "Candidate Gate Test")
    _git(repo, "config", "user.email", "candidate@example.invalid")
    portal = repo / "portal_bot"
    portal.mkdir()
    (portal / "db.py").write_text("def init_db():\n    return None\n", encoding="utf-8")
    (portal / "migrations.py").write_text(
        'POSTGRES_SCHEMA_BOOTSTRAP_LOCK = "pokrov_schema_bootstrap"\n',
        encoding="utf-8",
    )
    (portal / "nested").mkdir()
    (portal / "nested" / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    _git(repo, "add", "portal_bot")
    _git(repo, "commit", "--quiet", "-m", "candidate")
    commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    archive = tmp_path / "candidate.tar"
    with archive.open("wb") as stream:
        _git(repo, "archive", "--format=tar", commit, "portal_bot", stdout=stream)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    return repo, archive, commit, digest


def _write_tar(path: Path, members: list[tuple[tarfile.TarInfo, bytes]]) -> str:
    with tarfile.open(path, "w") as archive:
        for info, payload in members:
            archive.addfile(info, io.BytesIO(payload) if info.isfile() else None)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_member(name: str, payload: bytes = b"x") -> tuple[tarfile.TarInfo, bytes]:
    info = tarfile.TarInfo(name)
    info.mode = 0o644
    info.size = len(payload)
    return info, payload


def _base_argv(
    report: Path,
    archive: Path,
    digest: str,
    commit: str,
    *,
    apply: bool = False,
) -> list[str]:
    argv = [
        "--brain-ip",
        "192.0.2.10",
        "--passwords",
        str(report.parent / "PASSWORDS.txt"),
        "--candidate-archive",
        str(archive),
        "--candidate-sha256",
        digest,
        "--candidate-commit",
        commit,
        "--source-db",
        "portal",
        "--confirm-source",
        "portal",
        "--target-db",
        "portal_ci_rehearsal",
        "--confirm-target",
        "portal_ci_rehearsal",
        "--report",
        str(report),
    ]
    return [*argv, "--apply"] if apply else argv


def _remote_success(module, commit: str, digest: str) -> dict:
    pre_counts = {
        "users": {"total": 3, "bound": 2, "unbound": 1},
        "accounts": 2,
        "account_identities": 2,
        "account_devices": 1,
        "auth_sessions": 1,
        "entitlement_grants": 2,
        "account_entitlement_grants": 1,
        "support_tickets": {"total": 2, "bound": 1, "unbound": 1},
        "support_ticket_messages": 2,
        "support_attachments": {"total": 2, "bound": 1, "unbound": 1, "dangling": 0},
    }
    post_counts = json.loads(json.dumps(pre_counts))
    post_counts["users"] = {"total": 3, "bound": 3, "unbound": 0}
    post_counts["account_entitlement_grants"] = 3
    return {
        "schema_version": 1,
        "gate": module.GATE_NAME,
        "status": "PASS",
        "candidate": {
            "commit": commit,
            "archive_sha256": digest,
            "runner_sha256": module.REMOTE_RUNNER_SHA256,
        },
        "source_database": "portal",
        "target_database": "portal_ci_rehearsal",
        "checks": {
            "target_access": {
                "status": "PASS",
                "database_identity": True,
                "session_identity": True,
                "ordinary_login": True,
                "database_owner": True,
                "database_public_access_revoked": True,
                "schema_usage": True,
                "schema_create": True,
                "schema_public_access_revoked": True,
                "users_select": True,
                "public_objects_total": 62,
                "public_objects_owned": 62,
            },
            "pre_migration": {
                "status": "PASS",
                "schema": {"tables_present": 9},
                "counts": pre_counts,
                "legacy_entitlement_grants": {
                    "status": "PASS",
                    "rows_sha256": "c" * 64,
                    "schema_sha256": "d" * 64,
                },
            },
            "ddl_lock_impact": {"status": "PASS", "milliseconds": 750, "sqlstate_class": "55"},
            "advisory_lock": {"status": "PASS"},
            "migration_first": {"status": "PASS", "milliseconds": 1200},
            "migration_second": {"status": "PASS", "milliseconds": 300},
            "schema_contract": {"status": "PASS", "tables": 12, "columns": 4, "indexes": 7, "markers": 2},
            "post_migration": {
                "status": "PASS",
                "counts": post_counts,
                "legacy_entitlement_grants": {
                    "status": "PASS",
                    "rows_sha256": "c" * 64,
                    "schema_sha256": "d" * 64,
                },
            },
            "skip_locked": {"status": "PASS", "selected": 2, "distinct": True},
            "bind_retry": {
                "status": "PASS",
                "winners": 1,
                "losers": 1,
                "loser_state": "already_bound",
                "retry_state": "canonical_existing",
                "messages": 1,
            },
            "commit_ack_loss": {
                "status": "PASS",
                "commit_forwarded": True,
                "response_dropped": True,
                "commit_error": True,
                "committed_rows": 1,
            },
        },
        "durations_ms": {"total": 4000},
        "synthetic_cleanup": "confirmed",
    }


def test_destructive_database_guards_are_exact_and_rehearsal_only() -> None:
    module = _load_script()

    assert module.validate_database_selection(
        "portal", "portal", "portal_ci_rehearsal", "portal_ci_rehearsal"
    ) == ("portal", "portal_ci_rehearsal")
    invalid = [
        ("portal-prod", "portal-prod", "portal_ci_rehearsal", "portal_ci_rehearsal"),
        ("portal", "wrong", "portal_ci_rehearsal", "portal_ci_rehearsal"),
        ("portal", "portal", "portal_ci", "portal_ci"),
        ("portal", "portal", "portal_ci_rehearsal", "wrong"),
        ("portal", "portal", "portal", "portal"),
        ("portal", "portal", "Portal_rehearsal", "Portal_rehearsal"),
        ("portal", "portal", "portal.._rehearsal", "portal.._rehearsal"),
    ]
    for values in invalid:
        with pytest.raises(module.GateError):
            module.validate_database_selection(*values)


def test_exact_git_archive_validation_and_dirty_tree_guard(tmp_path: Path) -> None:
    module = _load_script()
    repo, archive, commit, digest = _candidate_repo(tmp_path)

    candidate = module.validate_candidate_archive(archive, digest, commit, repo_root=repo)

    assert candidate.commit == commit
    assert candidate.sha256 == digest
    assert candidate.tracked_files == 3
    assert candidate.size_bytes == archive.stat().st_size
    with pytest.raises(module.GateError, match="candidate_sha256_mismatch"):
        module.validate_candidate_archive(archive, "0" * 64, commit, repo_root=repo)

    (repo / "portal_bot" / "db.py").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(module.GateError, match="candidate_tree_dirty"):
        module.validate_candidate_archive(archive, digest, commit, repo_root=repo)


def test_candidate_archive_includes_tracked_shared_runtime_truth(tmp_path: Path) -> None:
    module = _load_script()
    repo, _archive, _commit, _digest = _candidate_repo(tmp_path)
    shared = repo / "shared"
    shared.mkdir()
    (shared / "tariff-catalog.json").write_text('{"plans":[]}\n', encoding="utf-8")
    _git(repo, "add", "shared")
    _git(repo, "commit", "--quiet", "-m", "shared truth")
    commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    archive = tmp_path / "candidate-with-shared.tar"
    with archive.open("wb") as stream:
        _git(repo, "archive", "--format=tar", commit, "portal_bot", "shared", stdout=stream)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()

    candidate = module.validate_candidate_archive(archive, digest, commit, repo_root=repo)

    assert candidate.tracked_files == 4


def test_candidate_archive_allows_tracked_env_example_template(tmp_path: Path) -> None:
    module = _load_script()
    repo, _archive, _commit, _digest = _candidate_repo(tmp_path)
    (repo / "portal_bot" / ".env.example").write_text(
        "DATABASE_URL=replace-at-deploy\n",
        encoding="utf-8",
    )
    _git(repo, "add", "portal_bot/.env.example")
    _git(repo, "commit", "--quiet", "-m", "tracked env template")
    commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    archive = tmp_path / "candidate-with-env-example.tar"
    with archive.open("wb") as stream:
        _git(repo, "archive", "--format=tar", commit, "portal_bot", stdout=stream)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()

    candidate = module.validate_candidate_archive(archive, digest, commit, repo_root=repo)

    assert candidate.tracked_files == 4


def test_candidate_archive_enforces_local_size_limit(monkeypatch, tmp_path: Path) -> None:
    module = _load_script()
    repo, archive, commit, digest = _candidate_repo(tmp_path)
    monkeypatch.setattr(module, "MAX_CANDIDATE_ARCHIVE_BYTES", archive.stat().st_size - 1)

    with pytest.raises(module.GateError, match="candidate_archive_too_large"):
        module.validate_candidate_archive(archive, digest, commit, repo_root=repo)


def test_archive_rejects_unexpected_secret_symlink_and_traversal_members(tmp_path: Path) -> None:
    module = _load_script()
    repo, _archive, commit, _digest = _candidate_repo(tmp_path)

    bad_members: list[list[tuple[tarfile.TarInfo, bytes]]] = [
        [_file_member("portal_bot/db.py"), _file_member("outside.txt")],
        [_file_member("portal_bot/db.py"), _file_member("portal_bot/.env", b"DATABASE_URL=x")],
        [_file_member("portal_bot/db.py"), _file_member("portal_bot/credentials.json")],
        [_file_member("portal_bot/db.py"), _file_member("portal_bot/passwords.txt")],
        [_file_member("portal_bot/db.py"), _file_member("portal_bot/client_secret.json")],
        [_file_member("portal_bot/db.py"), _file_member("portal_bot/../../escape")],
        [_file_member("portal_bot/db.py"), _file_member("/portal_bot/absolute")],
    ]
    link = tarfile.TarInfo("portal_bot/link")
    link.type = tarfile.SYMTYPE
    link.linkname = "/etc/passwd"
    bad_members.append([_file_member("portal_bot/db.py"), (link, b"")])

    for index, members in enumerate(bad_members):
        archive = tmp_path / f"bad-{index}.tar"
        digest = _write_tar(archive, members)
        with pytest.raises(module.GateError):
            module.validate_candidate_archive(archive, digest, commit, repo_root=repo)


def test_archive_requires_head_commit_and_rejects_tracked_key_material(tmp_path: Path) -> None:
    module = _load_script()
    repo, archive, commit, digest = _candidate_repo(tmp_path)
    (repo / "portal_bot" / "next.py").write_text("next\n", encoding="utf-8")
    _git(repo, "add", "portal_bot/next.py")
    _git(repo, "commit", "--quiet", "-m", "next")

    with pytest.raises(module.GateError, match="candidate_commit_not_head"):
        module.validate_candidate_archive(archive, digest, commit, repo_root=repo)

    secret = repo / "portal_bot" / "client.key"
    secret.write_text("not-a-real-key\n", encoding="utf-8")
    _git(repo, "add", "portal_bot/client.key")
    _git(repo, "commit", "--quiet", "-m", "unsafe material")
    unsafe_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    unsafe_archive = tmp_path / "unsafe.tar"
    with unsafe_archive.open("wb") as stream:
        _git(repo, "archive", "--format=tar", unsafe_commit, "portal_bot", stdout=stream)
    unsafe_digest = hashlib.sha256(unsafe_archive.read_bytes()).hexdigest()
    with pytest.raises(module.GateError, match="candidate_archive_sensitive_path"):
        module.validate_candidate_archive(
            unsafe_archive, unsafe_digest, unsafe_commit, repo_root=repo
        )


def test_plan_only_validates_candidate_and_never_constructs_ssh(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    module = _load_script()
    repo, archive, commit, digest = _candidate_repo(tmp_path)
    report = tmp_path / "reports" / "plan.json"
    report.parent.mkdir()
    passwords = report.parent / "PASSWORDS.txt"
    passwords.write_text("BRAINnode\nssh-secret-never-read\n", encoding="utf-8")
    monkeypatch.setattr(module, "REPO_ROOT", repo)

    class ForbiddenSSH:
        def __init__(self, *_args, **_kwargs):
            raise AssertionError("plan-only constructed SSH")

    monkeypatch.setattr(module.paramiko, "SSHClient", ForbiddenSSH)

    assert module.main(_base_argv(report, archive, digest, commit)) == 0

    evidence = json.loads(report.read_text(encoding="utf-8"))
    assert evidence["status"] == "PLAN_ONLY"
    assert evidence["ssh"] == "NOT_REQUESTED"
    assert evidence["candidate"] == {
        "commit": commit,
        "archive_sha256": digest,
        "runner_sha256": module.REMOTE_RUNNER_SHA256,
        "tracked_files": 3,
    }
    output = capsys.readouterr()
    assert output.out.strip() == "PLAN_ONLY"
    assert "ssh-secret-never-read" not in output.out + output.err + report.read_text(encoding="utf-8")


def test_existing_report_refuses_before_archive_or_ssh(monkeypatch, tmp_path: Path) -> None:
    module = _load_script()
    report = tmp_path / "existing.json"
    report.write_text('{"keep":true}\n', encoding="utf-8")

    monkeypatch.setattr(
        module,
        "validate_candidate_archive",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("archive touched")),
    )
    monkeypatch.setattr(
        module.paramiko,
        "SSHClient",
        lambda: (_ for _ in ()).throw(AssertionError("SSH touched")),
    )
    with pytest.raises(SystemExit, match="report_exists"):
        module.main(
            _base_argv(
                report,
                tmp_path / "missing.tar",
                "0" * 64,
                "1" * 40,
            )
        )
    assert report.read_text(encoding="utf-8") == '{"keep":true}\n'


def test_ssh_is_strict_with_tofu_forced_off(monkeypatch) -> None:
    module = _load_script()
    ssh = SimpleNamespace(connect_calls=[], close=lambda: None)

    def connect(**kwargs):
        ssh.connect_calls.append(kwargs)

    ssh.connect = connect
    policy_calls = []
    monkeypatch.setattr(module.paramiko, "SSHClient", lambda: ssh)
    monkeypatch.setattr(
        module,
        "configure_ssh_host_key_policy",
        lambda client, **kwargs: policy_calls.append((client, kwargs)) or client,
    )

    assert module._connect_ssh("192.0.2.10", "ssh-password") is ssh
    assert policy_calls == [(ssh, {"allow_trust_on_first_use": False})]
    assert ssh.connect_calls[0]["username"] == "root"
    assert ssh.connect_calls[0]["port"] == module.BRAIN_SSH_PORT
    assert ssh.connect_calls[0]["password"] == "ssh-password"
    assert ssh.connect_calls[0]["look_for_keys"] is False
    assert ssh.connect_calls[0]["allow_agent"] is False


def test_password_and_remote_errors_are_never_disclosed(tmp_path: Path) -> None:
    module = _load_script()
    passwords = tmp_path / "PASSWORDS.txt"
    passwords.write_text(
        "BRAINnode\n"
        "ssh-ed25519 AAAATEST comment\n"
        "-----BEGIN PRIVATE KEY-----\n"
        "PRIVATEKEYBODY\n"
        "-----END PRIVATE KEY-----\n"
        "operator-password\n",
        encoding="utf-8",
    )
    assert module._parse_password(passwords) == "operator-password"

    raw = "password=hunter2 postgresql://operator:secret@brain/portal customer-row=42"
    error = module.remote_error("runner", RuntimeError(raw))
    assert str(error) == "remote_runner_failed"
    assert raw not in repr(error)
    for forbidden in ("hunter2", "postgresql://", "customer-row"):
        assert forbidden not in repr(error)


def test_report_redaction_rejects_secrets_urls_and_row_values() -> None:
    module = _load_script()
    module.assert_report_safe({"status": "PASS", "counts": {"users": 3}})
    unsafe = [
        {"password": "anything"},
        {"detail": "postgresql://user:pass@host/db"},
        {"detail": "DATABASE_URL=postgresql://host/db"},
        {"customer_id": 7},
        {"row_value": "alice@example.invalid"},
        {"nonce": "secret-synthetic-name"},
    ]
    for value in unsafe:
        with pytest.raises(module.GateError):
            module.assert_report_safe(value)


def test_target_url_is_derived_without_connecting_to_source_or_rendering_secret() -> None:
    module = _load_script()
    live = "postgresql+psycopg2://portal_user:top-secret@127.0.0.1:5432/portal?sslmode=require"

    target = module.derive_target_url(live, "portal", "portal_ci_rehearsal")

    assert target.database == "portal_ci_rehearsal"
    assert target.username == "portal_user"
    assert target.password == "top-secret"
    assert target.query["sslmode"] == "require"
    with pytest.raises(module.GateError):
        module.derive_target_url(live.replace("/portal?", "/other?"), "portal", "portal_ci_rehearsal")
    with pytest.raises(module.GateError):
        module.derive_target_url("sqlite:///portal.db", "portal", "portal_ci_rehearsal")


def test_remote_command_has_no_secret_or_database_url() -> None:
    module = _load_script()
    scratch = "/tmp/pokrov-postgres-candidate-gates/" + "a" * 32
    command = module.build_remote_command(scratch)

    assert command == (
        "umask 077; exec timeout --signal=TERM --kill-after=15s "
        f"{module.REMOTE_RUNNER_TIMEOUT_SECONDS}s /root/portal_bot/venv/bin/python "
        f"{scratch}/runner.py"
    )
    assert "DATABASE_URL" not in command
    assert "postgresql://" not in command
    assert "password" not in command.lower()


def test_remote_runner_defines_all_target_only_checks_without_importing_api() -> None:
    module = _load_script()
    source = module.REMOTE_RUNNER_SOURCE
    compile(source, "remote_postgres_candidate_runner.py", "exec")

    required = [
        "/root/portal_bot/.env",
        "make_url",
        ".set(database=target_database)",
        "PGOPTIONS",
        "lock_timeout",
        "statement_timeout",
        "idle_in_transaction_session_timeout",
        "current_database()",
        "target_access_contract",
        "current_user = session_user",
        "has_schema_privilege",
        "has_table_privilege",
        "public_objects_owned",
        "database_public_access_revoked",
        "schema_public_access_revoked",
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
        "ACCESS SHARE",
        "ALTER TABLE support_attachments ADD COLUMN",
        "pg_try_advisory_xact_lock",
        "POSTGRES_SCHEMA_BOOTSTRAP_LOCK",
        "db.init_db()",
        "migration.account_foundation.v1",
        "migration.support_account_ownership.v1",
        "FOR UPDATE SKIP LOCKED",
        "ticket_id IS NULL",
        "message_id IS NULL",
        "expires_at IS NOT NULL",
        "expires_at <=",
        "FOR UPDATE",
        "UPDATE support_attachments",
        "already_bound",
        "canonical_existing",
        "sslmode",
        "disable",
        "CommandComplete",
        "COMMIT",
    ]
    assert all(fragment in source for fragment in required)
    assert "import api" not in source
    assert "CREATE DATABASE" not in source.upper()
    assert "DROP DATABASE" not in source.upper()
    assert "engine_source" not in source
    assert "print(" not in source


def test_remote_runner_emits_only_safe_failure_code_for_invalid_request(tmp_path: Path) -> None:
    module = _load_script()
    runner = tmp_path / "runner.py"
    runner.write_text(module.REMOTE_RUNNER_SOURCE, encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(runner)],
        input="not-json postgresql://user:secret@host/portal customer-row=42",
        text=True,
        capture_output=True,
        timeout=10,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload == {
        "schema_version": 1,
        "gate": module.GATE_NAME,
        "status": "FAIL",
        "error": "request_invalid",
        "synthetic_cleanup": "unknown",
    }
    rendered = completed.stdout + completed.stderr
    assert "postgresql://" not in rendered
    assert "customer-row" not in rendered


def _packet(kind: bytes, payload: bytes) -> bytes:
    return kind + (len(payload) + 4).to_bytes(4, "big") + payload


def _startup_packet() -> bytes:
    payload = (196608).to_bytes(4, "big") + b"user\x00portal\x00database\x00portal_ci_rehearsal\x00\x00"
    return (len(payload) + 4).to_bytes(4, "big") + payload


def test_postgres_protocol_parser_handles_fragmented_startup_and_packets() -> None:
    module = _load_script()
    parser = module.PostgresProtocolParser(expect_startup=True)
    stream = _startup_packet() + _packet(b"p", b"password\x00") + _packet(b"Q", b" COMMIT ; \x00")
    frames = []
    for cut in (1, 2, 3, 5, 7, len(stream)):
        if not stream:
            break
        chunk, stream = stream[:cut], stream[cut:]
        frames.extend(parser.feed(chunk))
    if stream:
        frames.extend(parser.feed(stream))

    assert [frame.kind for frame in frames] == [None, b"p", b"Q"]
    assert module.is_frontend_commit(frames[-1]) is True
    assert "password" not in repr(parser)


def test_commit_ack_drop_state_forwards_commit_and_drops_fragmented_response() -> None:
    module = _load_script()
    state = module.CommitAckDropState()
    frontend = _startup_packet() + _packet(b"Q", b"COMMIT\x00")
    forwarded = b""
    for byte in frontend:
        forwarded += state.process_frontend(bytes([byte]))
    assert forwarded == frontend
    assert state.commit_forwarded is True

    insert_complete = _packet(b"C", b"INSERT 0 1\x00")
    commit_complete = _packet(b"C", b"COMMIT\x00")
    ready = _packet(b"Z", b"I")
    backend = insert_complete + commit_complete + ready
    delivered = b""
    for size in (2, 1, 4, 3, 8, 1024):
        chunk, backend = backend[:size], backend[size:]
        delivered += state.process_backend(chunk)
    if backend:
        delivered += state.process_backend(backend)

    assert delivered == insert_complete
    assert state.response_dropped is True
    assert state.process_backend(_packet(b"Z", b"I")) == b""


def test_protocol_parser_rejects_malformed_lengths() -> None:
    module = _load_script()
    with pytest.raises(module.ProtocolError):
        module.PostgresProtocolParser(expect_startup=False).feed(b"Q\x00\x00\x00\x03")
    with pytest.raises(module.ProtocolError):
        module.PostgresProtocolParser(expect_startup=True).feed(b"\x00\x00\x00\x04")


def test_remote_report_validation_is_strict_and_aggregate_only() -> None:
    module = _load_script()
    commit = "a" * 40
    digest = "b" * 64
    report = _remote_success(module, commit, digest)

    assert module.validate_remote_report(
        report,
        source="portal",
        target="portal_ci_rehearsal",
        commit=commit,
        archive_sha256=digest,
    )["status"] == "PASS"

    for mutation in (
        {**report, "database_url": "postgresql://user:secret@host/db"},
        {**report, "row_id": 42},
        {**report, "synthetic_cleanup": "unknown"},
        {**report, "target_database": "portal"},
        {
            **report,
            "candidate": {
                "commit": "c" * 40,
                "archive_sha256": digest,
                "runner_sha256": module.REMOTE_RUNNER_SHA256,
            },
        },
    ):
        with pytest.raises(module.GateError):
            module.validate_remote_report(
                mutation,
                source="portal",
                target="portal_ci_rehearsal",
                commit=commit,
                archive_sha256=digest,
            )

    changed_total = json.loads(json.dumps(report))
    changed_total["checks"]["post_migration"]["counts"]["support_tickets"] = {
        "total": 3,
        "bound": 2,
        "unbound": 1,
    }
    incomplete_schema = json.loads(json.dumps(report))
    incomplete_schema["checks"]["schema_contract"] = {
        "status": "PASS",
        "tables": 0,
        "columns": 0,
        "indexes": 0,
        "markers": 0,
    }
    missing_target_access = json.loads(json.dumps(report))
    del missing_target_access["checks"]["target_access"]
    leaking_target_access = json.loads(json.dumps(report))
    leaking_target_access["checks"]["target_access"]["username"] = "app-role-must-not-leak"
    incomplete_target_access = json.loads(json.dumps(report))
    incomplete_target_access["checks"]["target_access"]["public_objects_owned"] = 61
    changed_legacy_entitlements = json.loads(json.dumps(report))
    changed_legacy_entitlements["checks"]["post_migration"]["counts"]["entitlement_grants"] = 1
    stale_schema_contract = json.loads(json.dumps(report))
    stale_schema_contract["checks"]["schema_contract"] = {
        "status": "PASS",
        "tables": 11,
        "columns": 3,
        "indexes": 6,
        "markers": 2,
    }
    changed_legacy_rows = json.loads(json.dumps(report))
    changed_legacy_rows["checks"]["post_migration"]["legacy_entitlement_grants"][
        "rows_sha256"
    ] = "e" * 64
    changed_legacy_schema = json.loads(json.dumps(report))
    changed_legacy_schema["checks"]["post_migration"]["legacy_entitlement_grants"][
        "schema_sha256"
    ] = "f" * 64
    for mutation in (
        changed_total,
        incomplete_schema,
        missing_target_access,
        leaking_target_access,
        incomplete_target_access,
        changed_legacy_entitlements,
        stale_schema_contract,
        changed_legacy_rows,
        changed_legacy_schema,
    ):
        with pytest.raises(module.GateError):
            module.validate_remote_report(
                mutation,
                source="portal",
                target="portal_ci_rehearsal",
                commit=commit,
                archive_sha256=digest,
            )


class _FakeSFTP:
    def __init__(self, *, fail_put: bool = False) -> None:
        self.fail_put = fail_put
        self.puts: list[tuple[str, str]] = []
        self.writes: list[tuple[str, bytes]] = []
        self.chmods: list[tuple[str, int]] = []
        self.renames: list[tuple[str, str]] = []
        self.timeouts: list[int] = []
        self.closed = False

    def get_channel(self):
        parent = self

        class Channel:
            def settimeout(self, timeout: int) -> None:
                parent.timeouts.append(timeout)

        return Channel()

    def put(self, local: str, remote: str) -> None:
        if self.fail_put:
            raise OSError("remote path and password must stay private")
        self.puts.append((local, remote))

    def file(self, remote: str, _mode: str):
        parent = self

        class Writer(io.BytesIO):
            def close(self) -> None:
                if not self.closed:
                    parent.writes.append((remote, self.getvalue()))
                super().close()

        return Writer()

    def chmod(self, remote: str, mode: int) -> None:
        self.chmods.append((remote, mode))

    def posix_rename(self, source: str, target: str) -> None:
        self.renames.append((source, target))

    def close(self) -> None:
        self.closed = True


class _FakeSSH:
    def __init__(self, sftp: _FakeSFTP) -> None:
        self.sftp = sftp
        self.closed = False

    def open_sftp(self) -> _FakeSFTP:
        return self.sftp

    def close(self) -> None:
        self.closed = True


def test_remote_scratch_upload_is_private_atomic_and_always_cleaned(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_script()
    archive = tmp_path / "candidate.tar"
    archive.write_bytes(b"candidate")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    candidate = module.CandidateArchive(archive, digest, "a" * 40, 1, archive.stat().st_size)
    sftp = _FakeSFTP()
    ssh = _FakeSSH(sftp)
    commands: list[str] = []
    success = _remote_success(module, candidate.commit, candidate.sha256)

    def fake_remote_run(_ssh, command, **kwargs):
        commands.append(command)
        if "sha256sum" in command:
            return f"{digest}  candidate.tar.partial\n"
        if command.startswith("umask 077; exec"):
            assert json.loads(kwargs["stdin_data"])["target_database"] == "portal_ci_rehearsal"
            return json.dumps(success)
        return ""

    monkeypatch.setattr(module, "_remote_run", fake_remote_run)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _n: "a" * 32)

    result = module._execute_remote_gate(
        ssh,
        candidate=candidate,
        source="portal",
        target="portal_ci_rehearsal",
    )

    scratch = "/tmp/pokrov-postgres-candidate-gates/" + "a" * 32
    assert result["status"] == "PASS"
    assert sftp.puts == [(str(archive), f"{scratch}/candidate.tar.partial")]
    assert all(mode == 0o600 for _path, mode in sftp.chmods)
    assert (f"{scratch}/candidate.tar.partial", f"{scratch}/candidate.tar") in sftp.renames
    assert (f"{scratch}/runner.py.partial", f"{scratch}/runner.py") in sftp.renames
    assert any("mkdir -m 0700" in command for command in commands)
    assert commands[-1].startswith("rm -rf -- /tmp/pokrov-postgres-candidate-gates/")
    assert "DATABASE_URL" not in "\n".join(commands)
    assert "postgresql://" not in "\n".join(commands)
    assert sftp.closed is True
    assert sftp.timeouts == [120]


@pytest.mark.parametrize("failure", ["put", "runner"])
def test_remote_archive_and_extracted_code_cleanup_runs_on_every_failure(
    monkeypatch, tmp_path: Path, failure: str
) -> None:
    module = _load_script()
    archive = tmp_path / "candidate.tar"
    archive.write_bytes(b"candidate")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    candidate = module.CandidateArchive(archive, digest, "a" * 40, 1, archive.stat().st_size)
    sftp = _FakeSFTP(fail_put=failure == "put")
    ssh = _FakeSSH(sftp)
    commands: list[str] = []

    def fake_remote_run(_ssh, command, **_kwargs):
        commands.append(command)
        if "sha256sum" in command:
            return f"{digest}  candidate.tar.partial\n"
        if command.startswith("umask 077; exec") and failure == "runner":
            raise module.remote_error("runner", RuntimeError("DATABASE_URL=secret"))
        return ""

    monkeypatch.setattr(module, "_remote_run", fake_remote_run)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _n: "b" * 32)

    with pytest.raises(module.RemoteGateError):
        module._execute_remote_gate(
            ssh,
            candidate=candidate,
            source="portal",
            target="portal_ci_rehearsal",
        )

    assert commands[-1] == (
        "rm -rf -- /tmp/pokrov-postgres-candidate-gates/" + "b" * 32
    )
    assert "secret" not in repr(commands)


def test_failure_report_marks_synthetic_cleanup_ambiguous(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    module = _load_script()
    repo, archive, commit, digest = _candidate_repo(tmp_path)
    report = tmp_path / "failure.json"
    passwords = tmp_path / "PASSWORDS.txt"
    passwords.write_text("BRAINnode\nssh-secret\n", encoding="utf-8")
    monkeypatch.setattr(module, "REPO_ROOT", repo)
    monkeypatch.setattr(
        module,
        "_apply_gate",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(module.remote_error("runner")),
    )

    with pytest.raises(SystemExit, match="remote_runner_failed"):
        module.main(_base_argv(report, archive, digest, commit, apply=True))

    evidence = json.loads(report.read_text(encoding="utf-8"))
    assert evidence["status"] == "FAIL"
    assert evidence["phase"] == "remote_runner"
    assert evidence["state"] == "failed"
    assert evidence["synthetic_cleanup"] == "unknown"
    assert evidence["error"] == "remote_runner_failed"
    rendered = report.read_text(encoding="utf-8") + capsys.readouterr().err
    assert "ssh-secret" not in rendered
    assert "postgresql://" not in rendered


def test_atomic_report_is_0600_current_user_only_and_no_clobber(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_script()
    report = tmp_path / "evidence.json"
    payload = {"status": "PLAN_ONLY", "ssh": "NOT_REQUESTED"}
    opens: list[tuple[int, int]] = []
    real_open = os.open

    def recording_open(path, flags, mode=0o777):
        opens.append((flags, mode))
        return real_open(path, flags, mode)

    monkeypatch.setattr(module.os, "open", recording_open)
    module.write_report_atomic(report, payload)

    assert json.loads(report.read_text(encoding="utf-8")) == payload
    if os.name == "nt":
        sid = module._windows_current_user_sid()
        dacl = module._windows_file_dacl_sddl(report)
        assert dacl.startswith("D:P")
        assert sid in dacl
        assert dacl.count("(A;") == 1
    else:
        assert any(flags & os.O_EXCL and stat.S_IMODE(mode) == 0o600 for flags, mode in opens)
    with pytest.raises(module.GateError, match="report_exists"):
        module.write_report_atomic(report, payload)
    assert not list(tmp_path.glob(".*.tmp"))


def test_report_path_must_be_outside_any_git_worktree(tmp_path: Path) -> None:
    module = _load_script()
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").write_text("gitdir: elsewhere", encoding="utf-8")
    with pytest.raises(module.GateError, match="report_inside_git"):
        module.validate_report_path(repo / "report.json")
