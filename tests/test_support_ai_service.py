import asyncio
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))


class _FakeResponse:
    def __init__(
        self,
        status: int,
        payload: dict,
        *,
        raw_body: bytes | None = None,
        content_length: int | None = None,
        stream_chunk_size: int = 4096,
    ):
        self.status = status
        self._payload = payload
        self._body = raw_body if raw_body is not None else json.dumps(payload).encode("utf-8")
        self.content_length = len(self._body) if content_length is None else content_length
        self.content = _FakeContent(self._body, stream_chunk_size=stream_chunk_size)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def text(self):
        return self._body.decode("utf-8")

    async def json(self, content_type=None):
        return self._payload


class _FakeContent:
    def __init__(self, body: bytes, *, stream_chunk_size: int):
        self.body = body
        self.stream_chunk_size = max(1, int(stream_chunk_size))
        self.requested_chunk_sizes: list[int] = []
        self.yielded_bytes = 0
        self.position = 0

    async def read(self, size: int) -> bytes:
        self.requested_chunk_sizes.append(int(size))
        if self.position >= len(self.body):
            return b""
        chunk_size = min(max(1, int(size)), self.stream_chunk_size)
        chunk = self.body[self.position : self.position + chunk_size]
        self.position += len(chunk)
        self.yielded_bytes += len(chunk)
        return chunk

    async def iter_chunked(self, size: int):
        self.requested_chunk_sizes.append(int(size))
        chunk_size = min(max(1, int(size)), self.stream_chunk_size)
        for start in range(0, len(self.body), chunk_size):
            chunk = self.body[start : start + chunk_size]
            self.yielded_bytes += len(chunk)
            yield chunk


class _FakeSession:
    def __init__(self, owner):
        self.owner = owner

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def post(self, url, *, headers, json):
        self.owner.posts.append({"url": url, "headers": headers, "json": json})
        response = _FakeResponse(
            self.owner.status,
            self.owner.payload,
            raw_body=self.owner.raw_body,
            content_length=self.owner.content_length,
            stream_chunk_size=self.owner.stream_chunk_size,
        )
        self.owner.responses.append(response)
        return response


class _FakeSessionFactory:
    def __init__(
        self,
        *,
        status=200,
        payload=None,
        raw_body: bytes | None = None,
        content_length: int | None = None,
        stream_chunk_size: int = 4096,
    ):
        self.status = status
        self.payload = payload or {"choices": [{"message": {"content": "Ответ из базы знаний."}}]}
        self.raw_body = raw_body
        self.content_length = content_length
        self.stream_chunk_size = stream_chunk_size
        self.posts = []
        self.responses: list[_FakeResponse] = []

    def __call__(self, *, timeout):
        self.timeout = timeout
        return _FakeSession(self)


class _RaisingSessionFactory:
    def __call__(self, *, timeout):
        self.timeout = timeout
        raise RuntimeError("provider request echoed private input")


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

    def test_openrouter_payload_has_openai_shape_and_no_identifiers(self) -> None:
        import support_ai_service

        knowledge_path = self._knowledge_path()
        config = support_ai_service.SupportAIConfig(
            enabled=True,
            api_key="sk-test",
            api_base_url="https://openrouter.ai/api/v1",
            model="deepseek-v4-flash-0731",
            reasoning_effort="medium",
            timeout_seconds=7.0,
            knowledge_path=str(knowledge_path),
            max_user_chars=500,
            max_answer_chars=2000,
            max_output_tokens=700,
        )
        fake_factory = _FakeSessionFactory()
        try:
            reply = asyncio.run(
                support_ai_service.generate_support_reply(
                    "Мой email user@example.com, ссылка vless://secret-profile и карта 4111111111111111",
                    ticket_id=424242,
                    user_tg_id=1001001,
                    config=config,
                    session_factory=fake_factory,
                )
            )
        finally:
            knowledge_path.unlink(missing_ok=True)

        self.assertEqual(reply, "Ответ из базы знаний.")
        self.assertEqual(len(fake_factory.posts), 1)
        post = fake_factory.posts[0]
        self.assertEqual(post["url"], "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(post["headers"]["Authorization"], "Bearer sk-test")
        self.assertEqual(
            set(post["json"]),
            {"model", "messages", "temperature", "n", "reasoning"},
        )
        self.assertEqual(post["json"]["model"], "deepseek/deepseek-v4-flash-0731")
        self.assertEqual(post["json"]["temperature"], 0.2)
        self.assertNotIn("max_tokens", post["json"])
        self.assertEqual(post["json"]["n"], 1)
        self.assertEqual(post["json"]["reasoning"], {"effort": "medium", "exclude": True})
        self.assertEqual([item["role"] for item in post["json"]["messages"]], ["system", "user"])
        self.assertIn("compact structured format", post["json"]["messages"][0]["content"])
        self.assertIn("Support knowledge JSON", post["json"]["messages"][0]["content"])
        user_payload = post["json"]["messages"][-1]["content"]
        self.assertIn("[email-redacted]", user_payload)
        self.assertIn("[private-link-redacted]", user_payload)
        self.assertIn("[digits-redacted]", user_payload)
        self.assertNotIn("user@example.com", user_payload)
        self.assertNotIn("vless://secret-profile", user_payload)
        serialized = json.dumps(post, ensure_ascii=False)
        self.assertNotIn("424242", serialized)
        self.assertNotIn("1001001", serialized)

    def test_support_sanitizer_redacts_private_categories(self) -> None:
        import support_ai_service

        telegram_hash = "a" * 64
        cases = [
            (
                "email",
                "Связь: person@private.invalid",
                "person@private.invalid",
                "[email-redacted]",
            ),
            (
                "proxy-link",
                "Профиль vless://opaque-user@edge.invalid:443?security=tls",
                "vless://opaque-user@edge.invalid:443?security=tls",
                "[private-link-redacted]",
            ),
            (
                "opaque-subscription-path",
                "https://edge.invalid/s8Kx2mP7qR4wT/",
                "https://edge.invalid/s8Kx2mP7qR4wT/",
                "[private-link-redacted]",
            ),
            (
                "sub-token-path",
                "https://edge.invalid/sub/AlphabeticOpaqueTokenValue",
                "https://edge.invalid/sub/AlphabeticOpaqueTokenValue",
                "[private-link-redacted]",
            ),
            (
                "short-camel-sub-token-path",
                "https://edge.invalid/sub/AbCdEfGhIjKl",
                "https://edge.invalid/sub/AbCdEfGhIjKl",
                "[private-link-redacted]",
            ),
            (
                "all-lower-sub-token-path",
                "https://edge.invalid/sub/abcdefghijkl",
                "https://edge.invalid/sub/abcdefghijkl",
                "[private-link-redacted]",
            ),
            (
                "subscription-token-path",
                "https://edge.invalid/subscription/MixedOpaqueTokenValue42",
                "https://edge.invalid/subscription/MixedOpaqueTokenValue42",
                "[private-link-redacted]",
            ),
            (
                "pokrov-opaque-token-path",
                "https://sub.pokrov.test/AlphabeticOpaqueTokenValue",
                "https://sub.pokrov.test/AlphabeticOpaqueTokenValue",
                "[private-link-redacted]",
            ),
            (
                "pokrov-lower-digit-token-path",
                "https://api.pokrov.test/connect/abcdefghijkl12",
                "https://api.pokrov.test/connect/abcdefghijkl12",
                "[private-link-redacted]",
            ),
            (
                "url-userinfo",
                "https://client-name:client-pass@edge.invalid/profile",
                "https://client-name:client-pass@edge.invalid/profile",
                "[private-link-redacted]",
            ),
            (
                "sensitive-query",
                "https://edge.invalid/profile?access_token=opaque-value",
                "https://edge.invalid/profile?access_token=opaque-value",
                "[private-link-redacted]",
            ),
            (
                "camel-sensitive-query",
                "https://edge.invalid/profile?authToken=opaque-value",
                "https://edge.invalid/profile?authToken=opaque-value",
                "[private-link-redacted]",
            ),
            (
                "bracket-sensitive-query",
                "https://edge.invalid/profile?token[]=opaque-value",
                "https://edge.invalid/profile?token[]=opaque-value",
                "[private-link-redacted]",
            ),
            (
                "sensitive-fragment",
                "https://edge.invalid/profile#access_token=opaque-value",
                "https://edge.invalid/profile#access_token=opaque-value",
                "[private-link-redacted]",
            ),
            (
                "percent-encoded-url",
                "https%3A%2F%2Fedge.invalid%2Fsubscription%2FAlphabeticOpaqueTokenValue",
                "AlphabeticOpaqueTokenValue",
                "[private-link-redacted]",
            ),
            (
                "double-percent-encoded-url",
                "https%253A%252F%252Fedge.invalid%252Fsub%252FNestedOpaqueTokenValue",
                "NestedOpaqueTokenValue",
                "[private-link-redacted]",
            ),
            (
                "json-escaped-url",
                r"https:\/\/edge.invalid\/subscription\/EscapedOpaqueTokenValue",
                "EscapedOpaqueTokenValue",
                "[private-link-redacted]",
            ),
            (
                "encoded-userinfo",
                "https://client%2Dname:client%2Dpass@edge.invalid/profile",
                "client%2Dpass",
                "[private-link-redacted]",
            ),
            (
                "backtick-wrapped-private-url",
                "`https://edge.invalid/sub/BacktickOpaqueTokenValue`",
                "BacktickOpaqueTokenValue",
                "[private-link-redacted]",
            ),
            (
                "smart-quoted-private-url",
                "“https://edge.invalid/sub/SmartQuoteOpaqueTokenValue”",
                "SmartQuoteOpaqueTokenValue",
                "[private-link-redacted]",
            ),
            (
                "email-inside-public-host-url",
                "https://docs.pokrov.space/contact/person@private.invalid",
                "person@private.invalid",
                "[private-link-redacted]",
            ),
            (
                "refresh-token-inside-public-host-url",
                "https://docs.pokrov.space/reference/pkr_rt_abcdefghijklmnop",
                "pkr_rt_abcdefghijklmnop",
                "[private-link-redacted]",
            ),
            (
                "recovery-code",
                "Код PKR-A2B3-C4D5-E6F7",
                "PKR-A2B3-C4D5-E6F7",
                "[recovery-code-redacted]",
            ),
            (
                "activation-key",
                "Ключ POKROV-A1B2-C3D4",
                "POKROV-A1B2-C3D4",
                "[activation-key-redacted]",
            ),
            (
                "uuid",
                "UUID 123e4567-e89b-12d3-a456-426614174000",
                "123e4567-e89b-12d3-a456-426614174000",
                "[uuid-redacted]",
            ),
            (
                "uuid-v7",
                "UUID 01890f3e-a7b2-7cc3-98c4-d5e6f7a8b9c0",
                "01890f3e-a7b2-7cc3-98c4-d5e6f7a8b9c0",
                "[uuid-redacted]",
            ),
            (
                "refresh-token",
                "pkr_rt_abcdefghijklmnopqrstuvwxyz0123456789_-",
                "pkr_rt_abcdefghijklmnopqrstuvwxyz0123456789_-",
                "[refresh-token-redacted]",
            ),
            (
                "signed-session",
                "eyJpZCI6MTAwMSwiZXhwIjoyMDAwMDAwMDAwfQ.ZXhhbXBsZS1zaWduYXR1cmUtMTIzNDU2Nzg5MA",
                "eyJpZCI6MTAwMSwiZXhwIjoyMDAwMDAwMDAwfQ.ZXhhbXBsZS1zaWduYXR1cmUtMTIzNDU2Nzg5MA",
                "[session-token-redacted]",
            ),
            (
                "jwt-session",
                "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMDAxIiwiZXhwIjoyMDAwMDAwMDAwfQ.c2lnbmF0dXJlLWJ5dGVzLTEyMzQ1Njc4OTA",
                "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMDAxIiwiZXhwIjoyMDAwMDAwMDAwfQ.c2lnbmF0dXJlLWJ5dGVzLTEyMzQ1Njc4OTA",
                "[session-token-redacted]",
            ),
            (
                "labelled-init-data",
                f"initData=query_id=AAExample&user=%7B%22id%22%3A1001%7D&auth_date=1700000000&hash={telegram_hash}",
                "AAExample",
                "[telegram-init-data-redacted]",
            ),
            (
                "webapp-init-data",
                f"tgWebAppData=query_id=DDExample&user=%7B%22id%22%3A1004%7D&auth_date=1700000003&hash={telegram_hash}",
                "DDExample",
                "[telegram-init-data-redacted]",
            ),
            (
                "header-init-data",
                f"X-Telegram-Init-Data: query_id=BBExample&user=%7B%22id%22%3A1002%7D&auth_date=1700000001&hash={telegram_hash}",
                "BBExample",
                "[telegram-init-data-redacted]",
            ),
            (
                "raw-init-data",
                f"query_id=CCExample&user=%7B%22id%22%3A1003%7D&auth_date=1700000002&hash={telegram_hash}",
                "CCExample",
                "[telegram-init-data-redacted]",
            ),
            (
                "raw-init-data-without-query-id",
                f"user=%7B%22id%22%3A1005%7D&auth_date=1700000004&hash={telegram_hash}",
                "1700000004",
                "[telegram-init-data-redacted]",
            ),
            (
                "decoded-user-raw-init-data",
                f'user={{"id":1007,"first_name":"Synthetic User"}}&auth_date=1700000011&hash={telegram_hash}',
                "Synthetic User",
                "[telegram-init-data-redacted]",
            ),
            (
                "minimal-raw-init-data",
                f"auth_date=1700000005&hash={telegram_hash}",
                "1700000005",
                "[telegram-init-data-redacted]",
            ),
            (
                "signed-raw-init-data",
                f"user=%7B%22id%22%3A1006%7D&auth_date=1700000006&signature=signed-value&hash={telegram_hash}",
                "signed-value",
                "[telegram-init-data-redacted]",
            ),
            (
                "raw-init-data-extra-fields",
                f"chat=synthetic-chat-payload&chat_instance=synthetic-chat-instance&user=%7B%22id%22%3A1008%7D&auth_date=1700000012&hash={telegram_hash}",
                "synthetic-chat-payload",
                "[telegram-init-data-redacted]",
            ),
            (
                "quoted-json-init-data",
                f'"initData": "auth_date=1700000007&hash={telegram_hash}"',
                "1700000007",
                "[telegram-init-data-redacted]",
            ),
            (
                "percent-encoded-init-data",
                f"tgWebAppData=auth_date%3D1700000008%26hash%3D{telegram_hash}",
                "1700000008",
                "[telegram-init-data-redacted]",
            ),
            (
                "raw-percent-encoded-init-data",
                f"auth_date%3D1700000009%26hash%3D{telegram_hash}",
                "1700000009",
                "[telegram-init-data-redacted]",
            ),
            (
                "percent-encoded-recovery-code",
                "PKR%2DA2B3%2DC4D5%2DE6F7",
                "A2B3%2DC4D5",
                "[recovery-code-redacted]",
            ),
            (
                "percent-encoded-activation-key",
                "POKROV%2DA1B2%2DC3D4",
                "A1B2%2DC3D4",
                "[activation-key-redacted]",
            ),
            (
                "percent-encoded-uuid",
                "123e4567%2De89b%2D12d3%2Da456%2D426614174000",
                "123e4567%2De89b",
                "[uuid-redacted]",
            ),
            (
                "compact-uuid",
                "123e4567e89b12d3a456426614174000",
                "123e4567e89b12d3a456426614174000",
                "[uuid-redacted]",
            ),
            (
                "percent-encoded-refresh-token",
                "pkr%5Frt%5Fabcdefghijklmnop",
                "abcdefghijklmnop",
                "[refresh-token-redacted]",
            ),
            (
                "percent-encoded-jwt",
                "eyJhbGciOiJub25lIn0%2EeyJpZCI6MX0%2Ec2lnbmVk",
                "eyJpZCI6MX0",
                "[session-token-redacted]",
            ),
            (
                "short-jwt",
                "eyJhbGciOiJub25lIn0.eyJpZCI6MX0.c2lnbmVk",
                "eyJpZCI6MX0",
                "[session-token-redacted]",
            ),
            (
                "unicode-email",
                "Почта “пользователь＠пример.рф”",
                "пользователь＠пример.рф",
                "[email-redacted]",
            ),
            (
                "unicode-code-separators",
                "Код PKR–A2B3  C4D5－E6F7",
                "A2B3  C4D5",
                "[recovery-code-redacted]",
            ),
            (
                "fullwidth-activation-key",
                "Ключ ＰＯＫＲＯＶ－Ａ１Ｂ２－Ｃ３Ｄ４",
                "ＰＯＫＲＯＶ",
                "[activation-key-redacted]",
            ),
            (
                "cyrillic-adjacent-code",
                "доPKR-A2B3-C4D5-E6F7после",
                "PKR-A2B3-C4D5-E6F7",
                "[recovery-code-redacted]",
            ),
            (
                "cyrillic-adjacent-uuid",
                "до123e4567-e89b-12d3-a456-426614174000после",
                "123e4567-e89b-12d3-a456-426614174000",
                "[uuid-redacted]",
            ),
            (
                "session-token-label",
                "session_token=synthetic-session-value",
                "synthetic-session-value",
                "[credential-redacted]",
            ),
            (
                "client-secret-label",
                r'client_secret=\"synthetic-client-value\"',
                "synthetic-client-value",
                "[credential-redacted]",
            ),
            (
                "russian-password-label",
                "пароль: «синтетическое-значение»",
                "синтетическое-значение",
                "[credential-redacted]",
            ),
            (
                "russian-access-token-label",
                "токен доступа = “синтетический-токен”",
                "синтетический-токен",
                "[credential-redacted]",
            ),
            (
                "basic-authorization",
                "Authorization: Basic QWxhZGRpbjpvcGVuU2VzYW1l",
                "QWxhZGRpbjpvcGVuU2VzYW1l",
                "[credential-redacted]",
            ),
            (
                "api-key-space-label",
                "API key: secret",
                "secret",
                "[credential-redacted]",
            ),
            (
                "wireguard-private-key",
                "PrivateKey = zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz=",
                "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz=",
                "[credential-redacted]",
            ),
            (
                "smart-quoted-private-key",
                "private_key: ‘synthetic-private-key-value’",
                "synthetic-private-key-value",
                "[credential-redacted]",
            ),
            (
                "zero-width-obfuscated-label",
                "p\u200brivate_k\u200bey=synthetic-zero-width-value",
                "synthetic-zero-width-value",
                "[credential-redacted]",
            ),
            (
                "idna-ideographic-stop-email",
                "Почта: synthetic-user@example。invalid",
                "synthetic-user@example。invalid",
                "[email-redacted]",
            ),
            (
                "cyrillic-adjacent-long-digits",
                "до4111 1111 1111 1111после",
                "4111 1111 1111 1111",
                "[digits-redacted]",
            ),
            (
                "placeholder-looking-password",
                "password=[email-redacted]",
                "[email-redacted]",
                "[credential-redacted]",
            ),
            (
                "untrusted-docs-host-token",
                "https://docs.attacker.invalid/sub/alllettertoken",
                "alllettertoken",
                "[private-link-redacted]",
            ),
            (
                "github-private-token",
                "https://github.com/example/repository?private_token=synthetic-query-value",
                "synthetic-query-value",
                "[private-link-redacted]",
            ),
            (
                "github-prefixed-private-token",
                "https://github.com/example/repository?x_private_token_v2=synthetic-prefixed-value",
                "synthetic-prefixed-value",
                "[private-link-redacted]",
            ),
            (
                "github-quoted-private-token",
                'https://github.com/example/repository?private_token="synthetic quoted value"',
                "synthetic quoted value",
                "[private-link-redacted]",
            ),
        ]
        for label in (
            "token",
            "access_token",
            "refresh_token",
            "api_key",
            "secret",
            "password",
            "hash",
            "authToken",
            "session_token",
            "client_secret",
        ):
            private_value = f"private-{label.replace('_', '-')}-value"
            cases.append(
                (
                    f"labelled-{label}",
                    f"{label}={private_value}",
                    private_value,
                    "[credential-redacted]",
                )
            )

        for case_name, source, private_value, placeholder in cases:
            with self.subTest(case=case_name):
                sanitized = support_ai_service.redact_support_text(source)
                self.assertTrue(placeholder in sanitized, case_name)
                self.assertFalse(private_value in sanitized, case_name)

    def test_support_sanitizer_structural_review_regressions(self) -> None:
        import support_ai_service

        ticket_uuid = "123e4567-e89b-12d3-a456-426614174000"
        short_jwt = "eyJhbGciOiJub25lIn0.eyJpZCI6MX0.c2lnbmVk"
        private_cases = [
            (
                "cyrillic-zero-width-api-key",
                "данные\u200bAPI key: synthetic-api-value",
                "synthetic-api-value",
            ),
            (
                "cyrillic-zero-width-private-key",
                "данные\u200bPrivateKey=synthetic-private-key-value",
                "synthetic-private-key-value",
            ),
            (
                "cyrillic-zero-width-private-token",
                "данные\u200bprivate_token=synthetic-private-token-value",
                "synthetic-private-token-value",
            ),
            (
                "trusted-host-trailing-dot",
                "https://docs.pokrov.space./sub/alllettertoken",
                "alllettertoken",
            ),
            (
                "trusted-host-leading-dot",
                "https://.docs.pokrov.space/sub/alllettertoken",
                "alllettertoken",
            ),
            (
                "semicolon-private-token",
                "https://github.com/example/repository?lang=ru;private_token=synthetic-semicolon-value",
                "synthetic-semicolon-value",
            ),
            (
                "nested-quoted-assignment",
                'https://github.com/example/repository?next="private_token=synthetic quoted value"',
                "synthetic quoted value",
            ),
            (
                "sensitive-key-nested-safe-url",
                "https://github.com/example/repository?private_token=https://github.com/public/reference",
                "private_token",
            ),
            (
                "keyless-jwt-fragment",
                f"https://github.com/example/repository#{short_jwt}",
                short_jwt,
            ),
            (
                "nested-vless-query",
                "https://github.com/example/repository?next=vless://opaque-user@edge.invalid:443",
                "opaque-user",
            ),
            (
                "nested-ss-fragment",
                "https://github.com/example/repository#next=ss://c3ludGhldGljLWNyZWRlbnRpYWw=",
                "c3ludGhldGljLWNyZWRlbnRpYWw=",
            ),
            (
                "encoded-nested-subscription-url",
                "https://github.com/example/repository?next=https%3A%2F%2Fedge.invalid%2Fsub%2FNestedOpaqueTokenValue",
                "NestedOpaqueTokenValue",
            ),
            (
                "trusted-host-ticket-uuid",
                f"https://docs.pokrov.space/tickets/{ticket_uuid}",
                ticket_uuid,
            ),
        ]
        for case_name, source, private_value in private_cases:
            with self.subTest(case=case_name):
                sanitized = support_ai_service.redact_support_text(source)
                self.assertEqual(sanitized, "[private-link-redacted]" if "://" in source else sanitized)
                self.assertNotIn(private_value, sanitized, case_name)
                self.assertTrue(
                    "[private-link-redacted]" in sanitized or "[credential-redacted]" in sanitized,
                    case_name,
                )

        punctuated = "До _vless://opaque-user@edge.invalid:443, после"
        self.assertEqual(
            support_ai_service.redact_support_text(punctuated),
            "До [private-link-redacted], после",
        )

        public_diagnostics = [
            "code=recovery_scope_forbidden",
            "код: recovery_scope_forbidden",
        ]
        for source in public_diagnostics:
            with self.subTest(public_diagnostic=source):
                self.assertEqual(support_ai_service.redact_support_text(source), source)

    def test_support_sanitizer_scans_raw_url_atoms_before_non_url_decoding(self) -> None:
        import support_ai_service

        commit = "0123456789abcdef0123456789abcdef01234567"
        encoded_safe = (
            "https%3A%2F%2Fgithub.com%2FKiwunaka%2FPOKROV-app%2Fcommit%2F" + commit
        )
        encoded_private = "https%3A%2F%2Fedge.invalid%2Fsub%2Fopaque-subscription-token"
        encoded_variants = [
            encoded_safe,
            encoded_safe.replace("%", "%25"),
            encoded_safe.replace("%", "%25").replace("%", "%25"),
            "%68%74%74%70%73%3A%2F%2Fgithub.com%2FKiwunaka%2FPOKROV-app%2Fcommit%2F"
            + commit,
            "%2568%2574%2574%2570%2573%253A%252F%252Fgithub.com%252FKiwunaka%252FPOKROV-app%252Fcommit%252F"
            + commit,
            "%252568%252574%252574%252570%252573%25253A%25252F%25252Fgithub.com%25252FKiwunaka%25252FPOKROV-app%25252Fcommit%25252F"
            + commit,
        ]
        for index, safe_url in enumerate(encoded_variants, start=1):
            with self.subTest(encoded_depth=index):
                self.assertEqual(support_ai_service.redact_support_text(safe_url), safe_url)

        delimiter_cases = [
            ("space", "%20", " "),
            ("tab", "%09", "\t"),
            ("newline", "%0A", "\n"),
            ("double-quote", "%22", '"'),
            ("single-quote", "%27", "'"),
            ("backtick", "%60", "`"),
        ]
        for case_name, encoded_delimiter, decoded_delimiter in delimiter_cases:
            source = encoded_safe + encoded_delimiter + encoded_private
            expected = encoded_safe + decoded_delimiter + "[private-link-redacted]"
            with self.subTest(delimiter=case_name):
                self.assertEqual(support_ai_service.redact_support_text(source), expected)

        direct_with_encoded_path = (
            "https://github.com/Kiwunaka/POKROV-app%2Fcommit%2F" + commit
        )
        self.assertEqual(
            support_ai_service.redact_support_text(direct_with_encoded_path),
            direct_with_encoded_path,
        )

        private_variants = [
            encoded_private,
            encoded_private.replace("%", "%25"),
            encoded_private.replace("%", "%25").replace("%", "%25"),
        ]
        for index, private_url in enumerate(private_variants, start=1):
            with self.subTest(private_depth=index):
                self.assertEqual(
                    support_ai_service.redact_support_text(private_url),
                    "[private-link-redacted]",
                )

    def test_support_sanitizer_rescans_mixed_percent_decoded_urls(self) -> None:
        import support_ai_service

        private_urls = [
            "https:%2F/edge.invalid/sub/abcdefghijkl",
            "h%74tps%3A%2F%2Fedge.invalid%2Fsub%2Fabcdefghijkl",
            "https://github.com%22@attacker.invalid/sub/abcdefghijkl",
            "https://github.com%22x@attacker.invalid/sub/abcdefghijkl",
            "https://github.com%20x@attacker.invalid/sub/abcdefghijkl",
            "https%2525252525253A%2525252525252F%2525252525252Fedge.invalid%2525252525252Fsub%2525252525252Fabcdefghijkl",
        ]
        for case_name, private_url in enumerate(private_urls):
            with self.subTest(case=case_name):
                self.assertEqual(
                    support_ai_service.redact_support_text(private_url),
                    "[private-link-redacted]",
                )

    def test_support_sanitizer_bounds_percent_rescan_work(self) -> None:
        import support_ai_service

        parts = []
        total = 0
        depth = 1
        while True:
            value = "https://edge.invalid/sub/abcdefghijkl"
            for _index in range(depth):
                value = quote(value, safe="")
            if total + len(value) + 1 > 65000:
                break
            parts.append(value)
            total += len(value) + 1
            depth += 3

        source = " ".join(parts)
        original_scanner = support_ai_service._redact_structured_spans
        original_decoder = support_ai_service._bounded_percent_decode
        decoded_chars = 0

        def count_decoded_chars(value):
            nonlocal decoded_chars
            decoded_chars += len(str(value or ""))
            return original_decoder(value)

        with patch.object(
            support_ai_service,
            "_bounded_percent_decode",
            side_effect=count_decoded_chars,
        ):
            with patch.object(
                support_ai_service,
                "_redact_structured_spans",
                wraps=original_scanner,
            ) as scan:
                sanitized = support_ai_service.redact_support_text(source)

        self.assertLessEqual(scan.call_count, len(parts) * 2 + 2)
        self.assertLessEqual(decoded_chars, len(source) * 10)
        self.assertLessEqual(len(sanitized), support_ai_service._MAX_SANITIZER_INPUT_CHARS)
        self.assertNotIn("edge.invalid", sanitized)
        self.assertNotIn("abcdefghijkl", sanitized)

    def test_support_sanitizer_detects_fully_encoded_telegram_before_url_atoms(self) -> None:
        import support_ai_service

        telegram_hash = "e" * 64
        raw_blob = (
            'initData=user={"id":1009,"url":"https://github.com/public/reference"}'
            f"&auth_date=1700000200&hash={telegram_hash}"
        )
        encoded_once = quote(raw_blob, safe="")
        encoded_variants = [
            encoded_once,
            quote(encoded_once, safe=""),
            quote(quote(encoded_once, safe=""), safe=""),
        ]
        for index, encoded_blob in enumerate(encoded_variants, start=1):
            with self.subTest(encoded_depth=index):
                self.assertEqual(
                    support_ai_service.redact_support_text(encoded_blob),
                    "[telegram-init-data-redacted]",
                )

        encoded_prose = quote("initData: empty; docs mention auth_date and hash placeholders", safe="")
        self.assertEqual(
            support_ai_service.redact_support_text(encoded_prose),
            "initData: empty; docs mention auth_date and hash placeholders",
        )

    def test_support_sanitizer_redacts_raw_telegram_init_data_before_url_atoms(self) -> None:
        import support_ai_service

        telegram_hash = "a" * 64
        source = (
            'initData=user={"id":1009,"first_name":"Private Person",'
            '"url":"https://github.com/public/reference"}'
            f"&auth_date=1700000200&hash={telegram_hash}"
        )

        sanitized = support_ai_service.redact_support_text(source)

        self.assertEqual(sanitized, "[telegram-init-data-redacted]")
        self.assertNotIn("Private Person", sanitized)

    def test_support_sanitizer_treats_left_labelled_url_as_private_value(self) -> None:
        import support_ai_service

        safe_url = "https://github.com/Kiwunaka/POKROV-app"
        cases = [
            (
                "private-token",
                f"private_token={safe_url}",
                "private_token=[private-link-redacted]",
            ),
            (
                "quoted-private-token-label",
                f'"private_token" = {safe_url}',
                '"private_token" = [private-link-redacted]',
            ),
            (
                "api-key-quoted-value",
                f'API key: "{safe_url}";',
                'API key: "[private-link-redacted]";',
            ),
            (
                "encoded-label-separator",
                f"client_secret%3D{safe_url}",
                "client_secret=[private-link-redacted]",
            ),
        ]
        for case_name, source, expected in cases:
            with self.subTest(case=case_name):
                self.assertEqual(support_ai_service.redact_support_text(source), expected)

        public_diagnostics = [
            f"code={safe_url}",
            "Diagnostic code=recovery_scope_forbidden",
            "Диагностика код: recovery_scope_forbidden",
        ]
        for source in public_diagnostics:
            with self.subTest(public=source):
                self.assertEqual(support_ai_service.redact_support_text(source), source)

    def test_support_sanitizer_rejects_malformed_or_confused_url_authority(self) -> None:
        import support_ai_service

        private_urls = [
            "https://github.com:notaport/Kiwunaka/POKROV-app",
            "https://github.com:70000/Kiwunaka/POKROV-app",
            "https://github.com./Kiwunaka/POKROV-app",
            "https://.github.com/Kiwunaka/POKROV-app",
            "https://github.com%2F@attacker.invalid/repository",
            "https://github.com%5C@attacker.invalid/repository",
            "https://github.com%23@attacker.invalid/sub/abc-def-ghi-jkl",
            "https://github.com%3F@attacker.invalid/sub/abc-def-ghi-jkl",
            "https://github.com/%2F%2Fattacker.invalid/repository",
            "https://github.com/@attacker.invalid/repository",
            "https://github.com%252F%2540attacker.invalid/repository",
            "https://github.com:/Kiwunaka/POKROV-app",
        ]
        for private_url in private_urls:
            with self.subTest(case=private_urls.index(private_url)):
                self.assertEqual(
                    support_ai_service.redact_support_text(private_url),
                    "[private-link-redacted]",
                )

        valid_port = "https://github.com:443/Kiwunaka/POKROV-app"
        self.assertEqual(support_ai_service.redact_support_text(valid_port), valid_port)

    def test_support_sanitizer_redacts_compacted_subscription_tokens(self) -> None:
        import support_ai_service

        private_cases = [
            (
                "https://edge.invalid/sub/opaque-subscription-token.",
                "[private-link-redacted].",
            ),
            (
                "https://edge.invalid/subscription/abcdefghijkl_123456,",
                "[private-link-redacted],",
            ),
            (
                "https://edge.invalid/sub/abc-def-ghi-jkl)",
                "[private-link-redacted])",
            ),
        ]
        for source, expected in private_cases:
            with self.subTest(source=source):
                self.assertEqual(support_ai_service.redact_support_text(source), expected)

        public_docs = "https://docs.pokrov.space/sub/opaque-subscription-token"
        self.assertEqual(support_ai_service.redact_support_text(public_docs), public_docs)

    def test_support_sanitizer_redacts_common_raw_tokens_and_pem_private_keys(self) -> None:
        import support_ai_service

        raw_tokens = [
            "ghp_" + ("A" * 36),
            "gho_" + ("B" * 36),
            "ghu_" + ("C" * 36),
            "ghs_" + ("D" * 36),
            "ghr_" + ("E" * 36),
            "github_pat_" + ("F" * 30),
            "glpat-" + ("G" * 24),
            "xoxb-123456789012-ABCDEFGHIJKLMNO",
            "AIza" + ("H" * 35),
        ]
        for index, raw_token in enumerate(raw_tokens):
            with self.subTest(token_shape=index):
                self.assertEqual(
                    support_ai_service.redact_support_text(f"prefix {raw_token} suffix"),
                    "prefix [secret-redacted] suffix",
                )

        pem_block = (
            "before\n"
            "-----BEGIN PRIVATE KEY-----\n"
            "U3ludGhldGljUHJpdmF0ZUtleUJsb2Nr\n"
            "-----END PRIVATE KEY-----\n"
            "after"
        )
        self.assertEqual(
            support_ai_service.redact_support_text(pem_block),
            "before\n[private-key-redacted]\nafter",
        )
        unclosed_pem = (
            "before\n-----BEGIN OPENSSH PRIVATE KEY-----\n"
            "U3ludGhldGljVW5jbG9zZWRLZXk="
        )
        self.assertEqual(
            support_ai_service.redact_support_text(unclosed_pem),
            "[content-truncated]",
        )
        public_key = "-----BEGIN PUBLIC KEY-----\nUHVibGljS2V5\n-----END PUBLIC KEY-----"
        self.assertEqual(support_ai_service.redact_support_text(public_key), public_key)
        self.assertEqual(support_ai_service.redact_support_text("AIza-short-public"), "AIza-short-public")

    def test_trailing_url_punctuation_split_has_linear_operation_count(self) -> None:
        import support_ai_service

        class CountingText(str):
            index_reads = 0
            slice_reads = 0

            def __getitem__(self, key):
                if isinstance(key, slice):
                    type(self).slice_reads += 1
                else:
                    type(self).index_reads += 1
                return super().__getitem__(key)

        trailing_count = 8192
        CountingText.index_reads = 0
        CountingText.slice_reads = 0
        source = CountingText("https://example.invalid/reference" + ("." * trailing_count))
        core, suffix = support_ai_service._split_trailing_url_punctuation(source)

        self.assertEqual(core, "https://example.invalid/reference")
        self.assertEqual(suffix, "." * trailing_count)
        self.assertEqual(CountingText.index_reads, trailing_count + 1)
        self.assertEqual(CountingText.slice_reads, 2)

    def test_support_sanitizer_preserves_safe_public_urls(self) -> None:
        import support_ai_service

        safe_urls = [
            "https://pokrov.space/",
            "https://docs.pokrov.space/help/getting-started?lang=ru",
            "https://github.com/Kiwunaka/POKROV-app/releases/tag/v1.0.0",
            "https://status.pokrov.space/public/subscription-guide",
            "https://github.com/Kiwunaka/POKROV-app/commit/0123456789abcdef0123456789abcdef01234567",
            "https://github.com/Kiwunaka/POKROV-app/commit/0123456789abcdef0123456789abcdef01234567?diff=split",
            "https://docs.pokrov.space/reference/123e4567-e89b-12d3-a456-426614174000",
            "https://docs.pokrov.space/reference/ABCDEFGHIJKLMNOPQRSTUVWXYZ123456",
            "https://docs.pokrov.space/sub/client-profile",
            "https://docs.pokrov.space/sub/abcdefghijkl",
            "`https://docs.pokrov.space/reference/123e4567-e89b-12d3-a456-426614174000`",
            "“https://docs.pokrov.space/sub/client-profile”",
        ]

        for safe_url in safe_urls:
            with self.subTest(url=safe_url):
                self.assertEqual(support_ai_service.redact_support_text(safe_url), safe_url)

    def test_support_sanitizer_bounds_normalization_work(self) -> None:
        import support_ai_service

        class OversizedText(str):
            def replace(self, *_args, **_kwargs):
                raise AssertionError("oversized-input-was-scanned")

        cases = [
            ("oversized-input", "A" * 200000),
            ("nfkc-expansion", "\ufdfa" * 10000),
        ]
        for case_name, source in cases:
            with self.subTest(case=case_name):
                sanitized = support_ai_service.redact_support_text(source)
                self.assertTrue("[content-truncated]" in sanitized, case_name)
                self.assertTrue(len(sanitized) <= 66000, case_name)

        oversized = OversizedText("A" * (support_ai_service._MAX_SANITIZER_INPUT_CHARS + 1))
        self.assertEqual(
            support_ai_service.redact_support_text(oversized),
            "[content-truncated]",
            "bound-before-materialization",
        )

    def test_support_sanitizer_nfkc_is_incremental_and_peak_bounded(self) -> None:
        import support_ai_service

        normalized_input_sizes: list[int] = []

        def expanding_nfkc(form: str, value: str) -> str:
            self.assertEqual(form, "NFKC")
            normalized_input_sizes.append(len(value))
            if len(value) > 1:
                raise AssertionError("nfkc-input-was-materialized")
            return value * 18

        legal_input = "A" * support_ai_service._MAX_SANITIZER_INPUT_CHARS
        with patch.object(support_ai_service.unicodedata, "normalize", side_effect=expanding_nfkc):
            sanitized = support_ai_service.redact_support_text(legal_input)

        self.assertEqual(sanitized, "[content-truncated]")
        self.assertTrue(normalized_input_sizes)
        self.assertEqual(max(normalized_input_sizes), 1)
        self.assertLessEqual(
            len(normalized_input_sizes),
            support_ai_service._MAX_SANITIZER_INPUT_CHARS // 18 + 2,
        )

    def test_support_sanitizer_fails_closed_for_telegram_blob_boundaries(self) -> None:
        import support_ai_service

        telegram_hash = "b" * 64
        cases = [
            (
                "embedded-pipe",
                f'initData=user={{"id":1001,"first_name":"Synthetic|Person"}}&auth_date=1700000100&hash={telegram_hash}',
                ("Synthetic", "Person", "1700000100"),
            ),
            (
                "html-entity-separators",
                f'user={{"id":1002,"first_name":"Entity Person"}}&amp;auth_date=1700000101&amp;hash={telegram_hash}',
                ("Entity Person", "1700000101", "amp;"),
            ),
            (
                "top-level-pipe-field",
                f'prefix initData=auth_date=1700000102&hash={telegram_hash} | user={{"id":1003,"first_name":"Trailing Person"}}',
                ("Trailing Person", "1700000102", telegram_hash),
            ),
            (
                "html-entity-top-level-pipe-field",
                f'prefix tgWebAppData=auth_date=1700000103&hash={telegram_hash} &#124; user={{"id":1004,"first_name":"Entity Trailing"}}',
                ("Entity Trailing", "1700000103", telegram_hash),
            ),
        ]
        for case_name, source, private_needles in cases:
            with self.subTest(case=case_name):
                sanitized = support_ai_service.redact_support_text(source)
                self.assertTrue(sanitized.endswith("[telegram-init-data-redacted]"), case_name)
                self.assertTrue(all(item not in sanitized for item in private_needles), case_name)

        public_prose = [
            "initData: empty value was received",
            "Docs: initData requires auth_date=<unix> and hash=<telegram-hash>.",
            "Diagnostic code=recovery_scope_forbidden",
            "Диагностика код: recovery_scope_forbidden",
        ]
        for source in public_prose:
            with self.subTest(public=source):
                self.assertEqual(support_ai_service.redact_support_text(source), source)

        oversized = (
            'user={"id":1003,"first_name":"Oversized Prefix Person"}&padding='
            + ("A" * 65536)
            + f"&auth_date=1700000104&hash={telegram_hash}"
        )
        sanitized = support_ai_service.redact_support_text(oversized)
        self.assertEqual(sanitized, "[content-truncated]", "oversized-init-data")
        self.assertNotIn("Oversized Prefix Person", sanitized, "oversized-init-data")

    def test_support_sanitizer_scans_subscription_paths_linearly(self) -> None:
        import support_ai_service

        segments = [item for _ in range(256) for item in ("sub", "reference")]
        source = "https://docs.pokrov.space/" + "/".join(segments)
        calls = 0

        def count_token_checks(_segment, *, allow_all_letters=False):
            nonlocal calls
            del allow_all_letters
            calls += 1
            return False

        with patch.object(
            support_ai_service,
            "_looks_like_token_path_segment",
            side_effect=count_token_checks,
        ):
            sanitized = support_ai_service.redact_support_text(source)

        self.assertNotIn("[private-link-redacted]", sanitized, "long-public-url")
        self.assertLessEqual(calls, len(segments) * 3, "linear-token-check-count")

        safe_urls = [
            f"https://github.com/Kiwunaka/POKROV-app/commit/{index:040x}"
            for index in range(256)
        ]
        old_internal_marker = "\ue000support-safe-url-deadbeef-0\ue001"
        many_urls = " ".join([old_internal_marker, *safe_urls])
        original_classifier = support_ai_service._http_url_is_private
        with patch.object(
            support_ai_service,
            "_http_url_is_private",
            wraps=original_classifier,
        ) as classify:
            many_sanitized = support_ai_service.redact_support_text(many_urls)

        self.assertEqual(many_sanitized, many_urls)
        self.assertEqual(classify.call_count, len(safe_urls))
        self.assertFalse(hasattr(support_ai_service, "_shield_http_urls"))
        self.assertTrue(hasattr(support_ai_service, "_redact_non_url_span"))

    def test_support_sanitizer_bounds_nested_url_classification_depth(self) -> None:
        import support_ai_service

        nested = "https://github.com/example/repository"
        for _index in range(64):
            nested = f"https://github.com/example/repository?next={nested}"

        original_classifier = support_ai_service._http_url_is_private
        with patch.object(
            support_ai_service,
            "_http_url_is_private",
            wraps=original_classifier,
        ) as classify:
            sanitized = support_ai_service.redact_support_text(nested)

        self.assertEqual(sanitized, "[private-link-redacted]")
        self.assertLessEqual(classify.call_count, 5)

    def test_support_helpers_enforce_exact_output_bounds(self) -> None:
        import support_ai_service

        class GuardedChunk(str):
            def __radd__(self, _other):
                raise AssertionError("provider-chunk-concatenated-before-slice")

        for limit in range(0, 9):
            with self.subTest(limit=limit):
                result = support_ai_service._truncate("abcdefghijk", limit)
                self.assertLessEqual(len(result), limit)

        content = [
            {"text": "prefix"},
            {"text": "B" * 65536},
            {"text": "tail"},
        ]
        extracted = support_ai_service._extract_assistant_content(
            {"choices": [{"message": {"content": content}}]}
        )
        self.assertLessEqual(
            len(extracted),
            support_ai_service._MAX_SANITIZER_INPUT_CHARS + 1,
            "bounded-provider-materialization",
        )

        guarded = GuardedChunk("C" * (support_ai_service._MAX_SANITIZER_INPUT_CHARS + 100))
        guarded_extracted = support_ai_service._extract_assistant_content(
            {"choices": [{"message": {"content": ["prefix", guarded]}}]}
        )
        self.assertLessEqual(
            len(guarded_extracted),
            support_ai_service._MAX_SANITIZER_INPUT_CHARS + 1,
        )

    def test_oversized_model_output_fails_closed_before_return(self) -> None:
        import support_ai_service

        knowledge_path = self._knowledge_path()
        oversized = (
            'user={"id":1004,"first_name":"Provider Prefix Person"}&padding='
            + ("C" * 65536)
            + "&auth_date=1700000103&hash="
            + ("c" * 64)
        )
        config = support_ai_service.SupportAIConfig(
            enabled=True,
            api_key="sk-test",
            api_base_url="https://openrouter.ai/api/v1",
            knowledge_path=str(knowledge_path),
            max_answer_chars=1000,
        )
        fake_factory = _FakeSessionFactory(
            payload={"choices": [{"message": {"content": oversized}}]},
        )
        try:
            reply = asyncio.run(
                support_ai_service.generate_support_reply(
                    "Проверка границы",
                    ticket_id=19,
                    user_tg_id=20,
                    config=config,
                    session_factory=fake_factory,
                )
            )
        finally:
            knowledge_path.unlink(missing_ok=True)

        self.assertEqual(reply, "[content-truncated]", "oversized-model-output")

    def test_provider_boundary_sanitizes_review_bypasses_in_both_directions(self) -> None:
        import support_ai_service

        knowledge_path = self._knowledge_path()
        safe_commit = "https://github.com/Kiwunaka/POKROV-app/commit/0123456789abcdef0123456789abcdef01234567"
        safe_docs = "https://docs.pokrov.space/reference/public-client-profile"
        private_text = "\n".join(
            [
                "https%3A%2F%2Fedge.invalid%2Fsubscription%2FProviderBoundaryOpaqueValue",
                f"auth_date=1700000010&hash={'d' * 64}",
                "PKR%2DA2B3%2DC4D5%2DE6F7",
                "Authorization: Basic U3ludGhldGljQm91bmRhcnk=",
                "данные\u200bAPI key: ProviderBoundaryCredential",
                "данные\u200bprivate_token=ProviderBoundaryPrivateToken",
                "PrivateKey=zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz=",
                "ProviderBoundaryUser@example。invalid",
                "до4111 1111 1111 1111после",
                "https://github.com/example/repository?lang=ru;private_token=ProviderBoundaryQueryValue",
                "_vless://ProviderBoundaryProxy@edge.invalid:443,",
                "code=recovery_scope_forbidden",
                safe_commit,
                safe_docs,
            ]
        )
        config = support_ai_service.SupportAIConfig(
            enabled=True,
            api_key="sk-test",
            api_base_url="https://openrouter.ai/api/v1",
            knowledge_path=str(knowledge_path),
            max_user_chars=5000,
            max_answer_chars=5000,
        )
        fake_factory = _FakeSessionFactory(
            payload={"choices": [{"message": {"content": private_text}}]},
        )
        try:
            reply = asyncio.run(
                support_ai_service.generate_support_reply(
                    private_text,
                    ticket_id=17,
                    user_tg_id=18,
                    config=config,
                    session_factory=fake_factory,
                )
            )
        finally:
            knowledge_path.unlink(missing_ok=True)

        outbound = fake_factory.posts[0]["json"]["messages"][-1]["content"]
        placeholders = (
            "[private-link-redacted]",
            "[telegram-init-data-redacted]",
            "[recovery-code-redacted]",
            "[credential-redacted]",
            "[email-redacted]",
            "[digits-redacted]",
        )
        private_needles = (
            "ProviderBoundaryOpaqueValue",
            "1700000010",
            "A2B3%2DC4D5",
            "U3ludGhldGljQm91bmRhcnk",
            "ProviderBoundaryCredential",
            "ProviderBoundaryPrivateToken",
            "ProviderBoundaryQueryValue",
            "ProviderBoundaryProxy",
            "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz",
            "ProviderBoundaryUser",
            "4111 1111 1111 1111",
        )
        for boundary_name, value in (("outbound", outbound), ("inbound", str(reply))):
            with self.subTest(boundary=boundary_name):
                self.assertTrue(all(item in value for item in placeholders), boundary_name)
                self.assertTrue(all(item not in value for item in private_needles), boundary_name)
                self.assertIn("code=recovery_scope_forbidden", value, boundary_name)
                self.assertIn(safe_commit, value, boundary_name)
                self.assertIn(safe_docs, value, boundary_name)

    def test_fourth_review_redactions_cross_both_provider_boundaries(self) -> None:
        import support_ai_service

        knowledge_path = self._knowledge_path()
        safe_encoded_url = (
            "https%3A%2F%2Fgithub.com%2FKiwunaka%2FPOKROV-app%2Fcommit%2F"
            "0123456789abcdef0123456789abcdef01234567"
        )
        raw_token = "ghp_" + ("J" * 36)
        private_text = "\n".join(
            [
                "private_token=https://github.com/Kiwunaka/POKROV-app",
                f"raw credential {raw_token}",
                "-----BEGIN PRIVATE KEY-----",
                "U3ludGhldGljQm91bmRhcnlLZXk=",
                "-----END PRIVATE KEY-----",
                safe_encoded_url,
            ]
        )
        config = support_ai_service.SupportAIConfig(
            enabled=True,
            api_key="sk-test",
            api_base_url="https://openrouter.ai/api/v1",
            knowledge_path=str(knowledge_path),
            max_user_chars=5000,
            max_answer_chars=5000,
        )
        fake_factory = _FakeSessionFactory(
            payload={"choices": [{"message": {"content": private_text}}]},
        )
        try:
            reply = asyncio.run(
                support_ai_service.generate_support_reply(
                    private_text,
                    ticket_id=23,
                    user_tg_id=24,
                    config=config,
                    session_factory=fake_factory,
                )
            )
        finally:
            knowledge_path.unlink(missing_ok=True)

        outbound = fake_factory.posts[0]["json"]["messages"][-1]["content"]
        for boundary_name, value in (("outbound", outbound), ("inbound", str(reply))):
            with self.subTest(boundary=boundary_name):
                self.assertIn("private_token=[private-link-redacted]", value)
                self.assertIn("[secret-redacted]", value)
                self.assertIn("[private-key-redacted]", value)
                self.assertIn(safe_encoded_url, value)
                self.assertNotIn(raw_token, value)

    def test_generate_support_reply_sanitizes_model_output_before_truncation(self) -> None:
        import support_ai_service

        knowledge_path = self._knowledge_path()
        config = support_ai_service.SupportAIConfig(
            enabled=True,
            api_key="sk-test",
            api_base_url="https://openrouter.ai/api/v1",
            knowledge_path=str(knowledge_path),
            max_answer_chars=30,
        )
        private_uuid = "123e4567-e89b-12d3-a456-426614174000"
        fake_factory = _FakeSessionFactory(
            payload={"choices": [{"message": {"content": f"Ответ: {private_uuid} затем"}}]},
        )
        try:
            reply = asyncio.run(
                support_ai_service.generate_support_reply(
                    "Проверьте ответ",
                    ticket_id=11,
                    user_tg_id=12,
                    config=config,
                    session_factory=fake_factory,
                )
            )
        finally:
            knowledge_path.unlink(missing_ok=True)

        self.assertTrue("[uuid-redacted]" in str(reply), "model-output-redaction")
        self.assertFalse(private_uuid in str(reply), "model-output-redaction")

    def test_provider_body_is_byte_bounded_before_json_parsing(self) -> None:
        import support_ai_service

        class TextOnlyFakeResponse:
            content_length = None

            def __init__(self, body: str):
                self.body = body

            async def text(self):
                return self.body

        oversized_body = b"{" + (b"A" * support_ai_service._MAX_PROVIDER_RESPONSE_BYTES)
        streamed = _FakeResponse(
            200,
            {},
            raw_body=oversized_body,
            content_length=-1,
            stream_chunk_size=4096,
        )
        with patch.object(support_ai_service.json, "loads") as parser:
            with self.assertRaises(support_ai_service._ProviderResponseTooLarge):
                asyncio.run(support_ai_service.read_bounded_provider_json(streamed))

        self.assertEqual(parser.call_count, 0)
        self.assertEqual(
            streamed.content.yielded_bytes,
            support_ai_service._MAX_PROVIDER_RESPONSE_BYTES + 1,
        )
        self.assertLessEqual(
            max(streamed.content.requested_chunk_sizes),
            support_ai_service._MAX_PROVIDER_RESPONSE_BYTES + 1,
        )

        declared = _FakeResponse(
            200,
            {},
            raw_body=b"{}",
            content_length=support_ai_service._MAX_PROVIDER_RESPONSE_BYTES + 1,
        )
        with self.assertRaises(support_ai_service._ProviderResponseTooLarge):
            asyncio.run(support_ai_service.read_bounded_provider_json(declared))
        self.assertEqual(declared.content.yielded_bytes, 0)

        text_only = TextOnlyFakeResponse('{"choices": []}')
        self.assertEqual(
            asyncio.run(support_ai_service.read_bounded_provider_json(text_only)),
            {"choices": []},
        )
        oversized_text_only = TextOnlyFakeResponse(
            "X" * (support_ai_service._MAX_PROVIDER_RESPONSE_BYTES + 1)
        )
        with self.assertRaises(support_ai_service._ProviderResponseTooLarge):
            asyncio.run(support_ai_service.read_bounded_provider_json(oversized_text_only))

    def test_oversized_provider_body_logs_only_fixed_code(self) -> None:
        import support_ai_service

        knowledge_path = self._knowledge_path()
        config = support_ai_service.SupportAIConfig(
            enabled=True,
            api_key="sk-test",
            api_base_url="https://openrouter.ai/api/v1",
            knowledge_path=str(knowledge_path),
        )
        oversized_body = b"{" + (b"B" * support_ai_service._MAX_PROVIDER_RESPONSE_BYTES)
        fake_factory = _FakeSessionFactory(
            raw_body=oversized_body,
            content_length=-1,
        )
        try:
            with self.assertLogs("support_ai_service", level="WARNING") as captured:
                reply = asyncio.run(
                    support_ai_service.generate_support_reply(
                        "Проверка размера ответа",
                        ticket_id=21,
                        user_tg_id=22,
                        config=config,
                        session_factory=fake_factory,
                    )
                )
        finally:
            knowledge_path.unlink(missing_ok=True)

        self.assertIsNone(reply)
        self.assertEqual(
            captured.output,
            [
                "WARNING:support_ai_service:support AI request failed "
                "status=0 code=provider_response_too_large"
            ],
        )

    def test_provider_failures_log_only_bounded_status_and_fixed_code(self) -> None:
        import support_ai_service

        config = support_ai_service.SupportAIConfig(enabled=True, api_key="sk-test")
        http_factory = _FakeSessionFactory(
            status=502,
            payload={"error": "provider echoed person@private.invalid and access_token=private-value"},
        )
        with self.assertLogs("support_ai_service", level="WARNING") as http_logs:
            http_reply = asyncio.run(
                support_ai_service.generate_support_reply(
                    "Проблема подключения",
                    ticket_id=13,
                    user_tg_id=14,
                    config=config,
                    session_factory=http_factory,
                )
            )
        self.assertIsNone(http_reply)
        self.assertTrue(
            http_logs.output == [
                "WARNING:support_ai_service:support AI request failed status=502 code=provider_http_error"
            ],
            "bounded-http-provider-log",
        )

        with self.assertLogs("support_ai_service", level="WARNING") as exception_logs:
            exception_reply = asyncio.run(
                support_ai_service.generate_support_reply(
                    "Проблема подключения",
                    ticket_id=15,
                    user_tg_id=16,
                    config=config,
                    session_factory=_RaisingSessionFactory(),
                )
            )
        self.assertIsNone(exception_reply)
        self.assertTrue(
            exception_logs.output == [
                "WARNING:support_ai_service:support AI request failed status=0 code=provider_request_error"
            ],
            "bounded-exception-provider-log",
        )

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

    def test_config_defaults_to_openrouter_deepseek_medium(self) -> None:
        import support_ai_service

        config = support_ai_service.SupportAIConfig.from_env({})

        self.assertEqual(config.api_base_url, "https://openrouter.ai/api/v1")
        self.assertEqual(config.model, "deepseek-v4-flash-0731")
        self.assertEqual(config.reasoning_effort, "medium")
        self.assertEqual(config.max_context_chars, 30000)
        self.assertEqual(config.max_output_tokens, 1200)
        self.assertEqual(config.timeout_seconds, 45.0)

    def test_agent_timeout_and_context_env_ceilings_are_exact_and_clamped(self) -> None:
        import support_ai_service

        exact = support_ai_service.SupportAIConfig.from_env(
            {
                "SUPPORT_AI_API_BASE_URL": "https://provider.example/v1",
                "SUPPORT_AI_TIMEOUT_SECONDS": "20",
                "SUPPORT_AI_MAX_CONTEXT_CHARS": "30000",
            }
        )
        clamped = support_ai_service.SupportAIConfig.from_env(
            {
                "SUPPORT_AI_API_BASE_URL": "https://provider.example/v1",
                "SUPPORT_AI_TIMEOUT_SECONDS": "20.1",
                "SUPPORT_AI_MAX_CONTEXT_CHARS": "30001",
            }
        )

        self.assertEqual(exact.timeout_seconds, 20.0)
        self.assertEqual(exact.max_context_chars, 30000)
        self.assertEqual(clamped.timeout_seconds, 20.0)
        self.assertEqual(clamped.max_context_chars, 30000)

    def test_exact_openrouter_route_allows_45_second_provider_window(self) -> None:
        import support_ai_service

        exact = support_ai_service.SupportAIConfig.from_env(
            {
                "SUPPORT_AI_API_BASE_URL": "https://openrouter.ai/api/v1",
                "SUPPORT_AI_TIMEOUT_SECONDS": "45",
            }
        )
        clamped = support_ai_service.SupportAIConfig.from_env(
            {
                "SUPPORT_AI_API_BASE_URL": "https://openrouter.ai/api/v1",
                "SUPPORT_AI_TIMEOUT_SECONDS": "45.1",
            }
        )

        self.assertEqual(exact.timeout_seconds, 45.0)
        self.assertEqual(clamped.timeout_seconds, 45.0)

    def test_provider_output_budget_is_hard_capped_at_live_validated_limit(self) -> None:
        import support_ai_service

        config = support_ai_service.SupportAIConfig.from_env(
            {"SUPPORT_AI_MAX_OUTPUT_TOKENS": "1201"}
        )

        self.assertEqual(config.max_output_tokens, 1200)

    def test_xcody_payload_has_no_openrouter_fields_or_headers(self) -> None:
        import support_ai_service

        knowledge_path = self._knowledge_path()
        try:
            config = support_ai_service.SupportAIConfig.from_env(
                {
                    "SUPPORT_AI_ENABLED": "true",
                    "XCODY_API_KEY": "sk-test",
                    "OPENROUTER_API_KEY": "must-not-win",
                    "DEEPSEEK_API_KEY": "must-not-win",
                    "SUPPORT_AI_KB_PATH": str(knowledge_path),
                    "SUPPORT_AI_OPENROUTER_DATA_COLLECTION": "deny",
                    "SUPPORT_AI_REFERER": "https://must-not-leak.invalid/",
                    "SUPPORT_AI_APP_TITLE": "must-not-leak",
                }
            )
            fake_factory = _FakeSessionFactory()
            asyncio.run(
                support_ai_service.generate_support_reply(
                    "Подключение не работает",
                    ticket_id=7,
                    user_tg_id=8,
                    config=config,
                    session_factory=fake_factory,
                )
            )
            post = fake_factory.posts[0]
            self.assertEqual(
                post["headers"],
                {"Authorization": "Bearer sk-test", "Content-Type": "application/json"},
            )
            self.assertNotIn("provider", post["json"])
            serialized = json.dumps(post, ensure_ascii=False)
            for forbidden in (
                "data_collection",
                "HTTP-Referer",
                "X-Title",
                "must-not-leak",
                "must-not-win",
            ):
                self.assertNotIn(forbidden, serialized)
        finally:
            knowledge_path.unlink(missing_ok=True)

    def test_exact_openrouter_route_maps_canonical_minimax_model(self) -> None:
        import support_ai_service

        knowledge_path = self._knowledge_path()
        try:
            config = support_ai_service.SupportAIConfig.from_env(
                {
                    "SUPPORT_AI_ENABLED": "true",
                    "SUPPORT_AI_API_KEY": "sk-or-test",
                    "SUPPORT_AI_API_BASE_URL": "https://openrouter.ai/api/v1",
                    "SUPPORT_AI_MODEL": "deepseek/deepseek-v4-flash-0731",
                    "SUPPORT_AI_KB_PATH": str(knowledge_path),
                }
            )
            fake_factory = _FakeSessionFactory()
            asyncio.run(
                support_ai_service.generate_support_reply(
                    "Подключение не работает",
                    ticket_id=7,
                    user_tg_id=8,
                    config=config,
                    session_factory=fake_factory,
                )
            )
            post = fake_factory.posts[0]
            self.assertEqual(post["url"], "https://openrouter.ai/api/v1/chat/completions")
            self.assertEqual(post["json"]["model"], "deepseek/deepseek-v4-flash-0731")
            self.assertEqual(post["json"]["reasoning"], {"effort": "medium", "exclude": True})
            self.assertNotIn("max_tokens", post["json"])
        finally:
            knowledge_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
