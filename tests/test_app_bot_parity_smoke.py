from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def _resolve_client_root(platform_checkout: Path) -> Path:
    override = os.environ.get("POKROV_CLIENT_ROOT", "").strip()
    if override:
        client_root = Path(override).expanduser().resolve()
        if not client_root.is_dir():
            raise FileNotFoundError(f"POKROV_CLIENT_ROOT does not exist: {client_root}")
        return client_root

    completed = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=platform_checkout,
        check=True,
        capture_output=True,
        text=True,
    )
    platform_root = Path(completed.stdout.strip()).resolve().parent
    client_repo = platform_root.parent / "POKROV-app"
    worktrees = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=client_repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    for block in worktrees.strip().split("\n\n"):
        fields = dict(line.split(" ", 1) for line in block.splitlines() if " " in line)
        if fields.get("branch") == "refs/heads/main" and fields.get("worktree"):
            return Path(fields["worktree"]).resolve()
    return client_repo


CLIENT_ROOT = _resolve_client_root(ROOT)
SCRIPT_PATH = ROOT / "scripts" / "app_bot_parity_smoke.py"


def _load_smoke_module():
    spec = importlib.util.spec_from_file_location("app_bot_parity_smoke", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_app_bot_parity_static_smoke_is_green_for_current_contracts():
    smoke = _load_smoke_module()

    report = smoke.build_report(ROOT, CLIENT_ROOT)

    assert report["ok"] is True
    checks = {check["id"]: check for check in report["checks"]}
    for check_id in (
        "platform_app_first_endpoints",
        "client_app_first_adapter",
        "webapp_cabinet_and_support",
        "telegram_bonus_contract",
        "support_ticket_contract",
        "safe_redeem_guard",
        "bot_entrypoints_present",
    ):
        assert checks[check_id]["status"] == "PASS"

    assert checks["manual_real_telegram_parity"]["status"] == "MANUAL_OWNER_TEST"
    assert checks["manual_live_account_parity"]["status"] == "MANUAL_OWNER_TEST"
