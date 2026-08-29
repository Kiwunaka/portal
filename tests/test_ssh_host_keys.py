import sys
from pathlib import Path
from unittest import mock

import pytest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ssh_host_keys import OpenSshConfigSession  # noqa: E402


def test_open_ssh_config_session_enforces_noninteractive_trusted_connection() -> None:
    completed = mock.Mock(returncode=0, stdout="ok\n", stderr="")
    with mock.patch("ssh_host_keys.subprocess.run", return_value=completed) as run:
        result = OpenSshConfigSession("pokrov-brain").run("printf ok", input_text="request", timeout=17)

    assert result is completed
    argv = run.call_args.args[0]
    assert "BatchMode=yes" in argv
    assert "StrictHostKeyChecking=yes" in argv
    assert "ClearAllForwardings=yes" in argv
    assert "RequestTTY=no" in argv
    assert argv[-2:] == ["pokrov-brain", "printf ok"]
    assert run.call_args.kwargs["input"] == "request"
    assert run.call_args.kwargs["timeout"] == 17


@pytest.mark.parametrize("alias", ["", "-unsafe", "alias with spaces", "alias;command"])
def test_open_ssh_config_session_rejects_unsafe_alias(alias: str) -> None:
    with pytest.raises(ValueError, match="safe configured alias"):
        OpenSshConfigSession(alias)


def test_open_ssh_config_session_requires_existing_explicit_config(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="readable file"):
        OpenSshConfigSession("pokrov-brain", tmp_path / "missing")
