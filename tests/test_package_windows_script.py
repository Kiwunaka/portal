from pathlib import Path
import subprocess


SCRIPT_PATH = Path("external/client-fork/app/scripts/package_windows.ps1")


def test_package_windows_script_parses() -> None:
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"[void][scriptblock]::Create((Get-Content -Raw '{SCRIPT_PATH.resolve()}'))",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_package_windows_script_canonicalizes_msix_output() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert 'Find-Artifact -pattern "*.msix" -description "Windows MSIX"' in script
    assert '$canonicalMsix = Join-Path $outDir "$appSlug-windows-setup-x64.msix"' in script


def test_package_windows_script_rejects_github_publisher_url() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "publisher_url:\\s*https://github\\.com/" in script


def test_package_windows_script_checks_msix_manifest_for_legacy_branding() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert 'Join-Path $msixInspectDir "AppxManifest.xml"' in script
    assert "Legacy Windows residue detected in MSIX manifest." in script
