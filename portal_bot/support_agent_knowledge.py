from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import unicodedata
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, Collection, Mapping
from urllib.parse import urlsplit


_ROOT_KEYS = frozenset({"version", "scope", "language", "rules", "fallback", "topics"})
_FALLBACK_KEYS = frozenset({"title", "body"})
_TOPIC_KEYS = frozenset({"id", "keywords", "body"})
_TOPIC_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_URL_RE = re.compile(r"https?://[^\s<>\"'`]+", re.IGNORECASE)
_PRIVATE_SCHEME_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:vless|vmess|trojan|ss|ssr|hysteria2?|hy2|tuic|wireguard|wg)://",
    re.IGNORECASE,
)
_SECRET_RE = re.compile(
    r"(?:"
    r"\bBearer\s+[A-Za-z0-9._~+/-]{8,}|"
    r"\bsk-[A-Za-z0-9_-]{8,}|"
    r"\b(?:api[_ -]?key|access[_ -]?token|private[_ -]?token|token|password|secret|private[_ -]?key)"
    r"\s*[:=]\s*[^\s]{8,}|"
    r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r")",
    re.IGNORECASE,
)
_IP_CANDIDATE_RE = re.compile(r"(?<![A-Fa-f0-9:.])(?:[A-Fa-f0-9]{0,4}:){2,}[A-Fa-f0-9:]{0,4}(?![A-Fa-f0-9:.])|(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")
_PUBLIC_URL_HOSTS = frozenset(
    {
        "pokrov.space",
        "app.pokrov.space",
        "api.pokrov.space",
        "connect.pokrov.space",
        "pay.pokrov.space",
        "docs.pokrov.space",
        "github.com",
        "t.me",
        "telegram.me",
        "play.google.com",
        "apps.apple.com",
        "learn.microsoft.com",
        "support.apple.com",
        "support.google.com",
    }
)
_MAX_FILE_BYTES = 65_536
_MAX_RULES = 20
_MAX_TOPICS = 100
_MAX_KEYWORDS = 20
_MAX_KEYWORD_CHARS = 80
_MAX_BODY_CHARS = 1_200
_MAX_INDEX_CHARS = 8_000
_MAX_RESULT_TOPICS = 5
_MAX_RESULT_CHARS = 6_000
_SEARCH_STOPWORDS = frozenset(
    {
        "pokrov",
        "покров",
        "что",
        "как",
        "ли",
        "это",
        "в",
        "во",
        "на",
        "с",
        "со",
        "по",
        "и",
        "или",
        "но",
        "не",
        "у",
        "к",
        "для",
        "через",
        "мой",
        "моя",
        "мою",
        "мне",
        "всё",
        "все",
        "ещё",
        "еще",
        "один",
        "одна",
        "какие",
        "какой",
        "правильно",
        "безопасно",
        "сделать",
        "делать",
        "проверить",
        "попробовать",
        "может",
        "можно",
        "показывает",
    }
)
_SEARCH_SCOPE_TOKENS = frozenset(
    {"hiddify", "happ", "v2rayng", "v2rayn", "streisand", "android", "windows", "ios", "macos"}
)
_SEARCH_SUFFIXES = tuple(
    sorted(
        {
            "иями",
            "ями",
            "ами",
            "ого",
            "ему",
            "ому",
            "ими",
            "ыми",
            "иях",
            "ах",
            "ях",
            "ую",
            "юю",
            "ая",
            "яя",
            "ое",
            "ее",
            "ие",
            "ые",
            "ый",
            "ий",
            "ой",
            "ей",
            "ов",
            "ев",
            "ам",
            "ям",
            "ом",
            "ем",
            "ет",
            "ют",
            "ут",
            "ит",
            "ат",
            "ят",
            "ть",
            "ся",
            "а",
            "я",
            "ы",
            "и",
            "у",
            "ю",
            "е",
            "о",
        },
        key=len,
        reverse=True,
    )
)


class KnowledgeValidationError(ValueError):
    """Fixed-code validation failure for the public support bundle."""


@dataclass(frozen=True, slots=True)
class KnowledgeHit:
    topic_id: str
    keywords: tuple[str, ...]
    body: str
    score: int


@dataclass(frozen=True, slots=True)
class KnowledgeSnapshot:
    version: str
    sha256: str
    topics_by_id: Mapping[str, KnowledgeHit]
    compact_index: str


@dataclass(frozen=True, slots=True)
class _TopicSearchFeatures:
    keyword_tokens: tuple[frozenset[str], ...]
    id_tokens: frozenset[str]
    body_tokens: frozenset[str]
    trigrams: frozenset[str]


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise KnowledgeValidationError("knowledge_duplicate_key")
        result[key] = value
    return result


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join("".join(char if char.isalnum() else " " for char in normalized).split())


def _tokens(value: str) -> frozenset[str]:
    return frozenset(part for part in _normalize_text(value).split() if part)


def _search_stem(token: str) -> str:
    if token in _SEARCH_STOPWORDS:
        return ""
    if len(token) < 5:
        return token
    for suffix in _SEARCH_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)]
    return token


def _search_tokens(value: str) -> frozenset[str]:
    return frozenset(
        stemmed
        for token in _normalize_text(value).split()
        if (stemmed := _search_stem(token))
    )


def _search_trigrams(value: str) -> frozenset[str]:
    cleaned = " ".join(
        token for token in _normalize_text(value).split() if token not in _SEARCH_STOPWORDS
    )
    padded = f" {cleaned} "
    return frozenset(padded[index : index + 3] for index in range(max(0, len(padded) - 2)))


def _validate_public_url(raw_url: str) -> None:
    candidate = raw_url.rstrip(".,);:!?]}")
    try:
        parsed = urlsplit(candidate)
        port = parsed.port
    except ValueError as exc:
        raise KnowledgeValidationError("knowledge_unsafe_url") from exc
    del port
    host = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme != "https"
        or not host
        or host not in _PUBLIC_URL_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise KnowledgeValidationError("knowledge_unsafe_url")
    if host == "connect.pokrov.space" and parsed.path not in {"", "/", "/..."}:
        raise KnowledgeValidationError("knowledge_private_connect_path")


def _validate_model_visible_text(value: str) -> None:
    if _PRIVATE_SCHEME_RE.search(value) or _SECRET_RE.search(value):
        raise KnowledgeValidationError("knowledge_sensitive_text")
    for match in _URL_RE.finditer(value):
        _validate_public_url(match.group(0))
    for match in _IP_CANDIDATE_RE.finditer(value):
        candidate = match.group(0).strip(":")
        if not candidate:
            continue
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            continue
        raise KnowledgeValidationError("knowledge_ip_address")


class SupportKnowledgeStore:
    def __init__(self) -> None:
        self.snapshot: KnowledgeSnapshot | None = None
        self._search_features: Mapping[str, _TopicSearchFeatures] = MappingProxyType({})

    def load(self, path: Path) -> KnowledgeSnapshot:
        try:
            raw = Path(path).read_bytes()
        except OSError as exc:
            raise KnowledgeValidationError("knowledge_file_unavailable") from exc
        if len(raw) > _MAX_FILE_BYTES:
            raise KnowledgeValidationError("knowledge_file_too_large")
        try:
            payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
        except KnowledgeValidationError:
            raise
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise KnowledgeValidationError("knowledge_json_invalid") from exc
        if not isinstance(payload, dict) or set(payload) != _ROOT_KEYS:
            raise KnowledgeValidationError("knowledge_root_invalid")
        if payload["scope"] != "public_support" or payload["language"] != "ru":
            raise KnowledgeValidationError("knowledge_scope_invalid")
        version = payload["version"]
        if not isinstance(version, str) or not 1 <= len(version) <= 64:
            raise KnowledgeValidationError("knowledge_version_invalid")

        rules = payload["rules"]
        if (
            not isinstance(rules, list)
            or len(rules) > _MAX_RULES
            or any(not isinstance(item, str) or not 1 <= len(item) <= 600 for item in rules)
        ):
            raise KnowledgeValidationError("knowledge_rules_invalid")
        fallback = payload["fallback"]
        if (
            not isinstance(fallback, dict)
            or set(fallback) != _FALLBACK_KEYS
            or not isinstance(fallback["title"], str)
            or not isinstance(fallback["body"], str)
            or not 1 <= len(fallback["title"]) <= 80
            or not 1 <= len(fallback["body"]) <= _MAX_BODY_CHARS
        ):
            raise KnowledgeValidationError("knowledge_fallback_invalid")

        raw_topics = payload["topics"]
        if not isinstance(raw_topics, list) or not 1 <= len(raw_topics) <= _MAX_TOPICS:
            raise KnowledgeValidationError("knowledge_topics_invalid")
        topics: dict[str, KnowledgeHit] = {}
        for raw_topic in raw_topics:
            if not isinstance(raw_topic, dict) or set(raw_topic) != _TOPIC_KEYS:
                raise KnowledgeValidationError("knowledge_topic_invalid")
            topic_id = raw_topic["id"]
            keywords = raw_topic["keywords"]
            body = raw_topic["body"]
            if not isinstance(topic_id, str) or not _TOPIC_ID_RE.fullmatch(topic_id) or topic_id in topics:
                raise KnowledgeValidationError("knowledge_topic_id_invalid")
            if (
                not isinstance(keywords, list)
                or not 1 <= len(keywords) <= _MAX_KEYWORDS
                or any(not isinstance(item, str) or not 1 <= len(item) <= _MAX_KEYWORD_CHARS for item in keywords)
            ):
                raise KnowledgeValidationError("knowledge_keywords_invalid")
            if not isinstance(body, str) or not 1 <= len(body) <= _MAX_BODY_CHARS:
                raise KnowledgeValidationError("knowledge_body_invalid")
            normalized_keywords = tuple(_normalize_text(item) for item in keywords)
            if any(not item for item in normalized_keywords):
                raise KnowledgeValidationError("knowledge_keywords_invalid")
            for value in (*normalized_keywords, body):
                _validate_model_visible_text(value)
            topics[topic_id] = KnowledgeHit(
                topic_id=topic_id,
                keywords=normalized_keywords,
                body=body,
                score=0,
            )

        index_lines = [
            json.dumps(
                {"id": topic.topic_id, "keywords": list(topic.keywords)},
                ensure_ascii=False,
                separators=(",", ":"),
            )
            for topic in sorted(topics.values(), key=lambda item: item.topic_id)
        ]
        compact_index = "\n".join(index_lines)
        if len(compact_index) > _MAX_INDEX_CHARS:
            raise KnowledgeValidationError("knowledge_index_too_large")
        candidate = KnowledgeSnapshot(
            version=version,
            sha256=hashlib.sha256(raw).hexdigest(),
            topics_by_id=MappingProxyType(dict(topics)),
            compact_index=compact_index,
        )
        search_features = {
            topic.topic_id: _TopicSearchFeatures(
                keyword_tokens=tuple(_search_tokens(keyword) for keyword in topic.keywords),
                id_tokens=_search_tokens(topic.topic_id.replace("_", " ")),
                body_tokens=_search_tokens(topic.body),
                trigrams=_search_trigrams(" ".join((*topic.keywords, topic.body))),
            )
            for topic in topics.values()
        }
        self.snapshot = candidate
        self._search_features = MappingProxyType(search_features)
        return candidate

    def _require_snapshot(self) -> KnowledgeSnapshot:
        if self.snapshot is None:
            raise KnowledgeValidationError("knowledge_not_loaded")
        return self.snapshot

    def search(
        self,
        query: str,
        limit: int,
        exclude_ids: Collection[str] = (),
    ) -> tuple[KnowledgeHit, ...]:
        snapshot = self._require_snapshot()
        if (
            not isinstance(query, str)
            or not 2 <= len(query) <= 200
            or "://" in query
            or "\\" in query
            or query.startswith("/")
            or re.match(r"^[A-Za-z]:", query)
            or type(limit) is not int
            or not 1 <= limit <= _MAX_RESULT_TOPICS
        ):
            raise KnowledgeValidationError("knowledge_query_invalid")
        excluded = set(exclude_ids)
        if any(not isinstance(item, str) or not _TOPIC_ID_RE.fullmatch(item) for item in excluded):
            raise KnowledgeValidationError("knowledge_exclusion_invalid")
        normalized_query = _normalize_text(query)
        query_tokens = _search_tokens(normalized_query)
        query_trigrams = _search_trigrams(normalized_query)
        padded_query = f" {normalized_query} "
        scored: list[KnowledgeHit] = []
        for topic in snapshot.topics_by_id.values():
            if topic.topic_id in excluded:
                continue
            features = self._search_features[topic.topic_id]
            exact_matches = sum(
                1
                for keyword, tokens in zip(topic.keywords, features.keyword_tokens)
                if tokens and f" {keyword} " in padded_query
            )
            keyword_overlap = sum(
                len(query_tokens & tokens) for tokens in features.keyword_tokens
            )
            covered_keywords = sum(
                1 for tokens in features.keyword_tokens if tokens and tokens <= query_tokens
            )
            trigram_denominator = len(query_trigrams) + len(features.trigrams)
            trigram_dice = (
                2 * len(query_trigrams & features.trigrams) / trigram_denominator
                if trigram_denominator
                else 0.0
            )
            scope_tokens = features.id_tokens & _SEARCH_SCOPE_TOKENS
            scope_penalty = 8 if scope_tokens and not scope_tokens & query_tokens else 0
            score = (
                8 * exact_matches
                + 4 * keyword_overlap
                + 2 * covered_keywords
                + 5 * len(query_tokens & features.id_tokens)
                + 3 * len(query_tokens & features.body_tokens)
                + round(60 * trigram_dice)
                - scope_penalty
            )
            if score > 0:
                scored.append(replace(topic, score=score))
        scored.sort(key=lambda item: (-item.score, item.topic_id))
        return tuple(scored[:limit])

    def read_topic_ids(self, ids: Collection[str]) -> tuple[KnowledgeHit, ...]:
        snapshot = self._require_snapshot()
        requested = tuple(ids)
        if (
            not 1 <= len(requested) <= _MAX_RESULT_TOPICS
            or len(set(requested)) != len(requested)
            or any(not isinstance(item, str) or item not in snapshot.topics_by_id for item in requested)
        ):
            raise KnowledgeValidationError("knowledge_topic_request_invalid")
        return tuple(snapshot.topics_by_id[item] for item in requested)

    def render_hits(self, hits: Collection[KnowledgeHit]) -> str:
        requested = tuple(hits)
        if len(requested) > _MAX_RESULT_TOPICS:
            raise KnowledgeValidationError("knowledge_result_count_invalid")
        accepted: list[dict[str, Any]] = []
        for hit in requested:
            item = {"id": hit.topic_id, "keywords": list(hit.keywords), "body": hit.body}
            candidate = json.dumps(
                {"topics": [*accepted, item]},
                ensure_ascii=False,
                separators=(",", ":"),
            )
            if len(candidate) > _MAX_RESULT_CHARS:
                break
            accepted.append(item)
        return json.dumps({"topics": accepted}, ensure_ascii=False, separators=(",", ":"))
