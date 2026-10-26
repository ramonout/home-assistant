"""Minimal client for the LOQED cloud integrations API."""

from __future__ import annotations

from typing import Any

import aiohttp

from .const import CLOUD_BASE_URL


class LoqedAuthError(Exception):
    """The personal access token was rejected."""


class LoqedCloudClient:
    """Talk to https://integrations.production.loqed.com."""

    def __init__(self, session: aiohttp.ClientSession, token: str) -> None:
        self._session = session
        self._headers = {"Authorization": f"Bearer {token}"}

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        async with self._session.request(
            method,
            f"{CLOUD_BASE_URL}/{path}",
            headers=self._headers,
            timeout=aiohttp.ClientTimeout(total=15),
            **kwargs,
        ) as resp:
            if resp.status in (401, 403):
                raise LoqedAuthError
            resp.raise_for_status()
            if resp.content_type == "application/json":
                return await resp.json()
            return None

    async def async_get_locks(self) -> list[dict[str, Any]]:
        """Return all locks of the account."""
        return (await self._request("get", "api/locks/"))["data"]

    async def async_set_setting(self, lock_id: str, name: str, value: int) -> None:
        """Change a single lock setting (signed 32-bit integer value)."""
        await self._request(
            "post",
            f"api/locks/{lock_id}/setting",
            json={"setting_name": name, "setting_value": value},
        )
