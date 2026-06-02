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
        return "free" in (self.node.code or "").lower()

    def _limit_ip_policy(self) -> int:
        """
        Per-node device policy.
        Free default: 1 device.
        Paid default: 5 devices.
        """
        if self._is_free_node():
            return max(
                0,
                self._node_or_global_int(
                    node_suffix="LIMIT_IP",
                    global_name="FREE_LIMIT_IP",
                    default=1,
                ),
            )
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
        Free default: 5 GB.
        Paid: always unlimited (0).
        """
        if self._is_free_node():
            return max(
                0,
                self._node_or_global_int(
                    node_suffix="TOTAL_GB",
                    global_name="FREE_TOTAL_GB",
                    default=5,
                ),
            )
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
        if not self.csrf_token:
            return {}
        return {"X-CSRF-Token": self.csrf_token}

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
        await self.ensure_session()
        async with self.session.get(
            f"{self._base()}/panel/api/inbounds/list",
            cookies=self.cookies,
            timeout=aiohttp.ClientTimeout(total=20),
        ) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
            if not data.get("success"):
                return []
            return data.get("obj", []) or []

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
    ) -> bool:
        if not self.cookies:
            ok = await self.login()
            if not ok:
                return False
        await self.ensure_session()

        # Control policies are node-based:
        # - free node(s): strict device + traffic caps
        # - paid node(s): higher device cap, unlimited traffic by default
        limit_ip = self._limit_ip_policy()
        total_gb_bytes = self._total_bytes_policy()

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
        target_inbound_id = int(inbound_id or self.node.inbound_id or 0)
        if target_inbound_id <= 0:
            return False
        payload = {"id": target_inbound_id, "settings": json.dumps({"clients": [client_obj]})}
        try:
            async with self.session.post(
                f"{self._base()}/panel/api/inbounds/addClient",
                json=payload,
                headers=await self._csrf_headers(),
                cookies=self.cookies,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    return False
                data = await resp.json()
                return bool(data.get("success"))
        except Exception as e:
            logger.exception("add_client error node=%s: %s", self.node.code, e)
            return False

    async def update_client_enable(
        self,
        client: dict,
        enable: bool,
        sub_id: str | None = None,
        hard_cap_gb_override: int | None = None,
        inbound_id: int | None = None,
        flow: str | None = None,
    ) -> bool:
        if not self.cookies:
            ok = await self.login()
            if not ok:
                return False
        await self.ensure_session()

        limit_ip = self._limit_ip_policy()
        if hard_cap_gb_override is None:
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
                data = await resp.json()
                return bool(data.get("success"))
        except Exception as e:
            logger.exception("update_client_enable error node=%s: %s", self.node.code, e)
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

        existing_by_inbound: dict[int, dict] = {}
        existing_primary = await self.find_client_by_tgid(tg_id)
        if existing_primary:
            primary_inbound_id = int(existing_primary.get("_panel_inbound_id") or target_inbound_ids[0])
            if primary_inbound_id > 0:
                existing_by_inbound[primary_inbound_id] = existing_primary

        using_default_find = getattr(getattr(self, "find_client_by_tgid", None), "__func__", None) is PanelClient.find_client_by_tgid
        if using_default_find and len(target_inbound_ids) > 1:
            existing_by_inbound = {
                inbound_id: client for inbound_id, client in await self.find_clients_by_tgid(tg_id)
            } or existing_by_inbound
        ok_all = True
        attempted_add = False

        for inbound_id in target_inbound_ids:
            existing = existing_by_inbound.get(inbound_id)
            flow = self._managed_flow_for_inbound(inbound_id)
            if existing:
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

    async def delete_client_uuid(self, client_uuid: str) -> bool:
        if not self.cookies:
            ok = await self.login()
            if not ok:
                return False
        await self.ensure_session()
        ok_any = False
        ok_all = True
        for inbound_id in self._managed_inbound_ids(include_disabled=True):
            try:
                async with self.session.post(
                    f"{self._base()}/panel/api/inbounds/{inbound_id}/delClient/{client_uuid}",
                    headers=await self._csrf_headers(),
                    cookies=self.cookies,
                    timeout=aiohttp.ClientTimeout(total=20),
                ) as resp:
                    if resp.status != 200:
                        ok_all = False
                        continue
                    data = await resp.json()
                    ok = bool(data.get("success"))
                    ok_any = ok_any or ok
                    ok_all = ok_all and ok
            except Exception as e:
                logger.exception("delete_client error node=%s inbound_id=%s: %s", self.node.code, inbound_id, e)
                ok_all = False
        return ok_any and ok_all

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
