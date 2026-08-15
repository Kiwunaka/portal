from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scripts import remote_install_emergency_runtime as installer  # noqa: E402


def test_local_engine_pin_rejects_placeholder(tmp_path) -> None:
    candidate = tmp_path / "pokrov-sing-box-linux-amd64"
    candidate.write_bytes(b"placeholder")

    with pytest.raises(SystemExit, match="does not match"):
        installer._validate_local_engine(candidate)


def test_backup_and_restore_are_bounded_to_three_exact_targets() -> None:
    backup_root = "/root/pokrov-emergency-runtime-backups/20260815T120000Z-7"

    backup = installer._backup_command(backup_root=backup_root)
    restore = installer._restore_command(backup_root=backup_root)

    for target in (
        installer.REMOTE_ENGINE,
        installer.REMOTE_SERVICE,
        installer.REMOTE_TIMER,
    ):
        assert target in backup
        assert target in restore
    assert "install -D -m 0755" in restore
    assert restore.count("install -D -m 0644") == 2
    assert "rm -rf" not in restore


def test_release_id_is_safe_path_component() -> None:
    release_id = installer._release_id()

    assert release_id.count("/") == 0
    assert release_id.count("\\") == 0
    assert release_id.endswith(f"-{installer.os.getpid()}")


def test_geoip_unit_creates_its_sandbox_writable_directory() -> None:
    service = (
        Path(__file__).resolve().parents[1]
        / "infra"
        / "pokrov-emergency-geoip-refresh.service"
    ).read_text(encoding="utf-8")

    assert "StateDirectory=pokrov-geoip" in service
    assert "StateDirectoryMode=0755" in service
    assert "ReadWritePaths=/var/lib/pokrov-geoip" in service
