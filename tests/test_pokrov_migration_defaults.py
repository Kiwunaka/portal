from pathlib import Path
import json
import os
import re
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
CLIENT_REPO_MARKERS = (
    "README.md",
    "melos.yaml",
    "config/product-contract.seed.json",
    "config/release-handoff.seed.json",
    "docs/README.md",
)


def _validated_client_repo(candidate: Path, *, source: str) -> Path:
    resolved = candidate.expanduser().resolve()
    assert resolved.is_dir(), f"POKROV-app {source} repository is absent at {resolved}"
    missing = [
        marker for marker in CLIENT_REPO_MARKERS
        if not (resolved / marker).exists()
    ]
    assert not missing, (
        f"POKROV-app {source} repository at {resolved} is missing markers: "
        + ", ".join(missing)
    )
    return resolved


def _resolve_pokrov_app_repo(platform_checkout: Path = ROOT) -> Path:
    if "POKROV_APP_REPO" in os.environ:
        override = os.environ["POKROV_APP_REPO"]
        assert override.strip(), (
            "POKROV_APP_REPO must be a non-blank path when present"
        )
        return _validated_client_repo(
            Path(override),
            source="override",
        )

    completed = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=platform_checkout,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, (
        "cannot resolve the platform common Git directory from "
        f"{platform_checkout.resolve()}: {completed.stderr.strip()}"
    )
    common_git_dir = Path(completed.stdout.strip()).resolve()
    assert common_git_dir.name == ".git" and (common_git_dir / "HEAD").exists(), (
        f"unexpected platform common Git directory: {common_git_dir}"
    )
    platform_repo_root = common_git_dir.parent
    sibling = platform_repo_root.parent / "POKROV-app"
    assert sibling.is_dir(), (
        f"POKROV-app sibling repository is absent at {sibling.resolve()}"
    )
    return _validated_client_repo(sibling, source="sibling")


POKROV_APP_ROOT = _resolve_pokrov_app_repo()
LEGACY_PUBLIC_MARKERS = (
    "portal-privacy.online",
    "kiwunaka.space",
    "portal_service_bot",
    "portal_privacy_helpbot",
    "portalfeedbackbot",
    "PORTAL ENTRY",
)


def _read_root(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def _read_pokrov_app(rel_path: str) -> str:
    return (POKROV_APP_ROOT / rel_path).read_text(encoding="utf-8")


def _without_legacy_marker_catalog(text: str) -> str:
    return re.sub(r"export const LEGACY_PUBLIC_MARKERS = \[(?:.|\n)*?\] as const;\n?", "", text)


def _assert_no_legacy_markers(label: str, text: str) -> None:
    for marker in LEGACY_PUBLIC_MARKERS:
        assert marker not in text, f"{label} still contains legacy public marker: {marker}"


def test_backend_and_web_defaults_point_to_pokrov_surface() -> None:
    shared_portal_text = _read_root("shared/portal-config.ts")
    config_text = _read_root("portal_bot/config.py")
    web_portal_text = _read_root("webapp/src/lib/portal.ts")
    marketing_portal_text = _read_root("marketing/src/lib/pokrov.ts")

    assert "pokrov.space" in config_text
    assert "api.pokrov.space" in config_text
    assert "app.pokrov.space" in config_text
    assert "connect.pokrov.space" in config_text
    assert "pay.pokrov.space" in config_text
    assert 'CLIENT_BRAND: str = (os.getenv("CLIENT_BRAND") or "POKROV Network").strip()' in config_text
    assert 'MAIN_BOT_USERNAME: str = (os.getenv("MAIN_BOT_USERNAME") or os.getenv("BOT_USERNAME") or "pokrov_vpnbot").lstrip("@")' in config_text
    assert 'NEWS_CHANNEL_URL: str = (os.getenv("NEWS_CHANNEL_URL") or "https://t.me/pokrov_vpn").strip()' in config_text
    assert "pokrov_feedbackbot" in config_text
    assert "network_marker_legacy_metadata" in _read_root("shared/product-facts.json")
    assert "export const CANONICAL_CLIENT_BRAND = PRODUCT_FACTS.brands.client;" in shared_portal_text
    assert "export const CANONICAL_CHECKOUT_URL = stripTrailingSlash(SURFACES.checkout);" in shared_portal_text
    assert "export const CANONICAL_PAY_ORIGIN = new URL(CANONICAL_CHECKOUT_URL).origin;" in shared_portal_text
    assert "export const CANONICAL_CONNECT_URL = stripTrailingSlash(SURFACES.connect);" in shared_portal_text
    assert "export const CANONICAL_FEEDBACK_BOT_URL = TELEGRAM.feedback_bot;" in shared_portal_text
    assert "CANONICAL_CLIENT_BRAND" in web_portal_text
    assert "CANONICAL_CHECKOUT_URL" in web_portal_text
    assert "CANONICAL_CONNECT_URL" in web_portal_text
    assert "getPortalPublicConfig" in web_portal_text
    assert "getCopyText" in web_portal_text
    assert "../../../shared/portal-config" in web_portal_text
    assert "../../../shared/copy" in web_portal_text
    assert "CANONICAL_CLIENT_BRAND" in marketing_portal_text
    assert "CANONICAL_CHECKOUT_URL" in marketing_portal_text
    assert "CANONICAL_CONNECT_URL" in marketing_portal_text
    assert "getPokrovPublicConfig" in marketing_portal_text
    assert "getCopyText" in marketing_portal_text
    assert "../../../shared/portal-config" in marketing_portal_text
    assert "../../../shared/copy" in marketing_portal_text
    _assert_no_legacy_markers("shared/portal-config.ts", _without_legacy_marker_catalog(shared_portal_text))
    _assert_no_legacy_markers("webapp/src/lib/portal.ts", _without_legacy_marker_catalog(web_portal_text))
    _assert_no_legacy_markers("marketing/src/lib/pokrov.ts", _without_legacy_marker_catalog(marketing_portal_text))
    _assert_no_legacy_markers("portal_bot/config.py", config_text)


def test_client_lane_docs_point_to_pokrov_app_as_development_truth() -> None:
    docs_index = _read_root("docs/README.md")
    system_overview = _read_root("docs/architecture/system-overview.md")
    developer_guide = _read_root("docs/developer/developer-guide.md")
    repository_map = _read_root("docs/developer/repository-map.md")
    app_next_summary = _read_root("docs/archive/client-lanes/app-next-bootstrap-summary.md")
    bridge_summary = _read_root("docs/archive/client-lanes/legacy-bridge-retirement-summary.md")
    repo_readme = _read_pokrov_app("README.md")
    app_readme = _read_pokrov_app("docs/README.md")
    app_cutover = _read_pokrov_app("docs/operations/cutover-readiness.md")

    assert "Active Android/Windows client truth lives only under `C:/Users/kiwun/Documents/ai/POKROV-app/docs/`" in docs_index
    assert "| `CANONICAL` | active client docs | `C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md` |" in docs_index
    assert "| `HISTORICAL_REFERENCE` | retired client lanes | `docs/archive/client-lanes/` |" in docs_index
    assert "`POKROV-app/main` is the only active client development and client-doc truth" in system_overview
    assert "`app-next/` is the retired bootstrap-source archive/reference workspace" in system_overview
    assert "`external/client-fork/app/` is the retired rollback/archive client reference workspace" in system_overview
    assert (
        "Active Android and Windows code, client documentation, and release artifacts\n"
        "  live in the sibling C:/Users/kiwun/Documents/ai/POKROV-app repository.\n"
        "  POKROV-app/main is the client promotion line."
    ) in developer_guide
    assert (
        "Client behavior changes also update\n"
        "C:/Users/kiwun/Documents/ai/POKROV-app/docs/. Do not rewrite archived client\n"
        "summaries unless their archive label or retained evidence changes."
    ) in developer_guide
    assert (
        "C:/Users/kiwun/Documents/ai/POKROV-app is the active Android/Windows\n"
        "  repository. Code, client docs, and current artifacts promote through\n"
        "  POKROV-app/main."
    ) in repository_map
    assert (
        "| Active client contracts | "
        "C:/Users/kiwun/Documents/ai/POKROV-app/docs/README.md |"
    ) in repository_map
    assert "Canonical client repository for POKROV on Android and Windows." in repo_readme
    assert (
        "`POKROV-app/main` is the active client-development\n"
        "and client-documentation line; retained bridge bundles are archive evidence."
    ) in repo_readme
    assert (
        "`POKROV-app/main` owns client implementation and client release-readiness."
    ) in app_readme
    assert (
        "Use history to answer why. Never let archive, completed plans, generated "
        "references, or old decisions determine what to implement now."
    ) in app_readme
    assert (
        "| Continuing source target | `PRE_CANDIDATE_LOCAL` on `POKROV-app/main` |"
        in app_cutover
    )
    assert (
        "Signed release-index `true`; source seed remains `false`; "
        "public release/store/stable pointer remain absent"
        in app_cutover
    )
    assert "| New public cutover | `BLOCKED` |" in app_cutover
    assert (
        "The existing `1.1.6` publication does not approve new `1.2.0` bytes."
        in app_cutover
    )
    assert (
        "Windows direct unsigned beta with mandatory SmartScreen warning"
        in app_cutover
    )
    assert "bootstrap source removed from active policy and active docs on `2026-04-23`" in app_next_summary
    assert "active client canon moved to `C:/Users/kiwun/Documents/ai/POKROV-app`" in bridge_summary
    assert "retained bridge artifacts were mirrored into `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/`" in bridge_summary


def test_root_release_orchestration_uses_wrappers_and_bridge_archive_mirror() -> None:
    release_gate_text = _read_root("scripts/release_gate_check.py")
    client_gate_text = _read_root("scripts/run_client_release_gate.py")
    deployment_text = _read_root("docs/operations/deployment-and-access.md")
    handoff_seed_text = _read_pokrov_app("config/release-handoff.seed.json")
    handoff_seed = json.loads(handoff_seed_text)

    assert '[sys.executable, "scripts/run_client_release_gate.py", "test", "--suite", suite],' in release_gate_text
    assert '[sys.executable, "scripts/run_client_release_gate.py", "build", "--target", target],' in release_gate_text
    assert "external/client-fork/app" not in release_gate_text
    assert "def _resolve_client_root(platform_checkout: Path) -> Path:" in client_gate_text
    assert 'fields.get("branch") == "refs/heads/main"' in client_gate_text
    assert "CLIENT_ROOT = _resolve_client_root(REPO_ROOT)" in client_gate_text
    assert "Run POKROV-app release gates from the platform repo." in client_gate_text
    assert "status.android_shell_root" in client_gate_text
    assert "status.windows_shell_root" in client_gate_text
    assert "versioned bridge bundle mirrors and checksums under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/bridge/<version>/`" in deployment_text
    assert "write the active client-lane bundle into `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/`" in deployment_text
    assert (
        handoff_seed["release_truth"]["retained_bridge_archive_root"]
        == "artifacts/releases/bridge/0.9.0-beta+20508"
    )
    assert (
        handoff_seed["release_truth"]["active_release_metadata"]
        == "artifacts/releases/release-handoff.json"
    )


def test_runtime_bot_defaults_use_new_pokrov_identities() -> None:
    api_text = _read_root("portal_bot/api.py")
    bot_text = _read_root("portal_bot/bot.py")
    helpbot_text = _read_root("portal_bot/helpbot.py")
    worker_text = _read_root("portal_bot/worker.py")
    redirect_text = _read_root("portal_bot/legacy_redirect_bot.py")
    webapp_e2e_text = _read_root("webapp/e2e/admin-gate.spec.ts")
    config_text = _read_root("portal_bot/config.py")

    assert "@pokrov_supportbot" in api_text
    assert "@pokrov_vpnbot" in api_text
    assert "api.pokrov.space" in api_text
    assert "pay.pokrov.space" in api_text
    assert 'or "pokrov_vpnbot"' in bot_text
    assert 'or "pokrov_supportbot"' in bot_text
    assert 'or "api.pokrov.space"' in bot_text
    assert 'or "pokrov_vpnbot"' in helpbot_text
    assert 'or "pokrov_vpnbot"' in worker_text
    assert 'or "pokrov_supportbot"' in worker_text
    assert 'or "pokrov_feedbackbot"' in config_text
    assert "connect.pokrov.space" in config_text
    assert "https://t.me/pokrov_vpnbot" in redirect_text
    assert "https://connect.pokrov.space/s8Kx2mP7qR4wT/mock_token" in webapp_e2e_text
    assert "https://t.me/pokrov_supportbot" in webapp_e2e_text
    assert "https://t.me/pokrov_vpnbot?start=ref_mock" in webapp_e2e_text
    assert 'or "pokrov_vpnbot"' in config_text
    assert "https://t.me/pokrov_vpn" in config_text


def _write_client_repo_markers(root: Path) -> None:
    for relative_path in (
        "README.md",
        "melos.yaml",
        "config/product-contract.seed.json",
        "config/release-handoff.seed.json",
        "docs/README.md",
    ):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("test marker\n", encoding="utf-8")


def test_pokrov_app_repo_override_is_absolute_validated_and_skips_git(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    client_root = tmp_path / "client" / "POKROV-app"
    _write_client_repo_markers(client_root)
    override = client_root.parent / "unused" / ".." / client_root.name
    monkeypatch.setenv("POKROV_APP_REPO", str(override))

    def fail_git(*args: object, **kwargs: object) -> object:
        raise AssertionError("git must not run when POKROV_APP_REPO is present")

    monkeypatch.setattr(subprocess, "run", fail_git)
    assert _resolve_pokrov_app_repo(ROOT) == client_root.resolve()


@pytest.mark.parametrize("override", ["", " ", "\t"])
def test_pokrov_app_repo_present_blank_override_is_rejected_before_path_lookup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    override: str,
) -> None:
    valid_cwd = tmp_path / "cwd-with-client-markers"
    _write_client_repo_markers(valid_cwd)
    monkeypatch.chdir(valid_cwd)
    monkeypatch.setenv("POKROV_APP_REPO", override)

    def fail_git(*args: object, **kwargs: object) -> object:
        raise AssertionError("present POKROV_APP_REPO must not fall back to Git")

    monkeypatch.setattr(subprocess, "run", fail_git)
    with pytest.raises(
        AssertionError,
        match=r"POKROV_APP_REPO must be a non-blank path when present",
    ):
        _resolve_pokrov_app_repo(ROOT)


def test_pokrov_app_repo_resolves_from_root_and_linked_worktree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("POKROV_APP_REPO", raising=False)
    completed = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    platform_root = Path(completed.stdout.strip()).resolve().parent
    expected = (platform_root.parent / "POKROV-app").resolve()

    assert _resolve_pokrov_app_repo(platform_root) == expected
    assert _resolve_pokrov_app_repo(ROOT) == expected


def test_pokrov_app_repo_missing_sibling_has_useful_assertion(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("POKROV_APP_REPO", raising=False)
    platform_root = tmp_path / "workspace" / "VPN"
    platform_root.mkdir(parents=True)
    subprocess.run(
        ["git", "init", "--quiet"],
        cwd=platform_root,
        check=True,
        capture_output=True,
        text=True,
    )

    with pytest.raises(
        AssertionError,
        match=r"POKROV-app sibling repository is absent.*POKROV-app",
    ):
        _resolve_pokrov_app_repo(platform_root)
