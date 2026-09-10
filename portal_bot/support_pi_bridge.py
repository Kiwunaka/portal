"""Bounded stdio transport to pi-agent-core; no shell and no inherited secrets."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from support_agent_provider import ProviderCallError


async def run_pi_case(*, config, prompt: str, question: str, tools: list,
                      execute, timeout: float) -> dict:
    process = None
    try:
        async def run():
            nonlocal process
            process = await asyncio.create_subprocess_exec(
                os.getenv("SUPPORT_PI_NODE", "node"),
                str(Path(__file__).parent / "support_pi" / "runner.mjs"),
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL, limit=100000,
                env={key: os.environ[key] for key in ("PATH", "SystemRoot", "TEMP", "TMP") if key in os.environ},
            )

            async def send(value):
                process.stdin.write((json.dumps(value, ensure_ascii=False) + "\n").encode())
                await process.stdin.drain()

            await send({"api_key": config.api_key, "model": "deepseek/deepseek-v4.1-flash",
                        "prompt": prompt, "question": question, "tools": tools,
                        "context_chars": min(config.max_context_chars, 30000),
                        "timeout_ms": int(timeout * 1000)})
            calls = 0
            allowed = {tool["name"] for tool in tools}
            while True:
                line = await process.stdout.readline()
                if not line:
                    raise ValueError("pi_eof")
                event = json.loads(line)
                if event.get("type") == "error":
                    code = {"context_budget": "provider_request_too_large", "incomplete": "provider_choice_invalid",
                            "invalid_reply": "provider_content_invalid"}.get(event.get("code"), "provider_request_error")
                    raise ProviderCallError(retryable=False, code=code, status=0)
                if event.get("type") == "done":
                    if not isinstance(event.get("content"), str) or len(event["content"]) > 16000:
                        raise ValueError("pi_output")
                    return event
                if event.get("type") != "tool" or event.get("name") not in allowed or calls >= 12:
                    raise ValueError("pi_protocol")
                calls += 1
                await send(await execute(event["name"], event.get("args")))
        return await asyncio.wait_for(run(), timeout=timeout)
    except (OSError, ValueError, KeyError, asyncio.TimeoutError):
        raise ProviderCallError(retryable=False, code="provider_request_error", status=0) from None
    finally:
        if process is not None:
            if process.returncode is None:
                process.kill()
            await process.wait()
