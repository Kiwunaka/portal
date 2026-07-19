from __future__ import annotations

import ipaddress
import json
import re
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Collection, Mapping
from urllib.parse import urlsplit

from support_agent_policy import PolicySnapshot, rejects_forbidden_claim
from support_ai_service import redact_support_text


_MAX_API_MESSAGE_CHARS = 2_000
_MAX_MODEL_MESSAGE_CHARS = 1_200
_MAX_RAW_OUTPUT_CHARS = 20_000
_MAX_SELECTED_SOURCE_CHARS = 3_600
_PRIVATE_SCHEME_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:vless|vmess|trojan|ss|ssr|hysteria2?|hy2|tuic|wireguard|wg)://",
    re.IGNORECASE,
)
_BEARER_OR_SK_RE = re.compile(r"(?:\bBearer\s+[A-Za-z0-9._~+/-]{8,}|\bsk-[A-Za-z0-9_-]{8,})", re.IGNORECASE)
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
_INIT_DATA_RE = re.compile(
    r"(?:\bquery_id=|\bauth_date=\d{8,}&hash=|\buser=%7B%22id%22)",
    re.IGNORECASE,
)
_UUID_RE = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[1-5][0-9A-Fa-f]{3}-[89ABab][0-9A-Fa-f]{3}-[0-9A-Fa-f]{12}(?![0-9A-Fa-f])")
_PEM_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE)
_RAW_CONFIG_RE = re.compile(
    r"(?:\[Interface\]|\b(?:raw_config|private[_ -]?key|warp_private_key|wireguard_config)\s*[:=]|data:image/[^;,]+;base64,)",
    re.IGNORECASE,
)
_HIGH_ENTROPY_RE = re.compile(r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/]{48,}={0,2}(?![A-Za-z0-9+/=_-])")
_CARD_CANDIDATE_RE = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
_EMAIL_RE = re.compile(r"(?<![\w.!#$%&'*+/=?^_`{|}~-])[\w.!#$%&'*+/=?^_`{|}~-]{1,64}@(?:[\w-]{1,63}\.)+[\w-]{2,63}(?![\w-])", re.UNICODE)
_URL_RE = re.compile(r"https?://[^\s<>\"'`]+", re.IGNORECASE)
_DOMAIN_RE = re.compile(
    r"(?<![\w@.-])(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z]{2,63}(?::\d{1,5})?(?:/[^\s<>\"'`]*)?",
    re.IGNORECASE,
)
_IPV4_RE = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")
_IPV6_RE = re.compile(r"(?<![A-Fa-f0-9:])(?:[A-Fa-f0-9]{0,4}:){2,}[A-Fa-f0-9:]{0,4}(?![A-Fa-f0-9:])")
_PRIVATE_HOST_RE = re.compile(r"(?<![\w.-])(?:localhost|[a-z0-9-]{1,63}\.(?:internal|local|lan))(?![\w.-])", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[ ()-]?){9,14}\d(?!\d)")
_MARKER_RE = re.compile(r"\[[a-z-]+\]")
_LEGACY_REDACTION_MARKER_RE = re.compile(
    r"\[(?:activation-key|credential|digits|email|private-key|private-link|recovery-code|"
    r"refresh-token|secret|session-token|telegram-init-data|uuid)-redacted\]|\[content-truncated\]"
)
_WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)
_CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
_HUMAN_REQUEST_RE = re.compile(
    r"\b(?:оператор\w*|человек\w*|жив\w+\s+(?:поддержк\w*|специалист\w*|оператор\w*)|human agent)\b",
    re.IGNORECASE,
)
_OUT_OF_SCOPE_RES = (
    re.compile(
        r"\b(?:проверьте|проверь|посмотрите|откройте|зайдите|исправьте|inspect|check)\b"
        r".{0,60}\b(?:мой|мою|аккаунт|оплат\w*|ключ\w*|вложен\w*|скриншот\w*|баз\w*\s+данн\w*|сервер\w*|хост\w*|account|payment|attachment|database|server)\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(r"\b(?:выполните|выполни|запустите|запусти|execute|run)\b.{0,40}\b(?:команд\w*|shell|скрипт\w*|command)\b", re.IGNORECASE | re.DOTALL),
)
_PUBLIC_INPUT_HOSTS = frozenset(
    {
        "pokrov.space",
        "app.pokrov.space",
        "api.pokrov.space",
        "connect.pokrov.space",
        "pay.pokrov.space",
        "docs.pokrov.space",
        "t.me",
    }
)
_MODEL_OUTPUT_KEYS = frozenset({"schema_version", "status", "reply"})
_HANDOFF_FOOTER_RE = re.compile(
    r"(?:\r?\n){1,2}[ \t]*если\s+не\s+поможет[ \t]*:?[\s\S]*\Z",
    re.IGNORECASE,
)
_CODE_OWNED_HANDOFF_FOOTER = "Если не поможет\nНапишите в поддержку."
_UNSUPPORTED_MODEL_ACTION_RES = (
    re.compile(
        r"\b(?:удалите|удали|удалить|деинсталлируйте|деинсталлировать|переустанов\w*|"
        r"сбросьте|сбросить|очистите|очистить)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:выйдите|выйти)\s+из\s+(?:аккаунта|уч[её]тной\s+записи)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:перевыпуст\w*|отозв\w*|аннулир\w*|инвалидир\w*)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:\b(?:выпуск\w*|выдач\w*|замен\w*)\s+(?:нов\w+\s+)?"
        r"(?:ссылк\w*|ключ\w*|профил\w*)\b|"
        r"\b(?:отзыв\w*|аннулирован\w*)\s+(?:стар\w+\s+)?"
        r"(?:ссылк\w*|ключ\w*|профил\w*)\b)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:стар(?:ая|ый|ое|ую)|прежн(?:яя|ий|ее|юю))\s+"
        r"(?:ссылк\w*|ключ\w*|профил\w*).{0,60}"
        r"\b(?:перестан\w*|не\s+будет)\s+работ\w*",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:скомпрометирован\w*|утекш\w*).{0,40}\b(?:ссылк\w*|ключ\w*)"
        r".{0,80}\b(?:обнов\w*|замен\w*)",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"\b(?:мы\s+)?(?:выдадим|пришл[её]м|проверим|посмотрим|изучим|"
        r"исправим|настроим|освободим|передадим|поможем|подскажем|верн[её]мся)\b|"
        r"\bпередам\s+обращение\b|\bобращение\s+передано\b|"
        r"\b(?:он|она|поддержк\w*|оператор\w*)\s+верн[её]тся\s+с\s+ответом\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:поддержк\w*|оператор\w*|специалист\w*)[^.!?\n]{0,80}"
        r"\b(?:выдаст|пришл[её]т|перевыпустит|отзов[её]т|аннулирует|"
        r"освободит|исправит|настроит)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:поддержк\w*|оператор\w*|специалист\w*)[^.!?\n]{0,80}"
        r"\b(?:провер(?:ит|ят)|посмотр(?:ит|ят)|изуч(?:ит|ат)|исправ(?:ит|ят))\b[^.!?\n]{0,80}"
        r"\b(?:маршрут\w*|сервер\w*|инфраструктур\w*|аккаунт\w*|"
        r"оплат\w*|ключ\w*|ссылк\w*|профил\w*|конфиг\w*)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bпрофил\w*[^.!?\n]{0,40}\bактивир\w*\s+автоматическ\w*\b", re.IGNORECASE),
    re.compile(
        r"\b(?:если\s+пользователь|попроси|передай\s+оператору|не\s+углубляйся)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bинженер\w*\b", re.IGNORECASE),
    re.compile(
        r"\b(?:сбо\w*|глюк\w*)\b.{0,50}\b(?:это\s+)?нормальн\w*\b",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"(?:\bабсолютно\s+весь\b.{0,40}\bтрафик\b|"
        r"\bвесь\b.{0,40}\bтрафик\b.{0,40}\bбез\s+исключений\b|"
        r"\bгарантированно\b.{0,40}\bвесь\b.{0,40}\bтрафик\b)",
        re.IGNORECASE | re.DOTALL,
    ),
)
_UNQUALIFIED_FULL_TUNNEL_RE = re.compile(
    r"\bвесь\b[^.!?\n]{0,40}\bтрафик\w*\b[^.!?\n]{0,80}"
    r"\b(?:ид[её]т|ш[её]л|пойд[её]т|через\s+pokrov|через\s+туннел\w*)\b",
    re.IGNORECASE,
)
_FULL_TUNNEL_QUALIFIER_RE = re.compile(
    r"(?:\bпочти\s+весь\b|\bкроме\b[^.!?\n]{0,80}\bтехническ\w*\s+исключ\w*)",
    re.IGNORECASE,
)
_CONTEXTUAL_MODEL_ACTION_RES = (
    (
        re.compile(r"\b(?:батаре\w*|энергосбереж\w*|работ\w*\s+в\s+фон\w*)\b", re.IGNORECASE),
        re.compile(r"\b(?:батаре\w*|энергосбереж\w*|работ\w*\s+в\s+фон\w*)\b", re.IGNORECASE),
    ),
    (
        re.compile(
            r"\b(?:адаптивн\w*.{0,30}(?:батаре\w*|энерг\w*)|"
            r"спящ\w*.{0,30}прилож\w*|smart\s+network|умн\w*.{0,20}сет\w*|"
            r"авто(?:матическ\w*)?[ -]?(?:пере)?подключ\w*|"
            r"закреп\w*.{0,40}(?:недавн\w*|последн\w*)\s+прилож\w*)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        re.compile(
            r"\b(?:адаптивн\w*.{0,30}(?:батаре\w*|энерг\w*)|"
            r"спящ\w*.{0,30}прилож\w*|smart\s+network|умн\w*.{0,20}сет\w*|"
            r"авто(?:матическ\w*)?[ -]?(?:пере)?подключ\w*|"
            r"закреп\w*.{0,40}(?:недавн\w*|последн\w*)\s+прилож\w*)\b",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        re.compile(r"\bбонус\w*\b", re.IGNORECASE),
        re.compile(r"\bбонус\w*\b", re.IGNORECASE),
    ),
)
_GLOBAL_ENERGY_DISABLE_RE = re.compile(
    r"(?:\b(?:отключ\w*|выключ\w*)\b.{0,60}\b(?:энергосбереж\w*|оптимизац\w*\s+батаре\w*)\b|"
    r"\b(?:энергосбереж\w*|оптимизац\w*\s+батаре\w*)\b.{0,60}\b(?:отключ\w*|выключ\w*)\b)",
    re.IGNORECASE | re.DOTALL,
)


class InputDisposition(str, Enum):
    HARD_REJECT = "hard_reject"
    LOCAL_ESCALATE = "local_escalate"
    REDACT_CONTINUE = "redact_continue"
    CONTINUE = "continue"


class SafetyValidationError(ValueError):
    """Fixed-code rejection for unsafe model input or output."""


@dataclass(frozen=True, slots=True)
class InputBoundaryResult:
    disposition: InputDisposition
    model_text: str
    category_counts: Mapping[str, int]
    escalation_reason: str | None


@dataclass(frozen=True, slots=True)
class SafeSessionState:
    issue_topic_id: str | None
    attempted_steps: tuple[str, ...]
    last_outcome: str
    escalation_requested: bool
    unsuccessful_turns: int = 0


@dataclass(frozen=True, slots=True)
class ValidatedModelReply:
    status: str
    reply: str


def _fixed_counts(categories: Collection[str]) -> Mapping[str, int]:
    counts: dict[str, int] = {}
    for category in categories:
        counts[category] = counts.get(category, 0) + 1
    return MappingProxyType(dict(sorted(counts.items())))


def _luhn_valid(digits: str) -> bool:
    total = 0
    parity = len(digits) % 2
    for index, char in enumerate(digits):
        value = int(char)
        if index % 2 == parity:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def _hard_categories(text: str) -> list[str]:
    categories: list[str] = []
    checks = (
        ("private_link", _PRIVATE_SCHEME_RE),
        ("credential", _BEARER_OR_SK_RE),
        ("jwt", _JWT_RE),
        ("telegram_init_data", _INIT_DATA_RE),
        ("uuid", _UUID_RE),
        ("private_key", _PEM_RE),
        ("raw_config", _RAW_CONFIG_RE),
        ("high_entropy", _HIGH_ENTROPY_RE),
    )
    for category, pattern in checks:
        categories.extend(category for _ in pattern.finditer(text))
    for match in _CARD_CANDIDATE_RE.finditer(text):
        digits = "".join(char for char in match.group(0) if char.isdigit())
        if 13 <= len(digits) <= 19 and _luhn_valid(digits):
            categories.append("payment_card")
    return categories


def _is_allowlisted_input_url(raw_url: str) -> bool:
    candidate = raw_url.rstrip(".,);:!?]}")
    try:
        parsed = urlsplit(candidate)
        parsed.port
    except ValueError:
        return False
    host = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme != "https"
        or host not in _PUBLIC_INPUT_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        return False
    return host != "connect.pokrov.space" or parsed.path in {"", "/", "/..."}


def _replace_with_count(text: str, pattern: re.Pattern[str], marker: str) -> tuple[str, int]:
    count = 0

    def replace(_match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return marker

    return pattern.sub(replace, text), count


def _replace_urls(text: str, *, redact_all: bool) -> tuple[str, int]:
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        if not redact_all and _is_allowlisted_input_url(match.group(0)):
            return match.group(0)
        count += 1
        return "[url-redacted]"

    return _URL_RE.sub(replace, text), count


def _replace_ips(text: str) -> tuple[str, int]:
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        candidate = match.group(0).strip(":")
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            return match.group(0)
        count += 1
        return "[ip-redacted]"

    redacted = _IPV4_RE.sub(replace, text)
    return _IPV6_RE.sub(replace, redacted), count


def _redact_pii(text: str, *, redact_all_urls: bool = False) -> tuple[str, list[str]]:
    categories: list[str] = []
    value, count = _replace_with_count(text, _EMAIL_RE, "[email-redacted]")
    categories.extend(["email"] * count)
    value, count = _replace_urls(value, redact_all=redact_all_urls)
    categories.extend(["url"] * count)
    value, count = _replace_ips(value)
    categories.extend(["ip"] * count)
    value, count = _replace_with_count(value, _PRIVATE_HOST_RE, "[host-redacted]")
    categories.extend(["private_host"] * count)
    value, count = _replace_with_count(value, _PHONE_RE, "[phone-redacted]")
    categories.extend(["phone"] * count)
    legacy = redact_support_text(value)
    if legacy != value:
        categories.append("legacy_redaction")
    return legacy, categories


def _local_escalation_reason(text: str) -> str | None:
    if _HUMAN_REQUEST_RE.search(text):
        return "human_requested"
    if any(pattern.search(text) for pattern in _OUT_OF_SCOPE_RES):
        return "out_of_scope"
    return None


def classify_support_input(message: str) -> InputBoundaryResult:
    if not isinstance(message, str) or not message.strip() or len(message) > _MAX_API_MESSAGE_CHARS:
        return InputBoundaryResult(
            disposition=InputDisposition.LOCAL_ESCALATE,
            model_text="",
            category_counts=MappingProxyType({}),
            escalation_reason="invalid_input",
        )
    hard_categories = _hard_categories(message)
    if hard_categories:
        return InputBoundaryResult(
            disposition=InputDisposition.HARD_REJECT,
            model_text="",
            category_counts=_fixed_counts(hard_categories),
            escalation_reason="sensitive_input",
        )
    local_reason = _local_escalation_reason(message)
    if local_reason:
        if local_reason == "human_requested":
            redacted, pii_categories = _redact_pii(message)
            model_text = redacted[:_MAX_MODEL_MESSAGE_CHARS]
            truncated_hard = _hard_categories(model_text)
            if truncated_hard:
                return InputBoundaryResult(
                    disposition=InputDisposition.HARD_REJECT,
                    model_text="",
                    category_counts=_fixed_counts([*pii_categories, *truncated_hard]),
                    escalation_reason="sensitive_input",
                )
            return InputBoundaryResult(
                disposition=InputDisposition.LOCAL_ESCALATE,
                model_text=model_text,
                category_counts=_fixed_counts(pii_categories),
                escalation_reason=local_reason,
            )
        return InputBoundaryResult(
            disposition=InputDisposition.LOCAL_ESCALATE,
            model_text="",
            category_counts=MappingProxyType({}),
            escalation_reason=local_reason,
        )

    redacted, pii_categories = _redact_pii(message)
    model_text = redacted[:_MAX_MODEL_MESSAGE_CHARS]
    truncated_hard = _hard_categories(model_text)
    if truncated_hard:
        return InputBoundaryResult(
            disposition=InputDisposition.HARD_REJECT,
            model_text="",
            category_counts=_fixed_counts([*pii_categories, *truncated_hard]),
            escalation_reason="sensitive_input",
        )
    if pii_categories:
        remaining = _MARKER_RE.sub(" ", model_text)
        if len(_WORD_RE.findall(remaining)) < 3:
            return InputBoundaryResult(
                disposition=InputDisposition.LOCAL_ESCALATE,
                model_text="",
                category_counts=_fixed_counts(pii_categories),
                escalation_reason="insufficient_safe_context",
            )
        return InputBoundaryResult(
            disposition=InputDisposition.REDACT_CONTINUE,
            model_text=model_text,
            category_counts=_fixed_counts(pii_categories),
            escalation_reason=None,
        )
    return InputBoundaryResult(
        disposition=InputDisposition.CONTINUE,
        model_text=model_text,
        category_counts=MappingProxyType({}),
        escalation_reason=None,
    )


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SafetyValidationError("agent_output_duplicate_key")
        result[key] = value
    return result


def _output_contains_unsafe_text(reply: str) -> bool:
    if _hard_categories(reply) or _DOMAIN_RE.search(reply):
        return True
    redacted, categories = _redact_pii(reply, redact_all_urls=True)
    if any(category != "legacy_redaction" for category in categories):
        return True
    return _LEGACY_REDACTION_MARKER_RE.search(redacted) is not None


def validate_safe_reply(reply: str, policy: PolicySnapshot) -> str:
    if (
        not isinstance(reply, str)
        or not reply.strip()
        or len(reply) > policy.policy.max_reply_chars
        or not _CYRILLIC_RE.search(reply)
        or _output_contains_unsafe_text(reply)
        or rejects_forbidden_claim(policy, reply)
    ):
        raise SafetyValidationError("agent_output_reply_unsafe")
    return reply.strip()


def _has_unsupported_model_action(reply: str, source_text: str) -> bool:
    if any(pattern.search(reply) for pattern in _UNSUPPORTED_MODEL_ACTION_RES):
        return True
    if _UNQUALIFIED_FULL_TUNNEL_RE.search(reply) and not _FULL_TUNNEL_QUALIFIER_RE.search(reply):
        return True
    if _GLOBAL_ENERGY_DISABLE_RE.search(reply) and not _GLOBAL_ENERGY_DISABLE_RE.search(source_text):
        return True
    return any(
        reply_pattern.search(reply) and not source_pattern.search(source_text)
        for reply_pattern, source_pattern in _CONTEXTUAL_MODEL_ACTION_RES
    )


def _canonicalize_model_handoff_footer(reply: str) -> str:
    match = _HANDOFF_FOOTER_RE.search(reply)
    if match is None:
        return reply
    body = reply[: match.start()].rstrip()
    if not body:
        return reply
    return f"{body}\n\n{_CODE_OWNED_HANDOFF_FOOTER}"


def validate_model_output(
    raw_content: str,
    policy: PolicySnapshot,
    *,
    source_text: str,
) -> ValidatedModelReply:
    if (
        not isinstance(source_text, str)
        or not source_text.strip()
        or len(source_text) > _MAX_SELECTED_SOURCE_CHARS
    ):
        raise SafetyValidationError("agent_output_source_invalid")
    if not isinstance(raw_content, str) or not 1 <= len(raw_content) <= _MAX_RAW_OUTPUT_CHARS:
        raise SafetyValidationError("agent_output_size_invalid")
    try:
        payload = json.loads(raw_content, object_pairs_hook=_reject_duplicate_keys)
    except SafetyValidationError:
        raise
    except json.JSONDecodeError as exc:
        raise SafetyValidationError("agent_output_json_invalid") from exc
    if not isinstance(payload, dict) or set(payload) != _MODEL_OUTPUT_KEYS:
        raise SafetyValidationError("agent_output_root_invalid")
    status = payload["status"]
    if (
        payload["schema_version"] != "1"
        or not isinstance(status, str)
        or status not in {"answer", "escalate"}
    ):
        raise SafetyValidationError("agent_output_status_invalid")
    reply = validate_safe_reply(payload["reply"], policy)
    if status == "answer":
        reply = validate_safe_reply(_canonicalize_model_handoff_footer(reply), policy)
        if _has_unsupported_model_action(reply, source_text):
            raise SafetyValidationError("agent_output_unsupported_action")
    return ValidatedModelReply(status=status, reply=reply)
