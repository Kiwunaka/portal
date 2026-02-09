from __future__ import annotations

import json
import logging
from dataclasses import dataclass
import os

import aiohttp

from nodes_repo import NodeRuntime


logger = logging.getLogger(__name__)


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
        Free default: 2 devices.
        Paid default: 5 devices.
        """
        if self._is_free_node():
            return max(
                0,
                self._node_or_global_int(
                    node_suffix="LIMIT_IP",
                    global_name="FREE_LIMIT_IP",
                    default=2,
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
        Free default: 40 GB.
        Paid: always unlimited (0).
        """
        if self._is_free_node():
            return max(
                0,
                self._node_or_global_int(
                    node_suffix="TOTAL_GB",
                    global_name="FREE_TOTAL_GB",
                    default=40,
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

    async def update_client_enable(self, client: dict, enable: bool) -> bool:
        if not self.cookies:
            ok = await self.login()
            if not ok:
                return False
        await self.ensure_session()

        limit_ip = self._limit_ip_policy()
        total_gb_bytes = self._total_bytes_policy()

        # Keep expiry controlled by control-plane DB; keep traffic/device policies in panel.
        updated = {
            "id": client.get("id"),
            "email": client.get("email"),
            "flow": client.get("flow", self.node.flow),
            "totalGB": total_gb_bytes,
            "expiryTime": 0,
            "subId": client.get("subId", ""),
            "tgId": client.get("tgId", ""),
            "enable": enable,
            "limitIp": limit_ip,
            "reset": client.get("reset", 0),
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
                data = await resp.json()
                return bool(data.get("success"))
        except Exception as e:
            logger.exception("update_client_enable error node=%s: %s", self.node.code, e)
            return False

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
            return await self.update_client_enable(existing, enable)
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
