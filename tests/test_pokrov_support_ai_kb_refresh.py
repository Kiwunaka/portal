from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "pokrov_support_ai_kb_refresh.py"
    spec = importlib.util.spec_from_file_location("pokrov_support_ai_kb_refresh", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class _CountingProvider:
    def __init__(self, response: object | None = None) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def __call__(self, *, url, headers, payload, timeout_seconds):
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "payload": payload,
                "timeout_seconds": timeout_seconds,
            }
        )
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


def _copy_inventory(module, destination: Path) -> Path:
    for relative in module.SOURCE_ALLOWLIST:
        source = module.REPO_ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return destination


def _insert_into_first_allowed_heading(path: Path, text: str) -> None:
    content = path.read_text(encoding="utf-8")
    marker = "## Быстрый старт\n"
    assert marker in content
    path.write_text(content.replace(marker, marker + "\n" + text + "\n", 1), encoding="utf-8")


def test_inventory_is_exact_and_resolves_only_six_regular_in_root_files() -> None:
    module = _load_module()

    assert module.SOURCE_ALLOWLIST == (
        "shared/support-agent-policy.json",
        "docs/user/portal-vpn-user-guide-ru.md",
        "docs/user/compatibility-clients-guide-ru.md",
        "shared/product-facts.json",
        "shared/public-urls.json",
        "shared/tariff-catalog.json",
    )
    assert tuple(path.as_posix() for path in module.resolve_inventory(module.REPO_ROOT)) == module.SOURCE_ALLOWLIST
    assert "AGENTS.md" not in module.SOURCE_ALLOWLIST
    assert not any("architecture" in path or "operations" in path for path in module.SOURCE_ALLOWLIST)


def test_projections_include_exact_headings_and_json_keys_only() -> None:
    module = _load_module()
    projected = {
        item.path.as_posix(): item.text
        for item in module.project_sources(module.REPO_ROOT, module.resolve_inventory(module.REPO_ROOT))
    }

    portal = projected["docs/user/portal-vpn-user-guide-ru.md"]
    portal_headings = [line.lstrip("# ") for line in portal.splitlines() if line.startswith("#")]
    assert portal_headings == list(module.PORTAL_GUIDE_HEADINGS)
    assert "Статус документа" not in portal
    assert "Публичная версия приложения" not in portal
    assert "Как получить бонус `+5 дней`" in portal

    compatibility = projected["docs/user/compatibility-clients-guide-ru.md"]
    compatibility_headings = [line.lstrip("# ") for line in compatibility.splitlines() if line.startswith("#")]
    assert compatibility_headings == list(module.COMPATIBILITY_GUIDE_HEADINGS)
    assert "Официальные справки, по которым сверялась инструкция" not in compatibility

    policy = json.loads(projected["shared/support-agent-policy.json"])
    product = json.loads(projected["shared/product-facts.json"])
    public_urls = json.loads(projected["shared/public-urls.json"])
    tariff = json.loads(projected["shared/tariff-catalog.json"])
    assert tuple(policy) == module.JSON_PROJECTIONS["shared/support-agent-policy.json"]
    assert tuple(product) == module.JSON_PROJECTIONS["shared/product-facts.json"]
    assert tuple(public_urls) == module.JSON_PROJECTIONS["shared/public-urls.json"]
    assert tuple(tariff) == module.JSON_PROJECTIONS["shared/tariff-catalog.json"]
    assert "operations" not in product
    assert "referral_reward" not in product
    assert "contact" not in public_urls


def test_traversal_missing_and_out_of_root_symlink_are_rejected(tmp_path: Path) -> None:
    module = _load_module()

    with pytest.raises(module.KnowledgeValidationError, match="inventory_allowlist_invalid"):
        module.resolve_inventory(module.REPO_ROOT, inventory=("../AGENTS.md",))

    root = _copy_inventory(module, tmp_path / "repo")
    missing = root / module.SOURCE_ALLOWLIST[0]
    missing.unlink()
    with pytest.raises(module.KnowledgeValidationError, match="inventory_file_missing"):
        module.resolve_inventory(root)

    root = _copy_inventory(module, tmp_path / "repo-symlink")
    target = root / module.SOURCE_ALLOWLIST[0]
    outside = tmp_path / "outside-policy.json"
    outside.write_text("{}", encoding="utf-8")
    target.unlink()
    try:
        target.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"Windows symlink unavailable: {exc}")
    with pytest.raises(module.KnowledgeValidationError, match="inventory_symlink_forbidden"):
        module.resolve_inventory(root)


@pytest.mark.parametrize("failure", ("missing", "duplicate"))
def test_missing_or_duplicate_required_heading_stops_before_provider(tmp_path: Path, failure: str) -> None:
    module = _load_module()
    root = _copy_inventory(module, tmp_path / failure)
    guide = root / "docs/user/portal-vpn-user-guide-ru.md"
    text = guide.read_text(encoding="utf-8")
    heading = "## Быстрый старт"
    if failure == "missing":
        text = text.replace(heading, "## Удалённый обязательный раздел", 1)
    else:
        text += f"\n{heading}\nПовтор.\n"
    guide.write_text(text, encoding="utf-8")
    provider = _CountingProvider()

    with pytest.raises(module.KnowledgeValidationError, match=f"markdown_heading_{failure}"):
        module.run_xcody_refresh(repo_root=root, api_key="sk-test", provider=provider)

    assert provider.calls == []


def test_per_file_and_aggregate_caps_fail_closed_before_provider(tmp_path: Path) -> None:
    module = _load_module()
    root = _copy_inventory(module, tmp_path / "oversized")
    guide = root / "docs/user/portal-vpn-user-guide-ru.md"
    guide.write_text(guide.read_text(encoding="utf-8") + ("x" * 50_001), encoding="utf-8")
    provider = _CountingProvider()
    with pytest.raises(module.KnowledgeValidationError, match="source_file_too_large"):
        module.run_xcody_refresh(repo_root=root, api_key="sk-test", provider=provider)
    assert provider.calls == []

    oversized_docs = tuple(
        module.SourceDoc(path=Path(f"safe-{index}.md"), text="я" * 40_001)
        for index in range(5)
    )
    with pytest.raises(module.KnowledgeValidationError, match="source_bundle_too_large"):
        module.build_xcody_request(oversized_docs)
    assert module.MAX_SOURCE_FILE_CHARS == 50_000
    assert module.MAX_SOURCE_BUNDLE_CHARS == 200_000


@pytest.mark.parametrize(
    "unsafe_text",
    (
        "Профиль vless://opaque-user@private.invalid:443",
        "Ключ sk-abcdefghijklmnopqrstuvwxyz123456",
        "Внутренний адрес 10.12.0.7",
        r"Файл C:\private\runtime.env",
        "sudo systemctl restart pokrov",
        "XCODY_API_KEY=private-value",
        "Смотрите https://evil.invalid/private",
        "Сервис http://127.0.0.1:9000/admin",
    ),
)
def test_pre_provider_lint_rejects_unsafe_projected_content(tmp_path: Path, unsafe_text: str) -> None:
    module = _load_module()
    root = _copy_inventory(module, tmp_path / "unsafe")
    _insert_into_first_allowed_heading(root / "docs/user/portal-vpn-user-guide-ru.md", unsafe_text)
    provider = _CountingProvider()

    with pytest.raises(module.KnowledgeValidationError, match="projected_source_unsafe"):
        module.run_xcody_refresh(repo_root=root, api_key="sk-test", provider=provider)

    assert provider.calls == []


def test_run_xcody_uses_openai_chat_shape_and_validates_with_apply_validator(tmp_path: Path) -> None:
    module = _load_module()
    generated = json.loads((module.REPO_ROOT / "shared/support-ai-knowledge.json").read_text(encoding="utf-8"))
    response = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": json.dumps(generated, ensure_ascii=False, separators=(",", ":")),
                },
            }
        ]
    }
    provider = _CountingProvider(response)

    result = module.run_xcody_refresh(
        repo_root=module.REPO_ROOT,
        api_key="sk-test",
        base_url="https://enterprise.xcody.dev/v1",
        provider=provider,
    )

    assert result.payload["scope"] == "public_support"
    assert len(provider.calls) == 1
    call = provider.calls[0]
    assert call["url"] == "https://enterprise.xcody.dev/v1/chat/completions"
    assert call["headers"] == {
        "Authorization": "Bearer sk-test",
        "Content-Type": "application/json",
    }
    request = call["payload"]
    assert request["model"] == "minimax-m3"
    assert request["reasoning_effort"] == "medium"
    assert request["n"] == 1
    assert request["max_tokens"] == 16_000
    assert request["messages"][0]["role"] == "system"
    assert "closed JSON object" in request["messages"][0]["content"]
    source_packet = json.loads(request["messages"][1]["content"])
    projected = {item["path"]: item["content"] for item in source_packet["sources"]}
    assert "operations" not in json.loads(projected["shared/product-facts.json"])
    assert "contact" not in json.loads(projected["shared/public-urls.json"])

    invalid_response = tmp_path / "invalid-response.json"
    generated["unexpected"] = True
    invalid_response.write_text(json.dumps(generated, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(module.KnowledgeValidationError):
        module.apply_saved_response(invalid_response, tmp_path / "out.json")
    assert not (tmp_path / "out.json").exists()


def test_dry_run_audits_without_key_provider_call_or_source_dump(capsys) -> None:
    module = _load_module()
    provider = _CountingProvider()

    result = module.run_xcody_refresh(
        repo_root=module.REPO_ROOT,
        api_key="",
        provider=provider,
        dry_run=True,
    )

    assert result.payload is None
    assert result.audit["source_count"] == 6
    assert result.audit["request_chars"] > 0
    assert provider.calls == []

    exit_code = module.main(["run-xcody", "--dry-run"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert '"source_count":6' in output
    assert "Быстрый старт" not in output
    assert "support-ai-knowledge" not in output


def test_apply_response_writes_atomically_validated_runtime_payload(tmp_path: Path) -> None:
    module = _load_module()
    payload = json.loads((module.REPO_ROOT / "shared/support-ai-knowledge.json").read_text(encoding="utf-8"))
    response = tmp_path / "response.json"
    output = tmp_path / "nested" / "support-ai-knowledge.json"
    response.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    saved = module.apply_saved_response(response, output)

    assert saved["scope"] == "public_support"
    assert json.loads(output.read_text(encoding="utf-8")) == payload
    assert list(output.parent.glob(f".{output.name}.*.tmp")) == []


def test_runtime_support_kb_covers_common_compatible_client_cases() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    payload = json.loads((repo_root / "shared" / "support-ai-knowledge.json").read_text(encoding="utf-8"))
    topic_ids = {str(topic.get("id") or "") for topic in payload.get("topics") or []}

    assert len(topic_ids) >= 45
    for topic_id in {
        "choose_android_client",
        "choose_windows_client",
        "choose_ios_client",
        "paid_rewards",
        "reward_eligibility_unknown",
        "hiddify_import",
        "happ_import",
        "v2rayng_import",
        "v2rayn_import",
        "streisand_import",
        "connected_no_internet",
        "payment_not_applied",
        "ticket_smalltalk_or_test",
        "what_not_to_send_support",
    }:
        assert topic_id in topic_ids


def test_runtime_support_kb_has_exact_compatible_formats_and_paid_reward_boundary() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    payload = json.loads((repo_root / "shared" / "support-ai-knowledge.json").read_text(encoding="utf-8"))
    topics = {str(topic.get("id") or ""): str(topic.get("body") or "") for topic in payload.get("topics") or []}
    serialized = json.dumps(payload, ensure_ascii=False).lower()

    assert "hiddify" in serialized
    assert "happ" in serialized and "format=happ" in serialized
    assert "custom-tunnel-config" in serialized
    assert "замените ?" not in serialized
    assert "второй ?" not in serialized
    assert "активн" in topics["paid_rewards"].lower() and "платн" in topics["paid_rewards"].lower()
    assert "оператор" in topics["reward_eligibility_unknown"].lower()
    assert "hiddify" in topics["happ_import"].lower()
