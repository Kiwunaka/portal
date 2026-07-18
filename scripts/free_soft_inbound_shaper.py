#!/usr/bin/env python3
from __future__ import annotations

"""Plan, audit, apply, or roll back the dedicated free-soft nftables policy.

The policy is intentionally local-only and owns one stable nftables table. It
polices encrypted transport traffic on a dedicated TCP/UDP inbound port per
client IP in each direction. Clients behind the same NAT address share a cap;
this is not account-level enforcement.
"""

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence, TextIO


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "infra" / "free-soft-inbound.json"

NFT_FAMILY = "inet"
NFT_TABLE = "pokrov_free_soft"
NFT_INPUT_CHAIN = "pkr_soft_input"
NFT_OUTPUT_CHAIN = "pkr_soft_output"
POLICY_VERSION = 1

_IFACE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,14}$")
_RATE_RE = re.compile(r"^([1-9][0-9]{0,4})(kbit|mbit)$")
_TIMEOUT_RE = re.compile(r"^([1-9][0-9]{0,4})(s|m|h)$")

_MIN_RATE_BITS = 64_000
_MAX_RATE_BITS = 1_000_000_000
_MIN_METER_SIZE = 128
_MAX_METER_SIZE = 262_144
_MIN_TIMEOUT_SECONDS = 10
_MAX_TIMEOUT_SECONDS = 86_400
_MAX_BURST_KBYTES = 1_024


class ConfigError(ValueError):
    """Configuration error with a stable, non-sensitive error code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _strict_int(value: Any, *, code: str, message: str) -> int:
    if isinstance(value, bool):
        raise ConfigError(code, message)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isascii() and value.isdigit():
        return int(value, 10)
    raise ConfigError(code, message)


def _rate_bits(rate: str) -> int:
    match = _RATE_RE.fullmatch(rate)
    if match is None:
        raise ConfigError("invalid_rate", "rate must use a supported bit-rate unit")
    value = int(match.group(1), 10)
    multiplier = 1_000 if match.group(2) == "kbit" else 1_000_000
    bits_per_second = value * multiplier
    if not _MIN_RATE_BITS <= bits_per_second <= _MAX_RATE_BITS:
        raise ConfigError("invalid_rate", "rate is outside the supported range")
    return bits_per_second


def _timeout_seconds(timeout: str) -> int:
    match = _TIMEOUT_RE.fullmatch(timeout)
    if match is None:
        raise ConfigError(
            "invalid_meter_timeout",
            "meter timeout must use a supported duration unit",
        )
    value = int(match.group(1), 10)
    multiplier = {"s": 1, "m": 60, "h": 3_600}[match.group(2)]
    seconds = value * multiplier
    if not _MIN_TIMEOUT_SECONDS <= seconds <= _MAX_TIMEOUT_SECONDS:
        raise ConfigError(
            "invalid_meter_timeout",
            "meter timeout is outside the supported range",
        )
    return seconds


@dataclass(frozen=True)
class ShaperConfig:
    iface: str
    port: int
    rate: str
    meter_size: int = 65_535
    meter_timeout: str = "10m"
    burst_kbytes: int = 64

    def __post_init__(self) -> None:
        if not isinstance(self.iface, str) or _IFACE_RE.fullmatch(self.iface) is None:
            raise ConfigError("invalid_iface", "interface name is invalid")
        if isinstance(self.port, bool) or not isinstance(self.port, int):
            raise ConfigError("invalid_port", "port must be an integer")
        if not 1 <= self.port <= 65_535:
            raise ConfigError("invalid_port", "port is outside the supported range")
        if not isinstance(self.rate, str):
            raise ConfigError("invalid_rate", "rate must use a supported bit-rate unit")
        _rate_bits(self.rate)
        if isinstance(self.meter_size, bool) or not isinstance(self.meter_size, int):
            raise ConfigError("invalid_meter_size", "meter size must be an integer")
        if not _MIN_METER_SIZE <= self.meter_size <= _MAX_METER_SIZE:
            raise ConfigError(
                "invalid_meter_size",
                "meter size is outside the supported range",
            )
        if not isinstance(self.meter_timeout, str):
            raise ConfigError(
                "invalid_meter_timeout",
                "meter timeout must use a supported duration unit",
            )
        _timeout_seconds(self.meter_timeout)
        if isinstance(self.burst_kbytes, bool) or not isinstance(self.burst_kbytes, int):
            raise ConfigError("invalid_burst", "burst must be an integer")
        if not 1 <= self.burst_kbytes <= _MAX_BURST_KBYTES:
            raise ConfigError("invalid_burst", "burst is outside the supported range")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ShaperConfig":
        iface_value = payload.get("iface")
        if not isinstance(iface_value, str) or _IFACE_RE.fullmatch(iface_value) is None:
            raise ConfigError("invalid_iface", "interface name is invalid")

        port = _strict_int(
            payload.get("port"),
            code="invalid_port",
            message="port must be an integer",
        )
        if not 1 <= port <= 65_535:
            raise ConfigError("invalid_port", "port is outside the supported range")

        rate_value = payload.get("rate")
        if not isinstance(rate_value, str):
            raise ConfigError("invalid_rate", "rate must use a supported bit-rate unit")
        _rate_bits(rate_value)

        meter_size = _strict_int(
            payload.get("meter_size", 65_535),
            code="invalid_meter_size",
            message="meter size must be an integer",
        )
        if not _MIN_METER_SIZE <= meter_size <= _MAX_METER_SIZE:
            raise ConfigError(
                "invalid_meter_size",
                "meter size is outside the supported range",
            )

        timeout_value = payload.get("meter_timeout", "10m")
        if not isinstance(timeout_value, str):
            raise ConfigError(
                "invalid_meter_timeout",
                "meter timeout must use a supported duration unit",
            )
        _timeout_seconds(timeout_value)

        burst_kbytes = _strict_int(
            payload.get("burst_kbytes", 64),
            code="invalid_burst",
            message="burst must be an integer",
        )
        if not 1 <= burst_kbytes <= _MAX_BURST_KBYTES:
            raise ConfigError("invalid_burst", "burst is outside the supported range")

        return cls(
            iface=iface_value,
            port=port,
            rate=rate_value,
            meter_size=meter_size,
            meter_timeout=timeout_value,
            burst_kbytes=burst_kbytes,
        )

    @property
    def nft_rate(self) -> str:
        bits_per_second = _rate_bits(self.rate)
        if bits_per_second % 8_000 == 0:
            return f"{bits_per_second // 8_000} kbytes/second"
        return f"{bits_per_second // 8} bytes/second"


@dataclass(frozen=True)
class CommandStep:
    name: str
    argv: tuple[str, ...]
    stdin: str | None
    mutating: bool


@dataclass(frozen=True)
class CommandPlan:
    action: str
    config: ShaperConfig
    steps: tuple[CommandStep, ...]


ExecutorResult = tuple[int, str, str] | subprocess.CompletedProcess[str]
Executor = Callable[[tuple[str, ...], str | None], ExecutorResult]


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> ShaperConfig:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError(
            "invalid_config",
            "configuration file is unavailable or malformed",
        ) from exc
    if not isinstance(payload, dict):
        raise ConfigError("invalid_config", "configuration root must be an object")
    if payload.get("schema_version") != POLICY_VERSION:
        raise ConfigError("invalid_config", "configuration schema version is unsupported")
    return ShaperConfig.from_mapping(payload)


def _nft_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def build_setup_ruleset(config: ShaperConfig) -> str:
    iface = _nft_string(config.iface)
    port = config.port
    size = config.meter_size
    timeout = config.meter_timeout
    rate = config.nft_rate
    burst = config.burst_kbytes

    return (
        f"destroy table {NFT_FAMILY} {NFT_TABLE}\n"
        f"table {NFT_FAMILY} {NFT_TABLE} {{\n"
        "    set pkr_soft_v4_in {\n"
        "        type ipv4_addr\n"
        "        flags dynamic,timeout\n"
        f"        timeout {timeout}\n"
        "        gc-interval 1m\n"
        f"        size {size}\n"
        "    }\n"
        "    set pkr_soft_v6_in {\n"
        "        type ipv6_addr\n"
        "        flags dynamic,timeout\n"
        f"        timeout {timeout}\n"
        "        gc-interval 1m\n"
        f"        size {size}\n"
        "    }\n"
        "    set pkr_soft_v4_out {\n"
        "        type ipv4_addr\n"
        "        flags dynamic,timeout\n"
        f"        timeout {timeout}\n"
        "        gc-interval 1m\n"
        f"        size {size}\n"
        "    }\n"
        "    set pkr_soft_v6_out {\n"
        "        type ipv6_addr\n"
        "        flags dynamic,timeout\n"
        f"        timeout {timeout}\n"
        "        gc-interval 1m\n"
        f"        size {size}\n"
        "    }\n"
        f"    chain {NFT_INPUT_CHAIN} {{\n"
        "        type filter hook input priority filter; policy accept;\n"
        f"        iifname {iface} meta nfproto ipv4 meta l4proto {{ tcp, udp }} "
        f"th dport {port} update @pkr_soft_v4_in "
        f"{{ ip saddr timeout {timeout} limit rate over {rate} "
        f"burst {burst} kbytes }} counter drop "
        'comment "pokrov-free-soft:v1:ipv4:input"\n'
        f"        iifname {iface} meta nfproto ipv6 meta l4proto {{ tcp, udp }} "
        f"th dport {port} update @pkr_soft_v6_in "
        f"{{ ip6 saddr timeout {timeout} limit rate over {rate} "
        f"burst {burst} kbytes }} counter drop "
        'comment "pokrov-free-soft:v1:ipv6:input"\n'
        "    }\n"
        f"    chain {NFT_OUTPUT_CHAIN} {{\n"
        "        type filter hook output priority filter; policy accept;\n"
        f"        oifname {iface} meta nfproto ipv4 meta l4proto {{ tcp, udp }} "
        f"th sport {port} update @pkr_soft_v4_out "
        f"{{ ip daddr timeout {timeout} limit rate over {rate} "
        f"burst {burst} kbytes }} counter drop "
        'comment "pokrov-free-soft:v1:ipv4:output"\n'
        f"        oifname {iface} meta nfproto ipv6 meta l4proto {{ tcp, udp }} "
        f"th sport {port} update @pkr_soft_v6_out "
        f"{{ ip6 daddr timeout {timeout} limit rate over {rate} "
        f"burst {burst} kbytes }} counter drop "
        'comment "pokrov-free-soft:v1:ipv6:output"\n'
        "    }\n"
        "}\n"
    )


def build_plan(action: str, config: ShaperConfig) -> CommandPlan:
    if action == "setup":
        ruleset = build_setup_ruleset(config)
        steps = (
            CommandStep(
                name="validate-ruleset",
                argv=("nft", "--check", "-f", "-"),
                stdin=ruleset,
                mutating=False,
            ),
            CommandStep(
                name="apply-ruleset",
                argv=("nft", "-f", "-"),
                stdin=ruleset,
                mutating=True,
            ),
        )
    elif action == "audit":
        steps = (
            CommandStep(
                name="audit-owned-table",
                argv=("nft", "--json", "list", "table", NFT_FAMILY, NFT_TABLE),
                stdin=None,
                mutating=False,
            ),
        )
    elif action == "rollback":
        steps = (
            CommandStep(
                name="rollback-owned-table",
                argv=("nft", "-f", "-"),
                stdin=f"destroy table {NFT_FAMILY} {NFT_TABLE}\n",
                mutating=True,
            ),
        )
    else:
        raise ValueError("unsupported shaper action")
    return CommandPlan(action=action, config=config, steps=steps)


def _step_report(step: CommandStep) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": step.name,
        "argv": list(step.argv),
        "mutating": step.mutating,
    }
    if step.stdin is not None:
        payload["input"] = step.stdin
        payload["input_sha256"] = hashlib.sha256(step.stdin.encode("utf-8")).hexdigest()
    return payload


def _base_report(plan: CommandPlan, *, apply: bool) -> dict[str, Any]:
    config = plan.config
    return {
        "schema_version": POLICY_VERSION,
        "action": plan.action,
        "mode": "apply" if apply else "dry-run",
        "status": "planned",
        "redacted": True,
        "local_only": True,
        "scope": {
            "family": NFT_FAMILY,
            "table": NFT_TABLE,
            "input_chain": NFT_INPUT_CHAIN,
            "output_chain": NFT_OUTPUT_CHAIN,
            "interface": config.iface,
            "port": config.port,
            "protocols": ["tcp", "udp"],
            "ip_families": ["ipv4", "ipv6"],
            "rate": config.rate,
            "nft_rate": config.nft_rate,
            "per_client_ip": True,
            "per_account_proof": False,
            "nat_clients_share_cap": True,
            "directional_cap": True,
            "meter_size": config.meter_size,
            "meter_timeout": config.meter_timeout,
            "burst_kbytes": config.burst_kbytes,
        },
        "steps": [_step_report(step) for step in plan.steps],
        "notes": [
            "This is packet policing on the dedicated inbound transport port.",
            "The cap is per observed client IP and per direction, not per account.",
            "Clients sharing one NAT address share the same directional cap.",
            "Executor stdout, stderr, environment, hostname, and user are omitted.",
        ],
    }


def _local_executor(argv: tuple[str, ...], stdin: str | None) -> ExecutorResult:
    return subprocess.run(
        list(argv),
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


def _return_code(result: ExecutorResult) -> int:
    if isinstance(result, tuple):
        if len(result) != 3:
            raise TypeError("executor returned an unsupported result")
        return int(result[0])
    return int(result.returncode)


def execute_plan(
    plan: CommandPlan,
    *,
    apply: bool = False,
    executor: Executor = _local_executor,
    platform_name: str | None = None,
) -> dict[str, Any]:
    report = _base_report(plan, apply=apply)
    if not apply:
        return report

    current_platform = platform_name if platform_name is not None else platform.system()
    if current_platform.strip().lower() != "linux":
        report["status"] = "refused"
        report["error_code"] = "linux_required"
        return report

    results: list[dict[str, Any]] = []
    report["results"] = results
    for step in plan.steps:
        try:
            return_code = _return_code(executor(step.argv, step.stdin))
        except Exception:
            results.append(
                {
                    "name": step.name,
                    "status": "failed",
                    "error_code": "executor_exception",
                }
            )
            report["status"] = "failed"
            report["failed_step"] = step.name
            report["error_code"] = "executor_exception"
            return report

        if return_code != 0:
            results.append(
                {
                    "name": step.name,
                    "status": "failed",
                    "return_code": return_code,
                }
            )
            report["status"] = "failed"
            report["failed_step"] = step.name
            report["error_code"] = "command_failed"
            return report

        results.append({"name": step.name, "status": "ok", "return_code": 0})

    report["status"] = "ok"
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan or locally execute the dedicated free-soft nftables policy.",
    )
    parser.add_argument("action", choices=("setup", "audit", "rollback"))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--iface")
    parser.add_argument("--port")
    parser.add_argument("--rate")
    parser.add_argument("--meter-size")
    parser.add_argument("--meter-timeout")
    parser.add_argument("--burst-kbytes")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="execute this plan on the local Linux host; default is JSON dry-run",
    )
    return parser


def _config_with_overrides(args: argparse.Namespace) -> ShaperConfig:
    config = load_config(args.config)
    payload: dict[str, Any] = {
        "iface": config.iface,
        "port": config.port,
        "rate": config.rate,
        "meter_size": config.meter_size,
        "meter_timeout": config.meter_timeout,
        "burst_kbytes": config.burst_kbytes,
    }
    overrides = {
        "iface": args.iface,
        "port": args.port,
        "rate": args.rate,
        "meter_size": args.meter_size,
        "meter_timeout": args.meter_timeout,
        "burst_kbytes": args.burst_kbytes,
    }
    payload.update({key: value for key, value in overrides.items() if value is not None})
    return ShaperConfig.from_mapping(payload)


def main(
    argv: Sequence[str] | None = None,
    *,
    executor: Executor = _local_executor,
    platform_name: str | None = None,
    stdout: TextIO = sys.stdout,
) -> int:
    args = _build_parser().parse_args(argv)
    try:
        config = _config_with_overrides(args)
        plan = build_plan(args.action, config)
        report = execute_plan(
            plan,
            apply=bool(args.apply),
            executor=executor,
            platform_name=platform_name,
        )
    except ConfigError as exc:
        report = {
            "schema_version": POLICY_VERSION,
            "status": "invalid",
            "error_code": exc.code,
            "redacted": True,
        }

    json.dump(report, stdout, ensure_ascii=True, indent=2, sort_keys=True)
    stdout.write("\n")
    if report["status"] in {"planned", "ok"}:
        return 0
    if report["status"] == "invalid":
        return 2
    if report["status"] == "refused":
        return 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
