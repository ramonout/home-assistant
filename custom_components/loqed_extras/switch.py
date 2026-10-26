"""Open House Mode switch."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import LoqedAuthError
from .const import (
    CORE_LOQED_DOMAIN,
    DOMAIN,
    OPEN_HOUSE_STATE_KEYS,
    SETTING_OPEN_HOUSE_MODE,
)
from .coordinator import LoqedExtrasConfigEntry, LoqedExtrasCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LoqedExtrasConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the switch."""
    async_add_entities([OpenHouseModeSwitch(hass, entry.runtime_data)])


class OpenHouseModeSwitch(CoordinatorEntity[LoqedExtrasCoordinator], SwitchEntity):
    """Switch for LOQED Open House Mode (Dutch: touwtje uit de brievenbus)."""

    _attr_has_entity_name = True
    _attr_translation_key = "open_house_mode"
    _attr_icon = "mdi:door-open"

    def __init__(self, hass: HomeAssistant, coordinator: LoqedExtrasCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.lock_id}_{SETTING_OPEN_HOUSE_MODE}"
        self._attr_device_info = self._device_info(hass, coordinator)
        self._optimistic: bool | None = None

    @staticmethod
    def _device_info(hass: HomeAssistant, coordinator: LoqedExtrasCoordinator) -> DeviceInfo:
        """Attach to the core LOQED device when it can be matched, else own device."""
        for core in hass.config_entries.async_entries(CORE_LOQED_DOMAIN):
            if core.data.get("id") == coordinator.lock_id and core.unique_id:
                return DeviceInfo(identifiers={(CORE_LOQED_DOMAIN, core.unique_id)})
        return DeviceInfo(
            identifiers={(DOMAIN, coordinator.lock_id)},
            manufacturer="LOQED",
            name=coordinator.data.get("name", "LOQED lock"),
        )

    @property
    def is_on(self) -> bool | None:
        """Return the mode state."""
        for key in OPEN_HOUSE_STATE_KEYS:
            if key in self.coordinator.data:
                return bool(self.coordinator.data[key])
        # Not reported by the list endpoint: fall back to the last value we set.
        return self._optimistic

    async def _async_set(self, value: bool) -> None:
        try:
            await self.coordinator.client.async_set_setting(
                self.coordinator.lock_id, SETTING_OPEN_HOUSE_MODE, int(value)
            )
        except LoqedAuthError as err:
            self.coordinator.config_entry.async_start_reauth(self.hass)
            raise HomeAssistantError("LOQED token rejected") from err
        except (aiohttp.ClientError, TimeoutError) as err:
            raise HomeAssistantError(f"Failed to set open house mode: {err}") from err
        self._optimistic = value
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable open house mode."""
        await self._async_set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable open house mode."""
        await self._async_set(False)
