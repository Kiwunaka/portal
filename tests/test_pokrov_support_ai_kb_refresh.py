from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "scripts" / "pokrov_support_ai_kb_refresh.py"
    spec = importlib.util.spec_from_file_location("pokrov_support_ai_kb_refresh", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_source_inventory_is_allowlisted_and_excludes_secret_paths() -> None:
    module = _load_module()

    paths = [path.as_posix() for path in module.collect_source_docs(module.REPO_ROOT)]

    assert "AGENTS.md" in paths
    assert "docs/architecture/support-feedback-flow.md" in paths
    assert "docs/user/portal-vpn-user-guide-ru.md" in paths
    assert "docs/user/compatibility-clients-guide-ru.md" in paths
    forbidden = ("portal_bot/.env", "VPN NODE SSH KEYS", "ops-local", "secrets for merchant")
    assert not any(part in path for path in paths for part in forbidden)


def test_prompt_packet_mentions_pi_openrouter_and_json_contract() -> None:
    module = _load_module()

    prompt = module.build_pi_prompt(
        [
            module.SourceDoc(
                path=Path("docs/user/portal-vpn-user-guide-ru.md"),
                text="Trial is 5 days. Support must not ask for card details.",
            )
        ]
    )

    assert "Pi harness" in prompt
    assert "OpenRouter" in prompt
    assert "deepseek/deepseek-v4-flash" in prompt
    assert "support-ai-knowledge.json" in prompt
    assert '"topics"' in prompt
    assert "Do not output markdown fences" in prompt


def test_extract_json_payload_accepts_fenced_output_and_validates_shape() -> None:
    module = _load_module()

    raw = """```json
{"version":"test","scope":"public_support","language":"ru","rules":["Answer briefly"],"fallback":{"body":"Escalate"},"topics":[{"id":"trial","keywords":["trial"],"body":"Trial is 5 days."}]}
```"""

    payload = module.extract_json_payload(raw)

    assert payload["version"] == "test"
    assert payload["topics"][0]["id"] == "trial"


def test_write_validated_payload_preserves_json_without_secrets() -> None:
    module = _load_module()
    payload = {
        "version": "test",
        "scope": "public_support",
        "language": "ru",
        "rules": ["Answer briefly"],
        "fallback": {"body": "Escalate"},
        "topics": [{"id": "trial", "keywords": ["trial"], "body": "Trial is 5 days."}],
    }

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "support-ai-knowledge.json"
        module.write_validated_payload(payload, out)
        saved = json.loads(out.read_text(encoding="utf-8"))

    assert saved["topics"][0]["body"] == "Trial is 5 days."
    assert "secret" not in json.dumps(saved, ensure_ascii=False).lower()


def test_runtime_support_kb_covers_common_compatible_client_cases() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    payload = json.loads((repo_root / "shared" / "support-ai-knowledge.json").read_text(encoding="utf-8"))
    topic_ids = {str(topic.get("id") or "") for topic in payload.get("topics") or []}

    assert len(topic_ids) >= 45
    for topic_id in {
        "choose_android_client",
        "choose_windows_client",
        "choose_ios_client",
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
