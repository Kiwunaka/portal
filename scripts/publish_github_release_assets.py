from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CLIENT_ROOT = REPO_ROOT.parent / "POKROV-app"
DEFAULT_ANDROID_APK = CLIENT_ROOT / "apps" / "android_shell" / "build" / "app" / "outputs" / "flutter-apk" / "app-release.apk"
DEFAULT_WINDOWS_EXE = (
    CLIENT_ROOT
    / "apps"
    / "windows_shell"
    / "build"
    / "release_bundle"
    / "pokrov-windows-beta-x64-0.2.0-beta.1-setup.exe"
)
DEFAULT_NOTES_FILE = REPO_ROOT / "docs" / "launch" / "open-beta-release-notes.md"
DEFAULT_DOCS_URL = "https://pokrov.space/install/"
DEFAULT_REPO = "Kiwunaka/POKROV-app"
CANONICAL_ANDROID_APK_NAME = "pokrov-android-universal.apk"
CANONICAL_WINDOWS_EXE_NAME = "pokrov-windows-setup-x64.exe"
GITHUB_API_BASE = "https://api.github.com"
GO_MARKER = "GO for public beta publication"
NO_GO_MARKER = "NO-GO"
ARTIFACT_STAGING_MARKER = "ARTIFACT STAGING GO FOR RUNTIME SMOKE"
NO_RUNTIME_SYNC_MARKER = "NO RUNTIME SYNC OR ANNOUNCEMENT"
NON_URL_P0_GREEN_MARKER = "NON-URL P0 GATES GREEN FOR ARTIFACT STAGING"
ONLY_RUNTIME_URL_SMOKE_MARKER = "ONLY REMAINING P0 GATE: RUNTIME APP-DOWNLOAD URL SMOKE"
ARTIFACT_STAGING_BLOCKER_MARKERS = (
    "BLOCKED_BY_ACCESS",
    "POST_DEPLOY_ONLY_BLOCKED_BY_ACCESS",
    "EXTERNAL_DEPENDENCY",
    "NOT_DONE_LOCAL_PLAN_READY_NO_GO",
    "safe_to_publish_public_beta=false",
    "safe_to_enable_paid_checkout=false",
)
BETA_TAG_RE = re.compile(r"^v?0\.\d+\.\d+-[0-9A-Za-z.-]*beta[0-9A-Za-z.-]*(?:\+[0-9A-Za-z.-]+)?$")


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


def _plan_failures(*, repo: str, tag: str, android_apk: Path, windows_exe: Path, notes_file: Path, docs_url: str) -> list[str]:
    failures: list[str] = []
    if not str(repo or "").strip() or "/" not in str(repo or ""):
        failures.append("GitHub repo must use owner/name format")
    if not BETA_TAG_RE.fullmatch(str(tag or "").strip()):
        failures.append("tag must be a 0.x.x beta tag, for example v0.2.0-beta.1")
    failures.extend(_artifact_failures(Path(android_apk), label="Android APK", suffix=".apk"))
    failures.extend(_artifact_failures(Path(windows_exe), label="Windows EXE", suffix=".exe"))
    if not Path(notes_file).is_file():
        failures.append(f"release notes file not found: {Path(notes_file)}")
    if not str(docs_url or "").startswith(DEFAULT_DOCS_URL):
        failures.append("APP_DOCS_URL must stay under https://pokrov.space/install/")
    return failures


def _token_from_env(env: dict[str, str] | None = None) -> str:
    source = os.environ if env is None else env
    return str(source.get("GITHUB_TOKEN") or source.get("GH_TOKEN") or "").strip()


def _gh_cli_authenticated() -> bool:
    gh = shutil.which("gh")
    if not gh:
        return False
    try:
        completed = subprocess.run(
            [gh, "auth", "status"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def _go_evidence_failure(path: Path | None) -> str:
    if path is None:
        return "GO evidence file is required for --execute"
    evidence_path = Path(path)
    if not evidence_path.is_file():
        return f"GO evidence file not found: {evidence_path}"
    text = evidence_path.read_text(encoding="utf-8", errors="replace")
    if GO_MARKER in text and NO_GO_MARKER not in text:
        return ""
    if ARTIFACT_STAGING_MARKER in text:
        if NO_RUNTIME_SYNC_MARKER not in text:
            return "artifact staging evidence must explicitly contain `NO RUNTIME SYNC OR ANNOUNCEMENT`"
        if NON_URL_P0_GREEN_MARKER not in text:
            return "artifact staging evidence must explicitly contain `NON-URL P0 GATES GREEN FOR ARTIFACT STAGING`"
        if ONLY_RUNTIME_URL_SMOKE_MARKER not in text:
            return "artifact staging evidence must explicitly contain `ONLY REMAINING P0 GATE: RUNTIME APP-DOWNLOAD URL SMOKE`"
        for blocker in ARTIFACT_STAGING_BLOCKER_MARKERS:
            if blocker in text:
                return f"artifact staging evidence still contains blocking marker `{blocker}`"
        return ""
    if GO_MARKER not in text or NO_GO_MARKER in text:
        return "GO evidence file is not a public-beta GO handoff"
    return ""


def _asset_info(source_path: Path, *, upload_name: str, role: str, content_type: str) -> dict[str, Any]:
    source = Path(source_path)
    return {
        "role": role,
        "source_path": str(source),
        "source_filename": source.name,
        "upload_name": upload_name,
        "size_bytes": source.stat().st_size,
        "sha256": _sha256(source),
        "content_type": content_type,
    }


def build_publish_plan(
    *,
    repo: str,
    tag: str,
    title: str,
    android_apk: Path,
    windows_exe: Path,
    notes_file: Path,
    docs_url: str,
    execute: bool,
    go_evidence_file: Path | None,
    env: dict[str, str] | None = None,
    gh_authenticated: bool = False,
) -> dict[str, Any]:
    failures = _plan_failures(
        repo=repo,
        tag=tag,
        android_apk=Path(android_apk),
        windows_exe=Path(windows_exe),
        notes_file=Path(notes_file),
        docs_url=docs_url,
    )
    if failures:
        raise SystemExit("GitHub release publish validation failed:\n" + "\n".join(f"- {failure}" for failure in failures))

    token = _token_from_env(env)
    release_auth_ready = bool(token) or bool(gh_authenticated)
    if execute:
        go_failure = _go_evidence_failure(go_evidence_file)
        if go_failure:
            raise SystemExit(go_failure)
        if not release_auth_ready:
            raise SystemExit("GitHub release auth is required for --execute: use authenticated `gh` CLI or GITHUB_TOKEN/GH_TOKEN.")

    repo = repo.strip()
    tag = tag.strip()
    title = title.strip() or f"POKROV {tag.lstrip('v')}"
    release_base = f"https://github.com/{repo}/releases/download/{tag}"
    return {
        "mode": "execute" if execute else "dry_run",
        "classification": "READY_TO_PUBLISH" if execute else "DRY_RUN",
        "repo": repo,
            "tag": tag,
        "title": title,
        "draft": False,
        "prerelease": True,
        "notes_file": str(Path(notes_file)),
        "go_evidence_file": str(Path(go_evidence_file)) if go_evidence_file else "",
        "token": {
            "present": bool(token),
            "source": "GITHUB_TOKEN_OR_GH_TOKEN" if token else "",
        },
        "github_cli": {
            "authenticated": bool(gh_authenticated),
        },
        "release_auth": {
            "ready": release_auth_ready,
            "methods": [
                method
                for method, enabled in (
                    ("GITHUB_TOKEN_OR_GH_TOKEN", bool(token)),
                    ("gh_cli_keyring", bool(gh_authenticated)),
                )
                if enabled
            ],
        },
        "execute_requirements": [
            "Current release handoff must contain `GO for public beta publication` and must not contain `NO-GO`, or the evidence file must contain `ARTIFACT STAGING GO FOR RUNTIME SMOKE`, `NON-URL P0 GATES GREEN FOR ARTIFACT STAGING`, `ONLY REMAINING P0 GATE: RUNTIME APP-DOWNLOAD URL SMOKE`, and `NO RUNTIME SYNC OR ANNOUNCEMENT` without unresolved blocker markers.",
            "Authenticated GitHub CLI (`gh auth status`) or GITHUB_TOKEN/GH_TOKEN must be available.",
            "Use --execute only after the release handoff is GO or after narrow artifact-staging authorization; dry-run is the default. Executed releases are public prereleases so runtime download smoke can verify stable GitHub asset URLs.",
        ],
        "assets": [
            _asset_info(
                Path(android_apk),
                upload_name=CANONICAL_ANDROID_APK_NAME,
                role="android_apk",
                content_type="application/vnd.android.package-archive",
            ),
            _asset_info(
                Path(windows_exe),
                upload_name=CANONICAL_WINDOWS_EXE_NAME,
                role="windows_exe",
                content_type="application/vnd.microsoft.portable-executable",
            ),
        ],
        "expected_urls": {
            "APP_ANDROID_PLAY_URL": "",
            "APP_ANDROID_APK_URL": f"{release_base}/{CANONICAL_ANDROID_APK_NAME}",
            "APP_WINDOWS_EXE_URL": f"{release_base}/{CANONICAL_WINDOWS_EXE_NAME}",
            "APP_DOCS_URL": docs_url,
        },
    }


class UrlLibGithubApi:
    def _headers(self, token: str, *, content_type: str = "application/json") -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type,
            "User-Agent": "POKROV-release-helper",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def create_release(self, *, repo: str, token: str, payload: dict[str, object]) -> dict[str, object]:
        url = f"{GITHUB_API_BASE}/repos/{repo}/releases"
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers=self._headers(token), method="POST")
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def upload_asset(
        self,
        *,
        upload_url: str,
        token: str,
        name: str,
        path: Path,
        content_type: str,
    ) -> dict[str, object]:
        base_url = upload_url.split("{", 1)[0]
        query = urllib.parse.urlencode({"name": name})
        url = f"{base_url}?{query}"
        data = Path(path).read_bytes()
        request = urllib.request.Request(
            url,
            data=data,
            headers=self._headers(token, content_type=content_type),
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))


class SubprocessGithubCli:
    def create_release(
        self,
        *,
        repo: str,
        tag: str,
        title: str,
        notes_file: Path,
        asset_paths: list[Path],
    ) -> dict[str, Any]:
        gh = shutil.which("gh")
        if not gh:
            raise SystemExit("GitHub CLI (`gh`) was selected for publish but is not available on PATH.")
        command = [
            gh,
            "release",
            "create",
            tag,
            *[str(path) for path in asset_paths],
            "--repo",
            repo,
            "--title",
            title,
            "--notes-file",
            str(notes_file),
            "--prerelease",
        ]
        created = subprocess.run(command, text=True, capture_output=True, check=False, timeout=180)
        if created.returncode != 0:
            message = (created.stderr or created.stdout or "gh release create failed").strip()
            raise SystemExit(message)

        release_url = created.stdout.strip()
        release_id = None
        uploaded_assets: list[dict[str, Any]] = []
        view = subprocess.run(
            [gh, "release", "view", tag, "--repo", repo, "--json", "databaseId,url,assets"],
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        if view.returncode == 0 and view.stdout.strip():
            payload = json.loads(view.stdout)
            release_id = payload.get("databaseId")
            release_url = payload.get("url") or release_url
            for asset in payload.get("assets") or []:
                uploaded_assets.append(
                    {
                        "name": asset.get("name", ""),
                        "browser_download_url": asset.get("url", ""),
                        "size_bytes": asset.get("size", 0),
                    }
                )
        return {
            "release_id": release_id,
            "release_url": release_url,
            "uploaded_assets": uploaded_assets,
        }


def _publish_with_gh_cli(plan: dict[str, Any], *, github_cli: Any | None = None) -> dict[str, Any]:
    cli = github_cli or SubprocessGithubCli()
    with tempfile.TemporaryDirectory(prefix=f"pokrov-gh-release-{plan['tag']}-") as temp_root:
        temp_dir = Path(temp_root)
        staged_assets: list[Path] = []
        for asset in plan["assets"]:
            staged = temp_dir / asset["upload_name"]
            shutil.copy2(Path(asset["source_path"]), staged)
            staged_assets.append(staged)

        published = cli.create_release(
            repo=plan["repo"],
            tag=plan["tag"],
            title=plan["title"],
            notes_file=Path(plan["notes_file"]),
            asset_paths=staged_assets,
        )

    uploaded_by_name = {asset.get("name"): asset for asset in published.get("uploaded_assets") or []}
    uploaded_assets = []
    for asset in plan["assets"]:
        observed = uploaded_by_name.get(asset["upload_name"], {})
        uploaded_assets.append(
            {
                "name": asset["upload_name"],
                "browser_download_url": observed.get("browser_download_url") or plan["expected_urls"].get(
                    "APP_ANDROID_APK_URL" if asset["role"] == "android_apk" else "APP_WINDOWS_EXE_URL",
                    "",
                ),
                "sha256": asset["sha256"],
                "size_bytes": observed.get("size_bytes") or asset["size_bytes"],
            }
        )
    return {
        "mode": "execute",
        "classification": "PUBLISHED_PRERELEASE",
        "release_id": published.get("release_id"),
        "release_url": published.get("release_url", ""),
        "uploaded_assets": uploaded_assets,
        "expected_urls": plan["expected_urls"],
        "publish_method": "gh_cli",
    }


def publish_from_plan(
    plan: dict[str, Any],
    *,
    token: str,
    github_api: Any | None = None,
    github_cli: Any | None = None,
) -> dict[str, Any]:
    if plan.get("mode") != "execute":
        raise SystemExit("Refusing to publish from a dry-run plan; rebuild with --execute after GO evidence is green.")
    if not str(token or "").strip():
        if plan.get("github_cli", {}).get("authenticated"):
            return _publish_with_gh_cli(plan, github_cli=github_cli)
        raise SystemExit("GitHub release auth is required for publish_from_plan.")

    api = github_api or UrlLibGithubApi()
    notes_body = Path(plan["notes_file"]).read_text(encoding="utf-8")
    release = api.create_release(
        repo=plan["repo"],
        token=token,
        payload={
            "tag_name": plan["tag"],
            "name": plan["title"],
            "body": notes_body,
            "draft": False,
            "prerelease": True,
        },
    )
    upload_url = str(release["upload_url"])
    uploaded_assets = []
    for asset in plan["assets"]:
        uploaded = api.upload_asset(
            upload_url=upload_url,
            token=token,
            name=asset["upload_name"],
            path=Path(asset["source_path"]),
            content_type=asset["content_type"],
        )
        uploaded_assets.append(
            {
                "name": uploaded.get("name", asset["upload_name"]),
                "browser_download_url": uploaded.get("browser_download_url", ""),
                "sha256": asset["sha256"],
                "size_bytes": asset["size_bytes"],
            }
        )
    return {
        "mode": "execute",
        "classification": "PUBLISHED_PRERELEASE",
        "release_id": release.get("id"),
        "release_url": release.get("html_url", ""),
        "uploaded_assets": uploaded_assets,
        "expected_urls": plan["expected_urls"],
        "publish_method": "github_rest",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a GitHub prerelease and upload POKROV APK/EXE assets only after explicit GO evidence."
    )
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repo in owner/name format.")
    parser.add_argument("--tag", required=True, help="Release tag. Must stay on the 0.x.x-beta line, for example v0.2.0-beta.1.")
    parser.add_argument("--title", default="", help="Release title. Defaults to POKROV <tag without v>.")
    parser.add_argument("--android-apk", default=str(DEFAULT_ANDROID_APK))
    parser.add_argument("--windows-exe", default=str(DEFAULT_WINDOWS_EXE))
    parser.add_argument("--notes-file", default=str(DEFAULT_NOTES_FILE))
    parser.add_argument("--docs-url", default=DEFAULT_DOCS_URL)
    parser.add_argument("--go-evidence-file", default="", help="Required with --execute. Must be a GO handoff or explicit artifact-staging authorization.")
    parser.add_argument("--execute", action="store_true", help="Actually create a GitHub prerelease and upload assets.")
    args = parser.parse_args()

    plan = build_publish_plan(
        repo=args.repo,
        tag=args.tag,
        title=args.title,
        android_apk=Path(args.android_apk),
        windows_exe=Path(args.windows_exe),
        notes_file=Path(args.notes_file),
        docs_url=args.docs_url,
        execute=args.execute,
        go_evidence_file=Path(args.go_evidence_file) if str(args.go_evidence_file or "").strip() else None,
        gh_authenticated=_gh_cli_authenticated(),
    )
    if args.execute:
        result = publish_from_plan(plan, token=_token_from_env())
    else:
        result = plan
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
