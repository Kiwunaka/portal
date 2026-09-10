from __future__ import annotations

from pathlib import Path


WORKFLOW = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "support-signing-custody.yml"
)


def _step(text: str, name: str) -> str:
    marker = f"      - name: {name}\n"
    start = text.index(marker)
    tail = text[start + len(marker) :]
    next_step = tail.find("\n      - name: ")
    return tail if next_step == -1 else tail[:next_step]


def test_custody_workflow_exposes_secrets_only_to_trusted_validation_step() -> None:
    text = WORKFLOW.read_text(encoding="utf-8-sig")
    validation = _step(text, "Verify hosted custody against client pin")
    checkout = _step(text, "Checkout trusted platform promotion line")
    prefix = text.split("      - name: Verify hosted custody against client pin", 1)[0]

    assert "pull_request:" not in text
    assert "    if: github.ref == 'refs/heads/master'" in text
    assert "ref: ${{ github.sha }}" in checkout
    assert "permissions:\n  contents: read" in text
    assert "POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64" not in prefix
    assert "POKROV_SUPPORT_MODE_CODE_SECRET" not in prefix
    assert "secrets.POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64" in validation
    assert "secrets.POKROV_SUPPORT_MODE_CODE_SECRET" in validation
    assert text.count("persist-credentials: false") == 2


def test_custody_workflow_uploads_only_public_receipt_and_optional_public_key_set() -> None:
    text = WORKFLOW.read_text(encoding="utf-8-sig")
    upload = _step(text, "Upload public custody receipt")

    assert "support-signing-custody-receipt.json" in upload
    assert "if-no-files-found: error" in upload
    assert "include-hidden-files" not in upload
    key_set = _step(text, "Upload signed public recipient key set")
    assert "github.event_name == 'workflow_dispatch' && inputs.recipient_key_id != ''" in key_set
    assert "path: ${{ runner.temp }}/support-signed-key-set.json" in key_set
    assert "if-no-files-found: error" in key_set
    validation = _step(text, "Verify hosted custody against client pin")
    env, run = validation.split("        run:", 1)
    assert "${{ inputs.recipient_key_id }}" in env
    assert "${{ inputs.recipient_public_key_b64 }}" in env
    assert "${{ inputs." not in run


def test_runtime_provision_requires_explicit_dispatch_and_has_only_public_artifact() -> None:
    text = WORKFLOW.read_text(encoding="utf-8-sig")
    step = _step(text, "Provision signer to prepared Brain receiver")
    upload = _step(text, "Upload public runtime provisioning receipt")
    guard = "if: github.event_name == 'workflow_dispatch' && inputs.provision_brain_runtime"
    assert guard in step and guard in upload
    assert "default: false" in text.split("      provision_brain_runtime:", 1)[1].split("      recipient_key_id:", 1)[0]
    assert "secrets.POKROV_SUPPORT_PROVISION_SSH_KEY" in step
    assert text.count("secrets.POKROV_SUPPORT_PROVISION_SSH_KEY") == 1
    assert "scripts/provision_support_mode_runtime.py" in step
    assert "path: ${{ runner.temp }}/support-runtime-provision-receipt.json" in upload
    assert "include-hidden-files" not in upload
