from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
import os
from datetime import datetime, timezone
import re
from urllib.parse import quote

import aiohttp

from nodes_repo import NodeRuntime
from node_policy import (
    FREE_SOFT_ROLE,
    FREE_STANDARD_QUOTA_BYTES,
    FREE_STANDARD_ROLE,
    node_access_role,
)
from transport_catalog import node_transport_profiles, transport_inbound_ids


logger = logging.getLogger(__name__)


def _deep_find(obj, keys: set[str]):
    if isinstance(obj, dict):
        for key, value in obj.items():
            normalized = re.sub(r"[^a-z0-9]+", "", str(key or "").lower())
            if normalized in keys:
                return value
            found = _deep_find(value, keys)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _deep_find(item, keys)
            if found is not None:
                return found
    return None


def _to_float(value) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except Exception:
        return None


def _size_to_bytes(value) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        numeric = float(value)
        if numeric <= 0:
            return 0
        return int(numeric)
    text = str(value).strip().replace(",", ".")
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*([kmgtp]?i?b)?", text, re.I)
    if not match:
        return None
    number = float(match.group(1))
    unit = (match.group(2) or "b").lower()
    factors = {
        "b": 1,
        "kb": 1024,
        "kib": 1024,
        "mb": 1024**2,
        "mib": 1024**2,
        "gb": 1024**3,
        "gib": 1024**3,
        "tb": 1024**4,
        "tib": 1024**4,
        "pb": 1024**5,
        "pib": 1024**5,
    }
    factor = factors.get(unit, 1)
    return int(max(0.0, number) * factor)


def _nested_value(obj, *path: str):
    current = obj
    for part in path:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


@dataclass
class PanelClient:
    node: NodeRuntime
    session: aiohttp.ClientSession | None = None
    cookies: aiohttp.CookieJar | None = None
    csrf_token: str | None = None

    def _env_name(self, suffix: str) -> str:
        import re

        code = re.sub(r"[^A-Z0-9]+", "_", (self.node.code or "").upper()).strip("_")
        return f"NODE_{code}_{suffix}"

    def _env(self, suffix: str) -> str:
        return (os.getenv(self._env_name(suffix)) or "").strip()

    @staticmethod
    def _to_int(value: str | None, default: int) -> int:
        if value is None:
            return default
        text = str(value).strip()
        if text == "":
            return default
        try:
            return int(text)
        except Exception:
            return default

    def _node_or_global_int(self, *, node_suffix: str, global_name: str, default: int) -> int:
        """
        Node-specific env has priority, global env is fallback.
        Example:
        - NODE_PL_FREE_LIMIT_IP
        - FREE_LIMIT_IP
        """
        node_val = self._env(node_suffix)
        if node_val != "":
            return self._to_int(node_val, default)
        return self._to_int(os.getenv(global_name), default)

    def _is_free_node(self) -> bool:
        return node_access_role(self.node) in {FREE_STANDARD_ROLE, FREE_SOFT_ROLE}

    def _limit_ip_policy(self) -> int:
        """
        Per-node device policy.
        Free contract: exactly 1 device.
        Paid default: 5 devices.
        """
        if node_access_role(self.node) in {FREE_STANDARD_ROLE, FREE_SOFT_ROLE}:
            return 1
        return max(
            0,
            self._node_or_global_int(
                node_suffix="LIMIT_IP",
                global_name="PAID_LIMIT_IP",
                default=5,
            ),
        )

    def _total_gb_policy(self) -> int:
        """
        Per-node traffic cap in GB.
        Free standard contract: exactly 5 GiB; free soft is unlimited here and
        enforced by the dedicated node shaper.
        Paid: always unlimited (0).
        """
        if node_access_role(self.node) == FREE_STANDARD_ROLE:
            return int(FREE_STANDARD_QUOTA_BYTES // (1024**3))
        return 0

    def _total_bytes_policy(self) -> int:
        gb = self._total_gb_policy()
        if gb <= 0:
            return 0
        return int(gb) * 1024 * 1024 * 1024

    def _base(self) -> str:
        base = self._env("PANEL_BASE_URL") or self.node.panel_base_url
        path = self._env("PANEL_PATH") or self.node.panel_path
        return f"{base.rstrip('/')}/{path.strip('/')}"

    @staticmethod
    def _as_bool(value) -> bool | None:
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return bool(value)
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off"}:
            return False
        return None

    @staticmethod
    def _as_epoch_seconds(value) -> int | None:
        if value is None:
            return None
        try:
            iv = int(value)
        except Exception:
            return None
        if iv <= 0:
            return None
        # x-ui can return ms timestamps.
        if iv > 10_000_000_000:
            iv //= 1000
        return iv

    @staticmethod
    def _decode_settings(raw) -> dict:
        if isinstance(raw, dict):
            return dict(raw)
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
            except Exception:
                return {}
            return parsed if isinstance(parsed, dict) else {}
        return {}

    def _managed_inbound_ids(self, *, include_disabled: bool = False) -> list[int]:
        ids = transport_inbound_ids(
            self.node,
            include_disabled=include_disabled,
            include_operator_lab=include_disabled,
        )
        if ids:
            return ids
        fallback = int(self.node.inbound_id or 0)
        return [fallback] if fallback > 0 else []

    def _transport_profile_for_inbound(self, inbound_id: int, *, include_disabled: bool = False) -> dict | None:
        target_id = int(inbound_id or 0)
        if target_id <= 0:
            return None
        for profile in node_transport_profiles(self.node, include_disabled=include_disabled):
            try:
                current_id = int(profile.get("inbound_id") or 0)
            except Exception:
                current_id = 0
            if current_id == target_id:
                return profile
        return None

    @staticmethod
    def _client_flow_value(flow, fallback: str | None = None) -> str:
        if flow is None:
            return str(fallback or "")
        return str(flow)

    def _managed_flow_for_inbound(self, inbound_id: int) -> str:
        profile = self._transport_profile_for_inbound(inbound_id, include_disabled=True) or {}
        if str(profile.get("kind") or "").lower() == "reality":
            return str(profile.get("flow") or self.node.flow or "")
        return ""

    def _selected_inbounds(self, inbounds: list[dict], *, include_disabled: bool = False) -> list[dict]:
        target_ids = set(self._managed_inbound_ids(include_disabled=include_disabled))
        if not target_ids:
            fallback = int(self.node.inbound_id or 0)
            return [inb for inb in inbounds if int(inb.get("id") or 0) == fallback]
        return [inb for inb in inbounds if int(inb.get("id") or 0) in target_ids]

    async def find_clients_by_tgid(self, tg_id: int, *, include_disabled: bool = False) -> list[tuple[int, dict]]:
        target_tg = str(tg_id).strip()
        matches: list[tuple[int, dict]] = []
        for inb in self._selected_inbounds(await self._get_inbounds(), include_disabled=include_disabled):
            inbound_id = int(inb.get("id") or 0)
            settings = self._decode_settings(inb.get("settings", "{}"))
            for client in settings.get("clients", []) or []:
                if str((client or {}).get("tgId", "")).strip() != target_tg:
                    continue
                item = dict(client or {})
                item["_panel_inbound_id"] = inbound_id
                profile = self._transport_profile_for_inbound(inbound_id, include_disabled=True)
                if profile:
                    item["_transport_profile"] = str(profile.get("name") or "")
                matches.append((inbound_id, item))
        matches.sort(key=lambda row: row[0])
        return matches

    async def ensure_session(self) -> None:
        if self.session is None:
            self.session = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True))

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()
            self.session = None
            self.cookies = None
            self.csrf_token = None

    async def _refresh_csrf_token(self) -> bool:
        """
        3x-ui 3.x requires CSRF on unsafe session-authenticated requests.
        Older x-ui/3x-ui builds do not expose this endpoint, so absence is not
        an error and the caller falls back to the legacy cookie flow.
        """
        await self.ensure_session()
        try:
            async with self.session.get(
                f"{self._base()}/csrf-token",
                headers={"X-Requested-With": "XMLHttpRequest"},
                cookies=self.cookies,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.cookies:
                    self.cookies = resp.cookies
                if resp.status != 200:
                    return False
                data = await resp.json(content_type=None)
        except Exception:
            return False

        if not isinstance(data, dict):
            return False
        token = data.get("obj") or data.get("csrfToken") or data.get("csrf_token") or data.get("token")
        if not token:
            return False
        self.csrf_token = str(token)
        return True

    async def _csrf_headers(self, *, refresh: bool = True) -> dict[str, str]:
        if refresh and not self.csrf_token:
            await self._refresh_csrf_token()
        headers = {"X-Requested-With": "XMLHttpRequest"}
        if not self.csrf_token:
            return headers
        headers["X-CSRF-Token"] = self.csrf_token
        return headers

    async def login(self) -> bool:
        await self.ensure_session()
        user = self._env("PANEL_USER") or self.node.panel_user
        pwd = self._env("PANEL_PASS") or self.node.panel_pass
        if not user or not pwd:
            logger.warning("panel credentials missing for node=%s (set %s/%s)", self.node.code, self._env_name("PANEL_USER"), self._env_name("PANEL_PASS"))
            return False
        try:
            await self._refresh_csrf_token()
            async with self.session.post(
                f"{self._base()}/login",
                data={"username": user, "password": pwd},
                headers=await self._csrf_headers(refresh=False),
                cookies=self.cookies,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    logger.warning("panel login failed (status=%s) node=%s", resp.status, self.node.code)
                    return False
                if resp.cookies:
                    self.cookies = resp.cookies
                return True
        except Exception as e:
            logger.exception("panel login error node=%s: %s", self.node.code, e)
            return False

    async def _get_inbounds(self) -> list[dict]:
        if not self.cookies:
            ok = await self.login()
            if not ok:
                return []

        async def _fetch() -> list[dict] | None:
            await self.ensure_session()
            try:
                async with self.session.get(
                    f"{self._base()}/panel/api/inbounds/list",
                    cookies=self.cookies,
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json(content_type=None)
                    if not isinstance(data, dict) or not data.get("success"):
                        return None
                    return data.get("obj", []) or []
            except Exception:
                return None

        inbounds = await _fetch()
        if inbounds is not None:
            return inbounds

        self.cookies = None
        self.csrf_token = None
        ok = await self.login()
        if not ok:
            return []
        inbounds = await _fetch()
        return inbounds if inbounds is not None else []

    async def get_server_status(self) -> dict | None:
        if not self.cookies:
            ok = await self.login()
            if not ok:
                return None
        await self.ensure_session()
        try:
            async with self.session.get(
                f"{self._base()}/panel/api/server/status",
                cookies=self.cookies,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json(content_type=None)
                if not isinstance(data, dict) or not bool(data.get("success")):
                    return None
                obj = data.get("obj")
                return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    async def get_system_metrics(self) -> dict[str, float | int | None]:
        status = await self.get_server_status()
        if not status:
            return {
                "cpu_percent": None,
                "memory_used_mb": None,
                "memory_total_mb": None,
                "disk_used_gb": None,
                "disk_total_gb": None,
                "disk_free_gb": None,
                "network_rx_bytes_total": None,
                "network_tx_bytes_total": None,
                "network_rx_bytes_per_sec": None,
                "network_tx_bytes_per_sec": None,
            }

        cpu_percent = _to_float(
            _deep_find(
                status,
                {
                    "cpu",
                    "cpupercent",
                    "cpuusage",
                    "cpucurrent",
                    "cpuuse",
                },
            )
        )

        mem_used_raw = _nested_value(status, "mem", "current") or _deep_find(
            status, {"memused", "memoryused", "currentmem", "currentmemory", "usedmemory"}
        )
        mem_total_raw = _nested_value(status, "mem", "total") or _deep_find(
            status, {"memtotal", "memorytotal", "totalmem", "totalmemory"}
        )
        disk_used_raw = _nested_value(status, "disk", "current") or _deep_find(status, {"diskused", "useddisk", "currdisk"})
        disk_total_raw = _nested_value(status, "disk", "total") or _deep_find(status, {"disktotal", "totaldisk"})
        disk_free_raw = _nested_value(status, "disk", "free") or _deep_find(
            status, {"diskfree", "freedisk", "diskavail", "diskavailable"}
        )
        net_tx_bytes_per_sec = _size_to_bytes(_nested_value(status, "netIO", "up"))
        net_rx_bytes_per_sec = _size_to_bytes(_nested_value(status, "netIO", "down"))
        net_tx_bytes_total = _size_to_bytes(_nested_value(status, "netTraffic", "sent"))
        net_rx_bytes_total = _size_to_bytes(_nested_value(status, "netTraffic", "recv"))

        mem_used_bytes = _size_to_bytes(mem_used_raw)
        mem_total_bytes = _size_to_bytes(mem_total_raw)
        disk_used_bytes = _size_to_bytes(disk_used_raw)
        disk_total_bytes = _size_to_bytes(disk_total_raw)
        disk_free_bytes = _size_to_bytes(disk_free_raw)
        if disk_free_bytes is None and disk_total_bytes is not None and disk_used_bytes is not None:
            disk_free_bytes = max(0, int(disk_total_bytes) - int(disk_used_bytes))

        return {
            "cpu_percent": round(cpu_percent, 1) if cpu_percent is not None else None,
            "memory_used_mb": int(round(mem_used_bytes / (1024**2))) if mem_used_bytes is not None else None,
            "memory_total_mb": int(round(mem_total_bytes / (1024**2))) if mem_total_bytes is not None else None,
            "disk_used_gb": round(disk_used_bytes / (1024**3), 2) if disk_used_bytes is not None else None,
            "disk_total_gb": round(disk_total_bytes / (1024**3), 2) if disk_total_bytes is not None else None,
            "disk_free_gb": round(disk_free_bytes / (1024**3), 2) if disk_free_bytes is not None else None,
            "network_rx_bytes_total": net_rx_bytes_total,
            "network_tx_bytes_total": net_tx_bytes_total,
            "network_rx_bytes_per_sec": net_rx_bytes_per_sec,
            "network_tx_bytes_per_sec": net_tx_bytes_per_sec,
        }

    async def get_node_runtime_snapshot(self) -> dict:
        """
        Read-only runtime telemetry from the node panel.

        3x-ui remains an execution layer; this snapshot is intentionally
        best-effort and must not become subscription/source-of-truth data.
        """
        started = time.monotonic()
        auth_ok = False
        error = ""
        status: dict | None = None
        metrics: dict[str, float | int | None] = {}
        inbound: dict | None = None
        online: dict[str, int] = {"online_keys_now": 0, "online_connections_now": 0}
        try:
            auth_ok = await self.login()
            auth_latency_ms = int(round((time.monotonic() - started) * 1000))
            if not auth_ok:
                return {
                    "node_code": str(getattr(self.node, "code", "") or ""),
                    "panel_auth_ok": False,
                    "panel_latency_ms": auth_latency_ms,
                    "csrf_mode": bool(self.csrf_token),
                    "api_token_mode": bool(self._env("PANEL_API_TOKEN")),
                    "error": "panel auth failed",
                    "server_status": None,
                    "system": {},
                    "inbound": None,
                    "online": online,
                }
            status = await self.get_server_status()
            metrics = await self.get_system_metrics()
            inbound = await self.get_inbound_snapshot()
            online = await self.get_node_online_summary()
            auth_latency_ms = int(round((time.monotonic() - started) * 1000))
        except Exception as exc:
            auth_latency_ms = int(round((time.monotonic() - started) * 1000))
            error = str(exc)[:300]
        return {
            "node_code": str(getattr(self.node, "code", "") or ""),
            "panel_auth_ok": bool(auth_ok),
            "panel_latency_ms": auth_latency_ms,
            "csrf_mode": bool(self.csrf_token),
            "api_token_mode": bool(self._env("PANEL_API_TOKEN")),
            "error": error,
            "server_status": status or None,
            "system": metrics or {},
            "inbound": inbound,
            "online": online or {"online_keys_now": 0, "online_connections_now": 0},
        }

    async def get_inbound_snapshot(self, inbound_id: int | None = None) -> dict | None:
        target_id = int(inbound_id or self.node.inbound_id or 0)
        if target_id <= 0:
            return None
        inbounds = await self._get_inbounds()
        for inb in inbounds:
            try:
                current_id = int(inb.get("id") or 0)
            except Exception:
                current_id = 0
            if current_id != target_id:
                continue

            stream_raw = inb.get("streamSettings")
            if stream_raw is None:
                stream_raw = inb.get("stream_settings")
            if isinstance(stream_raw, str):
                try:
                    stream = json.loads(stream_raw)
                except Exception:
                    stream = {}
            elif isinstance(stream_raw, dict):
                stream = dict(stream_raw)
            else:
                stream = {}

            reality = stream.get("realitySettings") or {}
            short_ids = reality.get("shortIds") or []
            if isinstance(short_ids, str):
                short_ids = [short_ids]
            server_names = reality.get("serverNames") or []
            if isinstance(server_names, str):
                server_names = [server_names]

            return {
                "inbound_id": current_id,
                "remark": str(inb.get("remark") or ""),
                "enable": bool(inb.get("enable", True)),
                "port": int(inb.get("port") or 0),
                "protocol": str(inb.get("protocol") or ""),
                "network": str(stream.get("network") or ""),
                "security": str(stream.get("security") or ""),
                "dest": str(reality.get("dest") or ""),
                "server_names": [str(x or "") for x in server_names if str(x or "").strip()],
                "short_ids": [str(x or "") for x in short_ids if str(x or "").strip()],
                "public_key": "",
            }
        return None

    async def _get_online_emails(self) -> tuple[bool, set[str]]:
        """
        Query online clients list from panel API.
        Returns (fetched, emails_set):
        - fetched=False means the endpoint is unavailable/error.
        - fetched=True means response parsed; empty set is valid (nobody online).
        """
        if not self.cookies:
            ok = await self.login()
            if not ok:
                return False, set()
        await self.ensure_session()
        try:
            async with self.session.get(
                f"{self._base()}/panel/api/inbounds/onlines",
                cookies=self.cookies,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    return False, set()
                data = await resp.json(content_type=None)
                if not isinstance(data, dict) or not bool(data.get("success")):
                    return False, set()
                obj = data.get("obj")
                if isinstance(obj, list):
                    return True, {str(x or "").strip() for x in obj if str(x or "").strip()}
                if isinstance(obj, dict):
                    vals = obj.get("emails")
                    if isinstance(vals, list):
                        return True, {str(x or "").strip() for x in vals if str(x or "").strip()}
                    return True, set()
                return True, set()
        except Exception:
            return False, set()

    async def get_usage_by_email(self, email: str) -> dict | None:
        """
        Returns aggregated traffic stats from panel clientStats across managed node inbounds.
        """
        total_up = 0
        total_down = 0
        found = False
        inbounds = await self._get_inbounds()
        for inb in self._selected_inbounds(inbounds):
            for cs in inb.get("clientStats", []) or []:
                if cs.get("email") == email:
                    total_up += int(cs.get("up", 0) or 0)
                    total_down += int(cs.get("down", 0) or 0)
                    found = True
        if not found:
            return None
        return {"up": total_up, "down": total_down, "total": total_up + total_down}

    async def find_client_by_tgid(self, tg_id: int) -> dict | None:
        matches = await self.find_clients_by_tgid(tg_id)
        if not matches:
            return None
        return matches[0][1]

    async def find_clients_by_identity(
        self,
        *,
        tg_id: int,
        client_uuid: str = "",
        email: str = "",
        include_disabled: bool = False,
    ) -> list[tuple[int, dict]]:
        """
        Find existing panel rows for the same backend account.

        Older imported clients can miss tgId while still carrying the canonical
        email or UUID. Treat those rows as the same account so resync can repair
        tgId/subId instead of failing on duplicate email during addClient.
        """
        target_tg = str(tg_id).strip()
        target_uuid = str(client_uuid or "").strip()
        target_email = str(email or "").strip()
        matches: list[tuple[int, dict]] = []
        seen: set[tuple[int, str, str]] = set()
        for inb in self._selected_inbounds(await self._get_inbounds(), include_disabled=include_disabled):
            inbound_id = int(inb.get("id") or 0)
            settings = self._decode_settings(inb.get("settings", "{}"))
            for client in settings.get("clients", []) or []:
                item = dict(client or {})
                panel_tg = str(item.get("tgId", "") or "").strip()
                panel_uuid = str(item.get("id", "") or "").strip()
                panel_email = str(item.get("email", "") or "").strip()
                if not (
                    (target_tg and panel_tg == target_tg)
                    or (target_uuid and panel_uuid == target_uuid)
                    or (target_email and panel_email == target_email)
                ):
                    continue
                item["_panel_inbound_id"] = inbound_id
                profile = self._transport_profile_for_inbound(inbound_id, include_disabled=True)
                if profile:
                    item["_transport_profile"] = str(profile.get("name") or "")
                identity_key = (inbound_id, panel_uuid, panel_email)
                if identity_key in seen:
                    continue
                seen.add(identity_key)
                matches.append((inbound_id, item))
        matches.sort(key=lambda row: row[0])
        return matches

    async def get_client_runtime_by_tgid(self, tg_id: int) -> dict | None:
        """
        Return best-effort runtime snapshot for a client on this node:
        - enable flag from panel client settings
        - traffic counters from clientStats
        - online status when the panel exposes it (field names vary by x-ui versions)
        """
        inbounds = await self._get_inbounds()
        for inb in self._selected_inbounds(inbounds):
            settings = self._decode_settings(inb.get("settings", "{}"))
            clients = settings.get("clients", []) or []
            target = None
            for c in clients:
                if str(c.get("tgId", "")).strip() == str(tg_id).strip():
                    target = dict(c or {})
                    target["_panel_inbound_id"] = int(inb.get("id") or 0)
                    break
            if not target:
                continue

            email = str(target.get("email", "") or "")
            stat = None
            for cs in inb.get("clientStats", []) or []:
                if str(cs.get("email", "") or "") == email:
                    stat = cs
                    break

            online = None
            last_online_epoch = None
            ip_count_value = None
            if isinstance(stat, dict):
                for key in ("online", "isOnline", "is_online"):
                    if key in stat:
                        online = self._as_bool(stat.get(key))
                        break
                if online is None:
                    ip_count = stat.get("ipCount", stat.get("ip_count"))
                    if ip_count is not None:
                        try:
                            ip_count_value = max(0, int(ip_count))
                            online = ip_count_value > 0
                        except Exception:
                            online = None
                            ip_count_value = None
                for key in ("lastOnlineTime", "lastOnline", "last_online", "lastSeen", "last_seen"):
                    if key in stat:
                        last_online_epoch = self._as_epoch_seconds(stat.get(key))
                        if last_online_epoch is not None:
                            break
            if online is None and email:
                fetched, online_emails = await self._get_online_emails()
                if fetched:
                    online = email in online_emails
            if online is None and last_online_epoch is not None:
                recent_sec = max(15, self._to_int(os.getenv("PANEL_ONLINE_RECENT_SECONDS"), 90))
                online = (int(datetime.now(timezone.utc).timestamp()) - int(last_online_epoch)) <= recent_sec

            up = int((stat or {}).get("up", 0) or 0)
            down = int((stat or {}).get("down", 0) or 0)
            last_online_at = None
            last_online_age_seconds = None
            if last_online_epoch is not None:
                dt = datetime.fromtimestamp(last_online_epoch, tz=timezone.utc)
                last_online_at = dt.isoformat().replace("+00:00", "Z")
                last_online_age_seconds = max(0, int(datetime.now(timezone.utc).timestamp()) - int(last_online_epoch))
            return {
                "email": email,
                "enable": bool(target.get("enable", True)),
                "online": online,
                "up": up,
                "down": down,
                "total": up + down,
                "ip_count": ip_count_value,
                "last_online_at": last_online_at,
                "last_online_age_seconds": last_online_age_seconds,
            }
        return None

    async def get_node_online_summary(self) -> dict[str, int]:
        """
        Return best-effort live summary for the configured inbound on this node.

        Metrics:
        - online_keys_now: distinct keys currently online on this node
        - online_connections_now: current connection estimate using panel ip_count,
          with a fallback of 1 per online key when ip_count is missing
        """
        inbounds = self._selected_inbounds(await self._get_inbounds())
        if not inbounds:
            return {
                "online_keys_now": 0,
                "online_connections_now": 0,
            }
        online_emails_fetched = False
        online_emails: set[str] = set()
        online_keys: set[str] = set()
        online_connections_by_email: dict[str, int] = {}

        for target_inbound in inbounds:
            settings = self._decode_settings(target_inbound.get("settings", "{}"))
            clients = settings.get("clients", []) or []
            stats_by_email: dict[str, dict] = {}
            for stat in target_inbound.get("clientStats", []) or []:
                email = str((stat or {}).get("email", "") or "").strip()
                if email:
                    stats_by_email[email] = stat

            for client in clients:
                email = str((client or {}).get("email", "") or "").strip()
                stat = stats_by_email.get(email)
                online = None
                ip_count_value = None
                last_online_epoch = None

                if isinstance(stat, dict):
                    for key in ("online", "isOnline", "is_online"):
                        if key in stat:
                            online = self._as_bool(stat.get(key))
                            break
                    if online is None:
                        ip_count = stat.get("ipCount", stat.get("ip_count"))
                        if ip_count is not None:
                            try:
                                ip_count_value = max(0, int(ip_count))
                                online = ip_count_value > 0
                            except Exception:
                                online = None
                                ip_count_value = None
                    for key in ("lastOnlineTime", "lastOnline", "last_online", "lastSeen", "last_seen"):
                        if key in stat:
                            last_online_epoch = self._as_epoch_seconds(stat.get(key))
                            if last_online_epoch is not None:
                                break

                if online is None and email:
                    if not online_emails_fetched:
                        online_emails_fetched, online_emails = await self._get_online_emails()
                    if online_emails_fetched:
                        online = email in online_emails
                if online is None and last_online_epoch is not None:
                    recent_sec = max(15, self._to_int(os.getenv("PANEL_ONLINE_RECENT_SECONDS"), 90))
                    online = (int(datetime.now(timezone.utc).timestamp()) - int(last_online_epoch)) <= recent_sec

                if online is not True or not email:
                    continue
                online_keys.add(email)
                online_connections_by_email[email] = max(
                    int(online_connections_by_email.get(email, 0)),
                    max(1, int(ip_count_value or 1)),
                )

        return {
            "online_keys_now": int(len(online_keys)),
            "online_connections_now": int(sum(online_connections_by_email.values())),
        }

    async def get_node_online_clients(self) -> list[dict]:
        """
        Return bounded live online client rows for operator aggregates.

        The payload deliberately exposes connection counts and identifiers only;
        raw source IP addresses stay in the per-user observer/admin card.
        """
        inbounds = self._selected_inbounds(await self._get_inbounds())
        if not inbounds:
            return []
        online_emails_fetched = False
        online_emails: set[str] = set()
        rows: list[dict] = []
        seen: set[tuple[int, str]] = set()

        for target_inbound in inbounds:
            inbound_id = int(target_inbound.get("id") or 0)
            settings = self._decode_settings(target_inbound.get("settings", "{}"))
            clients = settings.get("clients", []) or []
            stats_by_email: dict[str, dict] = {}
            for stat in target_inbound.get("clientStats", []) or []:
                email = str((stat or {}).get("email", "") or "").strip()
                if email:
                    stats_by_email[email] = dict(stat or {})

            for client in clients:
                item = dict(client or {})
                email = str(item.get("email", "") or "").strip()
                if not email:
                    continue
                identity = (inbound_id, email)
                if identity in seen:
                    continue
                stat = stats_by_email.get(email)
                online = None
                ip_count_value = None
                last_online_epoch = None

                if isinstance(stat, dict):
                    for key in ("online", "isOnline", "is_online"):
                        if key in stat:
                            online = self._as_bool(stat.get(key))
                            break
                    ip_count = stat.get("ipCount", stat.get("ip_count"))
                    if ip_count is not None:
                        try:
                            ip_count_value = max(0, int(ip_count))
                            if online is None:
                                online = ip_count_value > 0
                        except Exception:
                            ip_count_value = None
                    for key in ("lastOnlineTime", "lastOnline", "last_online", "lastSeen", "last_seen"):
                        if key in stat:
                            last_online_epoch = self._as_epoch_seconds(stat.get(key))
                            if last_online_epoch is not None:
                                break

                if online is None:
                    if not online_emails_fetched:
                        online_emails_fetched, online_emails = await self._get_online_emails()
                    if online_emails_fetched:
                        online = email in online_emails
                if online is None and last_online_epoch is not None:
                    recent_sec = max(15, self._to_int(os.getenv("PANEL_ONLINE_RECENT_SECONDS"), 90))
                    online = (int(datetime.now(timezone.utc).timestamp()) - int(last_online_epoch)) <= recent_sec

                if online is not True:
                    continue
                seen.add(identity)
                last_online_at = None
                last_online_age_seconds = None
                if last_online_epoch is not None:
                    dt = datetime.fromtimestamp(last_online_epoch, tz=timezone.utc)
                    last_online_at = dt.isoformat().replace("+00:00", "Z")
                    last_online_age_seconds = max(0, int(datetime.now(timezone.utc).timestamp()) - int(last_online_epoch))
                tg_id = None
                try:
                    raw_tg_id = str(item.get("tgId", "") or "").strip()
                    if raw_tg_id.lstrip("-").isdigit():
                        tg_id = int(raw_tg_id)
                except Exception:
                    tg_id = None
                rows.append(
                    {
                        "node_code": str(self.node.code or ""),
                        "node_name": str(getattr(self.node, "name", "") or ""),
                        "node_host": str(getattr(self.node, "host", "") or ""),
                        "inbound_id": inbound_id,
                        "tg_id": tg_id,
                        "panel_email": email,
                        "client_uuid": str(item.get("id", "") or ""),
                        "enabled": bool(item.get("enable", True)),
                        "ip_count": max(1, int(ip_count_value or 1)),
                        "up": int((stat or {}).get("up", 0) or 0) if isinstance(stat, dict) else 0,
                        "down": int((stat or {}).get("down", 0) or 0) if isinstance(stat, dict) else 0,
                        "last_online_at": last_online_at,
                        "last_online_age_seconds": last_online_age_seconds,
                    }
                )
        return rows

    async def add_client(
        self,
        *,
        client_uuid: str,
        email: str,
        tg_id: int,
        sub_id: str,
        enable: bool = True,
        total_gb: int = 0,
        expiry_time: int = 0,
        flow: str,
        inbound_id: int | None = None,
        total_bytes_override: int | None = None,
        limit_ip_override: int | None = None,
    ) -> bool:
        target_inbound_id = int(inbound_id or self.node.inbound_id or 0)
        if target_inbound_id <= 0:
            return False

        if not self.cookies:
            ok = await self.login()
            if not ok:
                return False
        await self.ensure_session()

        # Control policies are node-based:
        # - free node(s): strict device + traffic caps
        # - paid node(s): higher device cap, unlimited traffic by default
        limit_ip = self._limit_ip_policy() if limit_ip_override is None else max(0, int(limit_ip_override))
        total_gb_bytes = (
            self._total_bytes_policy()
            if total_bytes_override is None
            else max(0, int(total_bytes_override))
        )

        client_obj = {
            "id": client_uuid,
            "email": email,
            "flow": self._client_flow_value(flow, self.node.flow or ""),
            "totalGB": total_gb_bytes,
            "expiryTime": 0,
            "subId": sub_id,
            "tgId": str(tg_id),
            "enable": enable,
            "limitIp": limit_ip,
            "reset": 0,
        }
        payload = {"id": target_inbound_id, "settings": json.dumps({"clients": [client_obj]})}
        try:
            async with self.session.post(
                f"{self._base()}/panel/api/inbounds/addClient",
                json=payload,
                headers=await self._csrf_headers(),
                cookies=self.cookies,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status == 404:
                    return await self._add_client_modern(
                        client_obj=client_obj,
                        inbound_id=target_inbound_id,
                    )
                if resp.status != 200:
                    logger.warning(
                        "add_client legacy endpoint failed status=%s node=%s inbound=%s",
                        resp.status,
                        self.node.code,
                        target_inbound_id,
                    )
                    return False
                data = await resp.json()
                ok = bool(data.get("success"))
                if not ok:
                    logger.warning(
                        "add_client legacy endpoint returned false node=%s inbound=%s msg=%s",
                        self.node.code,
                        target_inbound_id,
                        str(data.get("msg") or "")[:200],
                    )
                return ok
        except Exception as e:
            logger.exception("add_client error node=%s: %s", self.node.code, e)
            return False

    async def _add_client_modern(self, *, client_obj: dict, inbound_id: int) -> bool:
        """
        3x-ui React builds moved client creation from the legacy
        /panel/api/inbounds/addClient endpoint to /panel/api/clients/add.
        Keep the legacy path as the first try so older x-ui nodes continue to
        work, and fall back here when a newer panel returns 404.
        """
        payload = {
            "client": {
                "email": client_obj.get("email", ""),
                "subId": client_obj.get("subId", ""),
                "id": client_obj.get("id", ""),
                "password": client_obj.get("password", ""),
                "auth": client_obj.get("auth", ""),
                "flow": client_obj.get("flow", ""),
                "totalGB": client_obj.get("totalGB", 0),
                "expiryTime": client_obj.get("expiryTime", 0),
                "reset": client_obj.get("reset", 0),
                "limitIp": client_obj.get("limitIp", 0),
                "tgId": self._to_int(str(client_obj.get("tgId", "") or ""), 0),
                "group": client_obj.get("group", ""),
                "comment": client_obj.get("comment", ""),
                "enable": bool(client_obj.get("enable", True)),
            },
            "inboundIds": [int(inbound_id)],
        }
        try:
            async with self.session.post(
                f"{self._base()}/panel/api/clients/add",
                json=payload,
                headers=await self._csrf_headers(),
                cookies=self.cookies,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "add_client modern endpoint failed status=%s node=%s inbound=%s",
                        resp.status,
                        self.node.code,
                        inbound_id,
                    )
                    return False
                data = await resp.json(content_type=None)
                ok = bool(data.get("success")) if isinstance(data, dict) else False
                if not ok:
                    logger.warning(
                        "add_client modern endpoint returned false node=%s inbound=%s msg=%s",
                        self.node.code,
                        inbound_id,
                        str((data or {}).get("msg") if isinstance(data, dict) else "")[:200],
                    )
                return ok
        except Exception as e:
            logger.exception("add_client modern endpoint error node=%s: %s", self.node.code, e)
            return False

    async def update_client_enable(
        self,
        client: dict,
        enable: bool,
        sub_id: str | None = None,
        hard_cap_gb_override: int | None = None,
        inbound_id: int | None = None,
        flow: str | None = None,
        total_bytes_override: int | None = None,
        limit_ip_override: int | None = None,
        lookup_client_uuid: str | None = None,
    ) -> bool:
        if not self.cookies:
            ok = await self.login()
            if not ok:
                return False
        await self.ensure_session()

        limit_ip = self._limit_ip_policy() if limit_ip_override is None else max(0, int(limit_ip_override))
        if total_bytes_override is not None:
            total_gb_bytes = max(0, int(total_bytes_override))
        elif hard_cap_gb_override is None:
            total_gb_bytes = self._total_bytes_policy()
        else:
            hard_cap_gb = max(0, int(hard_cap_gb_override or 0))
            total_gb_bytes = int(hard_cap_gb) * 1024 * 1024 * 1024 if hard_cap_gb > 0 else 0

        # Keep expiry controlled by control-plane DB; keep traffic/device policies in panel.
        updated = {
            "id": client.get("id"),
            "email": client.get("email"),
            "flow": self._client_flow_value(flow, client.get("flow") or self.node.flow or ""),
            "totalGB": total_gb_bytes,
            "expiryTime": 0,
            "subId": str(sub_id or client.get("subId", "") or ""),
            "tgId": client.get("tgId", ""),
            "enable": enable,
            "limitIp": limit_ip,
            "reset": client.get("reset", 0),
        }
        if not updated.get("id"):
            return False
        if client.get("comment"):
            updated["comment"] = client["comment"]

        target_inbound_id = int(inbound_id or client.get("_panel_inbound_id") or self.node.inbound_id or 0)
        if target_inbound_id <= 0:
            return False
        payload = {"id": target_inbound_id, "settings": json.dumps({"clients": [updated]})}
        lookup_uuid = str(lookup_client_uuid or updated["id"] or "").strip()
        if not lookup_uuid:
            return False
        try:
            async with self.session.post(
                f"{self._base()}/panel/api/inbounds/updateClient/{quote(lookup_uuid, safe='')}",
                json=payload,
                headers=await self._csrf_headers(),
                cookies=self.cookies,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status == 404:
                    return await self._update_client_modern(
                        updated=updated,
                        inbound_id=target_inbound_id,
                    )
                if resp.status != 200:
                    logger.warning(
                        "update_client legacy endpoint failed status=%s node=%s inbound=%s",
                        resp.status,
                        self.node.code,
                        target_inbound_id,
                    )
                    return False
                data = await resp.json()
                ok = bool(data.get("success"))
                if not ok:
                    logger.warning(
                        "update_client legacy endpoint returned false node=%s inbound=%s msg=%s",
                        self.node.code,
                        target_inbound_id,
                        str(data.get("msg") or "")[:200],
                    )
                return ok
        except Exception as e:
            logger.exception("update_client_enable error node=%s: %s", self.node.code, e)
            return False

    async def _update_client_modern(self, *, updated: dict, inbound_id: int) -> bool:
        email = str(updated.get("email", "") or "").strip()
        if not email:
            return False
        payload = {
            "email": email,
            "subId": str(updated.get("subId", "") or ""),
            "id": str(updated.get("id", "") or ""),
            "password": str(updated.get("password", "") or ""),
            "auth": str(updated.get("auth", "") or ""),
            "flow": str(updated.get("flow", "") or ""),
            "totalGB": int(updated.get("totalGB", 0) or 0),
            "expiryTime": int(updated.get("expiryTime", 0) or 0),
            "reset": int(updated.get("reset", 0) or 0),
            "limitIp": int(updated.get("limitIp", 0) or 0),
            "tgId": self._to_int(str(updated.get("tgId", "") or ""), 0),
            "group": str(updated.get("group", "") or ""),
            "comment": str(updated.get("comment", "") or ""),
            "enable": bool(updated.get("enable", True)),
            "inboundIds": [int(inbound_id)],
        }
        try:
            async with self.session.post(
                f"{self._base()}/panel/api/clients/update/{quote(email, safe='')}",
                json=payload,
                headers=await self._csrf_headers(),
                cookies=self.cookies,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "update_client modern endpoint failed status=%s node=%s inbound=%s",
                        resp.status,
                        self.node.code,
                        inbound_id,
                    )
                    return False
                data = await resp.json(content_type=None)
                ok = bool(data.get("success")) if isinstance(data, dict) else False
                if not ok:
                    logger.warning(
                        "update_client modern endpoint returned false node=%s inbound=%s msg=%s",
                        self.node.code,
                        inbound_id,
                        str((data or {}).get("msg") if isinstance(data, dict) else "")[:200],
                    )
                return ok
        except Exception as e:
            logger.exception("update_client modern endpoint error node=%s: %s", self.node.code, e)
            return False

    async def _reset_client_traffic_by_email(self, *, email: str, inbound_id: int | None = None) -> bool:
        """
        Try known 3x-ui API paths for traffic reset.
        Different panel builds expose different routes.
        """
        if not email:
            return False
        if not self.cookies:
            ok = await self.login()
            if not ok:
                return False
        await self.ensure_session()
        encoded_email = quote(str(email), safe="")
        target_inbound_id = int(inbound_id or self.node.inbound_id or 0)
        if target_inbound_id <= 0:
            return False
        paths = [
            f"/panel/api/inbounds/{target_inbound_id}/resetClientTraffic/{encoded_email}",
            f"/panel/api/inbounds/resetClientTraffic/{encoded_email}",
        ]
        for path in paths:
            try:
                async with self.session.post(
                    f"{self._base()}{path}",
                    headers=await self._csrf_headers(),
                    cookies=self.cookies,
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json(content_type=None)
                    if isinstance(data, dict) and bool(data.get("success")):
                        return True
            except Exception:
                continue
        return False

    async def _update_client_with_reset_flag(
        self,
        client: dict,
        *,
        inbound_id: int | None = None,
        flow: str | None = None,
    ) -> bool:
        """
        Fallback path when explicit reset endpoint is unavailable.
        """
        if not self.cookies:
            ok = await self.login()
            if not ok:
                return False
        await self.ensure_session()

        limit_ip = self._limit_ip_policy()
        total_gb_bytes = self._total_bytes_policy()
        updated = {
            "id": client.get("id"),
            "email": client.get("email"),
            "flow": self._client_flow_value(flow, client.get("flow") or self.node.flow or ""),
            "totalGB": total_gb_bytes,
            "expiryTime": 0,
            "subId": client.get("subId", ""),
            "tgId": client.get("tgId", ""),
            "enable": bool(client.get("enable", True)),
            "limitIp": limit_ip,
            # Some x-ui builds reset counters when this marker changes.
            "reset": int(time.time() * 1000),
        }
        if client.get("comment"):
            updated["comment"] = client["comment"]
        target_inbound_id = int(inbound_id or client.get("_panel_inbound_id") or self.node.inbound_id or 0)
        if target_inbound_id <= 0:
            return False
        payload = {"id": target_inbound_id, "settings": json.dumps({"clients": [updated]})}
        try:
            async with self.session.post(
                f"{self._base()}/panel/api/inbounds/updateClient/{updated['id']}",
                json=payload,
                headers=await self._csrf_headers(),
                cookies=self.cookies,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    return False
                data = await resp.json(content_type=None)
                return bool((data or {}).get("success"))
        except Exception:
            return False

    async def reset_client_traffic_by_tgid(self, tg_id: int) -> bool:
        matches = await self.find_clients_by_tgid(int(tg_id))
        if not matches:
            return False
        ok_all = True
        for inbound_id, client in matches:
            email = str(client.get("email") or "").strip()
            if await self._reset_client_traffic_by_email(email=email, inbound_id=inbound_id):
                continue
            flow = self._managed_flow_for_inbound(inbound_id)
            ok = await self._update_client_with_reset_flag(client, inbound_id=inbound_id, flow=flow)
            ok_all = ok_all and ok
        return ok_all

    async def _delete_client_from_inbound(self, *, inbound_id: int, client_uuid: str) -> bool:
        if not self.cookies:
            ok = await self.login()
            if not ok:
                return False
        await self.ensure_session()
        try:
            async with self.session.post(
                f"{self._base()}/panel/api/inbounds/{int(inbound_id)}/delClient/{client_uuid}",
                headers=await self._csrf_headers(),
                cookies=self.cookies,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    return False
                data = await resp.json()
                return bool(data.get("success"))
        except Exception as e:
            logger.exception(
                "delete_client_from_inbound error node=%s inbound_id=%s: %s",
                self.node.code,
                inbound_id,
                e,
            )
            return False

    async def _cleanup_cross_inbound_conflicts(
        self,
        *,
        tg_id: int,
        email: str,
        preserve_inbound_ids: set[int] | None = None,
    ) -> bool:
        """
        3x-ui enforces unique email per node (not only per inbound).
        If a user was moved between plan inbounds (e.g. pl_free -> pl), stale records
        in another inbound can block addClient with "Duplicate email".
        """
        inbounds = await self._get_inbounds()
        preserved = {int(x) for x in (preserve_inbound_ids or set()) if int(x) > 0}
        to_delete: list[tuple[int, str]] = []

        for inb in inbounds:
            inb_id = int(inb.get("id") or 0)
            if inb_id <= 0 or inb_id in preserved:
                continue
            settings = self._decode_settings(inb.get("settings", "{}"))
            clients = settings.get("clients", []) or []
            for c in clients:
                c_id = str(c.get("id") or "").strip()
                if not c_id:
                    continue
                c_tg = str(c.get("tgId", "")).strip()
                c_email = str(c.get("email", "")).strip()
                if c_tg == str(tg_id).strip() or (email and c_email == email):
                    to_delete.append((inb_id, c_id))

        if not to_delete:
            return True

        ok_all = True
        for inb_id, client_uuid in to_delete:
            ok = await self._delete_client_from_inbound(inbound_id=inb_id, client_uuid=client_uuid)
            ok_all = ok_all and ok
            if ok:
                logger.info(
                    "cleaned cross-inbound conflict node=%s from_inbound=%s client_uuid=%s",
                    self.node.code,
                    inb_id,
                    client_uuid,
                )
            else:
                logger.warning(
                    "failed to clean cross-inbound conflict node=%s from_inbound=%s client_uuid=%s",
                    self.node.code,
                    inb_id,
                    client_uuid,
                )
        return ok_all

    async def ensure_client(
        self,
        *,
        tg_id: int,
        client_uuid: str,
        email: str,
        sub_id: str,
        enable: bool,
    ) -> bool:
        """
        Idempotent: if client exists, just toggle enable; otherwise add.
        """
        target_inbound_ids = self._managed_inbound_ids()
        if not target_inbound_ids:
            target_inbound_ids = [int(self.node.inbound_id or 0)]
        target_inbound_ids = [x for x in target_inbound_ids if int(x) > 0]
        if not target_inbound_ids:
            return False

        existing_by_inbound: dict[int, dict] = {
            inbound_id: client
            for inbound_id, client in await self.find_clients_by_identity(
                tg_id=tg_id,
                client_uuid=client_uuid,
                email=email,
            )
        }
        ok_all = True
        attempted_add = False

        for inbound_id in target_inbound_ids:
            existing = existing_by_inbound.get(inbound_id)
            flow = self._managed_flow_for_inbound(inbound_id)
            if existing:
                existing = dict(existing)
                if email:
                    existing["email"] = email
                if client_uuid:
                    existing["id"] = client_uuid
                existing["tgId"] = str(tg_id)
                try:
                    ok = await self.update_client_enable(
                        existing,
                        enable,
                        sub_id=sub_id,
                        inbound_id=inbound_id,
                        flow=flow,
                    )
                except TypeError:
                    ok = await self.update_client_enable(existing, enable, sub_id=sub_id)
                ok_all = ok_all and ok
                continue
            attempted_add = True
            ok = await self.add_client(
                client_uuid=client_uuid,
                email=email,
                tg_id=tg_id,
                sub_id=sub_id,
                enable=enable,
                flow=flow,
                inbound_id=inbound_id,
            )
            ok_all = ok_all and ok

        cleanup_ok = True
        if attempted_add or len(target_inbound_ids) > 1:
            try:
                cleanup_ok = await self._cleanup_cross_inbound_conflicts(
                    tg_id=tg_id,
                    email=email,
                    preserve_inbound_ids=set(target_inbound_ids),
                )
            except TypeError:
                cleanup_ok = await self._cleanup_cross_inbound_conflicts(tg_id=tg_id, email=email)
            ok_all = ok_all and cleanup_ok
        if ok_all:
            return True

        if not attempted_add:
            return False

        try:
            cleanup_retry_ok = await self._cleanup_cross_inbound_conflicts(
                tg_id=tg_id,
                email=email,
                preserve_inbound_ids=set(target_inbound_ids),
            )
        except TypeError:
            cleanup_retry_ok = await self._cleanup_cross_inbound_conflicts(tg_id=tg_id, email=email)
        retry_ok = True
        for inbound_id in target_inbound_ids:
            if inbound_id in existing_by_inbound:
                continue
            flow = self._managed_flow_for_inbound(inbound_id)
            ok = await self.add_client(
                client_uuid=client_uuid,
                email=email,
                tg_id=tg_id,
                sub_id=sub_id,
                enable=enable,
                flow=flow,
                inbound_id=inbound_id,
            )
            retry_ok = retry_ok and ok
        return cleanup_retry_ok and retry_ok

    async def ensure_client_explicit(
        self,
        *,
        tg_id: int,
        client_uuid: str,
        email: str,
        sub_id: str,
        enable: bool,
        inbound_id: int,
        total_bytes: int,
        limit_ip: int,
    ) -> bool:
        """Ensure exactly one role-bound inbound without deleting the source profile."""
        target_inbound_id = int(inbound_id or 0)
        if target_inbound_id <= 0:
            return False
        existing_by_inbound = {
            int(found_inbound): dict(client or {})
            for found_inbound, client in await self.find_clients_by_identity(
                tg_id=int(tg_id),
                client_uuid=str(client_uuid or ""),
                email=str(email or ""),
            )
        }
        existing = existing_by_inbound.get(target_inbound_id)
        flow = self._managed_flow_for_inbound(target_inbound_id)
        if existing is not None:
            existing_uuid = str(existing.get("id") or "").strip()
            existing["id"] = str(client_uuid or existing.get("id") or "")
            existing["email"] = str(email or existing.get("email") or "")
            existing["tgId"] = str(int(tg_id))
            return bool(
                await self.update_client_enable(
                    existing,
                    bool(enable),
                    sub_id=str(sub_id or ""),
                    inbound_id=target_inbound_id,
                    flow=flow,
                    total_bytes_override=max(0, int(total_bytes)),
                    limit_ip_override=max(0, int(limit_ip)),
                    lookup_client_uuid=existing_uuid,
                )
            )
        return bool(
            await self.add_client(
                client_uuid=str(client_uuid or ""),
                email=str(email or ""),
                tg_id=int(tg_id),
                sub_id=str(sub_id or ""),
                enable=bool(enable),
                flow=flow,
                inbound_id=target_inbound_id,
                total_bytes_override=max(0, int(total_bytes)),
                limit_ip_override=max(0, int(limit_ip)),
            )
        )

    async def confirm_client_profile(
        self,
        *,
        tg_id: int,
        client_uuid: str,
        email: str,
        inbound_id: int,
        total_bytes: int,
        limit_ip: int,
        enabled: bool,
    ) -> bool:
        target_inbound_id = int(inbound_id or 0)
        if target_inbound_id <= 0:
            return False
        rows = await self.find_clients_by_identity(
            tg_id=int(tg_id),
            client_uuid=str(client_uuid or ""),
            email=str(email or ""),
            include_disabled=True,
        )
        for found_inbound, raw in rows:
            if int(found_inbound or 0) != target_inbound_id:
                continue
            client = dict(raw or {})
            if str(client.get("id") or "").strip() != str(client_uuid or "").strip():
                continue
            if str(client.get("tgId") or "").strip() != str(int(tg_id)):
                continue
            if bool(client.get("enable", True)) is not bool(enabled):
                continue
            if int(client.get("totalGB") or 0) != max(0, int(total_bytes)):
                continue
            if int(client.get("limitIp") or 0) != max(0, int(limit_ip)):
                continue
            return True
        return False

    async def delete_client_uuid(self, client_uuid: str) -> bool:
        if not self.cookies:
            ok = await self.login()
            if not ok:
                return False
        await self.ensure_session()

        target_uuid = str(client_uuid or "").strip()
        matched_emails: list[str] = []
        if target_uuid:
            try:
                for inb in self._selected_inbounds(await self._get_inbounds(), include_disabled=True):
                    settings = self._decode_settings(inb.get("settings", "{}"))
                    for client in settings.get("clients", []) or []:
                        if str((client or {}).get("id", "") or "").strip() != target_uuid:
                            continue
                        email = str((client or {}).get("email", "") or "").strip()
                        if email and email not in matched_emails:
                            matched_emails.append(email)
            except Exception as e:
                logger.exception("delete_client_uuid lookup error node=%s: %s", self.node.code, e)

        if matched_emails:
            ok_all = True
            ok_any = False
            for email in matched_emails:
                ok = await self.delete_client_email(email)
                ok_any = ok_any or ok
                ok_all = ok_all and ok
            if ok_any and ok_all:
                return True

        if not target_uuid:
            return False

        ok_any = False
        for inbound_id in self._managed_inbound_ids(include_disabled=True):
            try:
                async with self.session.post(
                    f"{self._base()}/panel/api/inbounds/{inbound_id}/delClient/{target_uuid}",
                    headers=await self._csrf_headers(),
                    cookies=self.cookies,
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    ok = bool(data.get("success"))
                    ok_any = ok_any or ok
            except Exception as e:
                logger.exception("delete_client error node=%s inbound_id=%s: %s", self.node.code, inbound_id, e)
        return ok_any

    async def delete_client_email(self, email: str, *, keep_traffic: bool = False) -> bool:
        clean_email = str(email or "").strip()
        if not clean_email:
            return False
        if not self.cookies:
            ok = await self.login()
            if not ok:
                return False
        await self.ensure_session()
        query = "?keepTraffic=1" if keep_traffic else ""
        try:
            async with self.session.post(
                f"{self._base()}/panel/api/clients/del/{quote(clean_email, safe='')}{query}",
                headers=await self._csrf_headers(),
                cookies=self.cookies,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    return False
                data = await resp.json()
                return bool(data.get("success"))
        except Exception as e:
            logger.exception("delete_client_email error node=%s email=%s: %s", self.node.code, clean_email, e)
            return False

    async def update_client_comment_by_tgid(self, tg_id: int, comment: str) -> bool:
        matches = await self.find_clients_by_tgid(tg_id)
        if not matches:
            return False
        ok_all = True
        for inbound_id, client in matches:
            updated = dict(client)
            updated["comment"] = comment
            flow = self._managed_flow_for_inbound(inbound_id)
            ok = await self.update_client_enable(
                updated,
                updated.get("enable", True),
                inbound_id=inbound_id,
                flow=flow,
            )
            ok_all = ok_all and ok
        return ok_all
