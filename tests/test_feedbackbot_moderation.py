import importlib
import os
import sys
import types
import unittest
import uuid
from pathlib import Path


def _install_aiogram_stubs() -> None:
    class DummyFilter:
        def __getattr__(self, _name):
            return self

        def __invert__(self):
            return self

        def __and__(self, _other):
            return self

        def startswith(self, *_args, **_kwargs):
            return self

    class DummyRouter:
        def message(self, *_args, **_kwargs):
            def decorator(func):
                return func

            return decorator

        def callback_query(self, *_args, **_kwargs):
            def decorator(func):
                return func

            return decorator

    class DummyDispatcher:
        def include_router(self, *_args, **_kwargs):
            return None

        def resolve_used_update_types(self):
            return []

    class DummyBot:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class DummyInlineKeyboardButton:
        model_fields = {
            "text": object(),
            "callback_data": object(),
            "url": object(),
            "copy_text": object(),
            "style": object(),
            "icon_custom_emoji_id": object(),
        }

        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class DummyInlineKeyboardMarkup:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    aiogram = types.ModuleType("aiogram")
    aiogram.Bot = DummyBot
    aiogram.Dispatcher = DummyDispatcher
    aiogram.Router = DummyRouter
    aiogram.F = DummyFilter()

    aiogram_filters = types.ModuleType("aiogram.filters")
    aiogram_filters.CommandStart = lambda *args, **kwargs: object()

    aiogram_types = types.ModuleType("aiogram.types")
    aiogram_types.CallbackQuery = type("CallbackQuery", (), {})
    aiogram_types.InlineKeyboardButton = DummyInlineKeyboardButton
    aiogram_types.InlineKeyboardMarkup = DummyInlineKeyboardMarkup
    aiogram_types.Message = type("Message", (), {})

    sys.modules["aiogram"] = aiogram
    sys.modules["aiogram.filters"] = aiogram_filters
    sys.modules["aiogram.types"] = aiogram_types


class FeedbackBotModerationTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        portal_dir = str(repo_root / "portal_bot")
        if portal_dir not in sys.path:
            sys.path.insert(0, portal_dir)

        self.db_path = str((repo_root / f"portal_feedback_test_{uuid.uuid4().hex}.db").resolve())
        db_uri_path = Path(self.db_path).as_posix()
        self._saved_env: dict[str, str | None] = {}
        for key in (
            "DATABASE_URL",
            "ADMIN_ID",
            "FEEDBACK_BOT_TOKEN",
            "FEEDBACK_USERNAME",
            "SUPPORT_USERNAME",
            "TG_BTN_EMOJI_PRIMARY_ID",
            "TG_BTN_EMOJI_SUCCESS_ID",
            "TG_BTN_EMOJI_DANGER_ID",
        ):
            self._saved_env[key] = os.environ.get(key)
        self._saved_modules = {
            name: sys.modules.get(name)
            for name in ("aiogram", "aiogram.filters", "aiogram.types")
        }

        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"
        os.environ["ADMIN_ID"] = "9999"
        os.environ["FEEDBACK_BOT_TOKEN"] = "feedback_test_token"
        os.environ["FEEDBACK_USERNAME"] = "pokrov_feedbackbot"
        os.environ["SUPPORT_USERNAME"] = "pokrov_supportbot"
        os.environ["TG_BTN_EMOJI_PRIMARY_ID"] = "5368324170671202286"
        os.environ["TG_BTN_EMOJI_SUCCESS_ID"] = "5373141891321699086"
        os.environ["TG_BTN_EMOJI_DANGER_ID"] = "5368324170671202299"

        _install_aiogram_stubs()

        for module_name in ("feedbackbot", "telegram_buttons", "db", "models", "migrations", "config", "copy_catalog"):
            sys.modules.pop(module_name, None)

        importlib.import_module("config")
        importlib.import_module("db")
        self.feedbackbot = importlib.import_module("feedbackbot")

    def tearDown(self) -> None:
        try:
            from db import engine

            engine.dispose()
        except Exception:
            pass
        for key, value in self._saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        try:
            Path(self.db_path).unlink(missing_ok=True)
        except Exception:
            pass
        for name, module in self._saved_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def test_upsert_feedback_entry_reuses_pending_row(self) -> None:
        from db import SessionLocal

        session = SessionLocal()
        try:
            first = self.feedbackbot.upsert_feedback_entry(
                session,
                tg_id=1001,
                username="mikhailovna",
                text="Первый отзыв",
            )
            second = self.feedbackbot.upsert_feedback_entry(
                session,
                tg_id=1001,
                username="mikhailovna",
                text="Обновленный отзыв",
            )
            self.assertEqual(first.id, second.id)
            self.assertEqual(second.text, "Обновленный отзыв")
            self.assertEqual(second.status, "new")
        finally:
            session.close()

    def test_publish_feedback_entry_is_idempotent_and_links_review(self) -> None:
        from db import SessionLocal
        from models import Review

        session = SessionLocal()
        try:
            entry = self.feedbackbot.upsert_feedback_entry(
                session,
                tg_id=1002,
                username="mikhailovna",
                text="Очень нравится спокойный запуск",
            )
            published_entry, review = self.feedbackbot.publish_feedback_entry(session, entry.id)
            republished_entry, republished_review = self.feedbackbot.publish_feedback_entry(session, entry.id)

            self.assertEqual(published_entry.status, "published")
            self.assertIsNotNone(published_entry.review_id)
            self.assertEqual(review.id, republished_review.id)
            self.assertEqual(published_entry.review_id, republished_entry.review_id)
            self.assertEqual(session.query(Review).count(), 1)
            self.assertTrue(republished_review.is_featured)
        finally:
            session.close()

    def test_delete_feedback_entry_removes_linked_review(self) -> None:
        from db import SessionLocal
        from models import FeedbackEntry, Review

        session = SessionLocal()
        try:
            entry = self.feedbackbot.upsert_feedback_entry(
                session,
                tg_id=1003,
                username="neo",
                text="Можно сделать ещё проще вход",
            )
            published_entry, review = self.feedbackbot.publish_feedback_entry(session, entry.id)
            deleted = self.feedbackbot.delete_feedback_entry(session, published_entry.id)

            self.assertTrue(deleted)
            self.assertIsNone(session.query(FeedbackEntry).filter_by(id=published_entry.id).first())
            self.assertIsNone(session.query(Review).filter_by(id=review.id).first())
        finally:
            session.close()

    def test_feedback_menu_buttons_use_modern_telegram_fields(self) -> None:
        markup = self.feedbackbot._menu_markup(is_admin=True)
        rows = markup.kwargs["inline_keyboard"]

        self.assertEqual(rows[0][0].kwargs["style"], "success")
        self.assertEqual(rows[1][0].kwargs["style"], "primary")
        self.assertEqual(rows[2][0].kwargs["style"], "primary")
        self.assertEqual(rows[0][0].kwargs["icon_custom_emoji_id"], "5373141891321699086")
        self.assertEqual(rows[1][0].kwargs["icon_custom_emoji_id"], "5368324170671202286")
        self.assertEqual(rows[2][0].kwargs["icon_custom_emoji_id"], "5368324170671202286")

    def test_shared_telegram_button_helper_supports_copy_text(self) -> None:
        telegram_buttons = importlib.import_module("telegram_buttons")

        button = telegram_buttons.modern_inline_button(
            text="Скопировать",
            copy_text="https://connect.pokrov.space/sub/test",
        )

        self.assertEqual(button.kwargs["copy_text"], {"text": "https://connect.pokrov.space/sub/test"})
        self.assertNotIn("callback_data", button.kwargs)


if __name__ == "__main__":
    unittest.main()
