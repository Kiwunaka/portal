from __future__ import annotations

import argparse
import functools
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = "space.pokrov.pokrov_android_shell"
LOCALHOST_HOSTS = {"127.0.0.1", "::1", "[::1]"}


@dataclass(frozen=True)
class Listener:
    protocol: str
    state: str
    host: str
    port: int
    process_name: str = ""
    pid: int | None = None


@dataclass(frozen=True)
class PortProbeResult:
    phase: str
    protocol: str
    host: str
    port: int
    reachable: bool
    stdout: str
    stderr: str


@dataclass(frozen=True)
class PackageEvidence:
    package_name: str
    version_name: str
    version_code: str
    installer_package_name: str
    code_path: str
    debuggable: bool
    release_evidence: str


def _sdk_root_candidates() -> list[Path]:
    candidates: list[Path] = []
    for env_name in ("ANDROID_AUDIT_SDK_ROOT", "ANDROID_SDK_ROOT", "ANDROID_HOME"):
        value = os.environ.get(env_name, "").strip()
        if value:
            candidates.append(Path(value))
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        candidates.append(Path(local_app_data) / "Android" / "Sdk")
    deduped: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate not in seen:
            deduped.append(candidate)
            seen.add(candidate)
    return deduped


@functools.lru_cache(maxsize=1)
def _adb_executable() -> str:
    override = os.environ.get("ANDROID_AUDIT_ADB", "").strip()
    if override:
        return override

    adb_name = "adb.exe" if os.name == "nt" else "adb"
    for sdk_root in _sdk_root_candidates():
        candidate = sdk_root / "platform-tools" / adb_name
        if candidate.exists():
            return str(candidate)

    resolved = shutil.which(adb_name)
    if resolved:
        return resolved
    return adb_name


def _adb_base(serial: str | None) -> list[str]:
    command = [_adb_executable()]
    if serial:
        command.extend(["-s", serial])
    return command


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_adb_shell(serial: str | None, shell_command: str) -> subprocess.CompletedProcess[str]:
    return _run([*_adb_base(serial), "shell", shell_command])


def _is_recoverable_adb_error(output: str) -> bool:
    normalized = " ".join(str(output or "").strip().lower().split())
    if not normalized:
        return False
    recoverable_snippets = (
        "device '",
        "device not found",
        "device offline",
        "device still authorizing",
        "no devices/emulators found",
    )
    return any(snippet in normalized for snippet in recoverable_snippets)


def _parse_package_evidence(
    raw: str,
    *,
    package_name: str,
    release_evidence: str = "",
) -> PackageEvidence:
    def _first(pattern: str) -> str:
        match = re.search(pattern, raw)
        return match.group(1).strip() if match is not None else ""

    flags_blob = _first(r"(?m)^\s*flags=\[([^\]]*)\]")
    return PackageEvidence(
        package_name=package_name,
        version_name=_first(r"\bversionName=([^\s]+)"),
        version_code=_first(r"\bversionCode=([^\s]+)"),
        installer_package_name=_first(r"\binstallerPackageName=([^\s]+)"),
        code_path=_first(r"\bcodePath=([^\s]+)"),
        debuggable="DEBUGGABLE" in flags_blob.upper() or bool(re.search(r"\bdebuggable=true\b", raw, flags=re.I)),
        release_evidence=str(release_evidence or "").strip(),
    )


def _collect_package_evidence(
    *,
    serial: str,
    package_name: str,
    release_evidence: str,
) -> PackageEvidence:
    proc = _run_adb_shell(serial, f"dumpsys package {package_name}")
    if proc.returncode != 0 or package_name not in (proc.stdout or ""):
        raise RuntimeError((proc.stderr or proc.stdout or f"package {package_name} was not found").strip())
    return _parse_package_evidence(proc.stdout, package_name=package_name, release_evidence=release_evidence)


def _package_evidence_failures(
    evidence: PackageEvidence,
    *,
    require_release_build: bool,
    expected_version_name: str,
    expected_version_code: str,
) -> list[str]:
    failures: list[str] = []
    if require_release_build and not evidence.release_evidence:
        failures.append("release-installed artifact evidence is missing")
    if require_release_build and evidence.debuggable:
        failures.append("installed package is debuggable while release build was required")
    if expected_version_name and evidence.version_name != expected_version_name:
        failures.append(
            f"installed versionName {evidence.version_name or '<missing>'} does not match expected {expected_version_name}"
        )
    if expected_version_code and evidence.version_code != expected_version_code:
        failures.append(
            f"installed versionCode {evidence.version_code or '<missing>'} does not match expected {expected_version_code}"
        )
    return failures


def _ensure_device_ready(serial: str) -> None:
    start_server = _run([_adb_executable(), "start-server"])
    if start_server.returncode != 0:
        raise RuntimeError((start_server.stderr or start_server.stdout or "adb start-server failed").strip())

    wait_for_device = _run([*_adb_base(serial), "wait-for-device"])
    if wait_for_device.returncode != 0:
        raise RuntimeError((wait_for_device.stderr or wait_for_device.stdout or "adb wait-for-device failed").strip())

    state = _run([*_adb_base(serial), "get-state"])
    if state.returncode != 0 or "device" not in (state.stdout or "").split():
        raise RuntimeError((state.stderr or state.stdout or "adb device is not ready").strip())


def _parse_ss_listeners(raw: str) -> list[Listener]:
    listeners: list[Listener] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("netid"):
            continue
        parts = re.split(r"\s+", line, maxsplit=5)
        if len(parts) < 5:
            continue
        protocol = parts[0].lower()
        state = parts[1].upper()
        local_address = parts[4]
        process_blob = parts[5] if len(parts) > 5 else ""
        try:
            host, port = _split_host_port(local_address)
        except ValueError:
            continue
        if host not in LOCALHOST_HOSTS:
            continue
        process_name = ""
        pid: int | None = None
        process_match = re.search(r'"([^"]+)",pid=(\d+)', process_blob)
        if process_match is not None:
            process_name = process_match.group(1)
            pid = int(process_match.group(2))
        listeners.append(
            Listener(
                protocol=protocol,
                state=state,
                host=_normalize_host(host),
                port=port,
                process_name=process_name,
                pid=pid,
            )
        )
    return listeners


def _normalize_host(host: str) -> str:
    if host == "[::1]":
        return "::1"
    return host


def _split_host_port(local_address: str) -> tuple[str, int]:
    local_address = local_address.strip()
    if local_address.startswith("["):
        match = re.match(r"^\[(.+)\]:(\d+)$", local_address)
        if match is None:
            raise ValueError(f"Unsupported local address format: {local_address}")
        return f"[{match.group(1)}]", int(match.group(2))
    host, port_text = local_address.rsplit(":", 1)
    return host, int(port_text)


def _listener_key(listener: Listener) -> tuple[str, str, int]:
    return listener.protocol, listener.host, listener.port


def _new_localhost_listeners(baseline: list[Listener], current: list[Listener]) -> list[Listener]:
    baseline_keys = {_listener_key(listener) for listener in baseline}
    return [listener for listener in current if _listener_key(listener) not in baseline_keys]


def _audit_failures(
    *,
    baseline: list[Listener],
    after_launch: list[Listener],
    after_connect: list[Listener],
    after_disconnect: list[Listener],
    probes: list[PortProbeResult],
) -> list[str]:
    failures: list[str] = []

    phase_snapshots = {
        "after_launch": after_launch,
        "after_connect": after_connect,
        "after_disconnect": after_disconnect,
    }
    for phase, listeners in phase_snapshots.items():
        for listener in _new_localhost_listeners(baseline, listeners):
            failures.append(
                f"{phase} exposes new localhost listener {listener.protocol}/{listener.host}:{listener.port}"
            )

    for probe in probes:
        if probe.reachable:
            failures.append(
                f"unauthenticated localhost probe succeeded for {probe.protocol}/{probe.host}:{probe.port} during {probe.phase}"
            )

    return failures


def _list_connected_devices() -> list[str]:
    proc = _run([_adb_executable(), "devices"])
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "adb devices failed").strip())
    devices: list[str] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices attached"):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


def _select_serial(requested_serial: str | None) -> str:
    if requested_serial:
        return requested_serial
    devices = _list_connected_devices()
    if len(devices) != 1:
        raise RuntimeError("Expected exactly one connected adb device or pass --serial explicitly")
    return devices[0]


def _collect_listeners(serial: str) -> list[Listener]:
    commands = [
        "ss -ltnup",
        "toybox ss -ltnup",
        "netstat -ltnup",
        "toybox netstat -ltnup",
    ]
    last_error = ""
    for command in commands:
        proc = _run_adb_shell(serial, command)
        if proc.returncode != 0:
            output = (proc.stderr or proc.stdout or "").strip()
            if _is_recoverable_adb_error(output):
                _ensure_device_ready(serial)
                proc = _run_adb_shell(serial, command)
        if proc.returncode == 0 and proc.stdout.strip():
            return _parse_ss_listeners(proc.stdout)
        last_error = (proc.stderr or proc.stdout or "").strip()
    raise RuntimeError(f"Failed to collect localhost listeners over adb shell: {last_error}")


def _launch_app(serial: str, package_name: str) -> None:
    proc = _run([*_adb_base(serial), "shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"])
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "failed to launch app").strip())


def _wait_for_manual_step(message: str, seconds: int) -> None:
    if seconds <= 0:
        return
    print(f"[wait] {message} ({seconds}s)")
    time.sleep(seconds)


def _probe_listener(serial: str, phase: str, listener: Listener) -> PortProbeResult:
    if listener.protocol != "tcp":
        return PortProbeResult(
            phase=phase,
            protocol=listener.protocol,
            host=listener.host,
            port=listener.port,
            reachable=False,
            stdout="",
            stderr="udp probe skipped",
        )

    host = "127.0.0.1" if listener.host == "::1" else listener.host
    commands = [
        f"toybox nc -z -w 1 {host} {listener.port}",
        f"nc -z -w 1 {host} {listener.port}",
    ]
    last_stdout = ""
    last_stderr = ""
    for command in commands:
        proc = _run_adb_shell(serial, command)
        last_stdout = (proc.stdout or "").strip()
        last_stderr = (proc.stderr or "").strip()
        if proc.returncode == 0:
            return PortProbeResult(
                phase=phase,
                protocol=listener.protocol,
                host=host,
                port=listener.port,
                reachable=True,
                stdout=last_stdout,
                stderr=last_stderr,
            )

    return PortProbeResult(
        phase=phase,
        protocol=listener.protocol,
        host=host,
        port=listener.port,
        reachable=False,
        stdout=last_stdout,
        stderr=last_stderr,
    )


def _snapshot_probe_results(serial: str, phase: str, baseline: list[Listener], current: list[Listener]) -> list[PortProbeResult]:
    return [_probe_listener(serial, phase, listener) for listener in _new_localhost_listeners(baseline, current)]


def _write_report(
    *,
    output_path: Path | None,
    serial: str,
    package_name: str,
    baseline: list[Listener],
    after_launch: list[Listener],
    after_connect: list[Listener],
    after_disconnect: list[Listener],
    probes: list[PortProbeResult],
    failures: list[str],
    package_evidence: PackageEvidence | None = None,
) -> None:
    if output_path is None:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "serial": serial,
        "package_name": package_name,
        "baseline": [asdict(item) for item in baseline],
        "after_launch": [asdict(item) for item in after_launch],
        "after_connect": [asdict(item) for item in after_connect],
        "after_disconnect": [asdict(item) for item in after_disconnect],
        "probes": [asdict(item) for item in probes],
        "failures": failures,
        "package_evidence": asdict(package_evidence) if package_evidence is not None else None,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Android localhost listeners over adb.")
    parser.add_argument("--serial", default="")
    parser.add_argument("--package", default=DEFAULT_PACKAGE)
    parser.add_argument("--release-evidence", default="")
    parser.add_argument("--require-release-build", action="store_true")
    parser.add_argument("--expected-version-name", default="")
    parser.add_argument("--expected-version-code", default="")
    parser.add_argument("--launch-wait-sec", type=int, default=5)
    parser.add_argument("--connect-wait-sec", type=int, default=0)
    parser.add_argument("--disconnect-wait-sec", type=int, default=0)
    parser.add_argument("--output", default="ops-local/android-localhost-audit.json")
    args = parser.parse_args()

    try:
        serial = _select_serial(args.serial.strip() or None)
        _ensure_device_ready(serial)
        package_evidence: PackageEvidence | None = None
        package_failures: list[str] = []
        if (
            args.require_release_build
            or str(args.release_evidence or "").strip()
            or str(args.expected_version_name or "").strip()
            or str(args.expected_version_code or "").strip()
        ):
            package_evidence = _collect_package_evidence(
                serial=serial,
                package_name=args.package,
                release_evidence=args.release_evidence,
            )
            package_failures = _package_evidence_failures(
                package_evidence,
                require_release_build=bool(args.require_release_build),
                expected_version_name=str(args.expected_version_name or "").strip(),
                expected_version_code=str(args.expected_version_code or "").strip(),
            )
            print(
                "[package] "
                f"{package_evidence.package_name} "
                f"versionName={package_evidence.version_name or '<missing>'} "
                f"versionCode={package_evidence.version_code or '<missing>'} "
                f"debuggable={'yes' if package_evidence.debuggable else 'no'}"
            )
        baseline = _collect_listeners(serial)
        print(f"[device] {serial}")
        print(f"[phase] baseline listeners: {len(baseline)}")

        _launch_app(serial, args.package)
        _wait_for_manual_step("waiting after app launch", args.launch_wait_sec)
        after_launch = _collect_listeners(serial)
        probes = _snapshot_probe_results(serial, "after_launch", baseline, after_launch)
        print(f"[phase] after_launch listeners: {len(after_launch)}")

        after_connect: list[Listener] = []
        after_disconnect: list[Listener] = []

        if args.connect_wait_sec > 0:
            _wait_for_manual_step(
                "connect the tunnel manually and accept VPN permission if prompted",
                args.connect_wait_sec,
            )
            after_connect = _collect_listeners(serial)
            probes.extend(_snapshot_probe_results(serial, "after_connect", baseline, after_connect))
            print(f"[phase] after_connect listeners: {len(after_connect)}")

        if args.disconnect_wait_sec > 0:
            _wait_for_manual_step(
                "disconnect the tunnel manually before the next snapshot",
                args.disconnect_wait_sec,
            )
            after_disconnect = _collect_listeners(serial)
            probes.extend(_snapshot_probe_results(serial, "after_disconnect", baseline, after_disconnect))
            print(f"[phase] after_disconnect listeners: {len(after_disconnect)}")

        failures = _audit_failures(
            baseline=baseline,
            after_launch=after_launch,
            after_connect=after_connect,
            after_disconnect=after_disconnect,
            probes=probes,
        )
        failures.extend(package_failures)
        output = Path(args.output).resolve() if args.output else None
        _write_report(
            output_path=output,
            serial=serial,
            package_name=args.package,
            baseline=baseline,
            after_launch=after_launch,
            after_connect=after_connect,
            after_disconnect=after_disconnect,
            probes=probes,
            failures=failures,
            package_evidence=package_evidence,
        )
        if output is not None:
            print(f"[report] {output}")
        for probe in probes:
            status = "reachable" if probe.reachable else "not_reachable"
            print(f"[probe] {probe.phase} {probe.protocol}/{probe.host}:{probe.port} {status}")
        if failures:
            for failure in failures:
                print(f"[fail] {failure}")
            return 2
        print("[pass] android localhost audit passed")
        return 0
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
