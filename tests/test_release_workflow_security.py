from __future__ import annotations

from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release-orchestrator-manual.yml"


def _run_orchestrator_block() -> str:
    text = WORKFLOW.read_text(encoding="utf-8-sig")
    marker = "      - name: Run orchestrator\n"
    start = text.index(marker)
    tail = text[start + len(marker) :]
    next_step = tail.find("\n      - name: ")
    if next_step != -1:
        tail = tail[:next_step]
    return tail


def test_manual_release_workflow_does_not_interpolate_dispatch_inputs_in_shell() -> None:
    block = _run_orchestrator_block()

    assert "${{ github.event.inputs" not in block
    assert "${{ inputs." not in block.split("        run: |", 1)[1]
    assert "BRAIN_IP: ${{ inputs.brain_ip }}" in block
    assert 'CMD=(python scripts/release_orchestrator.py --brain-ip "$BRAIN_IP"' in block


def test_manual_release_workflow_restricts_secret_bearing_target_hosts() -> None:
    text = WORKFLOW.read_text(encoding="utf-8-sig")
    block = _run_orchestrator_block()

    assert "NODE_PASS_BRAIN" not in text.split("jobs:", 1)[1].split("      - name: Run orchestrator", 1)[0]
    assert "NODE_PASS_BRAIN: ${{ secrets.NODE_PASS_BRAIN }}" in block
    assert "82.21.114.104) ;;" in block
    assert "pokrov.space) ;;" in block
    assert "api.pokrov.space) ;;" in block
    assert "brain_ip must match the canonical control-plane host" in block
