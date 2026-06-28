from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path
from types import ModuleType

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_script(script_name: str) -> ModuleType:
    path = REPO_ROOT / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(script_name.replace(".py", ""), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _FakeChannel:
    def __init__(self, code: int = 0) -> None:
        self._code = code

    def recv_exit_status(self) -> int:
        return self._code


class _FakeStream:
    def __init__(self, text: str = "", code: int = 0) -> None:
        self.channel = _FakeChannel(code)
        self._text = text

    def read(self) -> bytes:
        return self._text.encode("utf-8")


class _FakeSFTPFile:
    def __init__(self, ssh: "_FakeSSH", path: str, mode: str) -> None:
        self._ssh = ssh
        self._path = path
        self._mode = mode
        initial = b"" if "w" in mode else ssh.files.get(path, b"")
        self._buffer = io.BytesIO(initial)

    def __enter__(self):
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def read(self) -> bytes:
        return self._buffer.getvalue()

    def write(self, data) -> None:
        if isinstance(data, str):
            data = data.encode("utf-8")
        self._buffer = io.BytesIO(data)

    def close(self) -> None:
        if "w" in self._mode or "+" in self._mode:
            self._ssh.files[self._path] = self._buffer.getvalue()


class _FakeSFTP:
    def __init__(self, ssh: "_FakeSSH") -> None:
        self._ssh = ssh
        self.closed = False

    def file(self, path: str, mode: str):
        if "r" in mode and path not in self._ssh.files:
            raise IOError(path)
        return _FakeSFTPFile(self._ssh, path, mode)

    def stat(self, path: str):
        if path in self._ssh.dirs or path in self._ssh.files:
            return object()
        raise IOError(path)

    def mkdir(self, path: str) -> None:
        self._ssh.dirs.add(path)

    def put(self, local_path: str, remote_path: str) -> None:
        self._ssh.files[remote_path] = Path(local_path).read_bytes()

    def close(self) -> None:
        self.closed = True
        self._ssh.sftp_closed = True


class _FakeSSH:
    def __init__(self) -> None:
        self.commands: list[str] = []
        self.files: dict[str, bytes] = {"/root/portal_bot/.env": b"BOT_TOKEN=token\n"}
        self.dirs: set[str] = {"/", "/root", "/root/portal_bot"}
        self.connect_kwargs: dict[str, object] = {}
        self.closed = False
        self.sftp_closed = False

    def set_missing_host_key_policy(self, _policy) -> None:
        pass

    def connect(self, host: str | None = None, **kwargs) -> None:
        self.connect_kwargs = {"host": host or kwargs.get("hostname"), **kwargs}

    def exec_command(self, cmd: str, timeout: int):
        self.commands.append(cmd)
        out = "ok"
        if "systemctl is-active portal-worker" in cmd:
            out = "active"
        elif "systemctl restart portal-api" in cmd:
            out = "active\nactive\nactive\nactive"
        elif "select sub_token" in cmd:
            out = "Profile-Update-Interval: 24"
        elif "select tg_id, username" in cmd:
            out = "user row"
        return None, _FakeStream(out), _FakeStream("")

    def open_sftp(self):
        return _FakeSFTP(self)

    def close(self) -> None:
        self.closed = True


def _install_fake_ssh(module: ModuleType, monkeypatch) -> _FakeSSH:
    fake = _FakeSSH()
    monkeypatch.setattr(module.paramiko, "SSHClient", lambda: fake)
    monkeypatch.setattr(module.paramiko, "AutoAddPolicy", lambda: object())
    monkeypatch.setenv("NODE_PASS_BRAIN", "brain-secret")
    return fake


def test_migrate_sqlite_to_postgres_fails_closed_without_postgres_url(monkeypatch) -> None:
    module = _load_script("migrate_sqlite_to_postgres.py")
    monkeypatch.delenv("POSTGRES_DATABASE_URL", raising=False)
    monkeypatch.setattr(sys, "argv", ["migrate_sqlite_to_postgres.py", "--sqlite-url", "sqlite:///portal.db"])

    with pytest.raises(SystemExit) as exc:
        module.main()

    assert "Missing --postgres-url" in str(exc.value)


def test_remote_check_postgres_runs_read_only_checks_and_closes(monkeypatch) -> None:
    module = _load_script("remote_check_postgres.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(sys, "argv", ["remote_check_postgres.py", "--brain-ip", "82.21.114.104"])

    assert module.main() == 0

    joined = "\n".join(fake.commands)
    assert "psql --version" in joined
    assert "systemctl is-active postgresql" in joined
    assert "brain-secret" not in joined
    assert fake.closed is True


def test_remote_check_subscription_interval_validates_domain(monkeypatch) -> None:
    module = _load_script("remote_check_subscription_interval.py")
    monkeypatch.setattr(
        sys,
        "argv",
        ["remote_check_subscription_interval.py", "--brain-ip", "82.21.114.104", "--domain", "api.pokrov.space;id"],
    )

    with pytest.raises(SystemExit) as exc:
        module.main()

    assert "Invalid --domain" in str(exc.value)


def test_remote_check_subscription_interval_uses_safe_domain(monkeypatch) -> None:
    module = _load_script("remote_check_subscription_interval.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        ["remote_check_subscription_interval.py", "--brain-ip", "82.21.114.104", "--domain", "api.pokrov.space"],
    )

    assert module.main() == 0

    joined = "\n".join(fake.commands)
    assert "--resolve api.pokrov.space:443:127.0.0.1" in joined
    assert "Profile-Update-Interval" in joined
    assert fake.closed is True


def test_remote_inspect_user_quotes_db_name_and_runs_expected_queries(monkeypatch) -> None:
    module = _load_script("remote_inspect_user.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        ["remote_inspect_user.py", "--brain-ip", "82.21.114.104", "--tg-id", "1001", "--db-name", "portal;main"],
    )

    assert module.main() == 0

    joined = "\n".join(fake.commands)
    assert "psql -d 'portal;main'" in joined
    assert "from users where tg_id=1001" in joined
    assert "brain-secret" not in joined
    assert fake.closed is True


def test_remote_audit_inactive_users_dry_run_uses_psql_json_and_quotes_db(monkeypatch, capsys) -> None:
    module = _load_script("remote_audit_inactive_users.py")
    fake = _install_fake_ssh(module, monkeypatch)

    def fake_run(_ssh, cmd: str, *, timeout: int = 120):
        fake.commands.append(cmd)
        if "psql" in cmd:
            return 0, '{"candidates_total":0,"users_total":1}', ""
        return 0, "", ""

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["remote_audit_inactive_users.py", "--brain-ip", "82.21.114.104", "--db-name", "portal;main"],
    )

    assert module.main() == 0

    output = capsys.readouterr().out
    joined = "\n".join(fake.commands)
    uploaded_sql = b"\n".join(fake.files.values()).decode("utf-8", errors="replace")
    assert '"candidates_total": 0' in output
    assert "psql -d 'portal;main'" in joined
    assert "-v ON_ERROR_STOP=1" in joined
    assert "WITH base AS MATERIALIZED" in uploaded_sql
    assert "brain-secret" not in joined
    assert fake.closed is True


def test_remote_cleanup_inactive_users_dry_run_does_not_backup_or_purge(monkeypatch, capsys) -> None:
    module = _load_script("remote_cleanup_inactive_users.py")
    fake = _install_fake_ssh(module, monkeypatch)
    calls: list[str] = []

    monkeypatch.setattr(
        module,
        "_psql_json",
        lambda *_args, **_kwargs: {
            "candidates_total": 1,
            "candidate_ids": [1001],
            "risk_flags": {
                "stars_paid_positive_users": 0,
                "first_purchase_done_users": 0,
                "paid_pay_attempt_users": 0,
                "paid_external_order_users": 0,
                "support_ticket_users": 0,
            },
        },
    )
    monkeypatch.setattr(module, "_backup_postgres", lambda *_args, **_kwargs: calls.append("backup"))
    monkeypatch.setattr(module, "_run_panel_cleanup", lambda *_args, **_kwargs: calls.append("panel"))
    monkeypatch.setattr(sys, "argv", ["remote_cleanup_inactive_users.py", "--brain-ip", "82.21.114.104"])

    assert module.main() == 0

    output = capsys.readouterr().out
    assert '"mode": "dry_run"' in output
    assert calls == []
    assert fake.closed is True


def test_remote_cleanup_inactive_users_apply_requires_confirm(monkeypatch) -> None:
    module = _load_script("remote_cleanup_inactive_users.py")
    fake = _install_fake_ssh(module, monkeypatch)

    monkeypatch.setattr(
        module,
        "_psql_json",
        lambda *_args, **_kwargs: {
            "candidates_total": 1,
            "candidate_ids": [1001],
            "risk_flags": {
                "stars_paid_positive_users": 0,
                "first_purchase_done_users": 0,
                "paid_pay_attempt_users": 0,
                "paid_external_order_users": 0,
                "support_ticket_users": 0,
            },
        },
    )
    monkeypatch.setattr(sys, "argv", ["remote_cleanup_inactive_users.py", "--brain-ip", "82.21.114.104", "--apply"])

    with pytest.raises(SystemExit) as exc:
        module.main()

    assert "Refusing apply without --confirm PURGE_INACTIVE_14D" in str(exc.value)
    assert fake.closed is True


def test_remote_cleanup_inactive_users_panel_script_loads_env_before_db_import() -> None:
    module = _load_script("remote_cleanup_inactive_users.py")

    script = module._panel_cleanup_script([1001])

    assert "import os" in script
    assert 'load_env("/root/portal_bot/.env")' in script
    assert "from db import SessionLocal" in script
    assert script.index('load_env("/root/portal_bot/.env")') < script.index("from db import SessionLocal")


def test_remote_install_portal_worker_service_uploads_service_and_restart_commands(monkeypatch) -> None:
    module = _load_script("remote_install_portal_worker_service.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        ["remote_install_portal_worker_service.py", "--brain-ip", "82.21.114.104", "--ensure-embedded-off"],
    )

    assert module.main() == 0

    service = fake.files["/etc/systemd/system/portal-worker.service"].decode("utf-8")
    joined = "\n".join(fake.commands)
    assert "ExecStart=/root/portal_bot/venv/bin/python /root/portal_bot/worker.py" in service
    assert "WORKER_EMBEDDED=false" in joined
    assert "systemctl restart portal-worker" in joined
    assert fake.sftp_closed is True
    assert fake.closed is True


def test_remote_postgres_cutover_validates_identifiers_before_ssh(monkeypatch) -> None:
    module = _load_script("remote_postgres_cutover.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        ["remote_postgres_cutover.py", "--brain-ip", "82.21.114.104", "--db-name", "portal;drop"],
    )

    with pytest.raises(SystemExit) as exc:
        module.main()

    assert "Invalid --db-name" in str(exc.value)
    assert fake.connect_kwargs == {}


def test_remote_postgres_cutover_updates_env_and_masks_password(monkeypatch, capsys) -> None:
    module = _load_script("remote_postgres_cutover.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(module, "_random_password", lambda: "GeneratedDbPass123")
    monkeypatch.setattr(sys, "argv", ["remote_postgres_cutover.py", "--brain-ip", "82.21.114.104"])

    assert module.main() == 0

    env_text = fake.files["/root/portal_bot/.env"].decode("utf-8")
    output = capsys.readouterr().out
    assert "DATABASE_URL=postgresql+psycopg2://portal_app:GeneratedDbPass123@127.0.0.1:5432/portal" in env_text
    assert "DATABASE_URL=postgresql+psycopg2://portal_app:***@127.0.0.1:5432/portal" in output
    assert "GeneratedDbPass123" not in output
    assert "/root/portal_bot/migrate_sqlite_to_postgres.py" in fake.files
    assert fake.closed is True


def test_remote_reconcile_payment_rejects_unsafe_plan_code_before_ssh(monkeypatch) -> None:
    module = _load_script("remote_reconcile_payment.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_reconcile_payment.py",
            "--brain-ip",
            "82.21.114.104",
            "--tg-id",
            "1001",
            "--amount-stars",
            "500",
            "--plan-code",
            "3_months';drop",
        ],
    )

    with pytest.raises(SystemExit) as exc:
        module.main()

    assert "Invalid --plan-code" in str(exc.value)
    assert fake.connect_kwargs == {}


def test_remote_reconcile_payment_builds_bounded_sql_and_closes(monkeypatch) -> None:
    module = _load_script("remote_reconcile_payment.py")
    fake = _install_fake_ssh(module, monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_reconcile_payment.py",
            "--brain-ip",
            "82.21.114.104",
            "--tg-id",
            "1001",
            "--amount-stars",
            "500",
            "--plan-code",
            "3_months",
            "--db-name",
            "portal;main",
        ],
    )

    assert module.main() == 0

    joined = "\n".join(fake.commands)
    assert "psql -d 'portal;main'" in joined
    assert "plan_code = '3_months'" in joined
    assert "manual_reconcile" in joined
    assert "brain-secret" not in joined
    assert fake.closed is True
