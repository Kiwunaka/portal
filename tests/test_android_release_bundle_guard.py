from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POKROV_APP_ROOT = ROOT.parent / "POKROV-app"


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
    assert 'DEFAULT_CLIENT_ROOT = REPO_ROOT.parent / "POKROV-app"' in client_gate_text
    assert 'CLIENT_ROOT = Path(os.getenv("POKROV_APP_ROOT", str(DEFAULT_CLIENT_ROOT)))' in client_gate_text
    assert 'status.android_shell_root / "build" / "app" / "outputs" / "flutter-apk" / "app-release.apk"' in client_gate_text
    assert 'status.android_shell_root / "build" / "app" / "outputs" / "bundle" / "release" / "app-release.aab"' in client_gate_text
    assert "cwd=status.android_shell_root" in client_gate_text
    assert "raw Android wrapper artifacts are produced under `C:/Users/kiwun/Documents/ai/POKROV-app/apps/android_shell/build/app/outputs/...`" in deployment_text
    assert "store the active client-lane bundle under `C:/Users/kiwun/Documents/ai/POKROV-app/artifacts/releases/pokrov-app/<version>/`" in deployment_text
    assert "public cutover approval: `outside-store beta only`" in cutover_text
    assert "public Android release approval: `outside-store beta with operator attestation`" in cutover_text
