from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SHARED_DIR = _REPO_ROOT / "shared"


def _shared_file_path(filename: str) -> Path:
    return (_SHARED_DIR / filename).resolve()


@lru_cache(maxsize=None)
def _load_shared_json(filename: str) -> dict[str, Any]:
    path = _shared_file_path(filename)
    return json.loads(path.read_text(encoding="utf-8"))


def get_product_facts() -> dict[str, Any]:
    return _load_shared_json("product-facts.json")


def get_public_urls() -> dict[str, Any]:
    return _load_shared_json("public-urls.json")


def get_design_tokens() -> dict[str, Any]:
    return _load_shared_json("design-tokens.json")


def clear_shared_surface_fact_caches() -> None:
    _load_shared_json.cache_clear()
