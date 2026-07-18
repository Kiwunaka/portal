import copy
import json
import sys
import tempfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))


def _topic(topic_id: str, *, body: str = "Безопасный публичный ответ.", keywords: list[str] | None = None) -> dict:
    return {
        "id": topic_id,
        "keywords": keywords or [topic_id.replace("_", " ")],
        "body": body,
    }


def _valid_bundle() -> dict:
    return {
        "version": "test-1",
        "scope": "public_support",
        "language": "ru",
        "rules": ["Answer from supplied topics only."],
        "fallback": {"title": "manual_support", "body": "Передайте обращение оператору."},
        "topics": [
            _topic(
                "connected_no_internet",
                body="Переподключитесь и временно проверьте Private DNS.",
                keywords=["connected", "no internet", "нет интернета", "подключено но"],
            ),
            _topic(
                "slow_speed",
                body="Выберите ближайшую локацию и проверьте другую сеть.",
                keywords=["slow", "медленно", "скорость"],
            ),
        ],
    }


def _write_bundle(payload: dict) -> Path:
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False)
    with handle:
        json.dump(payload, handle, ensure_ascii=False)
    return Path(handle.name)


def test_repository_bundle_loads_and_ranks_known_connection_issue() -> None:
    from support_agent_knowledge import SupportKnowledgeStore

    store = SupportKnowledgeStore()
    snapshot = store.load(REPO_ROOT / "shared" / "support-ai-knowledge.json")
    hits = store.search("Подключено, но сайты не открываются", limit=3)

    assert len(snapshot.topics_by_id) == 60
    assert hits
    assert hits[0].topic_id == "connected_no_internet"
    assert len(snapshot.compact_index) <= 8_000
    assert "Support knowledge" not in snapshot.compact_index
    assert "Если вопрос зависит от аккаунта" not in snapshot.compact_index


def test_search_is_deterministic_bounded_and_can_exclude_prior_hits() -> None:
    from support_agent_knowledge import KnowledgeValidationError, SupportKnowledgeStore

    path = _write_bundle(_valid_bundle())
    store = SupportKnowledgeStore()
    try:
        store.load(path)
        first = store.search("подключено но нет интернета", limit=2)
        second = store.search("подключено но нет интернета", limit=2)
        excluded = store.search(
            "подключено но нет интернета",
            limit=2,
            exclude_ids={"connected_no_internet"},
        )
        with pytest.raises(KnowledgeValidationError):
            store.search("https://private.invalid/path", limit=2)
        with pytest.raises(KnowledgeValidationError):
            store.search("C:\\server\\support.txt", limit=2)
    finally:
        path.unlink(missing_ok=True)

    assert first == second
    assert first[0].topic_id == "connected_no_internet"
    assert all(hit.topic_id != "connected_no_internet" for hit in excluded)


def test_loader_rejects_unsafe_or_unbounded_bundles() -> None:
    from support_agent_knowledge import KnowledgeValidationError, SupportKnowledgeStore

    variants: list[tuple[str, dict]] = []

    wrong_scope = _valid_bundle()
    wrong_scope["scope"] = "internal_support"
    variants.append(("wrong-scope", wrong_scope))

    too_many = _valid_bundle()
    too_many["topics"] = [_topic(f"topic_{index}") for index in range(101)]
    variants.append(("too-many-topics", too_many))

    duplicate = _valid_bundle()
    duplicate["topics"].append(copy.deepcopy(duplicate["topics"][0]))
    variants.append(("duplicate-id", duplicate))

    invalid_id = _valid_bundle()
    invalid_id["topics"][0]["id"] = "../../private"
    variants.append(("invalid-id", invalid_id))

    too_many_keywords = _valid_bundle()
    too_many_keywords["topics"][0]["keywords"] = [f"keyword-{index}" for index in range(21)]
    variants.append(("too-many-keywords", too_many_keywords))

    oversized_body = _valid_bundle()
    oversized_body["topics"][0]["body"] = "а" * 1201
    variants.append(("oversized-body", oversized_body))

    private_link = _valid_bundle()
    private_link["topics"][0]["body"] = "Импортируйте vless://private-user@private.invalid:443"
    variants.append(("private-link", private_link))

    secret = _valid_bundle()
    secret["topics"][0]["body"] = "Ключ sk-abcdefghijklmnopqrstuvwxyz012345"
    variants.append(("secret", secret))

    labelled_secret = _valid_bundle()
    labelled_secret["topics"][0]["body"] = "private_token=ProviderBoundaryPrivateToken"
    variants.append(("labelled-secret", labelled_secret))

    store = SupportKnowledgeStore()
    for name, payload in variants:
        path = _write_bundle(payload)
        try:
            try:
                store.load(path)
            except KnowledgeValidationError:
                pass
            else:
                pytest.fail(f"unsafe knowledge variant accepted: {name}")
        finally:
            path.unlink(missing_ok=True)


def test_loader_rejects_file_over_65536_bytes_before_json_materialization() -> None:
    from support_agent_knowledge import KnowledgeValidationError, SupportKnowledgeStore

    handle = tempfile.NamedTemporaryFile("wb", suffix=".json", delete=False)
    with handle:
        handle.write(b"{" + (b" " * 65_536) + b"}")
    path = Path(handle.name)
    try:
        with pytest.raises(KnowledgeValidationError, match="knowledge_file_too_large"):
            SupportKnowledgeStore().load(path)
    finally:
        path.unlink(missing_ok=True)


def test_exact_id_reads_reject_unknown_and_more_than_five_topics() -> None:
    from support_agent_knowledge import KnowledgeValidationError, SupportKnowledgeStore

    payload = _valid_bundle()
    payload["topics"] = [_topic(f"safe_topic_{index}") for index in range(6)]
    path = _write_bundle(payload)
    store = SupportKnowledgeStore()
    try:
        store.load(path)
        with pytest.raises(KnowledgeValidationError):
            store.read_topic_ids(["missing_topic"])
        with pytest.raises(KnowledgeValidationError):
            store.read_topic_ids([f"safe_topic_{index}" for index in range(6)])
    finally:
        path.unlink(missing_ok=True)


def test_render_hits_stops_at_topic_boundary_under_6000_chars() -> None:
    from support_agent_knowledge import SupportKnowledgeStore

    payload = _valid_bundle()
    payload["topics"] = [
        _topic(f"large_topic_{index}", body=(chr(1072 + index) * 1190))
        for index in range(5)
    ]
    path = _write_bundle(payload)
    store = SupportKnowledgeStore()
    try:
        store.load(path)
        hits = store.read_topic_ids([f"large_topic_{index}" for index in range(5)])
        rendered = store.render_hits(hits)
    finally:
        path.unlink(missing_ok=True)

    assert len(rendered) <= 6_000
    parsed = json.loads(rendered)
    assert 1 <= len(parsed["topics"]) < 5
    assert all(len(item["body"]) == 1190 for item in parsed["topics"])


def test_public_pokrov_url_is_allowed_but_personal_connect_path_is_not() -> None:
    from support_agent_knowledge import KnowledgeValidationError, SupportKnowledgeStore

    public = _valid_bundle()
    public["topics"][0]["body"] = "Откройте https://pokrov.space/ и официальный кабинет."
    public_path = _write_bundle(public)
    try:
        SupportKnowledgeStore().load(public_path)
    finally:
        public_path.unlink(missing_ok=True)

    personal = _valid_bundle()
    personal["topics"][0]["body"] = "Откройте https://connect.pokrov.space/private-token-value"
    personal_path = _write_bundle(personal)
    try:
        with pytest.raises(KnowledgeValidationError):
            SupportKnowledgeStore().load(personal_path)
    finally:
        personal_path.unlink(missing_ok=True)
