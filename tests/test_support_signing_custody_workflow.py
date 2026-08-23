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
    prefix = text.split("      - name: Verify hosted custody against client pin", 1)[0]

    assert "pull_request:" not in text
    assert "permissions:\n  contents: read" in text
    assert "POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64" not in prefix
    assert "POKROV_SUPPORT_MODE_CODE_SECRET" not in prefix
    assert "secrets.POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64" in validation
    assert "secrets.POKROV_SUPPORT_MODE_CODE_SECRET" in validation
    assert text.count("persist-credentials: false") == 2


def test_custody_workflow_uploads_only_the_public_receipt() -> None:
    text = WORKFLOW.read_text(encoding="utf-8-sig")
    upload = _step(text, "Upload public custody receipt")

    assert "support-signing-custody-receipt.json" in upload
    assert "if-no-files-found: error" in upload
    assert "include-hidden-files" not in upload
