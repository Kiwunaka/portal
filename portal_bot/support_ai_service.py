from __future__ import annotations

import json
import html
import logging
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import unquote, urlsplit

import aiohttp


logger = logging.getLogger(__name__)

DEFAULT_API_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "deepseek-v4-flash-0731"
DEFAULT_REASONING_EFFORT = "medium"
OPENROUTER_API_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_DEEPSEEK_V4_FLASH_0731_MODEL = "deepseek/deepseek-v4-flash-0731"
DEFAULT_PROVIDER_TIMEOUT_SECONDS = 20.0
OPENROUTER_PROVIDER_TIMEOUT_SECONDS = 45.0
OPENROUTER_RUN_DEADLINE_SECONDS = 50.0
DEFAULT_RUN_DEADLINE_SECONDS = 25.0
DEFAULT_KNOWLEDGE_PATH = Path(__file__).resolve().parents[1] / "shared" / "support-ai-knowledge.json"

_MAX_SANITIZER_INPUT_CHARS = 65536
_MAX_PERCENT_DECODE_PASSES = 3
_MAX_PROVIDER_RESPONSE_BYTES = 262144
_PROVIDER_READ_CHUNK_BYTES = 8192
_CONTENT_TRUNCATION_PLACEHOLDER = "[content-truncated]"


class _ProviderResponseTooLarge(Exception):
    pass

_JSON_UNICODE_ESCAPE_RE = re.compile(r"\\u([0-9a-fA-F]{4})")
_EMAIL_RE = re.compile(
    r"(?<![\w.!#$%&'*+/=?^_`{|}~-])"
    r"[\w.!#$%&'*+/=?^_`{|}~-]{1,64}@(?:[\w-]{1,63}\.)+[\w-]{2,63}"
    r"(?![\w-])",
    re.UNICODE,
)
_PRIVATE_LINK_SCHEME_PATTERN = (
    r"(?:vless|vmess|trojan|ss|ssr|hysteria2?|hy2|tuic|wireguard|wg|socks5?)"
)
_HTTP_URL_START_PATTERN = (
    r"(?:"
    r"https?://|"
    r"https?%3a%2f%2f|https?%253a%252f%252f|https?%25253a%25252f%25252f|"
    r"%68%74%74%70(?:%73)?%3a%2f%2f|"
    r"%2568%2574%2574%2570(?:%2573)?%253a%252f%252f|"
    r"%252568%252574%252574%252570(?:%252573)?%25253a%25252f%25252f"
    r")"
)
_HTTP_URL_START_RE = re.compile(_HTTP_URL_START_PATTERN, re.IGNORECASE)
_DECODED_HTTP_USERINFO_CONFUSION_RE = re.compile(
    r"https?://[^\r\n/?#<>|]*@",
    re.IGNORECASE,
)
_URL_START_RE = re.compile(
    rf"(?:{_HTTP_URL_START_PATTERN}|_?{_PRIVATE_LINK_SCHEME_PATTERN}://)",
    re.IGNORECASE,
)
_ENCODED_URL_DELIMITER_RE = re.compile(
    r"(?:"
    r"%(?:25){0,2}(?:09|0a|0d|20|22|27|60)|"
    r"%(?:25){0,2}e2%(?:25){0,2}80%(?:25){0,2}(?:98|99|9c|9d)"
    r")",
    re.IGNORECASE,
)
_ENCODED_URL_BOUNDARY_RE = re.compile(
    r"(?:"
    r"%(?:25){0,2}(?:09|0a|0d|20|22|27|3a|3d|60)|"
    r"%(?:25){0,2}e2%(?:25){0,2}80%(?:25){0,2}(?:98|99|9c|9d)"
    r")$",
    re.IGNORECASE,
)
_PRIVATE_LINK_RE = re.compile(
    rf"(?<![A-Za-z0-9])_?{_PRIVATE_LINK_SCHEME_PATTERN}://[^\s<>\"'`“”‘’]+",
    re.IGNORECASE,
)
_TELEGRAM_INIT_DATA_LABEL_START_RE = re.compile(
    r"(?<![A-Za-z0-9_-])"
    r"[\"'“”‘’«»]?(?:initData|tgWebAppData|X-Telegram-Init-Data)[\"'“”‘’«»]?"
    r"(?![A-Za-z0-9_-])\s*[:=]\s*",
    re.IGNORECASE,
)
_TELEGRAM_INIT_DATA_FIELD_PATTERN = (
    r"(?:query_id|user|receiver|chat|chat_type|chat_instance|start_param|can_send_after|auth_date|hash|signature)"
)
_TELEGRAM_FIELD_NAME_RE = re.compile(
    rf"(?<![A-Za-z0-9_])({_TELEGRAM_INIT_DATA_FIELD_PATTERN})\s*=",
    re.IGNORECASE,
)
_TELEGRAM_AUTH_DATE_RE = re.compile(
    r"(?<![A-Za-z0-9_])auth_date\s*=\s*\d{9,12}(?!\d)",
    re.IGNORECASE,
)
_TELEGRAM_HASH_RE = re.compile(
    r"(?<![A-Za-z0-9_])hash\s*=\s*[0-9a-f]{64}(?![0-9a-f])",
    re.IGNORECASE,
)
_RECOVERY_CODE_RE = re.compile(
    r"(?<![A-Za-z0-9])PKR[ \t-]+[A-Z2-9]{4}(?:[ \t-]+[A-Z2-9]{4}){2}(?![A-Za-z0-9])",
    re.IGNORECASE,
)
_ACTIVATION_KEY_RE = re.compile(
    r"(?<![A-Za-z0-9])POKROV(?:[ \t-]+[A-Z0-9]{4,}){2,}(?![A-Za-z0-9])",
    re.IGNORECASE,
)
_UUID_RE = re.compile(
    r"(?<![0-9a-f])(?:"
    r"[0-9a-f]{8}[ \t-]+[0-9a-f]{4}[ \t-]+[0-9a-f]{4}[ \t-]+[0-9a-f]{4}[ \t-]+[0-9a-f]{12}"
    r"|[0-9a-f]{32})(?![0-9a-f])",
    re.IGNORECASE,
)
_REFRESH_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_-])pkr_rt_[A-Za-z0-9_-]{8,}(?![A-Za-z0-9_-])",
    re.IGNORECASE,
)
_SESSION_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_-])(?:"
    r"eyJ[A-Za-z0-9_-]{3,}\.[A-Za-z0-9_-]{6,}(?:\.[A-Za-z0-9_-]{6,})?"
    r"|[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}(?:\.[A-Za-z0-9_-]{16,})?"
    r")(?![A-Za-z0-9_-])"
)
_CREDENTIAL_LABEL_PATTERN = (
    r"access[\s_-]*token|refresh[\s_-]*token|auth[\s_-]*token|session[\s_-]*token|"
    r"client[\s_-]*secret|api[\s_-]*key|private[\s_-]*key|private[\s_-]*token|basic\s+authorization|"
    r"token|secret|password|hash|authorization|"
    r"токен(?:\s+(?:доступа|обновления|сессии))?|api\s*ключ|ключ\s*api|"
    r"секрет(?:\s+клиента)?|пароль|х[еэ]ш"
)
_LABELLED_CREDENTIAL_RE = re.compile(
    r"(?<![A-Za-z0-9_])"
    rf"(?P<label>[\"'“”‘’«»]?(?:{_CREDENTIAL_LABEL_PATTERN})[\"'“”‘’«»]?)"
    r"(?![A-Za-z0-9_А-Яа-яЁё])(?:\[\])?"
    r"(?P<separator>\s*[:=]\s*)"
    r"(?P<value>(?:Bearer|Basic)\s+[^\s,;|]+|"
    r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`[^`]*`|“[^”]*”|‘[^’]*’|«[^»]*»|[^\s,;&|<>]+)",
    re.IGNORECASE,
)
_SENSITIVE_URL_LEFT_CONTEXT_RE = re.compile(
    r"(?<![A-Za-z0-9_])"
    rf"[\"'“”‘’«»]?(?:{_CREDENTIAL_LABEL_PATTERN})[\"'“”‘’«»]?"
    r"(?![A-Za-z0-9_А-Яа-яЁё])(?:\[\])?[ \t]*[:=][ \t]*"
    r"(?:[\"'`“‘«][ \t]*)?$",
    re.IGNORECASE,
)
_LONG_DIGITS_RE = re.compile(r"(?<!\d)\d(?:[ \t-]{0,2}\d){11,18}(?!\d)")
_SECRET_RE = re.compile(
    r"(?<![A-Za-z0-9_-])(?:"
    r"sk-[A-Za-z0-9_-]{12,}|"
    r"gh[pousr]_[A-Za-z0-9]{20,255}|"
    r"github_pat_[A-Za-z0-9_]{20,255}|"
    r"glpat-[A-Za-z0-9_-]{20,255}|"
    r"xox[A-Za-z]-[A-Za-z0-9-]{10,255}|"
    r"AIza[A-Za-z0-9_-]{35}|"
    r"(?:Bearer|Basic)\s+[A-Za-z0-9._=+/-]{8,}"
    r")"
    r"(?![A-Za-z0-9_-])",
    re.IGNORECASE,
)
_PEM_PRIVATE_KEY_BEGIN_RE = re.compile(
    r"-----BEGIN (?P<label>(?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY)-----",
    re.IGNORECASE,
)
_PEM_PRIVATE_KEY_END_RE = re.compile(
    r"-----END (?P<label>(?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY)-----",
    re.IGNORECASE,
)

_GENERIC_PRIVATE_RE = re.compile(
    rf"(?P<private_link>{_PRIVATE_LINK_RE.pattern})"
    rf"|(?P<email>{_EMAIL_RE.pattern})"
    rf"|(?P<recovery>{_RECOVERY_CODE_RE.pattern})"
    rf"|(?P<activation>{_ACTIVATION_KEY_RE.pattern})"
    rf"|(?P<uuid>{_UUID_RE.pattern})"
    rf"|(?P<refresh>{_REFRESH_TOKEN_RE.pattern})"
    rf"|(?P<session>{_SESSION_TOKEN_RE.pattern})"
    rf"|(?P<labelled>{_LABELLED_CREDENTIAL_RE.pattern})"
    rf"|(?P<secret_value>{_SECRET_RE.pattern})"
    rf"|(?P<long_digits>{_LONG_DIGITS_RE.pattern})",
    re.IGNORECASE | re.UNICODE,
)

_PRIVATE_LINK_PLACEHOLDER = "[private-link-redacted]"
_PRIVATE_KEY_PLACEHOLDER = "[private-key-redacted]"
_TELEGRAM_INIT_DATA_PLACEHOLDER = "[telegram-init-data-redacted]"
_PUBLIC_REFERENCE_HOSTS = frozenset(
    {
        "docs.pokrov.space",
        "github.com",
        "pokrov.space",
        "status.pokrov.space",
        "www.pokrov.space",
    }
)
_SENSITIVE_QUERY_KEYS = {
    "accesstoken",
    "apikey",
    "auth",
    "authorization",
    "authtoken",
    "clientsecret",
    "code",
    "hash",
    "key",
    "password",
    "passwd",
    "refreshtoken",
    "secret",
    "session",
    "sessiontoken",
    "sig",
    "signature",
    "subscription",
    "subscriptiontoken",
    "token",
}
_SENSITIVE_QUERY_KEY_MARKERS = (
    "apikey",
    "authorization",
    "credential",
    "password",
    "passwd",
    "privatekey",
    "secret",
    "token",
)
_TRAILING_URL_PUNCTUATION = ".,;:!?)]}\\"
_URL_QUOTE_PAIRS = {"\"": "\"", "'": "'", "`": "`", "“": "”", "‘": "’", "«": "»"}


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    raw = (value or "").strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _parse_float(value: str | None, *, default: float) -> float:
    try:
        return float(str(value).strip())
    except Exception:
        return default


def _parse_int(value: str | None, *, default: int) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def _parse_reasoning_effort(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if raw in {"none", "low", "medium", "high", "xhigh", "max"}:
        return raw
    return DEFAULT_REASONING_EFFORT


def canonical_support_model(value: str | None) -> str:
    raw = (value or DEFAULT_MODEL).strip()
    if raw in {DEFAULT_MODEL, OPENROUTER_DEEPSEEK_V4_FLASH_0731_MODEL}:
        return DEFAULT_MODEL
    return raw


def _bounded_env_int(value: str | None, *, default: int, maximum: int, minimum: int = 1) -> int:
    parsed = _parse_int(value, default=default)
    if parsed < minimum:
        return default
    return min(parsed, maximum)


def _bounded_env_float(
    value: str | None,
    *,
    default: float,
    maximum: float,
    minimum: float = 0.1,
) -> float:
    parsed = _parse_float(value, default=default)
    if parsed < minimum:
        return default
    return min(parsed, maximum)


@dataclass(slots=True)
class SupportAIConfig:
    enabled: bool = False
    api_key: str = ""
    api_base_url: str = DEFAULT_API_BASE_URL
    model: str = DEFAULT_MODEL
    reasoning_effort: str = DEFAULT_REASONING_EFFORT
    timeout_seconds: float = 20.0
    knowledge_path: str = str(DEFAULT_KNOWLEDGE_PATH)
    max_context_chars: int = 30000
    max_user_chars: int = 1200
    max_answer_chars: int = 1200
    min_interval_seconds: float = 30.0
    max_output_tokens: int = 1200

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "SupportAIConfig":
        source: Mapping[str, str] = os.environ if env is None else env
        api_base_url = (source.get("SUPPORT_AI_API_BASE_URL") or DEFAULT_API_BASE_URL).strip().rstrip("/")
        api_key = (
            (source.get("SUPPORT_AI_API_KEY") or "").strip()
            or (source.get("XCODY_API_KEY") or "").strip()
        )
        return cls(
            enabled=_parse_bool(source.get("SUPPORT_AI_ENABLED"), default=False),
            api_key=api_key,
            api_base_url=api_base_url,
            model=canonical_support_model(source.get("SUPPORT_AI_MODEL")),
            reasoning_effort=_parse_reasoning_effort(source.get("SUPPORT_AI_REASONING_EFFORT")),
            timeout_seconds=_bounded_env_float(
                source.get("SUPPORT_AI_TIMEOUT_SECONDS"),
                default=DEFAULT_PROVIDER_TIMEOUT_SECONDS,
                maximum=provider_timeout_ceiling(api_base_url),
            ),
            knowledge_path=(source.get("SUPPORT_AI_KB_PATH") or str(DEFAULT_KNOWLEDGE_PATH)).strip(),
            max_context_chars=_bounded_env_int(
                source.get("SUPPORT_AI_MAX_CONTEXT_CHARS"), default=30000, maximum=30000
            ),
            max_user_chars=_bounded_env_int(
                source.get("SUPPORT_AI_MAX_USER_CHARS"), default=1200, maximum=1200
            ),
            max_answer_chars=_bounded_env_int(
                source.get("SUPPORT_AI_MAX_ANSWER_CHARS"), default=1200, maximum=1200
            ),
            min_interval_seconds=_parse_float(source.get("SUPPORT_AI_MIN_INTERVAL_SECONDS"), default=30.0),
            max_output_tokens=_bounded_env_int(
                source.get("SUPPORT_AI_MAX_OUTPUT_TOKENS"), default=1200, maximum=1200
            ),
        )


def is_exact_openrouter_route(api_base_url: str) -> bool:
    return str(api_base_url or "").rstrip("/").casefold() == OPENROUTER_API_BASE_URL.casefold()


def provider_timeout_ceiling(api_base_url: str) -> float:
    return (
        OPENROUTER_PROVIDER_TIMEOUT_SECONDS
        if is_exact_openrouter_route(api_base_url)
        else DEFAULT_PROVIDER_TIMEOUT_SECONDS
    )


def provider_run_deadline_ceiling(api_base_url: str) -> float:
    return (
        OPENROUTER_RUN_DEADLINE_SECONDS
        if is_exact_openrouter_route(api_base_url)
        else DEFAULT_RUN_DEADLINE_SECONDS
    )


def provider_wire_model(config: SupportAIConfig) -> str:
    """Map the canonical model ID only for the exact owned OpenRouter route."""
    if (
        canonical_support_model(config.model) == DEFAULT_MODEL
        and is_exact_openrouter_route(config.api_base_url)
    ):
        return OPENROUTER_DEEPSEEK_V4_FLASH_0731_MODEL
    return config.model


def provider_generation_controls(config: SupportAIConfig) -> dict[str, Any]:
    """Keep 0731 reasoning provider-managed while bounding the final answer."""
    if (
        canonical_support_model(config.model) == DEFAULT_MODEL
        and is_exact_openrouter_route(config.api_base_url)
    ):
        return {
            "reasoning": {
                "effort": config.reasoning_effort,
                "exclude": True,
            }
        }
    return {
        "max_tokens": config.max_output_tokens,
        "reasoning_effort": config.reasoning_effort,
    }


def _split_trailing_url_punctuation(value: str) -> tuple[str, str]:
    text = value if isinstance(value, str) else str(value or "")
    split_at = len(text)
    while split_at and text[split_at - 1] in _TRAILING_URL_PUNCTUATION:
        split_at -= 1
    return text[:split_at], text[split_at:]


def _bound_sanitizer_input(text: str) -> str:
    value = text if isinstance(text, str) else str(text or "")
    if len(value) > _MAX_SANITIZER_INPUT_CHARS:
        return _CONTENT_TRUNCATION_PLACEHOLDER
    return value.replace("\x00", "\ufffd")


def _decode_json_unicode_escape(match: re.Match[str]) -> str:
    codepoint = int(match.group(1), 16)
    if 0xD800 <= codepoint <= 0xDFFF:
        return "\ufffd"
    return chr(codepoint)


_NORMALIZED_CHAR_TRANSLATION = {
    ord("\u2010"): "-",
    ord("\u2011"): "-",
    ord("\u2012"): "-",
    ord("\u2013"): "-",
    ord("\u2014"): "-",
    ord("\u2015"): "-",
    ord("\u2212"): "-",
    ord("\u3002"): ".",
    ord("\uff61"): ".",
}


def _bounded_nfkc(value: str) -> str:
    parts: list[str] = []
    total = 0
    for char in value:
        normalized = unicodedata.normalize("NFKC", char)
        piece = "".join(
            item.translate(_NORMALIZED_CHAR_TRANSLATION)
            for item in normalized
            if unicodedata.category(item) != "Cf"
        )
        if len(piece) > _MAX_SANITIZER_INPUT_CHARS - total:
            return _CONTENT_TRUNCATION_PLACEHOLDER
        parts.append(piece)
        total += len(piece)
    return "".join(parts)


def _normalize_text_surface(value: str) -> str:
    normalized = _JSON_UNICODE_ESCAPE_RE.sub(_decode_json_unicode_escape, str(value or ""))
    normalized = normalized.replace("\\/", "/").replace("\\\"", "\"").replace("\\'", "'")
    normalized = html.unescape(normalized)
    if len(normalized) > _MAX_SANITIZER_INPUT_CHARS:
        return _CONTENT_TRUNCATION_PLACEHOLDER
    return _bounded_nfkc(normalized)


def _normalize_bounded_text(value: str) -> str:
    bounded = _bound_sanitizer_input(value)
    if bounded == _CONTENT_TRUNCATION_PLACEHOLDER:
        return bounded
    return _bound_sanitizer_input(_normalize_text_surface(bounded))


def _bounded_percent_decode(value: str) -> str:
    current = _bound_sanitizer_input(value)
    if current == _CONTENT_TRUNCATION_PLACEHOLDER:
        return current
    for _attempt in range(_MAX_PERCENT_DECODE_PASSES):
        if "%" not in current:
            break
        decoded = unquote(current, encoding="utf-8", errors="replace")
        if decoded == current:
            break
        current = _normalize_bounded_text(decoded)
        if current == _CONTENT_TRUNCATION_PLACEHOLDER:
            break
    return current


def _canonical_sensitive_key(value: str) -> str:
    decoded = _bounded_percent_decode(str(value or ""))
    return re.sub(r"[^a-z0-9]+", "", decoded.casefold())


def _is_sensitive_query_key(value: str) -> bool:
    raw = str(value or "")
    if len(raw) > 256:
        return True
    canonical = _canonical_sensitive_key(raw)
    return canonical in _SENSITIVE_QUERY_KEYS or any(
        marker in canonical for marker in _SENSITIVE_QUERY_KEY_MARKERS
    )


def _looks_like_token_path_segment(segment: str, *, allow_all_letters: bool = False) -> bool:
    value = _bounded_percent_decode(str(segment or "")).strip()
    if _UUID_RE.fullmatch(value) or _REFRESH_TOKEN_RE.fullmatch(value) or _SESSION_TOKEN_RE.fullmatch(value):
        return True
    if _RECOVERY_CODE_RE.fullmatch(value) or _ACTIVATION_KEY_RE.fullmatch(value):
        return True
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        return False
    compact = value.replace("-", "").replace("_", "")
    if allow_all_letters and len(compact) >= 12 and compact.isalnum():
        return True
    if len(value) < 12:
        return False

    has_lower = any(char.islower() for char in value)
    has_upper = any(char.isupper() for char in value)
    has_digit = any(char.isdigit() for char in value)
    if has_lower and has_upper and has_digit:
        return True
    if value.isalpha():
        if not allow_all_letters:
            return False
        return len(value) >= 12
    return len(value) >= 20 and has_digit and (has_lower or has_upper) and value.isalnum()


def _is_public_reference_host(host: str) -> bool:
    value = str(host or "").casefold()
    return value in _PUBLIC_REFERENCE_HOSTS


def _url_component_contains_private_value(value: str, *, allow_public_uuid: bool = False) -> bool:
    decoded = _bounded_percent_decode(str(value or ""))
    if decoded == _CONTENT_TRUNCATION_PLACEHOLDER:
        return True
    if allow_public_uuid and _UUID_RE.fullmatch(decoded):
        return False
    return bool(
        _EMAIL_RE.search(decoded)
        or _RECOVERY_CODE_RE.search(decoded)
        or _ACTIVATION_KEY_RE.search(decoded)
        or (_UUID_RE.search(decoded) and not allow_public_uuid)
        or _REFRESH_TOKEN_RE.search(decoded)
        or _SESSION_TOKEN_RE.search(decoded)
        or _LABELLED_CREDENTIAL_RE.search(decoded)
        or _SECRET_RE.search(decoded)
        or _LONG_DIGITS_RE.search(decoded)
    )


def _strip_url_value_quotes(value: str) -> str:
    current = str(value or "").strip()
    for _attempt in range(2):
        if len(current) < 2:
            break
        closing = _URL_QUOTE_PAIRS.get(current[0])
        if not closing or current[-1] != closing:
            break
        current = current[1:-1].strip()
    return current


def _url_value_is_private(value: str, *, public_reference: bool, depth: int) -> bool:
    if depth > 3:
        return True
    item = _strip_url_value_quotes(value)
    if len(item) > _MAX_SANITIZER_INPUT_CHARS:
        return True
    if not item:
        return False

    if re.search(
        rf"(?<![A-Za-z0-9])_?{_PRIVATE_LINK_SCHEME_PATTERN}://",
        item,
        re.IGNORECASE,
    ):
        return True

    nested_http = re.search(r"https?://", item, re.IGNORECASE)
    assignment_index = item.find("=")
    if assignment_index >= 0 and (
        nested_http is None or assignment_index < nested_http.start()
    ):
        key, nested_value = item.split("=", 1)
        if _is_sensitive_query_key(key):
            return True
        return _url_value_is_private(
            nested_value,
            public_reference=public_reference,
            depth=depth + 1,
        )

    if nested_http is not None:
        nested_end = _scan_url_end(item, nested_http.start())
        nested_core, _suffix = _split_trailing_url_punctuation(
            item[nested_http.start() : nested_end]
        )
        prefix = item[: nested_http.start()].strip()
        if prefix and _url_component_contains_private_value(prefix):
            return True
        if nested_end < len(item) and item[nested_end:].strip():
            return True
        return _http_url_is_private(nested_core, _depth=depth + 1)

    if _url_component_contains_private_value(item):
        return True
    if not public_reference and _looks_like_token_path_segment(item):
        return True
    return False


def _url_pairs_are_private(raw: str, *, public_reference: bool, depth: int) -> bool:
    value = str(raw or "").lstrip("?#")
    if len(value) > _MAX_SANITIZER_INPUT_CHARS:
        return True
    return any(
        _url_value_is_private(
            component,
            public_reference=public_reference,
            depth=depth,
        )
        for component in re.split(r"[&;]", value)
        if component
    )


def _is_public_uuid_path(host: str, segments: list[str], index: int) -> bool:
    return bool(
        host == "docs.pokrov.space"
        and index > 0
        and segments[index - 1].casefold() == "reference"
    )


def _is_pokrov_service_host(host: str) -> bool:
    value = str(host or "").casefold()
    return value == "pokrov.test" or value.endswith(".pokrov.test") or value.endswith(".pokrov.space")


def _decoded_url_authority(value: str) -> str:
    scheme_end = value.find("://")
    if scheme_end <= 0:
        return ""
    authority_start = scheme_end + 3
    authority_end = len(value)
    for delimiter in "/?#":
        position = value.find(delimiter, authority_start)
        if position >= 0:
            authority_end = min(authority_end, position)
    return value[authority_start:authority_end]


_ENCODED_AUTHORITY_DELIMITER_RE = re.compile(
    r"%(?:23|2f|3a|3f|40|5c)",
    re.IGNORECASE,
)


def _url_layer_authority_is_malformed(value: str) -> bool:
    if not value.casefold().startswith(("http://", "https://")):
        return False

    parsed = urlsplit(value)
    authority = _decoded_url_authority(value)
    if not authority or authority != parsed.netloc:
        return True
    if _ENCODED_AUTHORITY_DELIMITER_RE.search(authority):
        return True
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in authority):
        return True
    if (
        "\\" in authority
        or "@" in authority
        or parsed.username is not None
        or parsed.password is not None
    ):
        return True
    try:
        _parsed_port = parsed.port
    except ValueError:
        return True
    return authority.rsplit("@", 1)[-1].endswith(":")


def _url_decode_layers_have_authority_confusion(value: str) -> bool:
    current = str(value or "")
    for _attempt in range(_MAX_PERCENT_DECODE_PASSES + 1):
        if _url_layer_authority_is_malformed(current):
            return True
        if "%" not in current:
            break
        decoded = unquote(current, encoding="utf-8", errors="replace")
        if decoded == current:
            break
        current = _normalize_bounded_text(decoded)
        if current == _CONTENT_TRUNCATION_PLACEHOLDER:
            return True
    return False


def _path_has_authority_confusion(path: str, *, public_reference: bool) -> bool:
    if "\\" in path or path.startswith("//"):
        return True
    if not public_reference:
        return False
    first_segment = next((segment for segment in path.split("/") if segment), "")
    return "@" in first_segment


def _http_url_is_private(url: str, *, _depth: int = 0) -> bool:
    try:
        if _depth > 3:
            return True
        if _url_decode_layers_have_authority_confusion(url):
            return True
        decoded_url = _bounded_percent_decode(url)
        if decoded_url == _CONTENT_TRUNCATION_PLACEHOLDER:
            return True
        if not decoded_url.casefold().startswith(("http://", "https://")):
            return True
        if any(ord(char) < 32 or ord(char) == 127 for char in decoded_url):
            return True
        if "\\" in decoded_url:
            return True
        parsed = urlsplit(decoded_url)
        if parsed.scheme.casefold() not in {"http", "https"}:
            return True
        authority = _decoded_url_authority(decoded_url)
        if not authority or authority != parsed.netloc:
            return True
        if re.search(r"%(?:2f|5c|40)", authority, re.IGNORECASE):
            return True
        if any(char.isspace() for char in authority):
            return True
        _parsed_port = parsed.port
        host = str(parsed.hostname or "").casefold()
        if (
            not host
            or host.startswith(".")
            or host.endswith(".")
            or ".." in host
            or parsed.username is not None
            or parsed.password is not None
            or "@" in authority
        ):
            return True

        public_reference = _is_public_reference_host(host)
        if _path_has_authority_confusion(parsed.path, public_reference=public_reference):
            return True
        if _url_pairs_are_private(
            parsed.query,
            public_reference=public_reference,
            depth=_depth,
        ):
            return True
        if _url_pairs_are_private(
            parsed.fragment,
            public_reference=public_reference,
            depth=_depth,
        ):
            return True

        path_segments = [
            _bounded_percent_decode(segment)
            for segment in parsed.path.split("/")
            if segment
        ]
        for index, segment in enumerate(path_segments):
            if _url_component_contains_private_value(
                segment,
                allow_public_uuid=_is_public_uuid_path(host, path_segments, index),
            ):
                return True
        after_subscription_endpoint = False
        for segment in path_segments:
            if after_subscription_endpoint and _looks_like_token_path_segment(
                segment,
                allow_all_letters=not public_reference,
            ):
                return True
            if segment.casefold() in {"sub", "subscription"}:
                after_subscription_endpoint = True

        if public_reference:
            return False

        if any(_looks_like_token_path_segment(segment) for segment in path_segments):
            return True
        if _is_pokrov_service_host(host) and any(
            _looks_like_token_path_segment(segment, allow_all_letters=True)
            for segment in path_segments
        ):
            return True
        return False
    except Exception:
        return True


def _userinfo_marker_precedes_url_boundary(value: str, start: int) -> bool:
    lookahead = _bounded_percent_decode(value[start:])
    if lookahead == _CONTENT_TRUNCATION_PLACEHOLDER:
        return True
    marker_index = lookahead.find("@")
    if marker_index < 0:
        return False
    boundary_indexes = [
        index
        for delimiter in "/?#\r\n\t <>|\"'`“”‘’«»"
        if (index := lookahead.find(delimiter)) >= 0
    ]
    return not boundary_indexes or marker_index < min(boundary_indexes)


def _scan_url_end(value: str, start: int) -> int:
    index = start
    quoted_until = ""
    userinfo_confusion = False
    while index < len(value):
        char = value[index]
        if userinfo_confusion:
            if char == "@":
                userinfo_confusion = False
            index += 1
            continue
        if char == "%":
            encoded_delimiter = _ENCODED_URL_DELIMITER_RE.match(value, index)
            if encoded_delimiter is not None:
                if _userinfo_marker_precedes_url_boundary(value, encoded_delimiter.end()):
                    userinfo_confusion = True
                    index = encoded_delimiter.end()
                    continue
                break
        if quoted_until:
            if char == "\\" and index + 1 < len(value):
                index += 2
                continue
            if char == quoted_until:
                quoted_until = ""
            if char in "\r\n":
                break
            index += 1
            continue

        if char in "\r\n\t<>|”’»":
            break
        if char.isspace():
            next_index = index
            while next_index < len(value) and value[next_index] in " \t":
                next_index += 1
            previous_index = index - 1
            while previous_index >= start and value[previous_index].isspace():
                previous_index -= 1
            if (
                previous_index >= start
                and value[previous_index] == "="
                and next_index < len(value)
                and value[next_index] in _URL_QUOTE_PAIRS
            ):
                index = next_index
                continue
            break
        if char in _URL_QUOTE_PAIRS:
            if _userinfo_marker_precedes_url_boundary(value, index + 1):
                userinfo_confusion = True
                index += 1
                continue
            previous_index = index - 1
            while previous_index >= start and value[previous_index].isspace():
                previous_index -= 1
            if previous_index >= start and value[previous_index] == "=":
                quoted_until = _URL_QUOTE_PAIRS[char]
                index += 1
                continue
            break
        index += 1
    return index


def _url_start_has_boundary(value: str, start: int) -> bool:
    if start <= 0:
        return True
    if not re.match(r"[A-Za-z0-9]", value[start - 1]):
        return True
    prefix = value[max(0, start - 32) : start]
    return _ENCODED_URL_BOUNDARY_RE.search(prefix) is not None


def _split_line_ending(raw_line: str) -> tuple[str, str]:
    if raw_line.endswith("\r\n"):
        return raw_line[:-2], "\r\n"
    if raw_line.endswith(("\r", "\n")):
        return raw_line[:-1], raw_line[-1]
    return raw_line, ""


def _telegram_init_data_start(line: str) -> int | None:
    if _TELEGRAM_AUTH_DATE_RE.search(line) is None or _TELEGRAM_HASH_RE.search(line) is None:
        return None
    label_match = _TELEGRAM_INIT_DATA_LABEL_START_RE.search(line)
    if label_match is not None:
        return label_match.start()
    field_matches = list(_TELEGRAM_FIELD_NAME_RE.finditer(line))
    if not field_matches:
        return None
    return min(match.start() for match in field_matches)


def _redact_telegram_init_data(value: str) -> str:
    redacted_lines: list[str] = []
    for raw_line in value.splitlines(keepends=True):
        line, ending = _split_line_ending(raw_line)
        start = _telegram_init_data_start(line)
        if start is None:
            redacted_lines.append(raw_line)
            continue
        redacted_lines.append(line[:start] + _TELEGRAM_INIT_DATA_PLACEHOLDER + ending)
    return "".join(redacted_lines)


def _redact_fully_encoded_telegram_lines(value: str) -> str:
    parts: list[str] = []
    total = 0
    for raw_line in value.splitlines(keepends=True):
        line, ending = _split_line_ending(raw_line)
        replacement = raw_line
        if "%" in line:
            decoded = _bounded_percent_decode(line)
            if decoded == _CONTENT_TRUNCATION_PLACEHOLDER:
                return decoded
            if decoded != line and _telegram_init_data_start(decoded) is not None:
                replacement = _TELEGRAM_INIT_DATA_PLACEHOLDER + ending
        if len(replacement) > _MAX_SANITIZER_INPUT_CHARS - total:
            return _CONTENT_TRUNCATION_PLACEHOLDER
        parts.append(replacement)
        total += len(replacement)
    return "".join(parts)


def _redact_labelled_credential(match: re.Match[str]) -> str:
    raw_value = match.group("value")
    quote_pairs = {"\"": "\"", "'": "'", "“": "”", "‘": "’", "«": "»"}
    opening = raw_value[0] if raw_value else ""
    closing = quote_pairs.get(opening, "")
    quoted = bool(closing and len(raw_value) >= 2 and raw_value[-1] == closing)
    replacement = f"{opening}[credential-redacted]{closing}" if quoted else "[credential-redacted]"
    return f"{match.group('label')}{match.group('separator')}{replacement}"


def _generic_private_replacement(match: re.Match[str]) -> str:
    if match.group("labelled") is not None:
        return _redact_labelled_credential(match)
    replacements = (
        ("private_link", _PRIVATE_LINK_PLACEHOLDER),
        ("email", "[email-redacted]"),
        ("recovery", "[recovery-code-redacted]"),
        ("activation", "[activation-key-redacted]"),
        ("uuid", "[uuid-redacted]"),
        ("refresh", "[refresh-token-redacted]"),
        ("session", "[session-token-redacted]"),
        ("secret_value", "[secret-redacted]"),
        ("long_digits", "[digits-redacted]"),
    )
    for group_name, replacement in replacements:
        if match.group(group_name) is not None:
            return replacement
    return _CONTENT_TRUNCATION_PLACEHOLDER


def _redact_pem_private_keys(value: str) -> str:
    parts: list[str] = []
    cursor = 0
    total = 0
    while True:
        begin_match = _PEM_PRIVATE_KEY_BEGIN_RE.search(value, cursor)
        if begin_match is None:
            tail = value[cursor:]
            if len(tail) > _MAX_SANITIZER_INPUT_CHARS - total:
                return _CONTENT_TRUNCATION_PLACEHOLDER
            parts.append(tail)
            return "".join(parts)

        end_match = _PEM_PRIVATE_KEY_END_RE.search(value, begin_match.end())
        if end_match is None:
            return _CONTENT_TRUNCATION_PLACEHOLDER
        nested_begin = _PEM_PRIVATE_KEY_BEGIN_RE.search(
            value,
            begin_match.end(),
            end_match.start(),
        )
        if nested_begin is not None:
            return _CONTENT_TRUNCATION_PLACEHOLDER
        if begin_match.group("label").casefold() != end_match.group("label").casefold():
            return _CONTENT_TRUNCATION_PLACEHOLDER

        prefix = value[cursor : begin_match.start()]
        if len(prefix) > _MAX_SANITIZER_INPUT_CHARS - total:
            return _CONTENT_TRUNCATION_PLACEHOLDER
        parts.append(prefix)
        total += len(prefix)
        if len(_PRIVATE_KEY_PLACEHOLDER) > _MAX_SANITIZER_INPUT_CHARS - total:
            return _CONTENT_TRUNCATION_PLACEHOLDER
        parts.append(_PRIVATE_KEY_PLACEHOLDER)
        total += len(_PRIVATE_KEY_PLACEHOLDER)
        cursor = end_match.end()


def _prepared_span_has_url_atom(value: str) -> bool:
    return any(
        _url_start_has_boundary(value, match.start())
        for match in _URL_START_RE.finditer(value)
    )


def _collapse_nested_percent_escapes_for_probe(value: str) -> str:
    parts: list[str] = []
    index = 0
    while index < len(value):
        if value[index] != "%":
            parts.append(value[index])
            index += 1
            continue

        cursor = index + 1
        while value[cursor : cursor + 2].casefold() == "25":
            cursor += 2
        terminal = value[cursor : cursor + 2]
        if len(terminal) == 2 and all(char in "0123456789abcdefABCDEF" for char in terminal):
            byte_value = int(terminal, 16)
            parts.append(chr(byte_value) if byte_value < 128 else "\ufffd")
            index = cursor + 2
            continue

        parts.append("%")
        index = cursor if cursor > index + 1 else index + 1
    return "".join(parts)


def _has_residual_encoded_url_signature(value: str) -> bool:
    if "%" not in value:
        return False
    probe = _collapse_nested_percent_escapes_for_probe(value)
    return probe != value and _prepared_span_has_url_atom(probe)


def _prepare_non_url_span(value: str) -> str:
    decoded = _bounded_percent_decode(value)
    if decoded == _CONTENT_TRUNCATION_PLACEHOLDER:
        return decoded
    telegram_redacted = _redact_telegram_init_data(decoded)
    if len(telegram_redacted) > _MAX_SANITIZER_INPUT_CHARS:
        return _CONTENT_TRUNCATION_PLACEHOLDER
    prepared = _redact_pem_private_keys(telegram_redacted)
    if prepared == _CONTENT_TRUNCATION_PLACEHOLDER:
        return prepared
    if _has_residual_encoded_url_signature(prepared):
        return _PRIVATE_LINK_PLACEHOLDER
    if decoded != value and _DECODED_HTTP_USERINFO_CONFUSION_RE.search(prepared):
        return _PRIVATE_LINK_PLACEHOLDER
    return prepared


def _redact_generic_span(value: str, *, max_output_chars: int) -> str | None:
    limit = max(0, min(int(max_output_chars), _MAX_SANITIZER_INPUT_CHARS))
    parts: list[str] = []
    cursor = 0
    total = 0
    for match in _GENERIC_PRIVATE_RE.finditer(value):
        prefix = value[cursor : match.start()]
        replacement = _generic_private_replacement(match)
        if len(prefix) > limit - total:
            return None
        parts.append(prefix)
        total += len(prefix)
        if len(replacement) > limit - total:
            return None
        parts.append(replacement)
        total += len(replacement)
        cursor = match.end()

    tail = value[cursor:]
    if len(tail) > limit - total:
        return None
    parts.append(tail)
    return "".join(parts)


def _redact_non_url_span(
    value: str,
    *,
    max_output_chars: int = _MAX_SANITIZER_INPUT_CHARS,
    allow_percent_rescan: bool = True,
) -> str | None:
    prepared = _prepare_non_url_span(value)
    if prepared == _CONTENT_TRUNCATION_PLACEHOLDER:
        return prepared
    if _prepared_span_has_url_atom(prepared):
        if not allow_percent_rescan:
            return (
                _PRIVATE_LINK_PLACEHOLDER
                if len(_PRIVATE_LINK_PLACEHOLDER) <= max_output_chars
                else None
            )
        rescanned = _redact_structured_spans(prepared, allow_percent_rescan=False)
        return rescanned if len(rescanned) <= max_output_chars else None
    return _redact_generic_span(prepared, max_output_chars=max_output_chars)


def _redact_non_url_before_url(
    value: str,
    *,
    max_output_chars: int,
    allow_percent_rescan: bool,
) -> tuple[str | None, bool]:
    prepared = _prepare_non_url_span(value)
    if prepared == _CONTENT_TRUNCATION_PLACEHOLDER:
        return prepared, False
    if _prepared_span_has_url_atom(prepared):
        if not allow_percent_rescan:
            return (
                _PRIVATE_LINK_PLACEHOLDER
                if len(_PRIVATE_LINK_PLACEHOLDER) <= max_output_chars
                else None,
                False,
            )
        prepared = _redact_structured_spans(prepared, allow_percent_rescan=False)
        if len(prepared) > max_output_chars:
            return None, False
    assignment = _SENSITIVE_URL_LEFT_CONTEXT_RE.search(prepared)
    if assignment is None:
        return (
            _redact_generic_span(prepared, max_output_chars=max_output_chars),
            False,
        )

    protected_suffix = prepared[assignment.start() :]
    if len(protected_suffix) > max_output_chars:
        return None, True
    prefix = _redact_generic_span(
        prepared[: assignment.start()],
        max_output_chars=max_output_chars - len(protected_suffix),
    )
    if prefix is None:
        return None, True
    return prefix + protected_suffix, True


def _redact_structured_spans(
    value: str,
    *,
    allow_percent_rescan: bool = True,
) -> str:
    parts: list[str] = []
    cursor = 0
    total = 0

    for match in _URL_START_RE.finditer(value):
        if match.start() < cursor:
            continue
        if not _url_start_has_boundary(value, match.start()):
            continue
        non_url, left_sensitive_assignment = _redact_non_url_before_url(
            value[cursor : match.start()],
            max_output_chars=_MAX_SANITIZER_INPUT_CHARS - total,
            allow_percent_rescan=allow_percent_rescan,
        )
        if non_url is None:
            return _CONTENT_TRUNCATION_PLACEHOLDER
        if non_url == _CONTENT_TRUNCATION_PLACEHOLDER:
            return non_url
        parts.append(non_url)
        total += len(non_url)

        end = _scan_url_end(value, match.start())
        raw_url = value[match.start() : end]
        core, suffix = _split_trailing_url_punctuation(raw_url)
        if _HTTP_URL_START_RE.match(core):
            replacement = (
                _PRIVATE_LINK_PLACEHOLDER
                if left_sensitive_assignment or _http_url_is_private(core)
                else core
            )
        else:
            replacement = _PRIVATE_LINK_PLACEHOLDER

        if len(replacement) > _MAX_SANITIZER_INPUT_CHARS - total:
            return _CONTENT_TRUNCATION_PLACEHOLDER
        parts.append(replacement)
        total += len(replacement)
        if len(suffix) > _MAX_SANITIZER_INPUT_CHARS - total:
            return _CONTENT_TRUNCATION_PLACEHOLDER
        parts.append(suffix)
        total += len(suffix)
        cursor = end

    tail = _redact_non_url_span(
        value[cursor:],
        max_output_chars=_MAX_SANITIZER_INPUT_CHARS - total,
        allow_percent_rescan=allow_percent_rescan,
    )
    if tail is None:
        return _CONTENT_TRUNCATION_PLACEHOLDER
    if tail == _CONTENT_TRUNCATION_PLACEHOLDER:
        return tail
    parts.append(tail)
    return "".join(parts)


def redact_support_text(text: str) -> str:
    value = _normalize_bounded_text(text)
    if value == _CONTENT_TRUNCATION_PLACEHOLDER:
        return value
    value = _redact_fully_encoded_telegram_lines(value)
    if value == _CONTENT_TRUNCATION_PLACEHOLDER:
        return value
    value = _redact_telegram_init_data(value)
    return _redact_structured_spans(value)


def _truncate(value: str, limit: int) -> str:
    if limit <= 0:
        return ""
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    if limit <= 3:
        return "." * limit
    return text[: limit - 3].rstrip() + "..."


def _load_knowledge(path: str) -> dict[str, Any]:
    kb_path = Path(path)
    try:
        return json.loads(kb_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.warning("support AI knowledge base not found: %s", kb_path)
    except Exception as exc:
        logger.warning("support AI knowledge base failed to load: %s", exc)
    return {"rules": [], "fallback": {"body": "Escalate to manual support."}, "topics": []}


def _render_knowledge_context(knowledge: Mapping[str, Any], *, max_chars: int) -> str:
    rules = knowledge.get("rules") if isinstance(knowledge.get("rules"), list) else []
    fallback = knowledge.get("fallback") if isinstance(knowledge.get("fallback"), dict) else {}
    topics = knowledge.get("topics") if isinstance(knowledge.get("topics"), list) else []
    compact = {
        "rules": rules,
        "fallback": fallback.get("body") or fallback,
        "topics": [
            {
                "id": topic.get("id"),
                "body": topic.get("body"),
            }
            for topic in topics
            if isinstance(topic, dict)
        ],
    }
    return _truncate(json.dumps(compact, ensure_ascii=False, separators=(",", ":")), max_chars)


def _extract_assistant_content(payload: Mapping[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        if len(content) > _MAX_SANITIZER_INPUT_CHARS:
            return content[: _MAX_SANITIZER_INPUT_CHARS + 1]
        return content.strip()
    if isinstance(content, list):
        chunks: list[str] = []
        total = 0
        for index, item in enumerate(content):
            if index >= 1024:
                return _CONTENT_TRUNCATION_PLACEHOLDER
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                chunk = item["text"]
            elif isinstance(item, str):
                chunk = item
            else:
                continue
            limit = _MAX_SANITIZER_INPUT_CHARS + 1
            if chunks:
                if total >= limit:
                    return "".join(chunks)
                chunks.append("\n")
                total += 1
            remaining = limit - total
            if len(chunk) >= remaining:
                chunks.append(chunk[:remaining])
                return "".join(chunks)
            chunks.append(chunk)
            total += len(chunk)
        return "".join(chunks).strip()
    return ""


def _headers(config: SupportAIConfig) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }


def _payload(user_text: str, *, config: SupportAIConfig) -> dict[str, Any]:
    knowledge = _render_knowledge_context(_load_knowledge(config.knowledge_path), max_chars=config.max_context_chars)
    redacted_text = _truncate(redact_support_text(user_text), config.max_user_chars)
    system_prompt = (
        "You are a compact POKROV technical support assistant for Telegram, WebApp, and app tickets. "
        "Answer in Russian. Use only the provided support knowledge. "
        "Use a compact structured format with short section labels and line breaks: "
        "**Коротко:** one sentence, **Что сделать:** 2-4 numbered steps, "
        "and **Если не поможет:** what safe context to send support. "
        "Do not output HTML or tables. "
        "Do not ask for secrets, card details, raw connection links, QR codes, passwords, "
        "private keys, Telegram initData, or payment payloads. "
        "If unsure, say the human support team will check the ticket manually."
        f"\n\nSupport knowledge JSON:\n{knowledge}"
    )
    return {
        "model": provider_wire_model(config),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": redacted_text},
        ],
        "temperature": 0.2,
        "n": 1,
        **provider_generation_controls(config),
    }


async def read_bounded_provider_json(response: Any) -> Any:
    declared_length = getattr(response, "content_length", None)
    if declared_length is not None:
        try:
            parsed_length = int(declared_length)
        except (TypeError, ValueError):
            parsed_length = -1
        if parsed_length > _MAX_PROVIDER_RESPONSE_BYTES:
            raise _ProviderResponseTooLarge

    content = getattr(response, "content", None)
    read = getattr(content, "read", None)
    if callable(read):
        chunks: list[bytes] = []
        total = 0
        while True:
            remaining = _MAX_PROVIDER_RESPONSE_BYTES + 1 - total
            if remaining <= 0:
                raise _ProviderResponseTooLarge
            chunk = await read(min(_PROVIDER_READ_CHUNK_BYTES, remaining))
            if not chunk:
                break
            chunk_length = len(chunk)
            if chunk_length > remaining or chunk_length > _MAX_PROVIDER_RESPONSE_BYTES - total:
                raise _ProviderResponseTooLarge
            if not isinstance(chunk, bytes):
                chunk = bytes(chunk)
            total += chunk_length
            chunks.append(chunk)
        body = b"".join(chunks)
    else:
        text_reader = getattr(response, "text", None)
        if not callable(text_reader):
            raise ValueError("provider response body unavailable")
        text_body = await text_reader()
        if not isinstance(text_body, str):
            raise ValueError("provider response body is not text")
        if len(text_body) > _MAX_PROVIDER_RESPONSE_BYTES:
            raise _ProviderResponseTooLarge
        encoded_chunks: list[bytes] = []
        encoded_total = 0
        for start in range(0, len(text_body), _PROVIDER_READ_CHUNK_BYTES):
            encoded = text_body[start : start + _PROVIDER_READ_CHUNK_BYTES].encode("utf-8")
            if len(encoded) > _MAX_PROVIDER_RESPONSE_BYTES - encoded_total:
                raise _ProviderResponseTooLarge
            encoded_chunks.append(encoded)
            encoded_total += len(encoded)
        body = b"".join(encoded_chunks)
    return json.loads(body)


async def generate_support_reply(
    user_text: str,
    *,
    ticket_id: int,
    user_tg_id: int,
    config: SupportAIConfig | None = None,
    session_factory: Any | None = None,
) -> str | None:
    del ticket_id, user_tg_id
    cfg = config or SupportAIConfig.from_env()
    if not cfg.enabled or not cfg.api_key:
        return None

    timeout = aiohttp.ClientTimeout(total=max(1.0, float(cfg.timeout_seconds)))
    factory = session_factory or aiohttp.ClientSession
    url = f"{cfg.api_base_url.rstrip('/')}/chat/completions"
    try:
        async with factory(timeout=timeout) as session:
            async with session.post(url, headers=_headers(cfg), json=_payload(user_text, config=cfg)) as resp:
                if int(getattr(resp, "status", 0)) >= 400:
                    try:
                        status = int(getattr(resp, "status", 0) or 0)
                    except Exception:
                        status = 0
                    if status < 100 or status > 599:
                        status = 0
                    logger.warning("support AI request failed status=%s code=provider_http_error", status)
                    return None
                data = await read_bounded_provider_json(resp)
    except _ProviderResponseTooLarge:
        logger.warning("support AI request failed status=0 code=provider_response_too_large")
        return None
    except Exception:
        logger.warning("support AI request failed status=0 code=provider_request_error")
        return None

    if not isinstance(data, dict):
        return None
    answer = _extract_assistant_content(data)
    if not answer:
        return None
    return _truncate(redact_support_text(answer), cfg.max_answer_chars)
