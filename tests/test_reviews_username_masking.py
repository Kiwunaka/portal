import importlib
import os
import sys
import unittest
import uuid
from pathlib import Path

from fastapi.testclient import TestClient


class ReviewsUsernameMaskingTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self.db_path = str((repo_root / f"portal_reviews_mask_test_{uuid.uuid4().hex}.db").resolve())
        db_uri_path = Path(self.db_path).as_posix()
        self._saved_env: dict[str, str | None] = {}
        for k in ("DATABASE_URL", "BOT_TOKEN", "ADMIN_ID", "SUPPORT_USERNAME"):
            self._saved_env[k] = os.environ.get(k)

        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"
        os.environ["BOT_TOKEN"] = "test_bot_token_123"
        os.environ["ADMIN_ID"] = "9999"
        os.environ["SUPPORT_USERNAME"] = "pokrov_supportbot"

        for module_name in ("api", "db", "models", "migrations", "config"):
            if module_name in sys.modules:
                sys.modules.pop(module_name, None)

        importlib.import_module("config")
        importlib.import_module("db")
        self.api = importlib.import_module("api")
        importlib.reload(self.api)

    def tearDown(self) -> None:
        try:
            from db import engine

            engine.dispose()
        except Exception:
            pass
        for k, v in self._saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        try:
            Path(self.db_path).unlink(missing_ok=True)
        except Exception:
            pass

    def test_mask_public_username_cases(self) -> None:
        self.assertEqual(self.api._mask_public_username("alexey"), "alex****")
        self.assertEqual(self.api._mask_public_username("mikhailovna"), "mikh****")
        self.assertEqual(self.api._mask_public_username("m"), "m****")
        self.assertEqual(self.api._mask_public_username("@neo"), "neo****")
        self.assertEqual(self.api._mask_public_username(""), "Пользователь")
        self.assertEqual(self.api._mask_public_username(None), "Пользователь")

    def test_api_reviews_masks_username_values(self) -> None:
        from db import SessionLocal
        from models import Review

        s = SessionLocal()
        try:
            s.add(Review(tg_id=1001, username="@neo", rating=5, text="Стабильно", is_featured=True))
            s.add(Review(tg_id=1002, username="", rating=4, text="Ок", is_featured=True))
            s.commit()
        finally:
            s.close()

        client = TestClient(self.api.app)
        r = client.get("/api/reviews")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        usernames = [str(x.get("username") or "") for x in body.get("reviews", [])]
        self.assertIn("neo****", usernames)
        self.assertIn("Пользователь", usernames)
        self.assertNotIn("neo@", "".join(usernames))

    def test_api_reviews_only_returns_featured_rows(self) -> None:
        from db import SessionLocal
        from models import Review

        s = SessionLocal()
        try:
            s.add(
                Review(
                    tg_id=1001,
                    username="mikhailovna",
                    rating=5,
                    text="Очень спокойно работает каждый день",
                    is_featured=True,
                )
            )
            s.add(
                Review(
                    tg_id=1002,
                    username="hidden_user",
                    rating=5,
                    text="Не должен попасть на сайт",
                    is_featured=False,
                )
            )
            s.commit()
        finally:
            s.close()

        client = TestClient(self.api.app)
        r = client.get("/api/reviews")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertEqual(len(body.get("reviews", [])), 1)
        self.assertEqual(body["reviews"][0]["username"], "mikh****")
        self.assertEqual(body["reviews"][0]["text"], "Очень спокойно работает каждый день")


if __name__ == "__main__":
    unittest.main()
