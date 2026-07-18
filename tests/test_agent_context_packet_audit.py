from pathlib import Path

from scripts.agent_context_packet_audit import audit_text, main


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_audit_passes_when_dynamic_content_is_after_breakpoint() -> None:
    packet = """
# Stable role
You are a POKROV agent.

# Stable rules
Use canonical docs before external critique.

# CACHE BREAKPOINT

date: 2026-05-23
cwd: C:/Users/kiwun/Documents/ai/VPN
request_id: run-123
"""

    result = audit_text("packet.md", packet, min_cacheable_tokens=1)

    assert result.passed
    assert result.breakpoint_line is not None
    assert result.findings == []


def test_audit_fails_when_dynamic_content_is_in_stable_prefix() -> None:
    packet = """
# Stable role
date: 2026-05-23
git status: dirty

# CACHE BREAKPOINT
Task goes here.
"""

    result = audit_text("packet.md", packet, min_cacheable_tokens=1)

    assert not result.passed
    assert [finding.kind for finding in result.findings] == ["current-date", "git-status"]


def test_cli_returns_nonzero_for_prefix_violation(tmp_path) -> None:
    packet = tmp_path / "packet.md"
    packet.write_text("request_id: abc\n# CACHE BREAKPOINT\nTask", encoding="utf-8")

    assert main([str(packet), "--min-cacheable-tokens", "1"]) == 1


def test_ru_origin_handoff_is_current_and_reachable_from_owner() -> None:
    registry = (REPO_ROOT / "docs/README.md").read_text(encoding="utf-8")
    owner = (
        REPO_ROOT / "docs/operations/monitoring-and-visibility.md"
    ).read_text(encoding="utf-8")
    handoff_path = REPO_ROOT / "docs/operations/ru-origin-probe-handoff.md"

    assert handoff_path.is_file()
    assert (
        "| `ACTIVE_EXECUTION` | RU-origin probe | "
        "`docs/operations/ru-origin-probe-handoff.md` | `RECONCILED` |"
    ) in registry
    assert "ru-origin-probe-handoff.md" in owner
    assert "Document class: ACTIVE_EXECUTION" in handoff_path.read_text(
        encoding="utf-8"
    )
