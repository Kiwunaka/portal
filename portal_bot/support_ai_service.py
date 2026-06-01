from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import aiohttp


logger = logging.getLogger(__name__)

DEFAULT_API_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "deepseek/deepseek-v4-flash"
DEFAULT_KNOWLEDGE_PATH = Path(__file__).resolve().parents[1] / "shared" / "support-ai-knowledge.json"

_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PRIVATE_LINK_RE = re.compile(
    r"\b(?:vless|vmess|trojan|ss|ssr|hysteria2?|tuic)://[^\s<>)]+",
    re.IGNORECASE,
)
_INIT_DATA_RE = re.compile(r"\b(?:initData|tgWebAppData)=\S+", re.IGNORECASE)
_LONG_DIGITS_RE = re.compile(r"\b(?:\d[\s-]?){12,19}\b")
_SECRET_RE = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9._-]{16,})\b", re.IGNORECASE)


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


def _parse_openrouter_data_collection(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if raw in {"allow", "deny"}:
        return raw
    return ""


@dataclass
class SupportAIConfig:
    enabled: bool = False
    api_key: str = ""
    api_base_url: str = DEFAULT_API_BASE_URL
    model: str = DEFAULT_MODEL
    timeout_seconds: float = 20.0
    knowledge_path: str = str(DEFAULT_KNOWLEDGE_PATH)
    max_context_chars: int = 32000
    max_user_chars: int = 1200
    max_answer_chars: int = 1200
    min_interval_seconds: float = 30.0
    referer: str = "https://pokrov.space/"
    app_title: str = "POKROV support bot"
    openrouter_data_collection: str = ""

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "SupportAIConfig":
        source: Mapping[str, str] = os.environ if env is None else env
        api_key = (
            (source.get("SUPPORT_AI_API_KEY") or "").strip()
            or (source.get("OPENROUTER_API_KEY") or "").strip()
            or (source.get("DEEPSEEK_API_KEY") or "").strip()
        )
        return cls(
            enabled=_parse_bool(source.get("SUPPORT_AI_ENABLED"), default=False),
            api_key=api_key,
            api_base_url=(source.get("SUPPORT_AI_API_BASE_URL") or DEFAULT_API_BASE_URL).strip().rstrip("/"),
            model=(source.get("SUPPORT_AI_MODEL") or DEFAULT_MODEL).strip(),
            timeout_seconds=_parse_float(source.get("SUPPORT_AI_TIMEOUT_SECONDS"), default=20.0),
            knowledge_path=(source.get("SUPPORT_AI_KB_PATH") or str(DEFAULT_KNOWLEDGE_PATH)).strip(),
            max_context_chars=_parse_int(source.get("SUPPORT_AI_MAX_CONTEXT_CHARS"), default=32000),
            max_user_chars=_parse_int(source.get("SUPPORT_AI_MAX_USER_CHARS"), default=1200),
            max_answer_chars=_parse_int(source.get("SUPPORT_AI_MAX_ANSWER_CHARS"), default=1200),
            min_interval_seconds=_parse_float(source.get("SUPPORT_AI_MIN_INTERVAL_SECONDS"), default=30.0),
            referer=(source.get("SUPPORT_AI_REFERER") or "https://pokrov.space/").strip(),
            app_title=(source.get("SUPPORT_AI_APP_TITLE") or "POKROV support bot").strip(),
            openrouter_data_collection=_parse_openrouter_data_collection(
                source.get("SUPPORT_AI_OPENROUTER_DATA_COLLECTION")
            ),
        )


def redact_support_text(text: str) -> str:
    value = str(text or "")
    value = _EMAIL_RE.sub("[email-redacted]", value)
    value = _PRIVATE_LINK_RE.sub("[private-link-redacted]", value)
    value = _INIT_DATA_RE.sub("[telegram-init-data-redacted]", value)
    value = _SECRET_RE.sub("[secret-redacted]", value)
    value = _LONG_DIGITS_RE.sub("[digits-redacted]", value)
    return value


def _truncate(value: str, limit: int) -> str:
    if limit <= 0:
        return ""
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "..."


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
        return content.strip()
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                chunks.append(item["text"])
            elif isinstance(item, str):
                chunks.append(item)
        return "\n".join(chunks).strip()
    return ""


def _headers(config: SupportAIConfig) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    if "openrouter.ai" in config.api_base_url.lower():
        if config.referer:
            headers["HTTP-Referer"] = config.referer
        if config.app_title:
            headers["X-Title"] = config.app_title
    return headers


def _payload(user_text: str, *, ticket_id: int, config: SupportAIConfig) -> dict[str, Any]:
    knowledge = _render_knowledge_context(_load_knowledge(config.knowledge_path), max_chars=config.max_context_chars)
    redacted_text = _truncate(redact_support_text(user_text), config.max_user_chars)
    payload: dict[str, Any] = {
        "model": config.model,
        "temperature": 0.2,
        "max_tokens": 700,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a compact POKROV technical support assistant for Telegram, WebApp, and app tickets. "
                    "Answer in Russian. Use only the provided support knowledge. "
                    "Use a compact structured format with short section labels and line breaks: "
                    "**Коротко:** one sentence, **Что сделать:** 2-4 numbered steps, "
                    "and **Если не поможет:** what safe context to send support. "
                    "Do not output HTML or tables. "
                    "Do not ask for secrets, card details, raw connection links, QR codes, passwords, "
                    "private keys, Telegram initData, or payment payloads. "
                    "If unsure, say the human support team will check the ticket manually."
                ),
            },
            {
                "role": "system",
                "content": f"Support knowledge JSON:\n{knowledge}",
            },
            {
                "role": "user",
                "content": f"Ticket #{int(ticket_id)} user message, already redacted:\n{redacted_text}",
            },
        ],
    }
    if "openrouter.ai" in config.api_base_url.lower() and config.openrouter_data_collection:
        payload["provider"] = {"data_collection": config.openrouter_data_collection}
    return payload


async def generate_support_reply(
    user_text: str,
    *,
    ticket_id: int,
    user_tg_id: int,
    config: SupportAIConfig | None = None,
    session_factory: Any | None = None,
) -> str | None:
    del user_tg_id
    cfg = config or SupportAIConfig.from_env()
    if not cfg.enabled or not cfg.api_key:
        return None

    timeout = aiohttp.ClientTimeout(total=max(1.0, float(cfg.timeout_seconds)))
    factory = session_factory or aiohttp.ClientSession
    url = f"{cfg.api_base_url.rstrip('/')}/chat/completions"
    try:
        async with factory(timeout=timeout) as session:
            async with session.post(url, headers=_headers(cfg), json=_payload(user_text, ticket_id=ticket_id, config=cfg)) as resp:
                if int(getattr(resp, "status", 0)) >= 400:
                    body = await resp.text()
                    logger.warning("support AI request failed status=%s body=%s", resp.status, _truncate(body, 300))
                    return None
                data = await resp.json(content_type=None)
    except Exception as exc:
        logger.warning("support AI request failed: %s", exc)
        return None

    if not isinstance(data, dict):
        return None
    answer = _extract_assistant_content(data)
    if not answer:
        return None
    return _truncate(answer, cfg.max_answer_chars)
