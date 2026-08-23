"""Canonical Operator Center Admin API v2 package."""

from .meta import ADMIN_V2_SCHEMA, build_admin_v2_meta_response
from .roles import PERMISSIONS, ROLE_REGISTRY

__all__ = [
    "ADMIN_V2_SCHEMA",
    "PERMISSIONS",
    "ROLE_REGISTRY",
    "build_admin_v2_meta_response",
]
