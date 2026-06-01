"""Read-only operator copilot scaffold using OpenAI function calling.

This script exposes a tiny, audited tool surface for local operator questions.
The model may request tools, but only this process executes them, and every
tool here is read-only or pure formatting.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = "gpt-4.1-mini"

OPERATOR_INSTRUCTIONS = """You are the POKROV operator copilot.

Use tools only for read-only inspection, local guardrail checks, and handoff
formatting. You are not allowed to deploy, SSH, change users, grant access,
revoke access, alter payment state, print secrets, or claim that a manual owner
test has passed.

Keep POKROV release honesty:
- outside-store Android + Windows beta is GO only with accepted skips.
- do not claim store availability, stable 1.0.0, trusted Windows signing, raw
  Android physical-audit proof, or RU-origin readiness without current evidence.
- public wording must avoid direct-meaning product use of "VPN"; legacy
  "POKROV VPN" may appear only as a compatibility identifier.
- keep current-origin, brain-origin, and RU-origin evidence separate.

If a task needs access to secrets, payment dashboards, live deploy approval,
physical devices, Telegram accounts, or RU probe SSH, label it with the matching
manual status instead of pretending it is locally verified.
"""

CANONICAL_DOCS = {
    "docs_index": "docs/README.md",
    "product": "docs/product/portal-vpn-product.md",
    "public_beta_prd": "docs/product/public-beta-prd.md",
    "payment_contract": "docs/product/payment-and-access-key-contract.md",
    "system": "docs/architecture/system-overview.md",
    "app_first": "docs/architecture/app-first-and-bonus-flows.md",
    "deployment": "docs/operations/deployment-and-access.md",
    "monitoring": "docs/operations/monitoring-and-visibility.md",
    "release_runbook": "docs/operations/public-beta-release-runbook.md",
    "developer_guide": "docs/developer/developer-guide.md",
    "repository_map": "docs/developer/repository-map.md",
    "context_cost": "docs/developer/orchestration/context-cost-harnesses.md",
    "launch_decision": "docs/developer/work-orders/2026-04-open-beta-v4/13-launch-decision.md",
    "known_issues": "docs/launch/known-issues.md",
    "support_macros": "docs/launch/support-macros.md",
}

MANUAL_STATUSES = {
    "PASS",
    "FAIL",
    "SKIPPED_BY_OWNER",
    "SKIPPED_BY_OPERATOR",
    "OPERATOR_ATTESTED",
    "MANUAL_OWNER_TEST",
    "BLOCKED_BY_ACCESS",
    "NOT_REQUESTED",
    "UNKNOWN",
}


class ToolExecutionError(RuntimeError):
    """Raised when a model requests an unsupported or unsafe tool call."""


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[[dict[str, Any]], dict[str, Any]]

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "strict": True,
        }


def _json_schema_object(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(required if required is not None else properties.keys()),
        "additionalProperties": False,
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 80)].rstrip() + "\n...[truncated]"


def _tool_list_pokrov_canon(args: dict[str, Any]) -> dict[str, Any]:
    _ = args
    product_facts = _read_json(REPO_ROOT / "shared" / "product-facts.json")
    public_urls = _read_json(REPO_ROOT / "shared" / "public-urls.json")
    return {
        "brand": "POKROV",
        "identity_model": (product_facts.get("strategy") or {}).get("identity_model", "app-first"),
        "trial_days": (product_facts.get("trial") or {}).get("days", 5),
        "public_urls": public_urls,
        "canonical_docs": CANONICAL_DOCS,
        "release_truth": {
            "outside_store_android_windows_beta": "GO as of 2026-05-15 with accepted skips",
            "stable_or_store_release": "blocked until separate gates are green",
            "ru_origin_readiness": "do not claim without current RU-origin evidence",
        },
    }


def _tool_read_canonical_doc_excerpt(args: dict[str, Any]) -> dict[str, Any]:
    path_key = str(args.get("path_key") or "").strip()
    query = args.get("query")
    max_chars = int(args.get("max_chars") or 4000)
    if path_key not in CANONICAL_DOCS:
        raise ToolExecutionError(f"unsupported canonical doc key: {path_key}")
    max_chars = max(500, min(max_chars, 12000))
    path = (REPO_ROOT / CANONICAL_DOCS[path_key]).resolve()
    path.relative_to(REPO_ROOT.resolve())
    text = path.read_text(encoding="utf-8", errors="replace")
    if query:
        needle = str(query).casefold()
        lines = text.splitlines()
        matches: list[str] = []
        for index, line in enumerate(lines):
            if needle in line.casefold():
                start = max(0, index - 2)
                end = min(len(lines), index + 3)
                block = "\n".join(f"{line_no + 1}: {lines[line_no]}" for line_no in range(start, end))
                matches.append(block)
        excerpt = "\n\n---\n\n".join(matches) if matches else ""
    else:
        excerpt = text
    return {
        "path_key": path_key,
        "path": CANONICAL_DOCS[path_key],
        "query": query,
        "excerpt": _truncate(excerpt or "No matching excerpt found.", max_chars),
    }


def _tool_run_public_copy_guardrails(args: dict[str, Any]) -> dict[str, Any]:
    timeout_sec = max(5, min(int(args.get("timeout_sec") or 60), 240))
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_public_copy_guardrails.py", "-q"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=timeout_sec,
        check=False,
    )
    output = (completed.stdout + "\n" + completed.stderr).strip()
    return {
        "command": "python -m pytest tests/test_public_copy_guardrails.py -q",
        "exit_code": completed.returncode,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "output": _truncate(output, 6000),
    }


def _tool_check_payment_email_readiness(args: dict[str, Any]) -> dict[str, Any]:
    plan_code = str(args.get("plan_code") or "start_99").strip() or "start_99"
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        import payment_email_readiness_smoke
    finally:
        if sys.path[0] == str(REPO_ROOT / "scripts"):
            sys.path.pop(0)
    return payment_email_readiness_smoke.build_report(env=os.environ, plan_code=plan_code)


def _tool_build_origin_status_handoff(args: dict[str, Any]) -> dict[str, Any]:
    current_origin = _normalize_manual_status(args.get("current_origin"))
    brain_origin = _normalize_manual_status(args.get("brain_origin"))
    ru_origin = _normalize_manual_status(args.get("ru_origin"))
    notes = str(args.get("notes") or "").strip()
    lines = [
        "current-origin check: " + current_origin,
        "brain-origin check: " + brain_origin,
        "RU-origin check: " + ru_origin,
    ]
    if notes:
        lines.append("notes: " + notes)
    return {
        "current_origin": current_origin,
        "brain_origin": brain_origin,
        "ru_origin": ru_origin,
        "handoff": "\n".join(lines),
    }


def _normalize_manual_status(value: Any) -> str:
    status = str(value or "UNKNOWN").strip().upper()
    return status if status in MANUAL_STATUSES else "UNKNOWN"


def build_tool_registry() -> dict[str, ToolSpec]:
    tools = [
        ToolSpec(
            name="pokrov_list_canon",
            description="Return POKROV public facts, canonical docs, and release-truth reminders.",
            parameters=_json_schema_object({}),
            handler=_tool_list_pokrov_canon,
        ),
        ToolSpec(
            name="pokrov_read_canonical_doc_excerpt",
            description="Read an excerpt from an allowlisted canonical doc. Never reads arbitrary files.",
            parameters=_json_schema_object(
                {
                    "path_key": {
                        "type": "string",
                        "enum": sorted(CANONICAL_DOCS.keys()),
                        "description": "Allowlisted canonical doc key.",
                    },
                    "query": {
                        "type": ["string", "null"],
                        "description": "Optional case-insensitive search query.",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum excerpt characters, clamped between 500 and 12000.",
                    },
                }
            ),
            handler=_tool_read_canonical_doc_excerpt,
        ),
        ToolSpec(
            name="pokrov_run_public_copy_guardrails",
            description="Run local public-copy guardrail tests. Read-only; no network, SSH, or secrets.",
            parameters=_json_schema_object(
                {
                    "timeout_sec": {
                        "type": "integer",
                        "description": "Timeout in seconds, clamped between 5 and 240.",
                    }
                }
            ),
            handler=_tool_run_public_copy_guardrails,
        ),
        ToolSpec(
            name="pokrov_check_payment_email_readiness",
            description="Classify local Lava.top and email readiness env without printing secret values.",
            parameters=_json_schema_object(
                {
                    "plan_code": {
                        "type": "string",
                        "description": "Plan code to check for offer-specific env, for example start_99.",
                    }
                }
            ),
            handler=_tool_check_payment_email_readiness,
        ),
        ToolSpec(
            name="pokrov_build_origin_status_handoff",
            description="Format separate current-origin, brain-origin, and RU-origin evidence statuses.",
            parameters=_json_schema_object(
                {
                    "current_origin": {"type": "string", "enum": sorted(MANUAL_STATUSES)},
                    "brain_origin": {"type": "string", "enum": sorted(MANUAL_STATUSES)},
                    "ru_origin": {"type": "string", "enum": sorted(MANUAL_STATUSES)},
                    "notes": {"type": "string"},
                }
            ),
            handler=_tool_build_origin_status_handoff,
        ),
    ]
    return {tool.name: tool for tool in tools}


def tool_schemas() -> list[dict[str, Any]]:
    return [tool.schema() for tool in build_tool_registry().values()]


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    registry = build_tool_registry()
    if name not in registry:
        raise ToolExecutionError(f"unsupported tool: {name}")
    return registry[name].handler(arguments)


def _load_openai_client() -> Any:
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "The OpenAI SDK is required for ask. Install it in the ops "
            "environment, for example: python -m pip install openai"
        ) from exc
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _item_value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _extract_function_calls(response: Any) -> list[dict[str, str]]:
    output = _item_value(response, "output", []) or []
    calls: list[dict[str, str]] = []
    for item in output:
        if _item_value(item, "type") != "function_call":
            continue
        calls.append(
            {
                "name": str(_item_value(item, "name", "")),
                "arguments": str(_item_value(item, "arguments", "{}") or "{}"),
                "call_id": str(_item_value(item, "call_id", "")),
            }
        )
    return calls


def _response_text(response: Any) -> str:
    text = _item_value(response, "output_text", "")
    if text:
        return str(text)
    output = _item_value(response, "output", []) or []
    fragments: list[str] = []
    for item in output:
        if _item_value(item, "type") != "message":
            continue
        for content in _item_value(item, "content", []) or []:
            if _item_value(content, "type") == "output_text":
                fragments.append(str(_item_value(content, "text", "")))
    return "\n".join(fragment for fragment in fragments if fragment)


def run_openai_loop(question: str, *, model: str = DEFAULT_MODEL, max_steps: int = 6) -> dict[str, Any]:
    client = _load_openai_client()
    response = client.responses.create(
        model=model,
        instructions=OPERATOR_INSTRUCTIONS,
        input=question,
        tools=tool_schemas(),
        parallel_tool_calls=False,
    )
    trace: list[dict[str, Any]] = []

    for _step in range(max(1, max_steps)):
        calls = _extract_function_calls(response)
        if not calls:
            return {
                "response_id": _item_value(response, "id", ""),
                "answer": _response_text(response),
                "trace": trace,
            }
        outputs: list[dict[str, str]] = []
        for call in calls:
            try:
                args = json.loads(call["arguments"] or "{}")
                result = execute_tool(call["name"], args)
            except Exception as exc:  # noqa: BLE001 - returned to model as tool error
                result = {"error": type(exc).__name__, "message": str(exc)}
            trace.append({"tool": call["name"], "arguments": call["arguments"], "result": result})
            outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": call["call_id"],
                    "output": json.dumps(result, ensure_ascii=False),
                }
            )
        response = client.responses.create(
            model=model,
            instructions=OPERATOR_INSTRUCTIONS,
            input=outputs,
            previous_response_id=_item_value(response, "id", None),
            tools=tool_schemas(),
            parallel_tool_calls=False,
        )

    return {
        "response_id": _item_value(response, "id", ""),
        "answer": _response_text(response),
        "trace": trace,
        "warning": "max tool-call steps reached",
    }


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="POKROV read-only operator copilot.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-tools", help="Print available OpenAI function schemas.")

    tool_parser = subparsers.add_parser("tool", help="Run one local tool directly.")
    tool_parser.add_argument("name")
    tool_parser.add_argument("--args-json", default="{}")
    tool_parser.add_argument("--args-file", default="", help="Path to a UTF-8 JSON file with tool arguments.")

    ask_parser = subparsers.add_parser("ask", help="Ask through OpenAI with read-only tools enabled.")
    ask_parser.add_argument("question")
    ask_parser.add_argument("--model", default=os.getenv("POKROV_OPENAI_MODEL", DEFAULT_MODEL))
    ask_parser.add_argument("--max-steps", type=int, default=6)

    args = parser.parse_args(argv)
    if args.command == "list-tools":
        _print_json(tool_schemas())
        return 0
    if args.command == "tool":
        raw_args = Path(args.args_file).read_text(encoding="utf-8-sig") if args.args_file else args.args_json
        payload = execute_tool(args.name, json.loads(raw_args))
        _print_json(payload)
        return 0
    if args.command == "ask":
        payload = run_openai_loop(args.question, model=args.model, max_steps=args.max_steps)
        _print_json(payload)
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
