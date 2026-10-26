"""Data coordinator for LOQED Extras."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LoqedAuthError, LoqedCloudClient
from .const import CONF_LOCK_ID, DOMAIN, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)

type LoqedExtrasConfigEntry = ConfigEntry[LoqedExtrasCoordinator]


class LoqedExtrasCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll the cloud API for the settings of one lock."""

    config_entry: LoqedExtrasConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: LoqedExtrasConfigEntry,
        client: LoqedCloudClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        self.client = client
        self.lock_id: str = entry.data[CONF_LOCK_ID]

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            locks = await self.client.async_get_locks()
        except LoqedAuthError as err:
            raise ConfigEntryAuthFailed from err
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Error talking to LOQED cloud: {err}") from err
        for lock in locks:
            if lock["id"] == self.lock_id:
                _LOGGER.debug("Lock payload: %s", lock)
                return lock
        raise UpdateFailed(f"Lock {self.lock_id} not found in LOQED account")
