from __future__ import annotations

import importlib.util
import io
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "remote_schedule_release_announcement.py"
)
SCRIPTS_DIR = str(MODULE_PATH.parent)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
SPEC = importlib.util.spec_from_file_location(
    "remote_schedule_release_announcement_test_module", MODULE_PATH
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class _Channel:
    def __init__(self, code: int) -> None:
        self._code = code

    def recv_exit_status(self) -> int:
        return self._code


class _Stream(io.BytesIO):
    def __init__(self, value: str, code: int = 0) -> None:
        super().__init__(value.encode())
        self.channel = _Channel(code)


class _RemoteFile(io.StringIO):
    def __init__(self, owner, path: str) -> None:
        super().__init__()
        self._owner = owner
        self._path = path

    def close(self) -> None:
        self._owner.files[self._path] = self.getvalue()
        super().close()


class _Sftp:
    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.modes: dict[str, int] = {}

    def file(self, path: str, mode: str):
        assert mode == "w"
        return _RemoteFile(self, path)

    def chmod(self, path: str, mode: int) -> None:
        self.modes[path] = mode

    def close(self) -> None:
        pass


class _Ssh:
    def __init__(self) -> None:
        self.commands: list[str] = []
        self.sftp = _Sftp()
        self.closed = False

    def exec_command(self, command: str, timeout: int = 60):
        self.commands.append(command)
        if "--property=LoadState" in command:
            output = "not-found"
        elif "--property=ActiveState,NextElapseUSecRealtime,Unit" in command:
            output = "ActiveState=active\nUnit=pokrov-release-announcement.service"
        else:
            output = "ok"
        return None, _Stream(output), _Stream("")

    def open_sftp(self) -> _Sftp:
        return self.sftp

    def close(self) -> None:
        self.closed = True


def test_scheduler_uses_brain_connection_and_persistent_guarded_timer(
    monkeypatch, capsys
) -> None:
    ssh = _Ssh()
    connection: dict[str, object] = {}

    def fake_connect_node(**kwargs):
        connection.update(kwargs)
        return ssh, "key"

    when = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    monkeypatch.setattr(MODULE, "connect_node", fake_connect_node)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "remote_schedule_release_announcement.py",
            "--brain-ip",
            "82.21.114.104",
            "--when",
            when,
            "--schedule-id",
            "release-1.1.5-test",
            "--title",
            "POKROV 1.1.5",
            "--summary",
            "Стабильное обновление доступно.",
            "--link",
            "https://pokrov.space/install/",
            "--telegram-text",
            "POKROV 1.1.5 доступен.",
        ],
    )

    assert MODULE.main() == 0
    assert connection["code"] == "brain"
    assert connection["user"] == "root"
    assert connection["host"] == "82.21.114.104"
    config_path = "/root/portal_bot/ops-schedules/release-1.1.5-test.json"
    assert ssh.sftp.modes[config_path] == 0o600
    assert json.loads(ssh.sftp.files[config_path])["delete_after_success"] is True
    command = next(item for item in ssh.commands if item.startswith("systemd-run"))
    assert "--timer-property=Persistent=true" in command
    assert "/root/portal_bot/release_announcement_job.py" in command
    assert ssh.closed is True
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is True
    assert result["guarded_actions"] == ["live_update.create", "broadcast.send"]
