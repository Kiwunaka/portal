import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))


class _FakeResponse:
    def __init__(self, status: int, payload: dict):
        self.status = status
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def text(self):
        return json.dumps(self._payload)

    async def json(self, content_type=None):
        return self._payload


class _FakeSession:
    def __init__(self, owner):
        self.owner = owner

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def post(self, url, *, headers, json):
        self.owner.posts.append({"url": url, "headers": headers, "json": json})
        return _FakeResponse(self.owner.status, self.owner.payload)


class _FakeSessionFactory:
    def __init__(self, *, status=200, payload=None):
        self.status = status
        self.payload = payload or {"choices": [{"message": {"content": "Ответ из базы знаний."}}]}
        self.posts = []

    def __call__(self, *, timeout):
        self.timeout = timeout
        return _FakeSession(self)


class SupportAIServiceTests(unittest.TestCase):
    def _knowledge_path(self) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False)
        with tmp:
            json.dump(
                {
                    "version": "test",
                    "rules": ["Answer in Russian.", "Do not ask for card details."],
                    "fallback": {"body": "Escalate uncovered questions."},
                    "topics": [{"id": "trial", "body": "Trial duration is 5 days."}],
                },
                tmp,
            )
        return Path(tmp.name)

    def test_generate_support_reply_uses_deepseek_chat_and_redacts_private_input(self) -> None:
        import support_ai_service

        knowledge_path = self._knowledge_path()
        config = support_ai_service.SupportAIConfig(
            enabled=True,
            api_key="sk-test",
            api_base_url="https://api.deepseek.com",
            model="deepseek-v4-flash",
            timeout_seconds=7.0,
            knowledge_path=str(knowledge_path),
            max_user_chars=500,
            max_answer_chars=2000,
        )
        fake_factory = _FakeSessionFactory()
        try:
            reply = asyncio.run(
                support_ai_service.generate_support_reply(
                    "Мой email user@example.com, ссылка vless://secret-profile и карта 4111111111111111",
                    ticket_id=42,
                    user_tg_id=1001,
                    config=config,
                    session_factory=fake_factory,
                )
            )
        finally:
            knowledge_path.unlink(missing_ok=True)

        self.assertEqual(reply, "Ответ из базы знаний.")
        self.assertEqual(len(fake_factory.posts), 1)
        post = fake_factory.posts[0]
        self.assertEqual(post["url"], "https://api.deepseek.com/chat/completions")
        self.assertEqual(post["headers"]["Authorization"], "Bearer sk-test")
        self.assertEqual(post["json"]["model"], "deepseek-v4-flash")
        self.assertIn("compact structured format", post["json"]["messages"][0]["content"])
        user_payload = post["json"]["messages"][-1]["content"]
        self.assertIn("[email-redacted]", user_payload)
        self.assertIn("[private-link-redacted]", user_payload)
        self.assertIn("[digits-redacted]", user_payload)
        self.assertNotIn("user@example.com", user_payload)
        self.assertNotIn("vless://secret-profile", user_payload)

    def test_generate_support_reply_returns_none_when_disabled_or_http_fails(self) -> None:
        import support_ai_service

        disabled = support_ai_service.SupportAIConfig(enabled=False, api_key="sk-test")
        fake_factory = _FakeSessionFactory()
        reply = asyncio.run(
            support_ai_service.generate_support_reply(
                "trial?",
                ticket_id=1,
                user_tg_id=2,
                config=disabled,
                session_factory=fake_factory,
            )
        )
        self.assertIsNone(reply)
        self.assertEqual(fake_factory.posts, [])

        enabled = support_ai_service.SupportAIConfig(enabled=True, api_key="sk-test")
        failing_factory = _FakeSessionFactory(status=500, payload={"error": "bad"})
        reply = asyncio.run(
            support_ai_service.generate_support_reply(
                "trial?",
                ticket_id=1,
                user_tg_id=2,
                config=enabled,
                session_factory=failing_factory,
            )
        )
        self.assertIsNone(reply)
        self.assertEqual(len(failing_factory.posts), 1)

    def test_config_defaults_to_openrouter_deepseek_flash(self) -> None:
        import support_ai_service

        config = support_ai_service.SupportAIConfig.from_env({})

        self.assertEqual(config.api_base_url, "https://openrouter.ai/api/v1")
        self.assertEqual(config.model, "deepseek/deepseek-v4-flash")
        self.assertEqual(config.max_context_chars, 32000)
        self.assertEqual(config.openrouter_data_collection, "")

    def test_openrouter_data_collection_policy_is_optional(self) -> None:
        import support_ai_service

        knowledge_path = self._knowledge_path()
        try:
            default_config = support_ai_service.SupportAIConfig(
                enabled=True,
                api_key="sk-test",
                api_base_url="https://openrouter.ai/api/v1",
                knowledge_path=str(knowledge_path),
            )
            fake_factory = _FakeSessionFactory()
            asyncio.run(
                support_ai_service.generate_support_reply(
                    "Подключение не работает",
                    ticket_id=7,
                    user_tg_id=8,
                    config=default_config,
                    session_factory=fake_factory,
                )
            )
            self.assertNotIn("provider", fake_factory.posts[0]["json"])

            strict_config = support_ai_service.SupportAIConfig.from_env(
                {
                    "SUPPORT_AI_ENABLED": "true",
                    "SUPPORT_AI_API_KEY": "sk-test",
                    "SUPPORT_AI_KB_PATH": str(knowledge_path),
                    "SUPPORT_AI_OPENROUTER_DATA_COLLECTION": "deny",
                }
            )
            strict_factory = _FakeSessionFactory()
            asyncio.run(
                support_ai_service.generate_support_reply(
                    "Профиль пустой",
                    ticket_id=9,
                    user_tg_id=10,
                    config=strict_config,
                    session_factory=strict_factory,
                )
            )
            self.assertEqual(strict_factory.posts[0]["json"]["provider"], {"data_collection": "deny"})
        finally:
            knowledge_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
