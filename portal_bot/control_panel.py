from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))
load_dotenv()

from db import SessionLocal
from models import User, UserNode
from node_policy import free_pool_node_codes, node_code_base, paid_pool_nodes, user_uses_free_pool
from nodes_repo import enabled_nodes
from panel_client import PanelClient


logger = logging.getLogger(__name__)


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
    def _free_node_codes(nodes: list) -> list[str]:
        return free_pool_node_codes(nodes)

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
            # Keep existing clients if node code matches, otherwise rebuild.
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
        finally:
            s.close()

    @staticmethod
    def _compare_node_inbound(node, runtime: dict | None, *, error: str = "") -> dict:
        runtime = runtime or {}
        expected_sni = str(getattr(node, "reality_sni", "") or "").strip()
        expected_sid = str(getattr(node, "reality_sid", "") or "").strip()
        expected_pbk = str(getattr(node, "reality_pbk", "") or "").strip()
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
            "pbk_match": (not expected_pbk) or (not str(runtime.get("public_key") or "")) or (expected_pbk == str(runtime.get("public_key") or "")),
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
                error = str(exc)[:200]
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
            logger.warning("user_nodes persist failed: %s", e)
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
            toggled = False
            for n in candidates:
                try:
                    c = await self._clients[n.code].find_client_by_tgid(tg_id)
                    if not c:
                        continue
                    results[n.code] = await self._clients[n.code].update_client_enable(c, enable, sub_id=sub_id)
                    toggled = True
                    break
                except Exception:
                    results[n.code] = False
            if not toggled and candidates:
                # User absent on the pool is not an error for compatibility.
                results[candidates[0].code] = True
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

        rows: list[dict] = []
        for n in selected_nodes:
            code = str(getattr(n, "code", "") or "").strip()
            client = None
            runtime = None
            error = ""
            try:
                client = await self._clients[code].find_client_by_tgid(int(tg_id))
                if client:
                    runtime = await self._clients[code].get_client_runtime_by_tgid(int(tg_id))
            except Exception as exc:
                error = str(exc)[:200]
            rows.append(
                {
                    "node_code": code,
                    "node_name": str(getattr(n, "name", "") or ""),
                    "node_host": str(getattr(n, "host", "") or ""),
                    "node_enabled": bool(getattr(n, "enabled", True)),
                    "node_healthy": bool(getattr(n, "is_healthy", False)),
                    "client": client,
                    "runtime": runtime,
                    "error": error,
                }
            )
        return rows

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
                    "panel_error": str(exc)[:200],
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
                return {"node_code": "", "rows": [], "error": "missing_node_code"}
            async with semaphore:
                try:
                    rows = await self._clients[code].get_node_online_clients()
                    return {"node_code": code, "rows": rows, "error": ""}
                except Exception as exc:
                    return {"node_code": code, "rows": [], "error": str(exc)[:300]}

        collected = await asyncio.gather(*[_collect(n) for n in selected_nodes], return_exceptions=False)
        rows: list[dict] = []
        errors: list[dict] = []
        for item in collected:
            if not item:
                continue
            if item.get("error"):
                errors.append({"node_code": item.get("node_code"), "error": item.get("error")})
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
                        "error": str(exc)[:300],
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
        user = None
        try:
            s = SessionLocal()
            try:
                user = s.query(User).filter_by(tg_id=int(tg_id)).first()
            finally:
                s.close()
        except Exception:
            user = None

        if user_uses_free_pool(user or SimpleNamespace(sub_type=sub_type, current_plan_code=None)):
            nodes = await self.refresh()
            free_codes = self._free_node_codes(nodes)
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
            u = s.query(User).filter_by(uuid=user_uuid).first()
            if not u:
                return False
            sub_id = u.sub_token or str(u.tg_id)
            if user_uses_free_pool(u):
                nodes = await self.refresh()
                free_codes = self._free_node_codes(nodes)
                if not free_codes:
                    return False
                res = await self.ensure_user_on_all_nodes(
                    tg_id=u.tg_id,
                    client_uuid=u.uuid,
                    email=u.email,
                    sub_id=sub_id,
                    enable=enable,
                    only_node_codes=free_codes,
                )
                return any(res.values())

            res = await self.ensure_user_on_all_nodes(
                tg_id=u.tg_id,
                client_uuid=u.uuid,
                email=u.email,
                sub_id=sub_id,
                enable=enable,
                only_node_codes=None,
            )
            return any(res.values())
        finally:
            s.close()

    async def update_client_traffic(self, tg_id: int, add_gb: int) -> bool:
        # Traffic/device policy is applied in panel_client based on node/env.
        # Here we just re-ensure user records to refresh policy safely.
        s = SessionLocal()
        try:
            u = s.query(User).filter_by(tg_id=tg_id).first()
            if not u:
                return False
            return await self.enable_client(u.uuid, True)
        finally:
            s.close()

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
