from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
load_dotenv()

from db import SessionLocal
from models import User, UserNode
from node_policy import (
    FREE_SOFT_ROLE,
    FREE_STANDARD_QUOTA_BYTES,
    FREE_STANDARD_ROLE,
    NodeAccessRoleError,
    free_pool_node_codes,
    node_access_role,
    node_code_base,
    paid_pool_nodes,
    user_free_access_role,
    user_uses_free_pool,
    validate_node_access_roles,
)
from nodes_repo import enabled_nodes
from panel_client import PanelClient, panel_error_kind


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RotationPanelResult:
    status: str
    code: str

    @property
    def succeeded(self) -> bool:
        return self.status == "succeeded"

    @property
    def manual_review(self) -> bool:
        return self.status == "manual_review"

    def __bool__(self) -> bool:
        return self.succeeded


@dataclass(frozen=True)
class PanelUserSnapshot:
    tg_id: int
    uuid: str
    email: str
    sub_token: str
    sub_type: str
    current_plan_code: str | None
    is_active: bool
    expiry_at: object | None
    free_profile_state: str
    free_profile_active_role: str


class ControlPanel:
    """
    Multi-node wrapper around 3x-ui panel API.
    Backward compatible: if `nodes` table is empty, falls back to legacy env node.
    """

    def __init__(self, concurrency: int = 4):
        self._concurrency = concurrency
        self._clients: dict[str, PanelClient] = {}

    @staticmethod
    def _node_base(code: str) -> str:
        return node_code_base(code)

    def _paid_node_groups(self, nodes: list) -> list[tuple[str, list]]:
        return [((getattr(node, "code", "") or "").strip(), [node]) for node in paid_pool_nodes(nodes)]

    @staticmethod
    def _free_node_codes(nodes: list, *, user: User | None = None) -> list[str]:
        access_role = user_free_access_role(user) if user is not None else FREE_STANDARD_ROLE
        return free_pool_node_codes(nodes, access_role=access_role)

    def _requested_node_groups(self, nodes: list, requested_codes: list[str]) -> list[tuple[str, list]]:
        groups: list[tuple[str, list]] = []
        seen: set[str] = set()
        for raw in requested_codes:
            key = (raw or "").lower().strip()
            if not key or key in seen:
                continue
            seen.add(key)

            exact = [n for n in nodes if (n.code or "").lower().strip() == key]
            if exact:
                groups.append((key, exact))
                continue

            base = self._node_base(key)
            by_base = [n for n in nodes if self._node_base(n.code) == base]
            if by_base:
                groups.append((key, by_base))
        return groups

    async def refresh(self) -> list:
        s = SessionLocal()
        try:
            nodes = enabled_nodes(s)
        finally:
            s.close()
        validate_node_access_roles(nodes)
        # Keep existing clients if node code matches, otherwise rebuild. The DB
        # session is closed before any async client cleanup.
        codes = {n.code for n in nodes}
        for code in list(self._clients.keys()):
            if code not in codes:
                try:
                    await self._clients[code].close()
                except Exception:
                    pass
                self._clients.pop(code, None)
        for n in nodes:
            if n.code not in self._clients:
                self._clients[n.code] = PanelClient(n)
        return nodes

    @staticmethod
    def _compare_node_inbound(node, runtime: dict | None, *, error: str = "") -> dict:
        runtime = runtime or {}
        expected_sni = str(getattr(node, "reality_sni", "") or "").strip()
        expected_sid = str(getattr(node, "reality_sid", "") or "").strip()
        expected_pbk = str(getattr(node, "reality_pbk", "") or "").strip()
        runtime_pbk = str(runtime.get("public_key") or "").strip()
        server_names = [str(x or "").strip() for x in runtime.get("server_names", [])]
        dest = str(runtime.get("dest", "") or "").strip()
        checks = {
            "inbound_present": bool(runtime) and not error,
            "enabled_match": bool(runtime.get("enable")) is True if runtime else False,
            "port_match": int(runtime.get("port") or 0) == int(getattr(node, "vless_port", 443) or 443),
            "protocol_match": str(runtime.get("protocol") or "") == "vless",
            "network_match": str(runtime.get("network") or "") == "tcp",
            "security_match": str(runtime.get("security") or "") == "reality",
            "sni_match": (not expected_sni) or (expected_sni in server_names) or dest.startswith(f"{expected_sni}:"),
            "sid_match": (not expected_sid) or (expected_sid in [str(x or "").strip() for x in runtime.get("short_ids", [])]),
            "pbk_match": (not expected_pbk) or (bool(runtime_pbk) and expected_pbk == runtime_pbk),
        }
        mismatches = [name for name, ok in checks.items() if not ok]
        return {
            "node_code": str(getattr(node, "code", "") or ""),
            "node_name": str(getattr(node, "name", "") or ""),
            "node_host": str(getattr(node, "host", "") or ""),
            "status": "ok" if not mismatches else "drift",
            "mismatches": mismatches,
            "error": error,
            "expected": {
                "inbound_id": int(getattr(node, "inbound_id", 0) or 0),
                "port": int(getattr(node, "vless_port", 443) or 443),
                "sni": expected_sni,
                "sid": expected_sid,
                "pbk": expected_pbk,
            },
            "runtime": runtime,
            "checks": checks,
        }

    async def login(self) -> bool:
        nodes = await self.refresh()
        ok_any = False
        for n in nodes:
            ok = await self._clients[n.code].login()
            ok_any = ok_any or ok
        return ok_any

    async def get_node_drift_report(self, *, node_codes: list[str] | None = None) -> dict:
        nodes = await self.refresh()
        if node_codes:
            allowed = {str(code or "").strip().lower() for code in node_codes if str(code or "").strip()}
            nodes = [n for n in nodes if str(getattr(n, "code", "") or "").strip().lower() in allowed]

        results: list[dict] = []
        for n in nodes:
            error = ""
            runtime = None
            try:
                runtime = await self._clients[n.code].get_inbound_snapshot(getattr(n, "inbound_id", None))
                if not runtime:
                    error = "inbound_not_found"
            except Exception as exc:
                error = panel_error_kind(exc)
            results.append(self._compare_node_inbound(n, runtime, error=error))

        return {
            "summary": {
                "total": len(results),
                "ok": sum(1 for row in results if row["status"] == "ok"),
                "drift": sum(1 for row in results if row["status"] != "ok"),
            },
            "results": results,
        }

    async def close(self) -> None:
        for c in list(self._clients.values()):
            try:
                await c.close()
            except Exception:
                pass
        self._clients.clear()

    async def get_existing_client(self, tg_id: int) -> dict | None:
        """
        Best-effort: search across enabled nodes.
        This avoids false negatives when a user exists only on a subset of nodes (e.g. FREE tier).
        """
        nodes = await self.refresh()
        if not nodes:
            return None
        for n in nodes:
            try:
                c = await self._clients[n.code].find_client_by_tgid(tg_id)
                if c:
                    owned = dict(c)
                    owned["_node_code"] = str(getattr(n, "code", "") or "")
                    owned["_node_id"] = int(getattr(n, "id", 0) or 0)
                    return owned
            except Exception:
                continue
        return None

    async def ensure_user_on_all_nodes(
        self,
        *,
        tg_id: int,
        client_uuid: str,
        email: str,
        sub_id: str,
        enable: bool,
        only_node_codes: list[str] | None = None,
    ) -> dict:
        nodes = await self.refresh()
        groups: list[tuple[str, list]]
        if only_node_codes:
            groups = self._requested_node_groups(nodes, only_node_codes)
        else:
            groups = self._paid_node_groups(nodes)
        if not groups:
            return {}

        results: dict[str, bool] = {}
        chosen_nodes: list = []
        for _group_key, candidates in groups:
            success = False
            for node in candidates:
                ok = await self._clients[node.code].ensure_client(
                    tg_id=tg_id,
                    client_uuid=client_uuid,
                    email=email,
                    sub_id=sub_id,
                    enable=enable,
                )
                results[node.code] = ok
                if ok:
                    chosen_nodes.append(node)
                    success = True
                    break
            if not success and candidates:
                results[candidates[0].code] = False

        # Persist mapping for observability/debug (best-effort)
        s = SessionLocal()
        try:
            for n in chosen_nodes:
                if not results.get(n.code):
                    continue
                if n.id is None:
                    # legacy node has no DB id
                    continue
                exists = s.query(UserNode).filter_by(tg_id=tg_id, node_id=n.id).first()
                if not exists:
                    s.add(UserNode(tg_id=tg_id, node_id=n.id, client_uuid=client_uuid, panel_email=email))
            s.commit()
        except Exception as e:
            logger.warning("user_nodes persist failed error_kind=%s", type(e).__name__)
        finally:
            s.close()

        return results

    async def set_existing_user_enabled_on_nodes(
        self,
        *,
        tg_id: int,
        node_codes: list[str],
        enable: bool,
        sub_id: str | None = None,
    ) -> dict[str, bool]:
        """
        Toggle user on specific nodes WITHOUT provisioning new clients.
        This is important for plan transitions (e.g. PAID -> FREE) where we must disable paid nodes
        but must not create new paid-node clients for a free user.
        """
        nodes = await self.refresh()
        groups = self._requested_node_groups(nodes, node_codes or [])
        results: dict[str, bool] = {}
        for _group_key, candidates in groups:
            for n in candidates:
                try:
                    matches = await self._clients[n.code].find_clients_by_tgid(
                        int(tg_id),
                        include_disabled=True,
                    )
                except Exception:
                    results[n.code] = False
                    continue
                if not matches:
                    # A successful exhaustive read proves absence.
                    results[n.code] = True
                    continue
                updated_all = True
                for inbound_id, client in matches:
                    try:
                        updated = await self._clients[n.code].update_client_enable(
                            client,
                            bool(enable),
                            sub_id=sub_id,
                            inbound_id=int(inbound_id),
                        )
                    except Exception:
                        updated = False
                    updated_all = updated_all and bool(updated)
                results[n.code] = updated_all
        return results

    async def get_user_key_snapshots(
        self,
        *,
        tg_id: int,
        node_codes: list[str] | None = None,
    ) -> list[dict]:
        nodes = await self.refresh()
        selected_nodes: list = []
        seen: set[str] = set()
        if node_codes:
            groups = self._requested_node_groups(nodes, node_codes)
            for _group_key, candidates in groups:
                for n in candidates:
                    code = str(getattr(n, "code", "") or "").strip()
                    if not code or code in seen:
                        continue
                    seen.add(code)
                    selected_nodes.append(n)
        else:
            selected_nodes = list(nodes)

        semaphore = asyncio.Semaphore(max(1, int(self._concurrency or 1)))

        async def _collect(node) -> dict:
            code = str(getattr(node, "code", "") or "").strip()
            client = None
            runtime = None
            error = ""
            try:
                async with semaphore:
                    client, runtime = await self._clients[code].get_client_snapshot_by_tgid(int(tg_id))
            except Exception as exc:
                error = panel_error_kind(exc)
            return {
                "node_code": code,
                "node_name": str(getattr(node, "name", "") or ""),
                "node_host": str(getattr(node, "host", "") or ""),
                "node_enabled": bool(getattr(node, "enabled", True)),
                "node_healthy": bool(getattr(node, "is_healthy", False)),
                "client": client,
                "runtime": runtime,
                "error": error,
            }

        return await asyncio.gather(*[_collect(node) for node in selected_nodes], return_exceptions=False)

    async def get_node_online_summaries(self, *, node_codes: list[str] | None = None) -> dict[str, dict]:
        nodes = await self.refresh()
        selected_nodes: list = []
        seen: set[str] = set()
        if node_codes:
            groups = self._requested_node_groups(nodes, node_codes)
            for _group_key, candidates in groups:
                for n in candidates:
                    code = str(getattr(n, "code", "") or "").strip()
                    if not code or code in seen:
                        continue
                    seen.add(code)
                    selected_nodes.append(n)
        else:
            selected_nodes = list(nodes)

        async def _collect(node):
            code = str(getattr(node, "code", "") or "").strip()
            if not code:
                return None
            try:
                summary = await self._clients[code].get_node_online_summary()
            except Exception as exc:
                summary = {
                    "online_keys_now": 0,
                    "online_connections_now": 0,
                    "panel_error": panel_error_kind(exc),
                }
            return code, summary

        rows = await asyncio.gather(*[_collect(n) for n in selected_nodes], return_exceptions=False)
        out: dict[str, dict] = {}
        for row in rows:
            if not row:
                continue
            code, summary = row
            out[str(code)] = dict(summary or {})
        return out

    async def get_node_online_clients(self, *, node_codes: list[str] | None = None) -> dict:
        nodes = await self.refresh()
        selected_nodes: list = []
        seen: set[str] = set()
        if node_codes:
            groups = self._requested_node_groups(nodes, node_codes)
            for _group_key, candidates in groups:
                for n in candidates:
                    code = str(getattr(n, "code", "") or "").strip()
                    if not code or code in seen:
                        continue
                    seen.add(code)
                    selected_nodes.append(n)
        else:
            selected_nodes = list(nodes)

        semaphore = asyncio.Semaphore(max(1, int(self._concurrency or 1)))

        async def _collect(node):
            code = str(getattr(node, "code", "") or "").strip()
            if not code:
                return {"node_code": "", "rows": [], "error_code": "missing_node_code"}
            async with semaphore:
                try:
                    rows = await self._clients[code].get_node_online_clients()
                    return {"node_code": code, "rows": rows, "error_code": ""}
                except Exception:
                    return {"node_code": code, "rows": [], "error_code": "panel_request_failed"}

        collected = await asyncio.gather(*[_collect(n) for n in selected_nodes], return_exceptions=False)
        rows: list[dict] = []
        errors: list[dict] = []
        for item in collected:
            if not item:
                continue
            if item.get("error_code"):
                errors.append(
                    {
                        "node_code": item.get("node_code"),
                        "evidence_code": item.get("error_code"),
                    }
                )
            rows.extend([dict(row or {}) for row in item.get("rows") or []])
        return {"rows": rows, "errors": errors}

    async def get_node_runtime_snapshots(self, *, node_codes: list[str] | None = None) -> dict[str, dict]:
        nodes = await self.refresh()
        selected_nodes: list = []
        seen: set[str] = set()
        if node_codes:
            groups = self._requested_node_groups(nodes, node_codes)
            for _group_key, candidates in groups:
                for n in candidates:
                    code = str(getattr(n, "code", "") or "").strip()
                    if not code or code in seen:
                        continue
                    seen.add(code)
                    selected_nodes.append(n)
        else:
            selected_nodes = list(nodes)

        semaphore = asyncio.Semaphore(max(1, int(self._concurrency or 1)))

        async def _collect(node):
            code = str(getattr(node, "code", "") or "").strip()
            if not code:
                return None
            async with semaphore:
                try:
                    snapshot = await self._clients[code].get_node_runtime_snapshot()
                except Exception as exc:
                    snapshot = {
                        "node_code": code,
                        "panel_auth_ok": False,
                        "panel_latency_ms": None,
                        "csrf_mode": False,
                        "api_token_mode": False,
                        "error": panel_error_kind(exc),
                        "server_status": None,
                        "system": {},
                        "inbound": None,
                        "online": {"online_keys_now": 0, "online_connections_now": 0},
                    }
                snapshot["node_name"] = str(getattr(node, "name", "") or "")
                snapshot["node_host"] = str(getattr(node, "host", "") or "")
                snapshot["node_enabled"] = bool(getattr(node, "enabled", True))
                snapshot["expected_inbound_id"] = int(getattr(node, "inbound_id", 0) or 0)
                return code, snapshot

        rows = await asyncio.gather(*[_collect(n) for n in selected_nodes], return_exceptions=False)
        out: dict[str, dict] = {}
        for row in rows:
            if not row:
                continue
            code, snapshot = row
            out[str(code)] = dict(snapshot or {})
        return out

    async def _resolve_target_node(self, node_code: str):
        wanted = str(node_code or "").strip().lower()
        if not wanted:
            return None
        nodes = await self.refresh()
        for n in nodes:
            if str(getattr(n, "code", "") or "").strip().lower() == wanted:
                return n
        wanted_base = self._node_base(wanted)
        for n in nodes:
            if self._node_base(getattr(n, "code", "")) == wanted_base:
                return n
        return None

    async def _resolve_exact_role_node(self, node_code: str, expected_access_role: str):
        wanted = str(node_code or "").strip().lower()
        nodes = await self.refresh()
        validate_node_access_roles(nodes)
        for node in nodes:
            if str(getattr(node, "code", "") or "").strip().lower() != wanted:
                continue
            actual_role = node_access_role(node, strict=True)
            if actual_role != str(expected_access_role or "").strip().lower():
                raise NodeAccessRoleError(
                    f"node {wanted} role mismatch: expected {expected_access_role}, got {actual_role}"
                )
            return node
        return None

    async def ensure_user_profile_on_node(
        self,
        *,
        tg_id: int,
        client_uuid: str,
        email: str,
        sub_id: str,
        node_code: str,
        expected_access_role: str,
        total_bytes: int,
        limit_ip: int,
    ) -> bool:
        node = await self._resolve_exact_role_node(node_code, expected_access_role)
        if node is None:
            return False
        return bool(
            await self._clients[str(node.code)].ensure_client_explicit(
                tg_id=int(tg_id),
                client_uuid=str(client_uuid or ""),
                email=str(email or ""),
                sub_id=str(sub_id or ""),
                enable=True,
                inbound_id=int(node.inbound_id),
                total_bytes=max(0, int(total_bytes)),
                limit_ip=max(0, int(limit_ip)),
            )
        )

    async def confirm_user_profile_on_node(
        self,
        *,
        tg_id: int,
        client_uuid: str,
        email: str,
        node_code: str,
        expected_access_role: str,
        total_bytes: int,
        limit_ip: int,
    ) -> bool:
        node = await self._resolve_exact_role_node(node_code, expected_access_role)
        if node is None:
            return False
        return bool(
            await self._clients[str(node.code)].confirm_client_profile(
                tg_id=int(tg_id),
                client_uuid=str(client_uuid or ""),
                email=str(email or ""),
                inbound_id=int(node.inbound_id),
                total_bytes=max(0, int(total_bytes)),
                limit_ip=max(0, int(limit_ip)),
                enabled=True,
            )
        )

    async def set_user_profile_enabled_on_node(
        self,
        *,
        tg_id: int,
        node_code: str,
        expected_access_role: str,
        enable: bool,
        sub_id: str | None = None,
    ) -> bool:
        node = await self._resolve_exact_role_node(node_code, expected_access_role)
        if node is None:
            return False
        panel_client = self._clients[str(node.code)]
        matches = await panel_client.find_clients_by_tgid(int(tg_id), include_disabled=True)
        normalized_role = str(expected_access_role or "").strip().lower()
        if normalized_role != "paid":
            matches = [
                (inbound_id, client)
                for inbound_id, client in matches
                if int(inbound_id or 0) == int(node.inbound_id or 0)
            ]
        elif enable:
            matches = [
                (inbound_id, client)
                for inbound_id, client in matches
                if str((client or {}).get("_transport_profile") or "").strip().lower() != "operator_lab"
            ]
        if not matches:
            return not bool(enable)
        total_bytes = FREE_STANDARD_QUOTA_BYTES if normalized_role == FREE_STANDARD_ROLE else 0
        limit_ip = 1 if normalized_role in {FREE_STANDARD_ROLE, FREE_SOFT_ROLE} else 5
        results = []
        for inbound_id, client in matches:
            results.append(
                bool(
                    await panel_client.update_client_enable(
                        client,
                        bool(enable),
                        sub_id=sub_id,
                        inbound_id=int(inbound_id),
                        total_bytes_override=total_bytes,
                        limit_ip_override=limit_ip,
                    )
                )
            )
        return all(results)

    async def reset_user_profile_traffic_on_node(
        self,
        *,
        tg_id: int,
        node_code: str,
        expected_access_role: str,
    ) -> bool:
        node = await self._resolve_exact_role_node(node_code, expected_access_role)
        if node is None:
            return False
        return bool(await self._clients[str(node.code)].reset_client_traffic_by_tgid(int(tg_id)))

    async def rotate_user_key_on_node(
        self,
        *,
        tg_id: int,
        node_code: str,
        old_key_uuid: str,
        new_key_uuid: str,
        sub_id: str,
    ) -> RotationPanelResult:
        node = await self._resolve_target_node(node_code)
        if node is None:
            return RotationPanelResult("retry", "rotation_panel_failed")
        return await self._rotate_user_key_on_nodes(
            nodes=[node],
            tg_id=tg_id,
            old_key_uuid=old_key_uuid,
            new_key_uuid=new_key_uuid,
            sub_id=sub_id,
        )

    async def get_user_profile_state_on_node(
        self,
        *,
        tg_id: int,
        client_uuid: str,
        email: str,
        node_code: str,
        expected_access_role: str,
    ) -> str:
        """Return the exact canonical-inbound preimage for compensation."""
        node = await self._resolve_exact_role_node(node_code, expected_access_role)
        if node is None:
            raise RuntimeError("profile_node_missing")
        rows = await self._clients[str(node.code)].find_clients_by_identity(
            tg_id=int(tg_id),
            client_uuid=str(client_uuid or ""),
            email=str(email or ""),
            include_disabled=True,
        )
        matching = [
            dict(client or {})
            for inbound_id, client in rows
            if int(inbound_id or 0) == int(node.inbound_id or 0)
        ]
        if not matching:
            return "absent"
        if len(matching) != 1:
            raise RuntimeError("profile_state_ambiguous")
        return "enabled" if bool(matching[0].get("enable", True)) else "disabled"

    async def restore_user_profile_state_on_node(
        self,
        *,
        tg_id: int,
        client_uuid: str,
        email: str,
        sub_id: str,
        node_code: str,
        expected_access_role: str,
        state: str,
    ) -> bool:
        """Restore one canonical inbound to a previously recorded safe state."""
        node = await self._resolve_exact_role_node(node_code, expected_access_role)
        if node is None:
            return False
        normalized_state = str(state or "").strip().lower()
        client = self._clients[str(node.code)]
        if normalized_state == "absent":
            return bool(
                await client.remove_client_explicit(
                    tg_id=int(tg_id),
                    client_uuid=str(client_uuid or ""),
                    email=str(email or ""),
                    inbound_id=int(node.inbound_id),
                )
            )
        if normalized_state not in {"enabled", "disabled"}:
            return False
        role = node_access_role(node, strict=True)
        total_bytes = FREE_STANDARD_QUOTA_BYTES if role == FREE_STANDARD_ROLE else 0
        limit_ip = 1 if role in {FREE_STANDARD_ROLE, FREE_SOFT_ROLE} else 5
        enabled = normalized_state == "enabled"
        ensured = await client.ensure_client_explicit(
            tg_id=int(tg_id),
            client_uuid=str(client_uuid or ""),
            email=str(email or ""),
            sub_id=str(sub_id or ""),
            enable=enabled,
            inbound_id=int(node.inbound_id),
            total_bytes=total_bytes,
            limit_ip=limit_ip,
        )
        if not ensured:
            return False
        if role == "paid":
            restored_all = await self.set_user_profile_enabled_on_node(
                tg_id=int(tg_id),
                node_code=str(node.code),
                expected_access_role=role,
                enable=enabled,
                sub_id=str(sub_id or ""),
            )
            if not restored_all:
                return False
        return bool(
            await client.confirm_client_profile(
                tg_id=int(tg_id),
                client_uuid=str(client_uuid or ""),
                email=str(email or ""),
                inbound_id=int(node.inbound_id),
                total_bytes=total_bytes,
                limit_ip=limit_ip,
                enabled=enabled,
            )
        )

    async def _read_rotation_client(self, *, node, tg_id: int) -> dict | None:
        """Read exactly one client on the node's managed inbound, or fail closed."""
        panel_client = self._clients[str(node.code)]
        rows = await panel_client.find_clients_by_tgid(int(tg_id), include_disabled=True)
        if not rows:
            return None
        matching = [
            dict(client or {})
            for inbound_id, client in rows
            if int(inbound_id or 0) == int(getattr(node, "inbound_id", 0) or 0)
        ]
        # A same-account client outside the canonical inbound is not absence:
        # it is ambiguous ownership and must block rotation before any write.
        if len(rows) != 1 or len(matching) != 1:
            raise RuntimeError("rotation_panel_ambiguous")
        return matching[0]

    @staticmethod
    def _rotation_observation(client: dict | None, *, old_key_uuid: str, new_key_uuid: str) -> str:
        if client is None:
            return "unknown"
        observed = str(client.get("id") or "").strip()
        if observed == str(old_key_uuid or "").strip():
            return "old"
        if observed == str(new_key_uuid or "").strip():
            return "new"
        return "unknown"

    async def _write_rotation_client(
        self,
        *,
        node,
        client: dict,
        tg_id: int,
        old_key_uuid: str,
        new_key_uuid: str,
        sub_id: str,
    ) -> str:
        old_uuid = str(old_key_uuid or "").strip()
        new_uuid = str(new_key_uuid or "").strip()
        if not old_uuid or not new_uuid or str(client.get("id") or "").strip() != old_uuid:
            return "unknown"
        updated = dict(client)
        updated["id"] = new_uuid
        updated["tgId"] = str(int(tg_id))
        try:
            role = node_access_role(node)
            total_bytes = FREE_STANDARD_QUOTA_BYTES if role == FREE_STANDARD_ROLE else 0
            limit_ip = 1 if role in {FREE_STANDARD_ROLE, FREE_SOFT_ROLE} else 5
            ok = await self._clients[str(node.code)].update_client_enable(
                updated,
                bool(client.get("enable", True)),
                sub_id=str(sub_id or ""),
                inbound_id=int(node.inbound_id),
                total_bytes_override=total_bytes,
                limit_ip_override=limit_ip,
                lookup_client_uuid=old_uuid,
            )
        except Exception:
            ok = False
        # A false/exceptional write is ambiguous. Always read back before
        # deciding whether this node was changed and needs compensation.
        try:
            observed = await self._read_rotation_client(node=node, tg_id=int(tg_id))
        except Exception:
            return "unknown"
        state = self._rotation_observation(observed, old_key_uuid=old_uuid, new_key_uuid=new_uuid)
        if not ok:
            return "new_ambiguous" if state == "new" else state
        if state != "new":
            return state
        try:
            confirmed = await self._clients[str(node.code)].confirm_client_profile(
                tg_id=int(tg_id),
                client_uuid=new_uuid,
                email=str(updated.get("email") or ""),
                inbound_id=int(node.inbound_id),
                total_bytes=total_bytes,
                limit_ip=limit_ip,
                enabled=bool(client.get("enable", True)),
            )
        except Exception:
            confirmed = False
        if confirmed:
            return "new"
        try:
            observed = await self._read_rotation_client(node=node, tg_id=int(tg_id))
        except Exception:
            return "unknown"
        state = self._rotation_observation(observed, old_key_uuid=old_uuid, new_key_uuid=new_uuid)
        return "new_unconfirmed" if state == "new" else state

    async def _restore_exact_client_on_node(
        self,
        *,
        node,
        client: dict,
        tg_id: int,
        old_key_uuid: str,
        new_key_uuid: str,
        sub_id: str,
    ) -> bool:
        old_uuid = str(old_key_uuid or "").strip()
        new_uuid = str(new_key_uuid or "").strip()
        if not old_uuid or not new_uuid:
            return False
        restored = dict(client)
        restored["id"] = old_uuid
        restored["tgId"] = str(int(tg_id))
        try:
            role = node_access_role(node)
            total_bytes = FREE_STANDARD_QUOTA_BYTES if role == FREE_STANDARD_ROLE else 0
            limit_ip = 1 if role in {FREE_STANDARD_ROLE, FREE_SOFT_ROLE} else 5
            ok = await self._clients[str(node.code)].update_client_enable(
                restored,
                bool(client.get("enable", True)),
                sub_id=str(sub_id or ""),
                inbound_id=int(node.inbound_id),
                total_bytes_override=total_bytes,
                limit_ip_override=limit_ip,
                lookup_client_uuid=new_uuid,
            )
        except Exception:
            ok = False
        try:
            observed = await self._read_rotation_client(node=node, tg_id=int(tg_id))
        except Exception:
            return False
        state = self._rotation_observation(observed, old_key_uuid=old_uuid, new_key_uuid=new_uuid)
        if state != "old":
            return False
        try:
            return bool(
                await self._clients[str(node.code)].confirm_client_profile(
                    tg_id=int(tg_id),
                    client_uuid=old_uuid,
                    email=str(restored.get("email") or ""),
                    inbound_id=int(node.inbound_id),
                    total_bytes=total_bytes,
                    limit_ip=limit_ip,
                    enabled=bool(client.get("enable", True)),
                )
            )
        except Exception:
            return False

    async def _apply_rotation_runtime_and_confirm(
        self,
        *,
        node,
        client: dict,
        tg_id: int,
        expected_key_uuid: str,
    ) -> bool:
        """Apply a confirmed panel UUID state to Xray, then recheck panel state.

        The post-apply readback confirms the durable panel client row. The
        authenticated restart acknowledgement plus an `xray.state=running`
        status read is the runtime-apply signal; a panel readback alone must
        never be treated as that signal.
        """
        panel_client = self._clients[str(node.code)]
        try:
            applied = await panel_client.restart_xray_service()
        except Exception:
            return False
        if not applied:
            return False
        try:
            ready = await panel_client.wait_for_xray_running()
        except Exception:
            return False
        if not ready:
            return False
        try:
            observed = await self._read_rotation_client(node=node, tg_id=int(tg_id))
        except Exception:
            return False
        if str((observed or {}).get("id") or "").strip() != str(expected_key_uuid or "").strip():
            return False
        try:
            role = node_access_role(node)
            total_bytes = FREE_STANDARD_QUOTA_BYTES if role == FREE_STANDARD_ROLE else 0
            limit_ip = 1 if role in {FREE_STANDARD_ROLE, FREE_SOFT_ROLE} else 5
            return bool(
                await panel_client.confirm_client_profile(
                    tg_id=int(tg_id),
                    client_uuid=str(expected_key_uuid or ""),
                    email=str(client.get("email") or ""),
                    inbound_id=int(node.inbound_id),
                    total_bytes=total_bytes,
                    limit_ip=limit_ip,
                    enabled=bool(client.get("enable", True)),
                )
            )
        except Exception:
            return False

    async def rotate_user_key_on_existing_nodes(
        self,
        *,
        tg_id: int,
        old_key_uuid: str,
        new_key_uuid: str,
        sub_id: str,
    ) -> RotationPanelResult:
        """Rotate every existing enabled-inventory copy without provisioning absent nodes."""
        nodes = await self.refresh()
        return await self._rotate_user_key_on_nodes(
            nodes=nodes,
            tg_id=tg_id,
            old_key_uuid=old_key_uuid,
            new_key_uuid=new_key_uuid,
            sub_id=sub_id,
        )

    async def rollback_user_key_rotation_on_node(
        self,
        *,
        tg_id: int,
        node_code: str,
        old_key_uuid: str,
        new_key_uuid: str,
        sub_id: str,
    ) -> RotationPanelResult:
        node = await self._resolve_target_node(node_code)
        if node is None:
            return RotationPanelResult("manual_review", "rotation_compensation_failed")
        return await self._rollback_user_key_rotation_on_nodes(
            nodes=[node],
            tg_id=tg_id,
            old_key_uuid=old_key_uuid,
            new_key_uuid=new_key_uuid,
            sub_id=sub_id,
        )

    async def rollback_user_key_rotation_on_existing_nodes(
        self,
        *,
        tg_id: int,
        old_key_uuid: str,
        new_key_uuid: str,
        sub_id: str,
    ) -> RotationPanelResult:
        return await self._rollback_user_key_rotation_on_nodes(
            nodes=await self.refresh(),
            tg_id=tg_id,
            old_key_uuid=old_key_uuid,
            new_key_uuid=new_key_uuid,
            sub_id=sub_id,
        )

    async def _rollback_user_key_rotation_on_nodes(
        self,
        *,
        nodes: list,
        tg_id: int,
        old_key_uuid: str,
        new_key_uuid: str,
        sub_id: str,
    ) -> RotationPanelResult:
        found = False
        complete = True
        runtime_reconcile: list[tuple[object, dict]] = []
        for node in nodes:
            code = str(getattr(node, "code", "") or "").strip()
            if not code or code not in self._clients:
                continue
            try:
                client = await self._read_rotation_client(node=node, tg_id=int(tg_id))
            except Exception:
                complete = False
                continue
            if client is None:
                continue
            found = True
            state = self._rotation_observation(client, old_key_uuid=old_key_uuid, new_key_uuid=new_key_uuid)
            if state == "old":
                runtime_reconcile.append((node, client))
                continue
            if state != "new" or not await self._restore_exact_client_on_node(
                node=node,
                client=client,
                tg_id=int(tg_id),
                old_key_uuid=old_key_uuid,
                new_key_uuid=new_key_uuid,
                sub_id=sub_id,
            ):
                complete = False
                continue
            runtime_reconcile.append((node, client))
        for node, client in runtime_reconcile:
            if not await self._apply_rotation_runtime_and_confirm(
                node=node,
                client=client,
                tg_id=int(tg_id),
                expected_key_uuid=str(old_key_uuid or ""),
            ):
                complete = False
        if not found or not complete:
            return RotationPanelResult("manual_review", "rotation_compensation_failed")
        return RotationPanelResult("succeeded", "compensated")

    async def _rotate_user_key_on_nodes(
        self,
        *,
        nodes: list,
        tg_id: int,
        old_key_uuid: str,
        new_key_uuid: str,
        sub_id: str,
    ) -> RotationPanelResult:
        old_uuid = str(old_key_uuid or "").strip()
        new_uuid = str(new_key_uuid or "").strip()
        if not old_uuid or not new_uuid:
            return RotationPanelResult("manual_review", "rotation_panel_manual_review")
        existing: list[tuple[object, dict, str]] = []
        # Preflight every node before the first write. New UUID is allowed only
        # as idempotent recovery from a prior interrupted attempt.
        for node in nodes:
            code = str(getattr(node, "code", "") or "").strip()
            if not code or code not in self._clients:
                continue
            try:
                client = await self._read_rotation_client(node=node, tg_id=int(tg_id))
            except Exception:
                return RotationPanelResult("manual_review", "rotation_panel_manual_review")
            if client is None:
                continue
            state = self._rotation_observation(client, old_key_uuid=old_uuid, new_key_uuid=new_uuid)
            if state == "unknown":
                return RotationPanelResult("manual_review", "rotation_panel_manual_review")
            existing.append((node, client, state))
        if not existing:
            return RotationPanelResult("retry", "rotation_panel_failed")

        async def compensate() -> bool:
            complete = True
            runtime_reconcile: list[tuple[object, dict]] = []
            for changed_node, changed_client, state in reversed(existing):
                if state == "old":
                    runtime_reconcile.append((changed_node, changed_client))
                    continue
                if state != "new":
                    complete = False
                    continue
                if not await self._restore_exact_client_on_node(
                    node=changed_node,
                    client=changed_client,
                    tg_id=int(tg_id),
                    old_key_uuid=old_uuid,
                    new_key_uuid=new_uuid,
                    sub_id=sub_id,
                ):
                    complete = False
                else:
                    runtime_reconcile.append((changed_node, changed_client))
            for restored_node, restored_client in runtime_reconcile:
                if not await self._apply_rotation_runtime_and_confirm(
                    node=restored_node,
                    client=restored_client,
                    tg_id=int(tg_id),
                    expected_key_uuid=old_uuid,
                ):
                    complete = False
            return complete

        for index, (node, client, state) in enumerate(existing):
            if state == "new":
                continue
            observed = await self._write_rotation_client(
                node=node,
                client=client,
                tg_id=int(tg_id),
                old_key_uuid=old_uuid,
                new_key_uuid=new_uuid,
                sub_id=sub_id,
            )
            if observed == "new":
                existing[index] = (node, client, "new")
                continue
            if observed in {"new_unconfirmed", "new_ambiguous"}:
                existing[index] = (node, client, "new")
            compensated = await compensate()
            if not compensated:
                return RotationPanelResult("manual_review", "rotation_compensation_failed")
            if observed in {"old", "new_unconfirmed", "new_ambiguous"}:
                return RotationPanelResult("retry", "rotation_panel_failed")
            return RotationPanelResult("manual_review", "rotation_panel_manual_review")
        # Panel/client readback only proves the durable panel row. Explicitly
        # apply every affected panel to Xray before canonical DB finalization.
        # An apply failure triggers best-effort restoration across every safely
        # restored panel, then still returns manual review because runtime state
        # on the failed panel is not proven.
        for node, client, _state in existing:
            if not await self._apply_rotation_runtime_and_confirm(
                node=node,
                client=client,
                tg_id=int(tg_id),
                expected_key_uuid=new_uuid,
            ):
                if not await compensate():
                    return RotationPanelResult("manual_review", "rotation_compensation_failed")
                return RotationPanelResult("manual_review", "rotation_runtime_apply_failed")
        return RotationPanelResult("succeeded", "rotated")

    async def set_user_key_enabled_on_node(
        self,
        *,
        tg_id: int,
        node_code: str,
        enable: bool,
        sub_id: str | None = None,
        hard_cap_gb: int | None = None,
    ) -> bool | None:
        n = await self._resolve_target_node(node_code)
        if not n:
            return None
        code = str(getattr(n, "code", "") or "").strip()
        try:
            client = await self._clients[code].find_client_by_tgid(int(tg_id))
            if not client:
                return None
            return bool(
                await self._clients[code].update_client_enable(
                    client,
                    bool(enable),
                    sub_id=sub_id,
                    hard_cap_gb_override=hard_cap_gb,
                )
            )
        except Exception:
            return False

    async def reset_user_key_traffic_on_node(self, *, tg_id: int, node_code: str) -> bool | None:
        n = await self._resolve_target_node(node_code)
        if not n:
            return None
        code = str(getattr(n, "code", "") or "").strip()
        try:
            client = await self._clients[code].find_client_by_tgid(int(tg_id))
            if not client:
                return None
            return bool(await self._clients[code].reset_client_traffic_by_tgid(int(tg_id)))
        except Exception:
            return False

    async def resync_user_key_subid_on_node(
        self,
        *,
        tg_id: int,
        node_code: str,
        sub_id: str,
        hard_cap_gb: int | None = None,
    ) -> bool | None:
        n = await self._resolve_target_node(node_code)
        if not n:
            return None
        code = str(getattr(n, "code", "") or "").strip()
        try:
            client = await self._clients[code].find_client_by_tgid(int(tg_id))
            if not client:
                return None
            enable = bool(client.get("enable", True))
            return bool(
                await self._clients[code].update_client_enable(
                    client,
                    enable,
                    sub_id=str(sub_id or ""),
                    hard_cap_gb_override=hard_cap_gb,
                )
            )
        except Exception:
            return False

    async def apply_user_key_limits_on_node(
        self,
        *,
        tg_id: int,
        node_code: str,
        hard_cap_gb: int | None = None,
        sub_id: str | None = None,
    ) -> bool | None:
        n = await self._resolve_target_node(node_code)
        if not n:
            return None
        code = str(getattr(n, "code", "") or "").strip()
        try:
            client = await self._clients[code].find_client_by_tgid(int(tg_id))
            if not client:
                return None
            enable = bool(client.get("enable", True))
            return bool(
                await self._clients[code].update_client_enable(
                    client,
                    enable,
                    sub_id=sub_id,
                    hard_cap_gb_override=hard_cap_gb,
                )
            )
        except Exception:
            return False

    async def add_client(self, user_uuid: str, email: str, sub_type: str, total_gb: int, tg_id: int, sub_token: str | None = None) -> bool:
        """
        Backward compatible signature used by bot.py.
        `sub_token` (preferred) is used as subscription subId in panels.
        """
        sub_id = sub_token or str(tg_id)
        user: PanelUserSnapshot | None = None
        try:
            s = SessionLocal()
            try:
                row = s.query(User).filter_by(tg_id=int(tg_id)).first()
                user = self._user_snapshot(row) if row is not None else None
            finally:
                s.close()
        except Exception:
            user = None

        if user_uses_free_pool(user or SimpleNamespace(sub_type=sub_type, current_plan_code=None)):
            nodes = await self.refresh()
            free_codes = self._free_node_codes(nodes, user=user)
            if not free_codes:
                return False
            res = await self.ensure_user_on_all_nodes(
                tg_id=tg_id,
                client_uuid=user_uuid,
                email=email,
                sub_id=sub_id,
                enable=True,
                only_node_codes=free_codes,
            )
            return any(res.values())

        res = await self.ensure_user_on_all_nodes(
            tg_id=tg_id,
            client_uuid=user_uuid,
            email=email,
            sub_id=sub_id,
            enable=True,
            only_node_codes=None,
        )
        return any(res.values())

    async def enable_client(self, user_uuid: str, enable: bool = True) -> bool:
        """
        Old code passes UUID only. We look up tg_id/email by UUID in our DB and then ensure across nodes.
        """
        s = SessionLocal()
        try:
            row = s.query(User).filter_by(uuid=user_uuid).first()
            user = self._user_snapshot(row) if row is not None else None
        finally:
            s.close()
        if user is None:
            return False
        return await self._set_user_snapshot_enabled(user, enable=bool(enable))

    @staticmethod
    def _user_snapshot(user: User) -> PanelUserSnapshot:
        return PanelUserSnapshot(
            tg_id=int(user.tg_id),
            uuid=str(user.uuid or ""),
            email=str(user.email or ""),
            sub_token=str(user.sub_token or ""),
            sub_type=str(user.sub_type or ""),
            current_plan_code=(str(user.current_plan_code) if user.current_plan_code is not None else None),
            is_active=bool(user.is_active),
            expiry_at=user.expiry_at,
            free_profile_state=str(getattr(user, "free_profile_state", "") or ""),
            free_profile_active_role=str(getattr(user, "free_profile_active_role", "") or ""),
        )

    async def _set_user_snapshot_enabled(self, user: PanelUserSnapshot, *, enable: bool) -> bool:
        sub_id = user.sub_token or str(user.tg_id)
        if not enable:
            nodes = await self.refresh()
            node_codes = [
                str(getattr(node, "code", "") or "").strip()
                for node in nodes
                if str(getattr(node, "code", "") or "").strip()
            ]
            if not node_codes:
                return False
            results = await self.set_existing_user_enabled_on_nodes(
                tg_id=int(user.tg_id),
                node_codes=node_codes,
                enable=False,
                sub_id=sub_id,
            )
            return bool(results) and all(bool(value) for value in results.values())
        if user_uses_free_pool(user):
            nodes = await self.refresh()
            free_codes = self._free_node_codes(nodes, user=user)
            if not free_codes:
                return False
            result = await self.ensure_user_on_all_nodes(
                tg_id=user.tg_id,
                client_uuid=user.uuid,
                email=user.email,
                sub_id=sub_id,
                enable=True,
                only_node_codes=free_codes,
            )
            return any(result.values())
        result = await self.ensure_user_on_all_nodes(
            tg_id=user.tg_id,
            client_uuid=user.uuid,
            email=user.email,
            sub_id=sub_id,
            enable=True,
            only_node_codes=None,
        )
        return any(result.values())

    async def update_client_traffic(self, tg_id: int, add_gb: int) -> bool:
        # Traffic/device policy is applied in panel_client based on node/env.
        # Here we just re-ensure user records to refresh policy safely.
        s = SessionLocal()
        try:
            row = s.query(User).filter_by(tg_id=tg_id).first()
            user = self._user_snapshot(row) if row is not None else None
        finally:
            s.close()
        if user is None:
            return False
        return await self._set_user_snapshot_enabled(user, enable=True)

    async def set_client_traffic(self, tg_id: int, total_gb: int) -> bool:
        # Legacy compatibility: policy is node/env-driven, not ad-hoc per call.
        return await self.update_client_traffic(tg_id, 0)

    async def subtract_client_traffic(self, tg_id: int, sub_gb: int) -> bool:
        # Legacy compatibility: policy is node/env-driven, not ad-hoc per call.
        return await self.update_client_traffic(tg_id, 0)

    async def update_client_comment(self, tg_id: int, comment: str) -> bool:
        nodes = await self.refresh()
        ok_any = False
        for n in nodes:
            ok = await self._clients[n.code].update_client_comment_by_tgid(tg_id, comment)
            ok_any = ok_any or ok
        return ok_any

    async def delete_client(self, tg_id: int) -> bool:
        nodes = await self.refresh()
        ok_any = False
        for n in nodes:
            client = await self._clients[n.code].find_client_by_tgid(tg_id)
            if not client:
                continue
            uuid = client.get("id")
            if not uuid:
                continue
            ok = await self._clients[n.code].delete_client_uuid(uuid)
            ok_any = ok_any or ok
        return ok_any

    async def get_client_stats(self, email: str) -> dict | None:
        """
        Best-effort stats: scan nodes and return the first node where this email exists.
        """
        nodes = await self.refresh()
        if not nodes:
            return None
        for n in nodes:
            usage = await self._clients[n.code].get_usage_by_email(email)
            if usage is None:
                continue
            return {"up": usage["up"], "down": usage["down"], "total": usage["total"]}
        return {"up": 0, "down": 0, "total": 0}

    async def get_usage_by_tgid(self, tg_id: int) -> dict | None:
        """
        Return usage for a user by tg_id from the node where the client exists.
        """
        nodes = await self.refresh()
        if not nodes:
            return None
        for n in nodes:
            try:
                c = await self._clients[n.code].find_client_by_tgid(tg_id)
                if not c:
                    continue
                email = c.get("email")
                if not email:
                    continue
                usage = await self._clients[n.code].get_usage_by_email(email)
                if usage is None:
                    return {"up": 0, "down": 0, "total": 0, "email": email, "node_code": n.code}
                return {
                    "up": usage.get("up", 0),
                    "down": usage.get("down", 0),
                    "total": usage.get("total", 0),
                    "email": email,
                    "node_code": n.code,
                }
            except Exception:
                continue
        return None

    async def get_connection_status_by_tgid(self, tg_id: int, *, per_node_timeout_sec: float = 4.0) -> dict:
        """
        Best-effort online snapshot from panel runtimes across enabled nodes.

        Returns:
        {
          "known": bool,                # client exists on at least one node
          "state": "online|offline|unknown",
          "mapped_nodes": [code...],    # nodes where client record exists
          "online_nodes": [code...],    # subset where panel reports online=True
          "enabled_nodes": [code...],   # subset where client enable=True
          "last_online_at": iso|None,   # max known last-online among mapped nodes
          "last_online_age_seconds": int|None,
        }
        """
        nodes = await self.refresh()
        if not nodes:
            return {
                "known": False,
                "state": "unknown",
                "mapped_nodes": [],
                "online_nodes": [],
                "enabled_nodes": [],
                "last_online_at": None,
                "last_online_age_seconds": None,
            }

        async def _probe(node):
            try:
                snap = await asyncio.wait_for(
                    self._clients[node.code].get_client_runtime_by_tgid(tg_id),
                    timeout=max(0.5, float(per_node_timeout_sec)),
                )
            except Exception:
                return None
            if not snap:
                return None
            out = dict(snap)
            out["node_code"] = node.code
            return out

        rows = await asyncio.gather(*[_probe(n) for n in nodes], return_exceptions=False)
        found = [r for r in rows if r]
        if not found:
            return {
                "known": False,
                "state": "unknown",
                "mapped_nodes": [],
                "online_nodes": [],
                "enabled_nodes": [],
                "last_online_at": None,
                "last_online_age_seconds": None,
            }

        mapped_nodes = [str(r.get("node_code", "")) for r in found if r.get("node_code")]
        online_nodes = [str(r.get("node_code", "")) for r in found if r.get("online") is True and r.get("node_code")]
        enabled_nodes = [str(r.get("node_code", "")) for r in found if bool(r.get("enable", True)) and r.get("node_code")]
        last_online_age_values = [int(r.get("last_online_age_seconds")) for r in found if r.get("last_online_age_seconds") is not None]
        last_online_at_values = [str(r.get("last_online_at")) for r in found if r.get("last_online_at")]
        min_age = min(last_online_age_values) if last_online_age_values else None
        latest_iso = None
        if last_online_age_values and last_online_at_values:
            try:
                # Pick row with smallest age (most recent online activity).
                best = min(
                    (
                        (int(r.get("last_online_age_seconds")), str(r.get("last_online_at")))
                        for r in found
                        if r.get("last_online_age_seconds") is not None and r.get("last_online_at")
                    ),
                    key=lambda x: x[0],
                )
                latest_iso = best[1]
            except Exception:
                latest_iso = last_online_at_values[0]

        if online_nodes:
            state = "online"
        elif any(r.get("online") is False for r in found):
            state = "offline"
        else:
            state = "unknown"

        return {
            "known": True,
            "state": state,
            "mapped_nodes": mapped_nodes,
            "online_nodes": online_nodes,
            "enabled_nodes": enabled_nodes,
            "last_online_at": latest_iso,
            "last_online_age_seconds": min_age,
        }

    async def get_clients_list(self) -> list[dict] | None:
        """
        Compatibility: return clients list from the first node inbound.
        Used by health checks only.
        """
        nodes = await self.refresh()
        if not nodes:
            return []
        inbounds = await self._clients[nodes[0].code]._get_inbounds()
        for inb in inbounds:
            if inb.get("id") == nodes[0].inbound_id:
                try:
                    import json

                    settings = json.loads(inb.get("settings", "{}"))
                    return settings.get("clients", []) or []
                except Exception:
                    return []
        return []

    async def reset_client_traffic(self, tg_id: int, *, only_free: bool = False) -> bool:
        """
        Reset user traffic counters on panel side.
        - `only_free=True` targets free pool when available.
        - Backward-compatible fallback: if free pool is absent, probe all enabled nodes.
        """
        nodes = await self.refresh()
        if not nodes:
            return False

        target_nodes = list(nodes)
        if only_free:
            free_codes = set(self._free_node_codes(nodes))
            if free_codes:
                target_nodes = [n for n in nodes if (n.code or "") in free_codes]

        ok_any = False
        for n in target_nodes:
            try:
                ok = await self._clients[n.code].reset_client_traffic_by_tgid(int(tg_id))
                ok_any = ok_any or bool(ok)
            except Exception:
                continue
        return ok_any

    async def set_tariff_traffic(self, tg_id: int, new_total_gb: int) -> bool:
        # Legacy compatibility: policy is node/env-driven, not ad-hoc per call.
        return await self.update_client_traffic(tg_id, 0)
