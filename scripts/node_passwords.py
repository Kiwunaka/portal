from __future__ import annotations

import re
from pathlib import Path


def parse_inventory_codes(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    codes: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or "`" not in line:
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 4:
            continue
        code = parts[0].strip("`").strip().lower()
        if not code or code == "code":
            continue
        if not re.fullmatch(r"[a-z0-9_-]+", code):
            continue
        codes.append(code)
    return codes


def _find_marker_index(lines: list[str], code: str) -> int | None:
    code = str(code or "").strip().lower()
    if not code:
        return None
    marker_aliases = {
        "brain": ["brainnode"],
        "de": ["denodemax", "demax", "de node", "denode", "germany", "germany node", "германия"],
        "us": ["usnode"],
        "pl": ["plnode"],
        "it": ["itnode"],
        "nl": ["nlnode", "low ping v2"],
        "free": ["free node", "freenode"],
        "mini": ["ru sber", "russia", "rfmini"],
        "rf1": ["rfreserve1", "rf1", "russia reserve"],
    }
    patterns = [re.compile(rf"\b{re.escape(alias)}\b", flags=re.IGNORECASE) for alias in marker_aliases.get(code, [])]
    patterns.extend(
        [
            re.compile(rf"\b{re.escape(code)}node\b", flags=re.IGNORECASE),
            re.compile(rf"\b{re.escape(code)}\s*node\b", flags=re.IGNORECASE),
            re.compile(rf"\b{re.escape(code)}\b", flags=re.IGNORECASE),
        ]
    )
    if code == "free":
        patterns.insert(0, re.compile(r"\bfree\s*node\b", flags=re.IGNORECASE))
    for idx, line in enumerate(lines):
        if any(p.search(line) for p in patterns):
            return idx
    return None


def _password_candidates_near(lines: list[str], marker_idx: int) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()
    for j in range(marker_idx + 1, min(marker_idx + 15, len(lines))):
        raw = lines[j].strip()
        if not raw:
            continue
        if re.fullmatch(r"(\d{1,3}\.){3}\d{1,3}", raw):
            continue
        if raw.startswith("ssh-ed25519 ") or raw.startswith("ssh-rsa "):
            continue
        if "http://" in raw or "https://" in raw:
            continue
        if ":" in raw and len(raw.split()) > 1:
            continue
        if raw.startswith("PuTTY-") or raw.startswith("-----"):
            continue
        if raw not in seen:
            seen.add(raw)
            candidates.append(raw)
    return candidates


def _extract_password_near(lines: list[str], marker_idx: int) -> str:
    candidates = _password_candidates_near(lines, marker_idx)
    return candidates[0] if candidates else ""


def parse_password_candidates(path: Path, *, requested_codes: list[str] | None = None) -> dict[str, list[str]]:
    lines = [ln.rstrip("\n") for ln in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    out: dict[str, list[str]] = {}
    codes = [str(c).lower().strip() for c in (requested_codes or []) if str(c).strip()]
    if not codes:
        # Fallback for legacy behavior when no inventory is provided.
        codes = ["brain", "us", "pl", "it", "free"]
    for code in codes:
        idx = _find_marker_index(lines, code)
        if idx is None:
            continue
        candidates = _password_candidates_near(lines, idx)
        if candidates:
            out[code] = candidates
    return out


def parse_passwords(path: Path, *, requested_codes: list[str] | None = None) -> dict[str, str]:
    lines = [ln.rstrip("\n") for ln in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    out: dict[str, str] = {}
    codes = [str(c).lower().strip() for c in (requested_codes or []) if str(c).strip()]
    if not codes:
        # Fallback for legacy behavior when no inventory is provided.
        codes = ["brain", "us", "pl", "it", "free"]
    for code in codes:
        idx = _find_marker_index(lines, code)
        if idx is None:
            continue
        pw = _extract_password_near(lines, idx)
        if pw:
            out[code] = pw
    return out
