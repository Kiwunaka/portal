from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
LEGACY_ACTIVE_INVENTORY = REPO_ROOT / "docs" / "08-node-inventory.md"
ARCHIVE_INVENTORY = REPO_ROOT / "docs" / "archive" / "flat-docs" / "08-node-inventory.md"
DEFAULT_INVENTORY = ARCHIVE_INVENTORY

RE_IPV4 = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})")


@dataclass(frozen=True)
class InventoryNode:
    code: str
    ip: str
    role: str = ""
    physical_name: str = ""
    country: str = ""
    runtime_status: str = ""
    plan: str = ""


def _clean_cell(value: str) -> str:
    text = str(value or "").strip()
    while len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        text = text[1:-1].strip()
    return text


def _normalise_header(value: str) -> str:
    text = _clean_cell(value).casefold()
    text = re.sub(r"[^a-z0-9а-яё]+", "_", text).strip("_")
    aliases = {
        "physical_name": "physical_name",
        "physical": "physical_name",
        "name": "physical_name",
        "runtime_status": "runtime_status",
        "status": "runtime_status",
    }
    return aliases.get(text, text)


def resolve_inventory_path(path: str | Path | None = None) -> Path:
    candidate = Path(path) if path else DEFAULT_INVENTORY
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    candidate = candidate.resolve()
    if candidate.exists():
        return candidate

    try:
        is_legacy_default = candidate == LEGACY_ACTIVE_INVENTORY.resolve()
    except OSError:
        is_legacy_default = False
    if is_legacy_default and ARCHIVE_INVENTORY.exists():
        return ARCHIVE_INVENTORY
    raise FileNotFoundError(f"Inventory not found: {candidate}")


def _row_parts(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    return [part.strip() for part in stripped.strip("|").split("|")]


def _parse_row_with_header(parts: list[str], header_index: dict[str, int]) -> InventoryNode | None:
    code_index = header_index.get("code")
    if code_index is None or code_index >= len(parts):
        return None
    code = _clean_cell(parts[code_index]).lower()
    if not code or code == "code" or not re.fullmatch(r"[a-z0-9_-]+", code):
        return None

    ip = ""
    ip_index = header_index.get("ip")
    if ip_index is not None and ip_index < len(parts):
        ip = _clean_cell(parts[ip_index])
    if not RE_IPV4.fullmatch(ip):
        ip = ""

    def value(name: str) -> str:
        index = header_index.get(name)
        if index is None or index >= len(parts):
            return ""
        return _clean_cell(parts[index])

    return InventoryNode(
        code=code,
        ip=ip,
        role=value("role"),
        physical_name=value("physical_name"),
        country=value("country").upper(),
        runtime_status=value("runtime_status"),
        plan=value("plan"),
    )


def _parse_row_fallback(parts: list[str]) -> InventoryNode | None:
    if not parts:
        return None
    code = _clean_cell(parts[0]).lower()
    if not code or code == "code" or not re.fullmatch(r"[a-z0-9_-]+", code):
        return None
    ip = ""
    for part in reversed(parts):
        candidate = _clean_cell(part)
        if RE_IPV4.fullmatch(candidate):
            ip = candidate
            break
    role = _clean_cell(parts[2]) if len(parts) >= 5 else (_clean_cell(parts[1]) if len(parts) > 1 else "")
    physical_name = _clean_cell(parts[1]) if len(parts) >= 5 else ""
    return InventoryNode(code=code, ip=ip, role=role, physical_name=physical_name)


def read_inventory(path: str | Path | None = None, *, include_tbd: bool = False) -> list[InventoryNode]:
    resolved = resolve_inventory_path(path)
    text = resolved.read_text(encoding="utf-8", errors="replace")
    rows: list[InventoryNode] = []
    header_index: dict[str, int] = {}
    for line in text.splitlines():
        parts = _row_parts(line)
        if not parts:
            continue
        normalised = [_normalise_header(part) for part in parts]
        if "code" in normalised and "ip" in normalised:
            header_index = {name: index for index, name in enumerate(normalised)}
            continue
        if not any("`" in part for part in parts):
            continue
        row = _parse_row_with_header(parts, header_index) if header_index else _parse_row_fallback(parts)
        if row is None:
            continue
        if not row.ip and not include_tbd:
            continue
        rows.append(row)
    if not rows:
        raise ValueError(f"Failed to parse inventory: {resolved}")
    return rows


def inventory_ipv4_map(path: str | Path | None = None) -> dict[str, str]:
    return {row.code: row.ip for row in read_inventory(path) if row.ip}
