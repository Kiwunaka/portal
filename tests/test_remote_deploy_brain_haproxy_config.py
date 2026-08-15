from __future__ import annotations

import importlib.util
import shlex
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_module():
    path = SCRIPTS_DIR / "remote_deploy_brain_haproxy_config.py"
    spec = importlib.util.spec_from_file_location("remote_deploy_brain_haproxy_config", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class _Channel:
    def recv_exit_status(self) -> int:
        return 0


class _Stream:
    channel = _Channel()

    def read(self) -> bytes:
        return b""


class _Sftp:
    def __init__(self, files: dict[str, bytes]) -> None:
        self.files = files

    def put(self, source: str, target: str) -> None:
        self.files[target] = Path(source).read_bytes()

    def close(self) -> None:
        pass


class _Ssh:
    def __init__(self) -> None:
        self.commands: list[str] = []
        self.files: dict[str, bytes] = {}
        self.closed = False

    def exec_command(self, command: str, timeout: int):
        self.commands.append(command)
        return None, _Stream(), _Stream()

    def open_sftp(self):
        return _Sftp(self.files)

    def close(self) -> None:
        self.closed = True


def test_deploy_validates_backs_up_reloads_and_prunes(monkeypatch) -> None:
    module = _load_module()
    ssh = _Ssh()
    monkeypatch.setattr(module, "connect_node", lambda **_kwargs: (ssh, "password"))

    release_id = module.deploy(
        brain_ip="82.21.114.104",
        ssh_user="root",
        ssh_port=29374,
        passwords_path=Path("ignored"),
        source=REPO_ROOT / "infra" / "brain-haproxy-l4.cfg",
        remote_config="/etc/haproxy/haproxy.cfg",
    )

    uploaded = [path for path in ssh.files if path.startswith("/tmp/pokrov-haproxy-")]
    assert len(uploaded) == 1
    joined = "\n".join(ssh.commands)
    assert f"haproxy -c -f {shlex.quote(uploaded[0])}" in joined
    assert f"cp -a /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.bak-{release_id}" in joined
    assert f"install -m 0644 {shlex.quote(uploaded[0])} /etc/haproxy/haproxy.cfg" in joined
    assert "haproxy -c -f /etc/haproxy/haproxy.cfg" in joined
    assert "systemctl reload haproxy || systemctl restart haproxy" in joined
    assert "systemctl is-active haproxy" in joined
    assert "haproxy\\.cfg\\.bak\\-[0-9]{14}" in joined
    assert "head -n -5" in joined
    assert ssh.closed


def test_invalid_retention_or_remote_path_is_rejected() -> None:
    module = _load_module()

    for value in (0, 51):
        try:
            module._build_backup_prune_command("/etc/haproxy/haproxy.cfg", value)
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe retention was accepted")

    try:
        module._build_backup_prune_command("relative.cfg", 5)
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe remote path was accepted")
