from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Mapping, Sequence

from support_agent_knowledge import KnowledgeHit, KnowledgeSnapshot, SupportKnowledgeStore
from support_agent_policy import PolicySnapshot
from support_agent_safety import SafetyValidationError, validate_safe_reply

if TYPE_CHECKING:
    from support_agent_sessions import SessionState


RETRIEVER_VERSION = "code-owned-v1"
LOCAL_RENDERER_VERSION = "local-body-v1"
_HTTP_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_LOCAL_PREFIX = "Коротко\n"
_LOCAL_SUFFIX = "\n\nЕсли не поможет\nНапишите в поддержку."
_SHORT_FOLLOWUPS = frozenset(
    {
        "не помогло",
        "без изменений",
        "ничего не изменилось",
        "стало лучше",
        "стало хуже",
        "что дальше",
    }
)


class RetrievalDisposition(str, Enum):
    CONFIDENT = "confident"
    CANDIDATE = "candidate"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class RetrievalDecision:
    disposition: RetrievalDisposition
    context_topics: tuple[KnowledgeHit, ...]
    context_topic_ids: tuple[str, ...]
    grounding_topic_id: str | None
    retriever_sha256: str
    retriever_version: str = RETRIEVER_VERSION


@dataclass(frozen=True, slots=True)
class IntentRule:
    topic_id: str
    required_groups: tuple[tuple[str, ...], ...]
    forbidden_phrases: tuple[str, ...] = ()


LOCAL_RENDERABLE_TOPICS = MappingProxyType(
    {
        "android_battery_background": "36de67422426c31b4ab63d22b621bf251f1c11868653b8f7478e625cfbb36960",
        "connected_no_internet": "7ace3772bc507601cec30fc6e88691f7877b8586876677629bd0f2488998864f",
        "device_limit_help": "ec699ed37097497bf7633c02b04d60d3d5212783f5c0dad595038e2a8ff835a4",
        "happ_import": "a0c87653863054182bb8b8dd3c0254ba7522ea05c803241fd5bf1a1e7cee6d2c",
        "hiddify_empty_profile": "387cf6f4f429809024d9c6d33ca4ee82c9410d2501a4d6c56842f12c09c4e079",
        "hiddify_import": "209abd70a0d7c0350e59a390d3a772cf1eefcaac1f98e5453a3ce8a668dce7e5",
        "karing_import": "a0af16d4957204387d54f5e07da75bf87dac348a50902c71c206c4ef49c5636a",
        "one_site_not_open": "75af5e3b670d1359154637afaa98362fbd4d561e3ab64ffa6654e8ccff8d4c52",
        "other_network_client_conflict": "bcaf396a09925d8f2c9ef3d16a7cb34b5ac16fdc4644fecccef778f75c3eb30c",
        "private_dns_and_filters": "4303911da9ebe7956e57321f90b81c5f99ee193a2574a579c7d73084a0a12c57",
        "refresh_after_renewal": "a944ae88d4c1685c2ac0c3d7cb9e0bf810ba6530f2fe95db08e4903ab52c0d51",
        "routing_all_except_ru": "33f6d885b1c38ef94294a31b1598ac61b96fe60ef2982327066e50f363f6754e",
        "slow_speed": "ec38496aac090d55ecdbe855f361339622215005f20a380ed119a9768ee92e88",
        "streisand_import": "c8895b5a75c1a2a5a479f65dd78d04f404a555b52209278f3a12a99eb716a389",
        "v2rayn_import": "fe0f7adda0587c81c7294ad25d330475ffe208014f2b6f356d995490636f56c8",
        "v2rayn_proxy_tun": "e3ce9f663c23bbcfc3b053f599f0da6ad0ac24a4013d39326cb25b142bc4959f",
        "v2rayng_import": "747024440b6d32b06eca2194457a6a7f8b7601f00a2a4728d4eb9979b008bcce",
        "v2rayng_no_internet": "0e42b0225d0fb2ded78839e0c970c65fad567efe746cc355d6a432fb6dad9af8",
    }
)


def _normalize_route_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().replace("ё", "е")
    spaced = "".join(character if character.isalnum() else " " for character in normalized)
    return " ".join(spaced.split())


def _topic_body_sha256(body: str) -> str:
    canonical = unicodedata.normalize("NFKC", body).strip()
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _is_short_followup(normalized_text: str) -> bool:
    return len(normalized_text) <= 160 and normalized_text in _SHORT_FOLLOWUPS


INTENT_RULES = (
    IntentRule(
        "v2rayng_no_internet",
        (
            ("v2rayng",),
            (
                "нет интернета",
                "интернета нет",
                "без интернета",
                "интернет не открывается",
                "интернет совсем не открывается",
                "сайты не открываются",
                "без трафика",
            ),
        ),
        ("интернет работает", "уже импортирован"),
    ),
    IntentRule(
        "v2rayn_proxy_tun",
        (
            ("v2rayn",),
            ("tun", "системный прокси", "системным прокси"),
            ("без сети", "не работают", "конфликтует", "ломает сеть"),
        ),
        ("tun не включен", "программы работают", "как импортировать"),
    ),
    IntentRule(
        "hiddify_empty_profile",
        (("hiddify",), ("пустой", "пусто", "ничего нет")),
        ("не пустой", "серверы видны"),
    ),
    IntentRule(
        "android_battery_background",
        (
            ("android",),
            ("закрывает", "останавливается", "выгружается"),
            ("фон", "фоне", "фона", "экрана"),
        ),
        ("не закрывает", "не останавливается", "не выгружается"),
    ),
    IntentRule(
        "device_limit_help",
        (("лимит", "лимита", "слишком много"), ("устройство", "устройств")),
        ("не достигнут", "лимита нет", "не превышен"),
    ),
    IntentRule(
        "one_site_not_open",
        (
            ("один сайт", "конкретный сайт", "кроме одного"),
            ("не открывается", "не работает", "кроме одного"),
        ),
        ("нет такого", "все сайты не открываются"),
    ),
    IntentRule(
        "private_dns_and_filters",
        (
            ("private dns", "частный dns", "фильтр dns"),
            ("мешать", "мешает", "проверить", "ломает"),
        ),
        ("отключен и не мешает",),
    ),
    IntentRule(
        "other_network_client_conflict",
        (
            ("другой vpn", "два vpn", "еще один vpn"),
            ("мешать", "мешает", "конфликт", "конфликтует", "одновременно"),
        ),
        ("не включен", "конфликта нет"),
    ),
    IntentRule(
        "refresh_after_renewal",
        (
            ("после продления", "продлил доступ", "продление"),
            ("старый срок", "не обновился", "обновить доступ"),
        ),
        ("новый срок уже появился",),
    ),
    IntentRule(
        "routing_all_except_ru",
        (
            ("российские сайты", "сайты рф", "ru напрямую"),
            ("напрямую", "без vpn"),
            ("остальные", "остальное", "другие"),
        ),
        ("не хочу",),
    ),
    IntentRule(
        "slow_speed",
        (
            (
                "низкая скорость",
                "скорость низкая",
                "скорость очень низкая",
                "работает медленно",
                "работает очень медленно",
                "очень медленное",
                "стало медленным",
                "тормозит",
                "скорость упала",
            ),
        ),
        ("не низкая", "работает быстро", "только один сайт"),
    ),
    IntentRule(
        "hiddify_import",
        (("hiddify",), ("импортировать", "добавить подписку", "вставить профиль")),
        ("уже импортирован", "профиль пустой", "пустой список", "ничего нет"),
    ),
    IntentRule(
        "happ_import",
        (("happ",), ("импортировать", "добавить подписку", "вставить профиль")),
        ("уже импортирован", "нет интернета"),
    ),
    IntentRule(
        "karing_import",
        (("karing",), ("импортировать", "добавить подписку", "вставить профиль")),
        ("уже импортирован", "нет интернета"),
    ),
    IntentRule(
        "streisand_import",
        (("streisand",), ("импортировать", "добавить подписку", "вставить профиль")),
        ("уже импортирован",),
    ),
    IntentRule(
        "v2rayn_import",
        (("v2rayn",), ("импортировать", "добавить подписку", "вставить профиль")),
        ("уже импортирован", "tun", "системный прокси", "без сети"),
    ),
    IntentRule(
        "v2rayng_import",
        (("v2rayng",), ("импортировать", "добавить подписку", "вставить профиль")),
        ("уже импортирован", "нет интернета", "без трафика"),
    ),
    IntentRule(
        "connected_no_internet",
        (
            (
                "pokrov подключен",
                "pokrov показывает подключение",
                "соединение установлено",
                "подключение активно",
            ),
            (
                "нет интернета",
                "интернета нет",
                "без интернета",
                "интернет не открывается",
                "интернет совсем не открывается",
                "сайты не открываются",
                "трафик не проходит",
            ),
        ),
        (
            "v2rayng",
            "v2rayn",
            "hiddify",
            "happ",
            "karing",
            "streisand",
            "интернет работает",
            "сайты открываются",
        ),
    ),
)


def _retriever_rules_sha256(rules: Sequence[IntentRule]) -> str:
    canonical = [
        {
            "topic_id": rule.topic_id,
            "required_groups": [
                [_normalize_route_text(phrase) for phrase in group]
                for group in rule.required_groups
            ],
            "forbidden_phrases": [
                _normalize_route_text(phrase) for phrase in rule.forbidden_phrases
            ],
        }
        for rule in rules
    ]
    serialized = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


RETRIEVER_RULES_SHA256 = _retriever_rules_sha256(INTENT_RULES)


def _matches(rule: IntentRule, normalized_text: str) -> bool:
    padded = f" {normalized_text} "

    def contains(phrase: str) -> bool:
        return f" {_normalize_route_text(phrase)} " in padded

    if any(contains(phrase) for phrase in rule.forbidden_phrases):
        return False
    return all(
        any(contains(phrase) for phrase in group)
        for group in rule.required_groups
    )


def _truncate_at_word(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    shortened = value[:limit].rstrip()
    if " " in shortened:
        shortened = shortened.rsplit(" ", 1)[0].rstrip()
    return shortened


class SupportGroundingEngine:
    def __init__(
        self,
        knowledge_store: SupportKnowledgeStore,
        knowledge: KnowledgeSnapshot,
        *,
        local_renderable_topics: Mapping[str, str] | None = None,
        local_renderer_version: str = LOCAL_RENDERER_VERSION,
        retrieval_limit: int = 3,
    ) -> None:
        if type(retrieval_limit) is not int or not 1 <= retrieval_limit <= 3:
            raise ValueError("grounding_retrieval_limit_invalid")
        self.knowledge_store = knowledge_store
        self.knowledge = knowledge
        self.retrieval_limit = retrieval_limit
        self.local_renderer_version = local_renderer_version
        self.local_renderable_topics = MappingProxyType(
            dict(
                LOCAL_RENDERABLE_TOPICS
                if local_renderable_topics is None
                else local_renderable_topics
            )
        )
        self._active_local_topics = frozenset(
            topic_id
            for topic_id, expected_hash in self.local_renderable_topics.items()
            if local_renderer_version == LOCAL_RENDERER_VERSION
            and topic_id in knowledge.topics_by_id
            and _topic_body_sha256(knowledge.topics_by_id[topic_id].body)
            == expected_hash
        )

    def _rule_is_active(self, rule: IntentRule) -> bool:
        return rule.topic_id in self._active_local_topics

    def select(
        self,
        redacted_message: str,
        session: SessionState | None,
    ) -> RetrievalDecision:
        text = _normalize_route_text(redacted_message)
        matched = [
            rule
            for rule in INTENT_RULES
            if self._rule_is_active(rule) and _matches(rule, text)
        ]
        grounding_id = matched[0].topic_id if len(matched) == 1 else None
        if grounding_id is None and session is not None and _is_short_followup(text):
            pinned = session.state.issue_topic_id
            if pinned in self._active_local_topics:
                grounding_id = pinned

        searched = list(
            self.knowledge_store.search(
                redacted_message,
                limit=self.retrieval_limit,
            )
        )
        if grounding_id is not None:
            primary = self.knowledge.topics_by_id[grounding_id]
            searched = [
                primary,
                *(hit for hit in searched if hit.topic_id != grounding_id),
            ][: self.retrieval_limit]
        topics = tuple(searched)
        disposition = (
            RetrievalDisposition.CONFIDENT
            if grounding_id is not None
            else RetrievalDisposition.CANDIDATE
            if topics
            else RetrievalDisposition.NONE
        )
        return RetrievalDecision(
            disposition=disposition,
            context_topics=topics,
            context_topic_ids=tuple(hit.topic_id for hit in topics),
            grounding_topic_id=grounding_id,
            retriever_sha256=RETRIEVER_RULES_SHA256,
        )

    def render_local(
        self,
        decision: RetrievalDecision,
        policy: PolicySnapshot,
    ) -> str | None:
        topic_id = decision.grounding_topic_id
        if decision.disposition is not RetrievalDisposition.CONFIDENT:
            return None
        if topic_id is None or topic_id not in self._active_local_topics:
            return None
        body = _HTTP_URL_RE.sub("", self.knowledge.topics_by_id[topic_id].body)
        body = " ".join(body.split())
        body_limit = policy.policy.max_reply_chars - len(_LOCAL_PREFIX) - len(_LOCAL_SUFFIX)
        if body_limit <= 0:
            return None
        body = _truncate_at_word(body, body_limit)
        if not body:
            return None
        try:
            return validate_safe_reply(
                f"{_LOCAL_PREFIX}{body}{_LOCAL_SUFFIX}",
                policy,
            )
        except SafetyValidationError:
            return None
