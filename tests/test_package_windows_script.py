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
SCRIPT_PATH = POKROV_APP_ROOT / "scripts" / "build-windows-release.ps1"


def _read_root(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def _read_pokrov_app(rel_path: str) -> str:
    return (POKROV_APP_ROOT / rel_path).read_text(encoding="utf-8")


def test_package_windows_script_parses() -> None:
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"[void][scriptblock]::Create((Get-Content -Raw '{SCRIPT_PATH}'))",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_package_windows_script_builds_versioned_release_bundle() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert '$windowsReleaseConfigPath = Join-Path $root "config\\\\windows-release.seed.json"' in script
    assert '$bundleFolderName = $windowsReleaseConfig.bundle_folder_template.Replace("{version}", $version)' in script
    assert '$zipName = $windowsReleaseConfig.zip_name_template.Replace("{version}", $version)' in script
    assert '$installerName = $windowsReleaseConfig.installer_name_template.Replace("{version}", $version)' in script
    assert '$manifestName = $windowsReleaseConfig.manifest_name_template.Replace("{version}", $version)' in script


def test_package_windows_script_validates_runtime_and_metadata_contracts() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert 'Join-Path $PSScriptRoot "validate-seed.ps1"' in script
    assert 'Join-Path $PSScriptRoot "sync-pokrov-core-runtime.ps1"' in script
    assert "Missing expected Windows release outputs" in script
    assert "CompanyName must be" in script


def test_package_windows_script_writes_bundle_manifest() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "New-ReleaseManifestFileList" in script
    assert "installer_path" in script
    assert "installer_sha256" in script
    assert "ConvertTo-Json -Depth 6" in script
    assert 'Write-Host "Windows bundle ready."' in script


def test_package_windows_script_builds_unsigned_installer_exe_with_iexpress() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "iexpress.exe" in script
    assert "install-pokrov.ps1" in script
    assert "Expand-Archive -Path `$zipPath" in script
    assert "Programs\\\\POKROV" in script


def test_package_windows_script_is_documented_as_active_client_release_step() -> None:
    deployment_text = _read_root("docs/operations/deployment-and-access.md")
    developer_text = _read_root("docs/developer/developer-guide.md")
    cutover_text = _read_pokrov_app("docs/operations/cutover-readiness.md")

    assert "python scripts/run_client_release_gate.py build --target windows" in deployment_text
    assert "C:/Users/kiwun/Documents/ai/POKROV-app/docs/" in developer_text
    assert "apps/windows_shell/build/release_bundle/" in cutover_text
    assert "Windows release state: `unsigned outside-store beta setup EXE refreshed for 1.0.0-beta; live install/app-session smoke remains manual`" in cutover_text
    assert "public cutover approval: `blocked for a new candidate`" in cutover_text
    assert "public Windows release approval: `blocked pending trusted-signing PASS for the exact candidate`" in cutover_text
    assert "repo-backed alpha or beta archive: `allowed`" in cutover_text
