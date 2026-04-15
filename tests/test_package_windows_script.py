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

    assert '$outputBaseName = Get-ConfigScalar -path $exeConfigPath -key "output_base_file_name"' in script
    assert '$builtMsixPath = Join-Path $releaseRunnerDir "$outputBaseName.msix"' in script
    assert '$canonicalMsix = Join-Path $outDir "$outputBaseName.msix"' in script
    assert 'Find-Artifact -patterns @("*.msix") -description "Windows MSIX"' in script


def test_package_windows_script_rejects_github_publisher_url() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "$publisherUrl -match '^https://github\\.com/'" in script


def test_package_windows_script_checks_msix_manifest_for_legacy_branding() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    assert 'Join-Path $extractDir "AppxManifest.xml"' in script
    assert 'Copy-Item $msixPath -Destination $zipPath -Force' in script
    assert 'Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force' in script
    assert 'Application Id=' in script
    assert "Legacy public Windows residue detected in MSIX manifest." in script
