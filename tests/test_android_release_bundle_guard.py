from pathlib import Path


def test_android_release_bundle_cleans_stale_intermediary_bundle() -> None:
    build_gradle = Path(
        "external/client-fork/app/android/app/build.gradle"
    ).read_text(encoding="utf-8")

    assert "intermediary_bundle" in build_gradle
    assert 'task.name == "packageReleaseBundle"' in build_gradle
