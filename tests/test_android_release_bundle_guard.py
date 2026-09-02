from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def _resolve_client_root(platform_checkout: Path) -> Path:
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


POKROV_APP_ROOT = _resolve_client_root(ROOT)


def _read_root(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def _read_pokrov_app(rel_path: str) -> str:
    return (POKROV_APP_ROOT / rel_path).read_text(encoding="utf-8")


def test_android_release_bundle_uses_canonical_pokrov_app_outputs() -> None:
    build_gradle = _read_pokrov_app("apps/android_shell/android/app/build.gradle")

    assert 'applicationId = "space.pokrov.pokrov_android_shell"' in build_gradle
    assert 'signingConfig = signingConfigs.debug' in build_gradle


def test_android_release_bundle_is_root_orchestrated_from_pokrov_app() -> None:
    release_gate_text = _read_root("scripts/release_gate_check.py")
    client_gate_text = _read_root("scripts/run_client_release_gate.py")
    deployment_text = _read_root("docs/operations/deployment-and-access.md")
    cutover_text = _read_pokrov_app("docs/operations/cutover-readiness.md")

    assert '"android-apk": "Client Android APK build",' in release_gate_text
    assert '"android-aab": "Client Android AAB build",' in release_gate_text
    assert '[sys.executable, "scripts/run_client_release_gate.py", "build", "--target", target],' in release_gate_text
    assert "def _resolve_client_root(platform_checkout: Path) -> Path:" in client_gate_text
    assert 'fields.get("branch") == "refs/heads/main"' in client_gate_text
    assert "CLIENT_ROOT = _resolve_client_root(REPO_ROOT)" in client_gate_text
    assert 'status.android_shell_root / "build" / "app" / "outputs" / "flutter-apk" / "app-release.apk"' in client_gate_text
    assert 'status.android_shell_root / "build" / "app" / "outputs" / "bundle" / "release" / "app-release.aab"' in client_gate_text
    assert "cwd=status.android_shell_root" in client_gate_text
    assert "raw Android wrapper artifacts are produced under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/build/app/outputs/...`" in deployment_text
    assert "store the active client-lane bundle under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/`" in deployment_text
    assert "| New public cutover | `BLOCKED_NO_PROMOTABLE_CANDIDATE`;" in cutover_text
    assert "build-4051 successor not created" in cutover_text
    assert (
        "| Final go/no-go | `NO_GO_EXACT_CANDIDATE_21_SERVICE_AVAILABILITY` |"
        in cutover_text
    )
