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


@dataclass
class PanelClient:
    node: NodeRuntime
    session: aiohttp.ClientSession | None = None
    cookies: aiohttp.CookieJar | None = None

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
        Free default: 30 GB.
        Paid: always unlimited (0).
        """
        if self._is_free_node():
            return max(
                0,
                self._node_or_global_int(
                    node_suffix="TOTAL_GB",
                    global_name="FREE_TOTAL_GB",
                    default=30,
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

    async def ensure_session(self) -> None:
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()
            self.session = None
            self.cookies = None

    async def login(self) -> bool:
        await self.ensure_session()
        user = self._env("PANEL_USER") or self.node.panel_user
        pwd = self._env("PANEL_PASS") or self.node.panel_pass
        if not user or not pwd:
            logger.warning("panel credentials missing for node=%s (set %s/%s)", self.node.code, self._env_name("PANEL_USER"), self._env_name("PANEL_PASS"))
            return False
        try:
            async with self.session.post(
                f"{self._base()}/login",
                data={"username": user, "password": pwd},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    logger.warning("panel login failed (status=%s) node=%s", resp.status, self.node.code)
                    return False
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

        mem_used_raw = _deep_find(status, {"memused", "memoryused", "currentmem", "currentmemory", "usedmemory"})
        mem_total_raw = _deep_find(status, {"memtotal", "memorytotal", "totalmem", "totalmemory"})
        disk_used_raw = _deep_find(status, {"diskused", "useddisk", "currdisk"})
        disk_total_raw = _deep_find(status, {"disktotal", "totaldisk"})
        disk_free_raw = _deep_find(status, {"diskfree", "freedisk", "diskavail", "diskavailable"})

        mem_used_bytes = _size_to_bytes(mem_used_raw)
        mem_total_bytes = _size_to_bytes(mem_total_raw)
        disk_used_bytes = _size_to_bytes(disk_used_raw)
        disk_total_bytes = _size_to_bytes(disk_total_raw)
        disk_free_bytes = _size_to_bytes(disk_free_raw)

        return {
            "cpu_percent": round(cpu_percent, 1) if cpu_percent is not None else None,
            "memory_used_mb": int(round(mem_used_bytes / (1024**2))) if mem_used_bytes is not None else None,
            "memory_total_mb": int(round(mem_total_bytes / (1024**2))) if mem_total_bytes is not None else None,
            "disk_used_gb": round(disk_used_bytes / (1024**3), 2) if disk_used_bytes is not None else None,
            "disk_total_gb": round(disk_total_bytes / (1024**3), 2) if disk_total_bytes is not None else None,
            "disk_free_gb": round(disk_free_bytes / (1024**3), 2) if disk_free_bytes is not None else None,
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
        Returns traffic stats from panel clientStats for this node inbound.
        """
        inbounds = await self._get_inbounds()
        for inb in inbounds:
            if inb.get("id") != self.node.inbound_id:
                continue
            for cs in inb.get("clientStats", []) or []:
                if cs.get("email") == email:
                    return {"up": cs.get("up", 0), "down": cs.get("down", 0), "total": cs.get("up", 0) + cs.get("down", 0)}
        return None

    async def find_client_by_tgid(self, tg_id: int) -> dict | None:
        inbounds = await self._get_inbounds()
        for inb in inbounds:
            if inb.get("id") != self.node.inbound_id:
                continue
            settings = json.loads(inb.get("settings", "{}"))
            for c in settings.get("clients", []):
                if str(c.get("tgId", "")).strip() == str(tg_id).strip():
                    return c
        return None

    async def get_client_runtime_by_tgid(self, tg_id: int) -> dict | None:
        """
        Return best-effort runtime snapshot for a client on this node:
        - enable flag from panel client settings
        - traffic counters from clientStats
        - online status when the panel exposes it (field names vary by x-ui versions)
        """
        inbounds = await self._get_inbounds()
        for inb in inbounds:
            if inb.get("id") != self.node.inbound_id:
                continue

            settings = json.loads(inb.get("settings", "{}"))
            clients = settings.get("clients", []) or []
            target = None
            for c in clients:
                if str(c.get("tgId", "")).strip() == str(tg_id).strip():
                    target = c
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
            "flow": flow,
            "totalGB": total_gb_bytes,
            "expiryTime": 0,
            "subId": sub_id,
            "tgId": str(tg_id),
            "enable": enable,
            "limitIp": limit_ip,
            "reset": 0,
        }
        payload = {"id": self.node.inbound_id, "settings": json.dumps({"clients": [client_obj]})}
        try:
            async with self.session.post(
                f"{self._base()}/panel/api/inbounds/addClient",
                json=payload,
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
            "flow": client.get("flow", self.node.flow),
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

        payload = {"id": self.node.inbound_id, "settings": json.dumps({"clients": [updated]})}
        try:
            async with self.session.post(
                f"{self._base()}/panel/api/inbounds/updateClient/{updated['id']}",
                json=payload,
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

    async def _reset_client_traffic_by_email(self, *, email: str) -> bool:
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
        paths = [
            f"/panel/api/inbounds/{int(self.node.inbound_id)}/resetClientTraffic/{encoded_email}",
            f"/panel/api/inbounds/resetClientTraffic/{encoded_email}",
        ]
        for path in paths:
            try:
                async with self.session.post(
                    f"{self._base()}{path}",
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

    async def _update_client_with_reset_flag(self, client: dict) -> bool:
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
            "flow": client.get("flow", self.node.flow),
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
        payload = {"id": self.node.inbound_id, "settings": json.dumps({"clients": [updated]})}
        try:
            async with self.session.post(
                f"{self._base()}/panel/api/inbounds/updateClient/{updated['id']}",
                json=payload,
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
        client = await self.find_client_by_tgid(int(tg_id))
        if not client:
            return False
        email = str(client.get("email") or "").strip()
        if await self._reset_client_traffic_by_email(email=email):
            return True
        return await self._update_client_with_reset_flag(client)

    async def _delete_client_from_inbound(self, *, inbound_id: int, client_uuid: str) -> bool:
        if not self.cookies:
            ok = await self.login()
            if not ok:
                return False
        await self.ensure_session()
        try:
            async with self.session.post(
                f"{self._base()}/panel/api/inbounds/{int(inbound_id)}/delClient/{client_uuid}",
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

    async def _cleanup_cross_inbound_conflicts(self, *, tg_id: int, email: str) -> bool:
        """
        3x-ui enforces unique email per node (not only per inbound).
        If a user was moved between plan inbounds (e.g. pl_free -> pl), stale records
        in another inbound can block addClient with "Duplicate email".
        """
        inbounds = await self._get_inbounds()
        target_inbound = int(self.node.inbound_id)
        to_delete: list[tuple[int, str]] = []

        for inb in inbounds:
            inb_id = int(inb.get("id") or 0)
            if inb_id <= 0 or inb_id == target_inbound:
                continue
            try:
                settings = json.loads(inb.get("settings", "{}"))
            except Exception:
                settings = {}
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
        existing = await self.find_client_by_tgid(tg_id)
        if existing:
            # Always normalize client fields according to current node policy.
            return await self.update_client_enable(existing, enable, sub_id=sub_id)
        # Handle stale records on other inbounds before add (e.g. free->paid transitions).
        await self._cleanup_cross_inbound_conflicts(tg_id=tg_id, email=email)
        ok = await self.add_client(
            client_uuid=client_uuid,
            email=email,
            tg_id=tg_id,
            sub_id=sub_id,
            enable=enable,
            flow=self.node.flow,
        )
        if ok:
            return True

        # One retry after conflict cleanup in case panel side state was stale.
        await self._cleanup_cross_inbound_conflicts(tg_id=tg_id, email=email)
        return await self.add_client(
            client_uuid=client_uuid,
            email=email,
            tg_id=tg_id,
            sub_id=sub_id,
            enable=enable,
            flow=self.node.flow,
        )

    async def delete_client_uuid(self, client_uuid: str) -> bool:
        if not self.cookies:
            ok = await self.login()
            if not ok:
                return False
        await self.ensure_session()
        try:
            async with self.session.post(
                f"{self._base()}/panel/api/inbounds/{self.node.inbound_id}/delClient/{client_uuid}",
                cookies=self.cookies,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    return False
                data = await resp.json()
                return bool(data.get("success"))
        except Exception as e:
            logger.exception("delete_client error node=%s: %s", self.node.code, e)
            return False

    async def update_client_comment_by_tgid(self, tg_id: int, comment: str) -> bool:
        client = await self.find_client_by_tgid(tg_id)
        if not client:
            return False
        client["comment"] = comment
        # Reuse enable update path with same enable state
        return await self.update_client_enable(client, client.get("enable", True))
