from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLIENT_ROOT = REPO_ROOT.parent / "POKROV-app"
ANDROID_OUTPUT_ROOT = CLIENT_ROOT / "apps" / "android_shell" / "build" / "app" / "outputs" / "flutter-apk"
DEFAULT_ANDROID_APK = ANDROID_OUTPUT_ROOT / "app-arm64-v8a-release.apk"
DEFAULT_ANDROID_ARMEABI_V7A_APK = ANDROID_OUTPUT_ROOT / "app-armeabi-v7a-release.apk"
DEFAULT_ANDROID_X86_64_APK = ANDROID_OUTPUT_ROOT / "app-x86_64-release.apk"
DEFAULT_ANDROID_UNIVERSAL_APK = ANDROID_OUTPUT_ROOT / "app-release.apk"
WINDOWS_OUTPUT_ROOT = CLIENT_ROOT / "apps" / "windows_shell" / "build" / "release_bundle"


def _newest_windows_setup() -> Path:
    candidates = [path for path in WINDOWS_OUTPUT_ROOT.glob("pokrov-windows-*-setup.exe") if path.is_file()]
    if candidates:
        return max(candidates, key=lambda path: path.stat().st_mtime_ns)
    return WINDOWS_OUTPUT_ROOT / "pokrov-windows-setup-x64.exe"


DEFAULT_WINDOWS_EXE = _newest_windows_setup()
DEFAULT_NOTES_FILE = REPO_ROOT / "docs" / "launch" / "open-beta-release-notes.md"
DEFAULT_DOCS_URL = "https://pokrov.space/install/"
DEFAULT_REPO = "Kiwunaka/pokrov"
DEFAULT_RELEASE_HANDOFF = CLIENT_ROOT / "artifacts" / "releases" / "release-handoff.json"
CANONICAL_ANDROID_APK_NAME = "pokrov-android-arm64-v8a.apk"
CANONICAL_ANDROID_ARMEABI_V7A_APK_NAME = "pokrov-android-armeabi-v7a.apk"
CANONICAL_ANDROID_X86_64_APK_NAME = "pokrov-android-x86_64.apk"
CANONICAL_ANDROID_UNIVERSAL_APK_NAME = "pokrov-android-universal.apk"
CANONICAL_WINDOWS_EXE_NAME = "pokrov-windows-setup-x64.exe"
PRERELEASE_TAG_RE = re.compile(
    r"^v?\d+\.\d+\.\d+-(?:beta|rc)(?:[.-][0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$",
    re.IGNORECASE,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _artifact_failures(path: Path, *, label: str, suffix: str) -> list[str]:
    artifact = Path(path)
    failures: list[str] = []
    if artifact.suffix.lower() != suffix:
        failures.append(f"{label} must have {suffix} extension: {artifact}")
    if not artifact.is_file():
        failures.append(f"{label} not found: {artifact}")
    return failures


def _normalize_sha256(value: object) -> str:
    return re.sub(r"[^0-9A-Fa-f]", "", str(value or "")).upper()


def _release_handoff_failures(
    release_handoff: Path | None,
    *,
    repo: str,
    tag: str,
    android_apk: Path,
    windows_exe: Path,
    android_variants: dict[str, Path] | None = None,
) -> list[str]:
    if release_handoff is None:
        return []
    path = Path(release_handoff)
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"release handoff could not be parsed: {path}: {exc}"]

    if isinstance(payload, dict) and payload.get("schema_version") == 2:
        release = payload.get("release")
        artifacts = payload.get("artifacts")
        if not isinstance(release, dict) or not isinstance(artifacts, list):
            return [f"strict-v2 release handoff is malformed: {path}"]

        failures: list[str] = []
        release_version = str(release.get("version") or "").strip()
        tag_version = str(tag or "").strip().removeprefix("v").split("-", 1)[0]
        if not release_version or release_version != tag_version:
            failures.append(
                f"strict-v2 release version does not match release tag {tag}: "
                f"expected {tag_version}, got {release_version or '<missing>'} from {path}"
            )

        planned: dict[tuple[str, str, str], tuple[str, Path, str]] = {
            ("android", "apk", "arm64-v8a"): (
                "Android arm64-v8a APK",
                Path(android_apk),
                CANONICAL_ANDROID_APK_NAME,
            ),
            ("windows", "exe", "x64"): (
                "Windows x64 EXE",
                Path(windows_exe),
                CANONICAL_WINDOWS_EXE_NAME,
            ),
        }
        variant_names = {
            "armeabi-v7a": CANONICAL_ANDROID_ARMEABI_V7A_APK_NAME,
            "x86_64": CANONICAL_ANDROID_X86_64_APK_NAME,
            "universal": CANONICAL_ANDROID_UNIVERSAL_APK_NAME,
        }
        for abi, source in (android_variants or {}).items():
            planned[("android", "apk", abi)] = (
                f"Android {abi} APK",
                Path(source),
                variant_names[abi],
            )

        declared: dict[tuple[str, str, str], dict[str, object]] = {}
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                failures.append(f"strict-v2 artifact #{index} is not an object in {path}")
                continue
            key = (
                str(artifact.get("platform") or "").strip(),
                str(artifact.get("kind") or "").strip(),
                str(artifact.get("architecture") or "").strip(),
            )
            if key in declared:
                failures.append(f"strict-v2 release handoff has duplicate artifact {key} in {path}")
                continue
            declared[key] = artifact

        for key, (label, source, canonical_name) in planned.items():
            artifact = declared.get(key)
            if artifact is None:
                failures.append(f"{label} is missing from strict-v2 release handoff {path}")
                continue
            expected_sha = _normalize_sha256(artifact.get("sha256"))
            actual_sha = _sha256(source)
            if len(expected_sha) != 64 or expected_sha != actual_sha:
                failures.append(
                    f"{label} SHA256 does not match strict-v2 release handoff for {tag}: "
                    f"expected {expected_sha or '<missing>'} from {path}, got {actual_sha} from {source}"
                )
            try:
                expected_size = int(artifact.get("size_bytes"))
            except (TypeError, ValueError):
                expected_size = -1
            actual_size = source.stat().st_size
            if expected_size != actual_size:
                failures.append(
                    f"{label} size does not match strict-v2 release handoff for {tag}: "
                    f"expected {expected_size} from {path}, got {actual_size} from {source}"
                )
            declared_name = str(artifact.get("file_name") or "").strip()
            if declared_name != canonical_name:
                failures.append(
                    f"{label} filename does not match canonical release asset: "
                    f"expected {canonical_name}, got {declared_name or '<missing>'} from {path}"
                )
            expected_url = f"https://github.com/{str(repo).strip()}/releases/download/{tag}/{canonical_name}"
            declared_url = str(artifact.get("public_url") or "").strip()
            if declared_url != expected_url:
                failures.append(
                    f"{label} public URL does not match planned tag {tag}: "
                    f"expected {expected_url}, got {declared_url or '<missing>'} from {path}"
                )

        for key in declared.keys() - planned.keys():
            failures.append(
                f"strict-v2 release handoff artifact {key} is not included in the GitHub release plan"
            )
        return failures

    handoff_tag = str(((payload.get("github_release") or {}) if isinstance(payload, dict) else {}).get("tag") or "").strip()
    if handoff_tag and handoff_tag != str(tag or "").strip():
        return []

    downloads = (payload.get("downloads") or {}) if isinstance(payload, dict) else {}
    windows_downloads = downloads.get("windows") or {} if isinstance(downloads, dict) else {}
    expected = {
        "Android APK": _normalize_sha256((downloads.get("android") or {}).get("sha256") if isinstance(downloads, dict) else ""),
        "Windows EXE": _normalize_sha256(
            windows_downloads.get("sha256") or windows_downloads.get("exe_sha256")
            if isinstance(windows_downloads, dict)
            else ""
        ),
    }
    actual = {
        "Android APK": (_sha256(Path(android_apk)), Path(android_apk)),
        "Windows EXE": (_sha256(Path(windows_exe)), Path(windows_exe)),
    }

    failures: list[str] = []
    for label, expected_sha in expected.items():
        actual_sha, source = actual[label]
        if expected_sha and expected_sha != actual_sha:
            failures.append(
                f"{label} SHA256 does not match release handoff for {tag}: "
                f"expected {expected_sha} from {path}, got {actual_sha} from {source}"
            )
    handoff_variants = (downloads.get("android") or {}).get("apk_variants") if isinstance(downloads, dict) else []
    expected_variant_hashes = {
        str(item.get("abi") or "").strip(): _normalize_sha256(item.get("sha256"))
        for item in (handoff_variants or [])
        if isinstance(item, dict)
    }
    for abi, source in (android_variants or {}).items():
        expected_sha = expected_variant_hashes.get(abi, "")
        if expected_sha:
            actual_sha = _sha256(source)
            if expected_sha != actual_sha:
                failures.append(
                    f"Android {abi} APK SHA256 does not match release handoff for {tag}: "
                    f"expected {expected_sha} from {path}, got {actual_sha} from {source}"
                )
    return failures


def _plan_failures(*, repo: str, tag: str, android_apk: Path, windows_exe: Path, notes_file: Path, docs_url: str) -> list[str]:
    failures: list[str] = []
    if not str(repo or "").strip() or "/" not in str(repo or ""):
        failures.append("GitHub repo must use owner/name format")
    if not PRERELEASE_TAG_RE.fullmatch(str(tag or "").strip()):
        failures.append("tag must be a beta/rc prerelease tag, for example v1.0.3-beta.1")
    failures.extend(_artifact_failures(Path(android_apk), label="Android APK", suffix=".apk"))
    failures.extend(_artifact_failures(Path(windows_exe), label="Windows EXE", suffix=".exe"))
    if not Path(notes_file).is_file():
        failures.append(f"release notes file not found: {Path(notes_file)}")
    if not str(docs_url or "").startswith(DEFAULT_DOCS_URL):
        failures.append("APP_DOCS_URL must stay under https://pokrov.space/install/")
    return failures


def _stage_dir_for_tag(tag: str) -> Path:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", str(tag or "").strip()).strip("-") or "release"
    return Path(tempfile.gettempdir()) / f"pokrov-release-{slug}"


def _ps_single_quote(value: Path | str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _copy_item_command(*, source: Path, destination: Path) -> str:
    return f"Copy-Item -LiteralPath {_ps_single_quote(source)} -Destination {_ps_single_quote(destination)} -Force"


def _artifact_info(source_path: Path, *, staged_path: Path, role: str) -> dict[str, object]:
    source = Path(source_path)
    staged = Path(staged_path)
    return {
        "role": role,
        "source_path": str(source),
        "source_filename": source.name,
        "path": str(staged),
        "filename": staged.name,
        "size_bytes": source.stat().st_size,
        "sha256": _sha256(source),
    }


def _gh_cli_status(gh_path: str | None = None) -> dict[str, object]:
    requested = None if gh_path is None else str(gh_path).strip()
    resolved = ""
    if requested is None:
        resolved = shutil.which("gh") or ""
    elif requested:
        resolved = shutil.which(requested) or (requested if Path(requested).is_file() else "")

    if resolved:
        return {
            "available": True,
            "path": resolved,
            "classification": "AVAILABLE",
            "next_action": "Run gh auth status and publish only after the release handoff is GO.",
        }
    return {
        "available": False,
        "path": requested or "",
        "classification": "BLOCKED_TOOL_MISSING",
        "next_action": "Install GitHub CLI (`gh`) and authenticate before running the printed release command.",
    }


def _build_plan(
    *,
    repo: str,
    tag: str,
    title: str,
    android_apk: Path,
    windows_exe: Path,
    notes_file: Path,
    docs_url: str,
    gh_path: str | None = None,
    stage_dir: Path | None = None,
    release_handoff: Path | None = None,
    android_armeabi_v7a_apk: Path | None = None,
    android_x86_64_apk: Path | None = None,
    android_universal_apk: Path | None = None,
) -> dict[str, object]:
    variant_sources = {
        abi: Path(path)
        for abi, path in (
            ("armeabi-v7a", android_armeabi_v7a_apk),
            ("x86_64", android_x86_64_apk),
            ("universal", android_universal_apk),
        )
        if path is not None
    }
    failures = _plan_failures(
        repo=repo,
        tag=tag,
        android_apk=android_apk,
        windows_exe=windows_exe,
        notes_file=notes_file,
        docs_url=docs_url,
    )
    for abi, path in variant_sources.items():
        failures.extend(_artifact_failures(path, label=f"Android {abi} APK", suffix=".apk"))
    if not failures:
        failures.extend(
            _release_handoff_failures(
                release_handoff,
                repo=repo,
                tag=tag,
                android_apk=Path(android_apk),
                windows_exe=Path(windows_exe),
                android_variants=variant_sources,
            )
        )
    if failures:
        raise SystemExit("GitHub release plan validation failed:\n" + "\n".join(f"- {failure}" for failure in failures))

    repo = repo.strip()
    tag = tag.strip()
    title = title.strip() or f"POKROV {tag.lstrip('v')}"
    android_apk = Path(android_apk)
    windows_exe = Path(windows_exe)
    notes_file = Path(notes_file)
    stage_dir = Path(stage_dir) if stage_dir else _stage_dir_for_tag(tag)
    staged_android_apk = stage_dir / CANONICAL_ANDROID_APK_NAME
    staged_android_variants = {
        "armeabi-v7a": stage_dir / CANONICAL_ANDROID_ARMEABI_V7A_APK_NAME,
        "x86_64": stage_dir / CANONICAL_ANDROID_X86_64_APK_NAME,
        "universal": stage_dir / CANONICAL_ANDROID_UNIVERSAL_APK_NAME,
    }
    staged_windows_exe = stage_dir / CANONICAL_WINDOWS_EXE_NAME
    release_base = f"https://github.com/{repo}/releases/download/{tag}"

    android_artifacts = [
        _artifact_info(android_apk, staged_path=staged_android_apk, role="android_arm64_apk"),
        *[
            _artifact_info(
                source,
                staged_path=staged_android_variants[abi],
                role=f"android_{abi.replace('-', '_')}_apk",
            )
            for abi, source in variant_sources.items()
        ],
    ]
    staged_android_paths = [Path(item["path"]) for item in android_artifacts]
    expected_variant_urls = {
        abi: f"{release_base}/{staged_android_variants[abi].name}" if abi in variant_sources else ""
        for abi in staged_android_variants
    }

    return {
        "mode": "plan_only",
        "note": "This helper does not publish or upload artifacts. Review gates before running the gh command manually.",
        "repo": repo,
        "tag": tag,
        "title": title,
        "draft": False,
        "prerelease": True,
        "artifacts": [
            *android_artifacts,
            _artifact_info(windows_exe, staged_path=staged_windows_exe, role="windows_exe"),
        ],
        "staging": {
            "directory": str(stage_dir),
            "note": "Run these commands before gh release create so GitHub asset URLs use canonical public filenames.",
            "commands": [
                f"New-Item -ItemType Directory -Force -Path {_ps_single_quote(stage_dir)} | Out-Null",
                _copy_item_command(source=android_apk, destination=staged_android_apk),
                *[
                    _copy_item_command(source=source, destination=staged_android_variants[abi])
                    for abi, source in variant_sources.items()
                ],
                _copy_item_command(source=windows_exe, destination=staged_windows_exe),
            ],
        },
        "expected_urls": {
            "APP_ANDROID_PLAY_URL": "",
            "APP_ANDROID_APK_URL": f"{release_base}/{staged_android_apk.name}",
            "APP_ANDROID_APK_ARM64_URL": f"{release_base}/{staged_android_apk.name}",
            "APP_ANDROID_APK_ARMEABI_V7A_URL": expected_variant_urls["armeabi-v7a"],
            "APP_ANDROID_APK_X86_64_URL": expected_variant_urls["x86_64"],
            "APP_ANDROID_APK_UNIVERSAL_URL": expected_variant_urls["universal"],
            "APP_WINDOWS_EXE_URL": f"{release_base}/{staged_windows_exe.name}",
            "APP_DOCS_URL": docs_url,
        },
        "tooling": {
            "gh": _gh_cli_status(gh_path),
        },
        "gh_command": [
            "gh",
            "release",
            "create",
            tag,
            *[str(path) for path in staged_android_paths],
            str(staged_windows_exe),
            "--repo",
            repo,
            "--title",
            title,
            "--notes-file",
            str(notes_file),
            "--prerelease",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a non-mutating GitHub Releases plan for POKROV split APK/EXE artifacts.")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repo in owner/name format.")
    parser.add_argument("--tag", required=True, help="Beta/rc release tag, for example v1.0.3-beta.1.")
    parser.add_argument("--title", default="", help="Release title. Defaults to POKROV <tag without v>.")
    parser.add_argument("--android-apk", default=str(DEFAULT_ANDROID_APK))
    parser.add_argument("--android-armeabi-v7a-apk", default=str(DEFAULT_ANDROID_ARMEABI_V7A_APK))
    parser.add_argument("--android-x86-64-apk", default=str(DEFAULT_ANDROID_X86_64_APK))
    parser.add_argument("--android-universal-apk", default=str(DEFAULT_ANDROID_UNIVERSAL_APK))
    parser.add_argument("--windows-exe", default=str(DEFAULT_WINDOWS_EXE))
    parser.add_argument("--notes-file", default=str(DEFAULT_NOTES_FILE))
    parser.add_argument("--docs-url", default=DEFAULT_DOCS_URL)
    parser.add_argument(
        "--stage-dir",
        default="",
        help="Optional local staging directory to use in the printed copy and gh commands. Defaults to a temp release directory.",
    )
    parser.add_argument(
        "--gh-path",
        default=None,
        help="Optional GitHub CLI path or command name to report in the non-mutating plan. The helper never executes it.",
    )
    parser.add_argument(
        "--release-handoff",
        default=str(DEFAULT_RELEASE_HANDOFF),
        help="Optional client release-handoff.json whose APK/EXE SHA256 values must match this plan when the tag matches.",
    )
    parser.add_argument(
        "--skip-release-handoff-check",
        action="store_true",
        help="Skip SHA256 comparison against the client release handoff. Use only when preparing a brand-new tag before handoff metadata exists.",
    )
    args = parser.parse_args()

    plan = _build_plan(
        repo=args.repo,
        tag=args.tag,
        title=args.title,
        android_apk=Path(args.android_apk),
        android_armeabi_v7a_apk=Path(args.android_armeabi_v7a_apk),
        android_x86_64_apk=Path(args.android_x86_64_apk),
        android_universal_apk=Path(args.android_universal_apk),
        windows_exe=Path(args.windows_exe),
        notes_file=Path(args.notes_file),
        docs_url=args.docs_url,
        gh_path=args.gh_path,
        stage_dir=Path(args.stage_dir) if str(args.stage_dir or "").strip() else None,
        release_handoff=None
        if args.skip_release_handoff_check
        else (Path(args.release_handoff) if str(args.release_handoff or "").strip() else None),
    )
    json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
