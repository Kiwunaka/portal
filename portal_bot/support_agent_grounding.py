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
from support_agent_safety import SafetyValidationError, validate_grounded_reply

if TYPE_CHECKING:
    from support_agent_sessions import SessionState


RETRIEVER_VERSION = "code-owned-v3"
LOCAL_RENDERER_VERSION = "local-body-v3"
_MAX_PINNED_FOLLOWUP_CHARS = 240
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
        "activation_key_vs_connection_link": "0ac3057751e942d48f5c96bdd1130fe7cf92b32e68db0a607081dc9e7c07e1eb",
        "android_battery_background": "5a09a84f21e52d1ca6ed56bec9f350c31808d69a70e411058df5bf195ea3cfc7",
        "beta_scope": "9e57af27af9c800cf3433824779056a1807850b58c96f17c63a98f1372471248",
        "connected_no_internet": "9c963318034cb8cadd617753de64c313d6c95ccec1308ec55a4fedba2061e26b",
        "connection_link_meaning": "6e2085b78ae3b87082a3be33c78fe468ef8b7ec62636a742c66c79ac5d068154",
        "connection_link_security": "1fc3e91f77cbead1c1b6709aafcbaa970dab5d32c109f7186e72b103d4ac39d2",
        "device_limit_help": "bb7f4e1eccde50041c0e74404976800bd7fe52947b240a7148f2c72883152972",
        "happ_import": "ad177dd08001a41218771d15d2cb7906fe77b7e6748801299368b595b39cd34f",
        "hiddify_empty_profile": "b19d929ed1a65fc009106a414897710c58d1345cf669ba3f12a13f066abef720",
        "hiddify_import": "b0d71b43c101258dc4c1d45df80d6a5aba1280bdc588077be384f13cd8512c24",
        "karing_import": "d05d7e9984317d8efaac40fa234219e6c39d6e325e0a821224ff0b66c8fb2797",
        "manual_path_when_app_unavailable": "b23ada61d35c7312a97b80d7304147bbfabca4714b78fd358bab2198695f955b",
        "one_active_client_rule": "22154f258d626009541c5b3d2943e5c5385ec072b8f953eadb8b2730c84393d5",
        "one_site_not_open": "7609ab592299cf6f10578f2d4c81e7b5cace798afb9edbc6f66b894e1e8b4031",
        "operator_handoff": "fd8b39d192de33550d86e7fbafd43fc085cfff0879f7835bb2b70b9b4be7b5c3",
        "other_network_client_conflict": "70aeb16bac579fc1f57c68ed4358fc78df68ba810c74cf394377cc3dbf449539",
        "private_dns_and_filters": "8a74b0f5e513df6946052c799f634a6e95164336f386161dc6b7052f1a9d9e9a",
        "refresh_after_renewal": "6059d8cb09bd54dd97ee120881f46e06d137a66564b5934b32cd02a42f172b0b",
        "routing_all_except_ru": "9de97577aeeab78b456e4a7c2f2fbf93a3a781b247ac15f28394938dfc9da52b",
        "slow_speed": "e438111bc98bb4fa4f45ac9990e72795941abef8807786fac780ec91f93244f9",
        "streisand_import": "093cc9bc8b06ee4b38ba0b99b46e99261031eeb916580e33204a78afad0e9787",
        "v2rayn_import": "28e4f8ecd51897cc65123f148618e0c356c137302fc93b2050e9df8c8288cbc7",
        "v2rayn_proxy_tun": "bd49563da88b7c77ad733252536a3bb2f4a79daa49e0535116286912020cd906",
        "v2rayng_import": "9c3555c155b2a5c14b01967c6f38e0d72427db6218d52f73e4ce51ae9f5a81db",
        "v2rayng_no_internet": "bd00ad9ad5325d73e1d9f9771a6aeb5f6c4d02ef97b544d3ae92ec66ff4cc3eb",
        "windows_network_reset_light": "35dd72cc352637599e0b2f0309ebdf36ec5db8c88762a6371162153d8d5a87dd",
    }
)
DIRECT_RENDER_TOPICS = frozenset(
    {
        "activation_key_vs_connection_link",
        "beta_scope",
        "connection_link_meaning",
        "connection_link_security",
        "manual_path_when_app_unavailable",
        "one_active_client_rule",
        "one_site_not_open",
        "operator_handoff",
        "windows_network_reset_light",
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
        "windows_network_reset_light",
        (
            ("windows",),
            ("после отключения pokrov", "после выключения клиента", "после клиента"),
            ("сеть", "интернет"),
        ),
        ("сеть работает нормально", "проблемы нет"),
    ),
    IntentRule(
        "manual_path_when_app_unavailable",
        (
            ("приложение pokrov", "pokrov"),
            ("недоступно", "нет приложения"),
            ("вручную", "ручное подключение"),
        ),
        ("приложение доступно",),
    ),
    IntentRule(
        "one_active_client_rule",
        (
            ("нескольких клиентах", "два клиента", "несколько клиентов"),
            ("одновременно",),
        ),
        ("не одновременно", "только один клиент уже"),
    ),
    IntentRule(
        "beta_scope",
        (
            ("beta", "бета"),
            ("на каких платформах", "где доступна", "платформах сейчас доступна"),
        ),
        ("не спрашиваю о платформах",),
    ),
    IntentRule(
        "activation_key_vs_connection_link",
        (
            ("activation key", "код активации"),
            ("ссылка подключения", "ссылки подключения"),
            ("отличить", "разница", "куда вводить"),
        ),
    ),
    IntentRule(
        "connection_link_meaning",
        (
            ("ссылка подключения",),
            ("что такое", "чем отличается", "для чего"),
        ),
        ("нельзя отправлять", "можно отправлять"),
    ),
    IntentRule(
        "connection_link_security",
        (
            ("личную ссылку", "qr"),
            ("нельзя отправлять", "можно отправлять", "другим людям", "безопасно делиться"),
        ),
    ),
    IntentRule(
        "operator_handoff",
        (
            ("ручная проверка", "оператор", "человек"),
            ("ai помощник", "ai помощнику", "вместо самостоятельного ответа", "не уверен"),
        ),
        ("ручная проверка не нужна",),
    ),
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
        pinned_context_id: str | None = None
        if not matched and session is not None and len(text) <= _MAX_PINNED_FOLLOWUP_CHARS:
            pinned = session.state.issue_topic_id
            if pinned in self._active_local_topics:
                pinned_context_id = pinned
                if _is_short_followup(text):
                    grounding_id = pinned

        searched = list(
            self.knowledge_store.search(
                redacted_message,
                limit=self.retrieval_limit,
            )
        )
        primary_id = grounding_id or pinned_context_id
        if primary_id is not None:
            primary = self.knowledge.topics_by_id[primary_id]
            searched = [
                primary,
                *(hit for hit in searched if hit.topic_id != primary_id),
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
            return validate_grounded_reply(
                f"{_LOCAL_PREFIX}{body}{_LOCAL_SUFFIX}",
                policy,
                source_text=body,
            )
        except SafetyValidationError:
            return None
