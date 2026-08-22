"""Compatibility runtime for the API and bot composition-root slices.

The platform historically exposed most helpers and handlers directly from
``portal_bot.api`` and ``portal_bot.bot``.  The domain slices keep that public
surface while moving route and handler implementations into focused modules.

Each slice receives the already-built composition-root namespace before its
definitions execute.  Definitions are then exported back to the owner module.
The owner module propagates later attribute replacements to every loaded slice;
this preserves existing operator scripts and tests that monkeypatch legacy
module attributes.

This module deliberately does not execute source strings or discover files.
Slice order is explicit in each composition root, so route registration remains
deterministic and reviewable.
"""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Any, MutableMapping, Sequence

_MODULE_IDENTITY_NAMES = frozenset(
    {
        "__builtins__",
        "__cached__",
        "__doc__",
        "__file__",
        "__loader__",
        "__name__",
        "__package__",
        "__spec__",
    }
)
_SLICE_REGISTRY: dict[str, tuple[ModuleType, ...]] = {}
_SLICE_IMPORT_OWNERS: dict[str, str] = {}


def _copy_owner_namespace(
    *,
    owner_namespace: MutableMapping[str, Any],
    slice_namespace: MutableMapping[str, Any],
    owned_names: frozenset[str] = frozenset(),
) -> None:
    for name, value in owner_namespace.items():
        if name in _MODULE_IDENTITY_NAMES or name in owned_names:
            continue
        slice_namespace[name] = value


def bootstrap_slice(
    slice_namespace: MutableMapping[str, Any],
    *,
    owner_name: str | None = None,
) -> None:
    """Seed a slice with its partially initialized composition-root globals."""

    resolved_owner_name = owner_name or _SLICE_IMPORT_OWNERS.get(
        str(slice_namespace.get("__name__") or "")
    )
    if not resolved_owner_name:
        raise RuntimeError("Slice was imported outside load_slices()")
    owner = sys.modules.get(resolved_owner_name)
    if owner is None:
        raise RuntimeError(f"Slice owner is not imported: {resolved_owner_name}")

    _copy_owner_namespace(
        owner_namespace=vars(owner),
        slice_namespace=slice_namespace,
    )
    slice_namespace["_SLICE_OWNER_NAME"] = resolved_owner_name
    slice_namespace["_SLICE_BOOTSTRAP_NAMES"] = frozenset(slice_namespace)


def _slice_exports(module: ModuleType) -> frozenset[str]:
    bootstrap_names = frozenset(getattr(module, "_SLICE_BOOTSTRAP_NAMES", frozenset()))
    return frozenset(
        name
        for name in vars(module)
        if name not in bootstrap_names and not name.startswith("_SLICE_")
    )


class _SliceOwnerModule(ModuleType):
    """Module type that mirrors legacy monkeypatches into loaded slices."""

    def __setattr__(self, name: str, value: Any) -> None:
        ModuleType.__setattr__(self, name, value)
        if name in _MODULE_IDENTITY_NAMES:
            return
        # Tests and reload tooling can retain an old owner object after a fresh
        # module with the same name has replaced it in ``sys.modules``. A late
        # monkeypatch cleanup on that stale object must not mutate the current
        # slice registry.
        if sys.modules.get(self.__name__) is not self:
            return
        for module in _SLICE_REGISTRY.get(self.__name__, ()):
            if name in vars(module):
                ModuleType.__setattr__(module, name, value)

    def __delattr__(self, name: str) -> None:
        ModuleType.__delattr__(self, name)
        if name in _MODULE_IDENTITY_NAMES:
            return
        if sys.modules.get(self.__name__) is not self:
            return
        for module in _SLICE_REGISTRY.get(self.__name__, ()):
            if name in vars(module):
                ModuleType.__delattr__(module, name)


def load_slices(
    owner_namespace: MutableMapping[str, Any],
    module_names: Sequence[str],
) -> tuple[ModuleType, ...]:
    """Import ordered slices, export their symbols, and bind compatibility."""

    owner_name = str(owner_namespace["__name__"])
    owner = sys.modules[owner_name]
    modules: list[ModuleType] = []
    registered_owned_names = {
        module.__name__: frozenset(getattr(module, "_SLICE_OWN_NAMES", ()))
        for module in _SLICE_REGISTRY.get(owner_name, ())
    }

    # ``importlib.reload(owner)`` keeps the existing module dictionary, and
    # test/runtime loaders can later restore an older owner object under the
    # same module name. Clear every registered slice export by ownership, not
    # by object identity. Otherwise a restored owner can seed an old function
    # into the slice bootstrap set; the freshly defined replacement then looks
    # inherited and silently disappears from the exported surface.
    for owned_names in registered_owned_names.values():
        for name in owned_names:
            owner_namespace.pop(name, None)

    for module_name in module_names:
        _SLICE_IMPORT_OWNERS[module_name] = owner_name
        previous = sys.modules.get(module_name)
        if previous is None:
            module = importlib.import_module(module_name)
        else:
            names_to_clear = frozenset(getattr(previous, "_SLICE_OWN_NAMES", ())) | (
                registered_owned_names.get(module_name, frozenset())
            )
            for name in names_to_clear:
                vars(previous).pop(name, None)
            module = importlib.reload(previous)
        actual_owner = str(getattr(module, "_SLICE_OWNER_NAME", ""))
        if actual_owner != owner_name:
            raise RuntimeError(
                f"Slice {module_name} belongs to {actual_owner or 'unknown'}, "
                f"not {owner_name}"
            )

        owned_names = _slice_exports(module)
        ModuleType.__setattr__(module, "_SLICE_OWN_NAMES", owned_names)
        for name in owned_names:
            owner_namespace[name] = vars(module)[name]
        modules.append(module)

    # Later slices can define helpers used by earlier handlers.  Refresh every
    # dependency only after the complete ordered surface has been exported.
    for module in modules:
        _copy_owner_namespace(
            owner_namespace=owner_namespace,
            slice_namespace=vars(module),
            owned_names=frozenset(getattr(module, "_SLICE_OWN_NAMES", ())),
        )

    loaded = tuple(modules)
    _SLICE_REGISTRY[owner_name] = loaded
    owner_namespace["_SLICE_MODULES"] = loaded
    if not isinstance(owner, _SliceOwnerModule):
        owner.__class__ = _SliceOwnerModule
    return loaded
