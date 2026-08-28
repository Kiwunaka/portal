from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "remote_rebind_owned_awg_lab_ports.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "remote_rebind_owned_awg_lab_ports", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_replace_listen_port_changes_only_exact_directive() -> None:
    raw = b"[Interface]\nListenPort = 51820\nPrivateKey = secret\n"

    changed = MODULE._replace_listen_port(raw, expected=51820, target=4500)

    assert changed == b"[Interface]\nListenPort = 4500\nPrivateKey = secret\n"


@pytest.mark.parametrize(
    "raw",
    (
        b"[Interface]\nPrivateKey = secret\n",
        b"[Interface]\nListenPort = 51831\n",
        b"[Interface]\nListenPort = 51820\nListenPort = 51820\n",
    ),
)
def test_replace_listen_port_fails_closed_on_precondition_mismatch(raw: bytes) -> None:
    with pytest.raises(MODULE.RebindError, match="precondition"):
        MODULE._replace_listen_port(raw, expected=51820, target=4500)


def test_material_with_port_preserves_non_port_fields() -> None:
    raw = (
        b'{"private_key":"secret","peers":[{"address":"example.invalid",'
        b'"port":51831,"public_key":"peer"}]}'
    )

    endpoint = MODULE._material_with_port(raw, expected=51831, target=3478)

    assert endpoint["private_key"] == "secret"
    assert endpoint["peers"][0] == {
        "address": "example.invalid",
        "port": 3478,
        "public_key": "peer",
    }
