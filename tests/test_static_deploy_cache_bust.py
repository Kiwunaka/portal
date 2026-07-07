import tempfile
import unittest
from pathlib import Path

from scripts.remote_deploy_brain_static_sites import _cache_bust_next_static_refs


class StaticDeployCacheBustTests(unittest.TestCase):
    def test_next_static_refs_get_release_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = root / "index.html"
            html.write_text(
                '<script src="/_next/static/chunks/a.js"></script>'
                '<link href="/_next/static/chunks/b.css" rel="stylesheet">',
                encoding="utf-8",
            )

            _cache_bust_next_static_refs(root, release_id="20260522010101", label="test")

            text = html.read_text(encoding="utf-8")
            self.assertIn("/_next/static/chunks/a.js?v=20260522010101", text)
            self.assertIn("/_next/static/chunks/b.css?v=20260522010101", text)

    def test_media_refs_do_not_get_release_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = root / "index.html"
            html.write_text(
                '<link rel="preload" href="/_next/static/media/font.woff2?v=old" as="font">'
                '<img src="/_next/static/media/logo.png">',
                encoding="utf-8",
            )

            _cache_bust_next_static_refs(root, release_id="20260522010101", label="test")

            text = html.read_text(encoding="utf-8")
            self.assertIn('/_next/static/media/font.woff2"', text)
            self.assertIn('/_next/static/media/logo.png"', text)
            self.assertNotIn("/_next/static/media/font.woff2?v=", text)
            self.assertNotIn("/_next/static/media/logo.png?v=", text)

    def test_existing_release_query_is_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = root / "index.html"
            html.write_text('<script src="/_next/static/chunks/a.js?v=old"></script>', encoding="utf-8")

            _cache_bust_next_static_refs(root, release_id="new", label="test")

            self.assertIn('/_next/static/chunks/a.js?v=new"', html.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
