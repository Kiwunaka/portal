import asyncio
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
            "web_app": object(),
            "style": object(),
            "icon_custom_emoji_id": object(),
            "copy_text": object(),
        }

        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            for key, value in kwargs.items():
                setattr(self, key, value)

    class DummyInlineKeyboardMarkup:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            for key, value in kwargs.items():
                setattr(self, key, value)

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

        os.environ["DATABASE_URL"] = f"sqlite:///{db_uri_path}"
        os.environ["ADMIN_ID"] = "9999"
        os.environ["FEEDBACK_BOT_TOKEN"] = "feedback_test_token"
        os.environ["FEEDBACK_USERNAME"] = "pokrov_feedbackbot"
        os.environ["SUPPORT_USERNAME"] = "pokrov_supportbot"
        os.environ["TG_BTN_EMOJI_PRIMARY_ID"] = "5368324170671202286"
        os.environ["TG_BTN_EMOJI_SUCCESS_ID"] = "5373141891321699086"
        os.environ["TG_BTN_EMOJI_DANGER_ID"] = "5368324170671202299"

        _install_aiogram_stubs()

        for module_name in ("feedbackbot", "db", "models", "migrations", "config", "copy_catalog", "telegram_buttons"):
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
        for module_name in ("feedbackbot", "telegram_buttons", "aiogram", "aiogram.filters", "aiogram.types"):
            sys.modules.pop(module_name, None)

    def test_feedback_back_and_start_clear_pending_feedback_prompt(self) -> None:
        class _FakeUser:
            id = 1004

        class _FakeMessage:
            from_user = _FakeUser()

            def __init__(self) -> None:
                self.edits: list[tuple[str, dict]] = []
                self.answers: list[tuple[str, dict]] = []

            async def edit_text(self, text, **kwargs):
                self.edits.append((str(text), dict(kwargs)))

            async def answer(self, text, **kwargs):
                self.answers.append((str(text), dict(kwargs)))

        class _FakeCallback:
            from_user = _FakeUser()

            def __init__(self) -> None:
                self.message = _FakeMessage()
                self.answers: list[tuple[str, bool]] = []

            async def answer(self, text="", show_alert=False):
                self.answers.append((str(text), bool(show_alert)))

        self.feedbackbot.pending_feedback.add(1004)
        callback = _FakeCallback()
        asyncio.run(self.feedbackbot.fb_back_home(callback))
        self.assertNotIn(1004, self.feedbackbot.pending_feedback)

        self.feedbackbot.pending_feedback.add(1004)
        message = _FakeMessage()
        asyncio.run(self.feedbackbot.start(message))
        self.assertNotIn(1004, self.feedbackbot.pending_feedback)

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

    def test_feedbackbot_keyboards_use_modern_button_fields_when_supported(self) -> None:
        telegram_buttons = importlib.import_module("telegram_buttons")
        if not telegram_buttons.SUPPORTS_BTN_STYLE:
            self.skipTest("aiogram InlineKeyboardButton has no style field")

        menu_buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in self.feedbackbot._menu_markup(is_admin=True).inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(menu_buttons["fb_new"], "style", None), telegram_buttons.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(menu_buttons["fb_admin_queue"], "style", None), telegram_buttons.BTN_STYLE_PRIMARY)
        if telegram_buttons.SUPPORTS_BTN_ICON:
            self.assertEqual(getattr(menu_buttons["fb_new"], "icon_custom_emoji_id", None), "5373141891321699086")

        entry_buttons = {
            str(getattr(button, "callback_data", "") or ""): button
            for row in self.feedbackbot._entry_keyboard(42).inline_keyboard
            for button in row
        }
        self.assertEqual(getattr(entry_buttons["fb_feature_42"], "style", None), telegram_buttons.BTN_STYLE_SUCCESS)
        self.assertEqual(getattr(entry_buttons["fb_delete_42"], "style", None), telegram_buttons.BTN_STYLE_DANGER)
        if telegram_buttons.SUPPORTS_BTN_ICON:
            self.assertEqual(getattr(entry_buttons["fb_delete_42"], "icon_custom_emoji_id", None), "5368324170671202299")

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


if __name__ == "__main__":
    unittest.main()
