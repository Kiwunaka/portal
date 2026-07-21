import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.remote_deploy_brain_static_sites import _strip_next_static_cache_busting


class StaticDeployCacheNormalizeTests(unittest.TestCase):
    def test_vendored_telegram_sdk_matches_reviewed_official_v63(self) -> None:
        sdk = Path(__file__).resolve().parents[1] / "webapp" / "public" / "telegram-web-app.js"

        self.assertEqual(116510, sdk.stat().st_size)
        self.assertEqual(
            "3549138a7934039fe7dfd1291a4ee739bd2b705a614308053a8b08a87d85c451",
            hashlib.sha256(sdk.read_bytes()).hexdigest(),
        )

    def test_release_query_is_stripped_from_next_static_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = root / "index.html"
            html.write_text(
                '<script src="/_next/static/chunks/a.js?v=old"></script>'
                '<link href="/_next/static/chunks/b.css?v=old" rel="stylesheet">',
                encoding="utf-8",
            )

            _strip_next_static_cache_busting(root, label="test")

            text = html.read_text(encoding="utf-8")
            self.assertIn('/_next/static/chunks/a.js"', text)
            self.assertIn('/_next/static/chunks/b.css"', text)
            self.assertNotIn("?v=", text)

    def test_other_query_parameters_and_fragments_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = root / "index.html"
            html.write_text(
                '<script src="/_next/static/chunks/a.js?v=old&other=x#ready"></script>'
                '<link href="/_next/static/chunks/b.css?theme=dark&v=old&lang=ru" rel="stylesheet">',
                encoding="utf-8",
            )

            _strip_next_static_cache_busting(root, label="test")

            text = html.read_text(encoding="utf-8")
            self.assertIn('/_next/static/chunks/a.js?other=x#ready"', text)
            self.assertIn('/_next/static/chunks/b.css?theme=dark&lang=ru"', text)

    def test_clean_and_non_versioned_refs_are_left_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = root / "index.html"
            original = (
                '<script src="/_next/static/chunks/a.js?theme=dark"></script>'
                '<link rel="preload" href="/_next/static/media/font.woff2" as="font">'
            )
            html.write_text(original, encoding="utf-8")
            before_mtime = html.stat().st_mtime_ns

            _strip_next_static_cache_busting(root, label="test")

            self.assertEqual(html.read_text(encoding="utf-8"), original)
            self.assertEqual(html.stat().st_mtime_ns, before_mtime)

    def test_media_refs_lose_stale_release_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = root / "index.html"
            html.write_text(
                '<link rel="preload" href="/_next/static/media/font.woff2?v=old" as="font">'
                '<img src="/_next/static/media/logo.png">',
                encoding="utf-8",
            )

            _strip_next_static_cache_busting(root, label="test")

            text = html.read_text(encoding="utf-8")
            self.assertIn('/_next/static/media/font.woff2"', text)
            self.assertIn('/_next/static/media/logo.png"', text)
            self.assertNotIn("?v=", text)


if __name__ == "__main__":
    unittest.main()
