"""Config flow for LOQED Extras."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LoqedAuthError, LoqedCloudClient
from .const import CONF_API_TOKEN, CONF_LOCK_ID, DOMAIN

TOKEN_URL = "https://integrations.production.loqed.com/personal-access-tokens"


class LoqedExtrasConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._token: str | None = None
        self._locks: list[dict[str, Any]] = []

    async def _async_fetch_locks(self, token: str) -> str | None:
        """Fetch locks; return an error key or None."""
        client = LoqedCloudClient(async_get_clientsession(self.hass), token)
        try:
            self._locks = await client.async_get_locks()
        except LoqedAuthError:
            return "invalid_auth"
        except (aiohttp.ClientError, TimeoutError):
            return "cannot_connect"
        return None if self._locks else "no_locks"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._token = user_input[CONF_API_TOKEN]
            if error := await self._async_fetch_locks(self._token):
                errors["base"] = error
            elif len(self._locks) == 1:
                return await self._async_create(self._locks[0])
            else:
                return await self.async_step_pick_lock()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_TOKEN): str}),
            description_placeholders={"token_url": TOKEN_URL},
            errors=errors,
        )

    async def async_step_pick_lock(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            lock = next(l for l in self._locks if l["id"] == user_input[CONF_LOCK_ID])
            return await self._async_create(lock)
        return self.async_show_form(
            step_id="pick_lock",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LOCK_ID): vol.In(
                        {l["id"]: l.get("name", l["id"]) for l in self._locks}
                    )
                }
            ),
        )

    async def _async_create(self, lock: dict[str, Any]) -> ConfigFlowResult:
        await self.async_set_unique_id(lock["id"])
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=lock.get("name", "LOQED") + " extras",
            data={CONF_API_TOKEN: self._token, CONF_LOCK_ID: lock["id"]},
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            if error := await self._async_fetch_locks(user_input[CONF_API_TOKEN]):
                errors["base"] = error
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_API_TOKEN: user_input[CONF_API_TOKEN]}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_TOKEN): str}),
            description_placeholders={"token_url": TOKEN_URL},
            errors=errors,
        )
