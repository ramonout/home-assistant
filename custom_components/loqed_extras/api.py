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
        # Without Accept: application/json the server answers auth failures with a
        # redirect to its HTML login page instead of a 401.
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

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
            body = await resp.read()
            if not body:
                return None
            try:
                # content_type=None: accept variants such as application/vnd.api+json
                return await resp.json(content_type=None)
            except ValueError:
                if method == "get":
                    raise aiohttp.ClientError(
                        f"Non-JSON response ({resp.content_type}): {body[:200]!r}"
                    ) from None
                return None

    async def async_get_locks(self) -> list[dict[str, Any]]:
        """Return all locks of the account."""
        payload = await self._request("get", "api/locks/")
        locks = payload.get("data") if isinstance(payload, dict) else payload
        if not isinstance(locks, list):
            raise aiohttp.ClientError(f"Unexpected locks payload: {payload!r:.200}")
        return locks

    async def async_set_setting(self, lock_id: str, name: str, value: int) -> None:
        """Change a single lock setting (signed 32-bit integer value)."""
        await self._request(
            "post",
            f"api/locks/{lock_id}/setting",
            json={"setting_name": name, "setting_value": value},
        )
