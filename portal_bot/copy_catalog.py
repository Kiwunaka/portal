from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_CATALOG_PATH = Path(__file__).resolve().parents[1] / "copy" / "catalog.ru.json"


@lru_cache(maxsize=1)
def _load_catalog() -> dict[str, Any]:
    if not _CATALOG_PATH.exists():
        return {"items": {}}
    return json.loads(_CATALOG_PATH.read_text(encoding="utf-8-sig"))


def get_copy_item(key: str) -> dict[str, Any] | None:
    items = _load_catalog().get("items") or {}
    value = items.get(str(key or ""))
    return value if isinstance(value, dict) else None


def get_copy_text(
    key: str,
    fallback: str = "",
    *,
    variables: dict[str, Any] | None = None,
) -> str:
    item = get_copy_item(key)
    text = str((item or {}).get("ru") or fallback or "")
    if variables:
        try:
            return text.format(**variables)
        except Exception:
            return text
    return text


def get_catalog_version() -> str:
    return str(_load_catalog().get("catalog_version") or "")
